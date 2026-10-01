from datetime import timedelta, datetime
import calendar
import decimal # 신규추가

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
# from rest_framework.permissions import AllowAny  # 개발 편의, 배포 시 IsAuthenticated 권장
from rest_framework.permissions import IsAuthenticated, AllowAny # 인증된 사용자만 접근
from rest_framework.pagination import PageNumberPagination

# Trade 모델 동적 선택: 기존에 MockTrade가 있으면 우선 사용
try:
    from .models import MockTrade as Trade
except Exception:
    try:
        from .models import PaperTrade as Trade
    except Exception:
        Trade = None  # 모델이 전혀 없는 경우도 대비

def _user_filter(qs, request):
    # user 필드가 있으면 로그인 유저로 필터, 없으면 그대로
    if hasattr(qs.model, 'user_id'):
        if request.user.is_authenticated:
            return qs.filter(user=request.user)
        else:
            # 로그인이 없다면 빈 결과(또는 전체 노출). 로컬 실험용으로 전체 노출하고 싶으면 qs 그대로 반환.
            return qs.none()
    return qs

def _trade_pnl(t):
    # 모델에 pnl 필드가 있으면 그대로, 없으면 계산
    if hasattr(t, 'pnl') and t.pnl is not None:
        return float(t.pnl)
    if hasattr(t, 'realized_pnl'):
        return float(t.realized_pnl)
    # 최소 계산 (entry/exit/qty/side)
    try:
        qty   = float(getattr(t, 'qty', 0) or 0)
        entry = float(getattr(t, 'entry_price', 0) or 0)
        exitp = float(getattr(t, 'exit_price', 0) or 0)
        side  = getattr(t, 'side', 'LONG')
        direction = 1 if side in ('LONG', 'BUY') else -1
        return (exitp - entry) * qty * direction
    except Exception:
        return 0.0

class MyPageSummaryAPI(APIView):
    """
    GET /mypage/summary/
    응답: { total_realized_pnl, cumulative_roi, win_rate, total_trades }
    """
    permission_classes = [AllowAny]

    def get(self, request):
        if not hasattr(Trade, 'objects'):
            return Response({
                "total_realized_pnl": "0.00",
                "cumulative_roi": "0.00",
                "win_rate": "0.00",
                "total_trades": 0
            })

        qs = _user_filter(Trade.objects.all(), request)
        total_trades = qs.count()

        closed = qs.exclude(exit_at__isnull=True)
        total_pnl = 0.0
        wins = 0
        denom = 0.0  # ROI 분모: |entry_price * qty| 합
        for t in closed:
            pnl = _trade_pnl(t)
            total_pnl += pnl
            if pnl > 0:
                wins += 1
            try:
                denom += abs(float(t.entry_price) * float(t.qty))
            except Exception:
                pass

        win_rate = (wins / closed.count() * 100.0) if closed.exists() else 0.0
        roi = (total_pnl / denom * 100.0) if denom > 0 else 0.0

        return Response({
            # snake_case
            "total_realized_pnl": f"{total_pnl:.2f}",
            "cumulative_roi": f"{roi:.2f}",
            "win_rate": f"{win_rate:.2f}",
            "total_trades": total_trades,
            # camelCase (프론트 호환)
            "totalRealizedPnl": f"{total_pnl:.2f}",
            "cumulativeReturnRate": f"{roi:.2f}",
            "winRate": f"{win_rate:.2f}",
            "tradeCount": total_trades,
            "_debugUser": request.user.get_username() if request.user.is_authenticated else "anonymous"
        })


class MyPagePNLHistoryAPI(APIView):
    """
    GET /mypage/pnl-history/?period=weekly|monthly
    응답: { period, pnl_entries: [ {date:'YYYY-MM-DD', realized_pnl:'...'} ] }
    """
    permission_classes = [AllowAny]

    def get(self, request):
        period = (request.GET.get("period") or "monthly").lower()
        days = 7 if period in ("weekly", "week") else 30
        end = timezone.now().date()
        start = end - timedelta(days=days - 1)

        entries = []
        if hasattr(Trade, 'objects'):
            qs = _user_filter(Trade.objects.all(), request)
            closed = qs.exclude(exit_at__isnull=True)

            # 날짜별 합계를 직접 누적(모델 필드 이름 차이를 흡수)
            daily = { (start + timedelta(i)): 0.0 for i in range(days) }
            for t in closed:
                d = getattr(t, "exit_at", None)
                if d is None:
                    continue
                d = (d.date() if hasattr(d, "date") else d)
                if start <= d <= end:
                    daily[d] = daily.get(d, 0.0) + _trade_pnl(t)

            for d in sorted(daily.keys()):
                entries.append({"date": d.isoformat(), "realized_pnl": f"{daily[d]:.2f}"})

        return Response({"period": period, "pnl_entries": entries})


