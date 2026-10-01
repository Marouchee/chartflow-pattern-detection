from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import decimal 
from django.utils import timezone 
from django.db import transaction 
import requests 
import json 

try:
    from chartapp.models import PaperTrade, PendingOrder 
    from accounts.models import User 
except Exception:
    PaperTrade = None
    PendingOrder = None
    User = None

# 외부 가격 API 연동 헬퍼 함수 (단일 심볼)
def _fetch_real_price(symbol):
    """단일 심볼의 현재 가격을 가져옵니다."""
    if not symbol:
        return None
    try:
        # Binance API (암호화폐 기준)
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return decimal.Decimal(data.get('price')) 
    except requests.exceptions.RequestException as e:
        # print(f"ERROR: Failed to fetch price for {symbol}: {e}")
        return None
    except Exception as e:
        # print(f"ERROR: Price parsing failed for {symbol}: {e}")
        return None

# 외부 가격 API 연동 헬퍼 함수 (다중 심볼)
def _fetch_real_prices(symbols):
    """
    주어진 심볼 목록에 대한 실시간 가격을 딕셔너리로 반환합니다.
    { "BTCUSDT": Decimal("..."), "ETHUSDT": Decimal("...") }
    """
    prices = {}
    if not symbols:
        return prices
        
    try:
        # 모든 심볼에 대해 개별 호출
        for symbol in set(symbols):
            price = _fetch_real_price(symbol)
            if price is not None:
                prices[symbol] = price
    except Exception as e:
        print(f"ERROR: Failed to fetch multiple prices: {e}")
        
    return prices

def _calculate_liq_price(side, entry_price, margin, quantity):
    if quantity == 0:
        return None
    try:
        price_change = margin / quantity 
        if side == PaperTrade.Side.LONG:
            liq_price = entry_price - price_change
        else:
            liq_price = entry_price + price_change
        return max(liq_price, decimal.Decimal(0))
    except Exception:
        return None

@transaction.atomic 
def _process_triggers(user, symbol_prices): 
    if not PaperTrade or not PendingOrder or not user or not symbol_prices:
        return

    for symbol, market_price in symbol_prices.items():
        if market_price <= 0:
            continue
            
        # 지정가 주문(PendingOrder) 실행
        long_limits = PendingOrder.objects.filter(
            user=user, symbol=symbol, side=PaperTrade.Side.LONG,
            trigger_price__gte=market_price
        )
        short_limits = PendingOrder.objects.filter(
            user=user, symbol=symbol, side=PaperTrade.Side.SHORT,
            trigger_price__lte=market_price
        )
        triggered_limits = list(long_limits) + list(short_limits)
        
        for order in triggered_limits:
            entry_price = order.trigger_price
            liq_price_calc = _calculate_liq_price(
                order.side, entry_price, order.margin, order.qty
            )
            PaperTrade.objects.create(
                user=user, symbol=order.symbol, side=order.side, qty=order.qty, margin=order.margin,
                leverage=order.leverage, order_type='limit', entry_price=entry_price,
                entry_at=timezone.now(), status=PaperTrade.Status.OPEN, liq_price=liq_price_calc
            )
            order.delete() 

        # TP/SL 및 강제 청산 실행
        open_positions = PaperTrade.objects.filter(user=user, symbol=symbol, status=PaperTrade.Status.OPEN)
        
        for pos in open_positions:
            tp_hit = pos.tp_price and (
                (pos.side == PaperTrade.Side.LONG and market_price >= pos.tp_price) or
                (pos.side == PaperTrade.Side.SHORT and market_price <= pos.tp_price)
            )
            sl_hit = pos.sl_price and (
                (pos.side == PaperTrade.Side.LONG and market_price <= pos.sl_price) or
                (pos.side == PaperTrade.Side.SHORT and market_price >= pos.sl_price)
            )
            liq_hit = pos.liq_price and (
                (pos.side == PaperTrade.Side.LONG and market_price <= pos.liq_price) or
                (pos.side == PaperTrade.Side.SHORT and market_price >= pos.liq_price)
            )

            if not tp_hit and not sl_hit and not liq_hit:
                continue

            exit_price = pos.liq_price if liq_hit else (pos.tp_price if tp_hit else pos.sl_price)
            
            if liq_hit:
                pnl = -pos.margin 
            else:
                pnl = pos.compute_pnl(exit_price=exit_price)
                if pnl is None: pnl = 0 
            
            pos.exit_price = exit_price
            pos.exit_at = timezone.now()
            pos.status = PaperTrade.Status.CLOSED
            pos.pnl = decimal.Decimal(pnl)
            pos.save()

            user.balance += (pos.margin + pos.pnl)
            user.save(update_fields=['balance'])