class MyPagePNLCalendarAPI(APIView):
    """
    GET /mypage/pnl-calendar/?year=YYYY&month=MM
    응답: { year, month, pnl_entries:[{date, realized_pnl}] }
    """
    permission_classes = [IsAuthenticated] # AllowAny -> IsAuthenticated 수정

    def get(self, request):
        now = timezone.now()
        year = int(request.GET.get("year") or now.year)
        month = int(request.GET.get("month") or now.month)
        last_day = calendar.monthrange(year, month)[1]
        start = datetime(year, month, 1).date()
        end   = datetime(year, month, last_day).date()

        entries = []
        if hasattr(Trade, 'objects'):
            qs = _user_filter(Trade.objects.all(), request)
            closed = qs.exclude(exit_at__isnull=True)

            # 월 범위 내 일자별 합계
            daily = { (datetime(year, month, d).date()): 0.0 for d in range(1, last_day + 1) }
            for t in closed:
                d = getattr(t, "exit_at", None)
                if d is None:
                    continue
                d = (d.date() if hasattr(d, "date") else d)
                if start <= d <= end:
                    daily[d] = daily.get(d, 0.0) + _trade_pnl(t)

            for d in sorted(daily.keys()):
                entries.append({"date": d.isoformat(), "realized_pnl": f"{daily[d]:.2f}"})

        return Response({"year": year, "month": month, "pnl_entries": entries})


from rest_framework.pagination import PageNumberPagination

class _TradePagination(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "size"
    max_page_size = 200

class MyPageTradeHistoryAPI(APIView, _TradePagination):
    """
    GET /mypage/trade-history/?page=1&size=20
    """
    permission_classes = [IsAuthenticated] 

    def get(self, request):
        if not hasattr(Trade, 'objects'):
            return Response({"count": 0, "next": None, "previous": None, "results": []})

        qs = _user_filter(Trade.objects.all(), request).filter(status=Trade.Status.CLOSED)

        # 정렬 기준: 종료된 순
        if hasattr(Trade, 'exit_at'):
            qs = qs.order_by('-exit_at')
        elif hasattr(Trade, 'created_at'):
            qs = qs.order_by('-created_at')

        try:
            # 페이지네이션 처리
            page = self.paginate_queryset(qs, request, view=self)
        except AssertionError as e:
            print(f"Pagination error (AssertionError): {e}")
            return Response({"error": "유효하지 않은 페이지 파라미터입니다."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Unexpected pagination error: {e}")
            return Response({"error": "거래 기록을 불러오는 중 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        def _get(v, *alts):
            for a in (v, *alts):
                if a is not None:
                    return a
            return None

        items = []
        try: # 데이터 처리 중 발생할 수 있는 예상치 못한 오류 감지
            for t in page:
                created_at = _get(getattr(t, 'exit_at', None), getattr(t, 'created_at', None))
                price = _get(getattr(t, 'exit_price', None), getattr(t, 'entry_price', None))
                qty = _get(getattr(t, 'qty', None), getattr(t, 'quantity', None))
                pnl_value = _get(getattr(t, 'pnl', None)) 

                db_side_raw = getattr(t, 'side', None)
                api_side = ''

                if isinstance(db_side_raw, str):
                    db_side_lower = db_side_raw.lower().strip()
                    if db_side_lower in ('long', 'buy'):
                        api_side = 'buy'
                    elif db_side_lower in ('short', 'sell'):
                        api_side = 'sell'

                items.append({
                    "id": t.id,
                    "symbol": getattr(t, 'symbol', ''),
                    "side": api_side,
                    "order_type": getattr(t, 'order_type', 'market'),
                    "trade_type": getattr(t, 'trade_type', 'futures'),
                    "quantity": str(qty) if qty is not None else "0",
                    "price": str(price) if price is not None else "0",
                    "leverage": getattr(t, 'leverage', 1) or 1,
                    "status": getattr(t, 'status', 'closed'),
                    "created_at": created_at.isoformat() if created_at else None,
                    "realized_pnl": str(pnl_value) if pnl_value is not None else "0.00",
                })
        except Exception as e:
            # 데이터 포맷팅 중 오류 발생 시 500 에러를 반환한다.
            print(f"Data formatting error in Trade History: {e}")
            return Response({"error": f"데이터 포맷팅 오류 발생: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        return self.get_paginated_response(items) # 항상 Response를 반환하도록 보장

class MyPageBalanceAPI(APIView):
    """
    GET /mypage/balance/
    현재 사용자의 지갑 잔액을 조회합니다. (13번)
    """
    permission_classes = [IsAuthenticated] # 인증된 사용자만

    def get(self, request): # User 모델에 balance 필드가 있다고 가정
        balance = getattr(request.user, 'balance', 0)
        return Response({"balance": str(balance)})

class MyPageResetBalanceAPI(APIView):
    """
    POST /mypage/reset-balance/
    사용자의 지갑 잔액을 100,000 USDT로 초기화
    """
    permission_classes = [IsAuthenticated] # 인증된 사용자만

    def post(self, request):
        user = request.user
        try: # 12번 요구사항에 따라 10만으로 리셋
            user.balance = decimal.Decimal("100000.00")
            user.save(update_fields=['balance']) # balance 필드만 업데이트
            
            return Response({
                "message": "잔액이 100,000 USDT로 초기화되었습니다.", 
                "new_balance": str(user.balance)
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)