class PaperPositionsAPI(APIView):
    """
    GET /papertrade/positions/
    사용자가 보유한 모든 포지션의 심볼 가격을 가져와 트리거를 처리하고 포지션을 반환합니다.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not PaperTrade:
            return Response([], status=status.HTTP_200_OK)

        # 현재 오픈된 포지션의 심볼 목록 수집 (포지션 + 지정가 주문)
        qs = PaperTrade.objects.filter(user=request.user, status=PaperTrade.Status.OPEN)
        pending_qs = PendingOrder.objects.filter(user=request.user)
        
        all_symbols = set()
        for p in qs:
            all_symbols.add(p.symbol)
        for o in pending_qs:
            all_symbols.add(o.symbol)

        # 모든 심볼의 실시간 가격 조회
        market_prices = _fetch_real_prices(list(all_symbols))
        
        # 모든 심볼에 대해 트리거 처리 (지정가 체결, TP/SL/청산)
        if market_prices:
            try:
                _process_triggers(request.user, market_prices)
            except Exception as e:
                print(f"Trigger processing failed: {e}")

        # 업데이트된 오픈 포지션 목록 반환
        qs = PaperTrade.objects.filter(user=request.user, status=PaperTrade.Status.OPEN)

        positions = []
        for p in qs:
            side_for_frontend = 'buy' if p.side == PaperTrade.Side.LONG else 'sell'
            
            # 해당 포지션의 심볼에 해당하는 가격을 가져와 응답에 포함
            price_for_pnl = market_prices.get(p.symbol)
            
            positions.append({
                "id": p.id,
                "user": p.user_id,
                "symbol": p.symbol,
                "quantity": str(p.qty),
                "margin": str(p.margin),
                "leverage": p.leverage,
                "entry_price": str(p.entry_price),
                "side": side_for_frontend,
                "tp_price": str(p.tp_price) if p.tp_price else None, 
                "sl_price": str(p.sl_price) if p.sl_price else None, 
                "liq_price": str(p.liq_price) if p.liq_price else None,
                # 해당 포지션 심볼의 실시간 가격을 응답에 포함
                "current_price": str(price_for_pnl) if price_for_pnl else None 
            })
        
        return Response(positions)

class PaperOrderAPI(APIView):
    """
    POST /papertrade/order/
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic 
    def post(self, request):
        if not PaperTrade or not PendingOrder or not User:
            return Response({"error": "모델이 준비되지 않았습니다."}, status=500)

        data = request.data
        user = request.user
        order_type = data.get('order_type', 'market')
        symbol = data.get('symbol')
        
        try:
            db_side = PaperTrade.Side.LONG if data.get('side') == 'buy' else PaperTrade.Side.SHORT
            quantity = decimal.Decimal(data.get('quantity', 0))
            leverage = int(data.get('leverage', 10))
            margin = decimal.Decimal(data.get('margin', 0)) 
            price_str = data.get('price')

            if margin <= 0 or quantity <= 0:
                 return Response({"error": "주문 금액 또는 수량이 유효하지 않습니다."}, status=400)
            if user.balance < margin:
                return Response({"error": "지갑 잔액이 부족합니다."}, status=400)
            
            if order_type == 'market':
                # 시장가 주문
                entry_price = _fetch_real_price(symbol)
                
                if entry_price is None or entry_price <= 0:
                    return Response({"error": f"{symbol}의 실시간 가격을 가져올 수 없습니다."}, status=503)

                liq_price_calc = _calculate_liq_price(
                    db_side, entry_price, margin, quantity
                )

                PaperTrade.objects.create(
                    user=user, symbol=symbol, side=db_side, qty=quantity, margin=margin,
                    leverage=leverage, order_type='market', entry_price=entry_price,
                    status=PaperTrade.Status.OPEN, liq_price=liq_price_calc 
                )
                user.balance -= margin
                user.save(update_fields=['balance'])
                
                return Response({
                    "message": f"시장가 주문 완료: {symbol} @ {entry_price.quantize(decimal.Decimal('0.01'))}",
                }, status=status.HTTP_201_CREATED)

            elif order_type == 'limit':
                # 지정가 주문
                trigger_price = decimal.Decimal(price_str)
                
                PendingOrder.objects.create(
                    user=user, symbol=symbol, side=db_side, qty=quantity, margin=margin,
                    leverage=leverage, order_type=PendingOrder.OrderType.LIMIT,
                    trigger_price=trigger_price
                )
                user.balance -= margin
                user.save(update_fields=['balance'])

                return Response({"message": f"지정가 주문 등록 완료: {symbol}"}, status=status.HTTP_201_CREATED)
            
            else:
                 return Response({"error": "알 수 없는 주문 유형입니다."}, status=400)
        
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class PaperTpSlAPI(APIView):
    """
    POST /papertrade/tpsl/
    """
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        data = request.data
        position_id = data.get('position_id')
        tp_price_str = data.get('tp')
        sl_price_str = data.get('sl')

        if not PaperTrade or not position_id:
            return Response({"error": "필수 정보가 누락되었습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            position = PaperTrade.objects.get(id=position_id, user=request.user, status=PaperTrade.Status.OPEN)

            position.tp_price = decimal.Decimal(tp_price_str) if tp_price_str and float(tp_price_str) > 0 else None
            position.sl_price = decimal.Decimal(sl_price_str) if sl_price_str and float(sl_price_str) > 0 else None
            
            position.save()
            
            return Response({"message": "TP/SL이 설정되었습니다."}, status=status.HTTP_200_OK)

        except PaperTrade.DoesNotExist:
            return Response({"error": "포지션을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"설정 실패: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaperCloseAPI(APIView):
    """
    POST /papertrade/close/
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        data = request.data
        user = request.user
        position_id = data.get('position_id')
        
        if not PaperTrade or not position_id:
            return Response({"error": "필수 정보가 누락되었습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pos = PaperTrade.objects.get(id=position_id, user=user, status=PaperTrade.Status.OPEN)
            symbol = pos.symbol
            
            # 종료 가격을 API에서 실시간으로 획득한다
            close_price = _fetch_real_price(symbol)

            if close_price is None or close_price <= 0:
                return Response({"error": f"포지션 종료 가격({symbol})을 가져올 수 없습니다."}, status=503)

            pnl = pos.compute_pnl(exit_price=close_price)
            if pnl is None:
                 pnl = 0

            pos.exit_price = close_price
            pos.exit_at = timezone.now()
            pos.status = PaperTrade.Status.CLOSED
            pos.pnl = decimal.Decimal(pnl)
            pos.save()

            user.balance += (pos.margin + pos.pnl)
            user.save(update_fields=['balance'])
            
            return Response({
                "message": f"{symbol} 포지션이 종료되었습니다. (@ {close_price.quantize(decimal.Decimal('0.01'))})",
                "realized_pnl": str(pos.pnl),
                "new_balance": str(user.balance)
            }, status=status.HTTP_200_OK)

        except PaperTrade.DoesNotExist:
            return Response({"error": "종료할 포지션을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"종료 실패: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PendingOrdersAPI(APIView):
    """
    GET /papertrade/pending/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not PendingOrder:
            return Response([], status=status.HTTP_200_OK)
            
        qs = PendingOrder.objects.filter(user=request.user).order_by('-created_at')
        
        orders = []
        for o in qs:
            side_for_frontend = 'buy' if o.side == PaperTrade.Side.LONG else 'sell'
            orders.append({
                "id": o.id,
                "symbol": o.symbol,
                "quantity": str(o.qty),
                "margin": str(o.margin),
                "leverage": o.leverage,
                "side": side_for_frontend,
                "trigger_price": str(o.trigger_price),
                "created_at": o.created_at.isoformat(),
            })
        return Response(orders)

class CancelOrderAPI(APIView):
    """
    POST /papertrade/cancel/
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        data = request.data
        user = request.user
        order_id = data.get('order_id')

        if not PendingOrder or not order_id:
            return Response({"error": "필수 정보가 누락되었습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = PendingOrder.objects.get(id=order_id, user=user)
            
            user.balance += order.margin
            user.save(update_fields=['balance'])
            
            order.delete()
            
            return Response({
                "message": f"{order.symbol} 지정가 주문이 취소되었습니다.",
                "new_balance": str(user.balance)
            }, status=status.HTTP_200_OK)

        except PendingOrder.DoesNotExist:
            return Response({"error": "취소할 주문을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"취소 실패: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RealTimePriceAPI(APIView):
    """
    GET /papertrade/price/?symbol=BTCUSDT
    단일 심볼의 실시간 가격을 반환합니다. (TradePanel 표시용)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        symbol = request.GET.get('symbol', 'BTCUSDT')
        price = _fetch_real_price(symbol)
        
        if price is None:
            return Response({"error": "Failed to fetch price"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({"symbol": symbol, "price": str(price)})