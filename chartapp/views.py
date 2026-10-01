from urllib.parse import urljoin
import traceback
import json

from django.shortcuts import render
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views import View
from django.db.models import Avg, Sum

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from .services import ChartAnalysisService, BySymbolAnalysisService
from .utils_dates import parse_date_str

def analyze_chart(request):
    if request.method == 'POST':
        symbol = request.POST.get('symbol')
        period = request.POST.get('period')
        service = ChartAnalysisService()
        result_img = service.analyze(symbol, period)
        # 결과 이미지를 저장하거나 base64로 인코딩하여 템플릿에 전달 가능
        return render(request, 'result.html', {'result_img': result_img})
    else:
        return render(request, 'input_form.html')

class ChartAnalysisAPIView(APIView):
    """
    POST 요청을 두 가지 방식으로 처리:
    1) 'image' 파일이 있으면 → 이미지 기반 분석
    2) 'symbol' & 'period'가 있으면 → 종목·기간 기반 분석
    """
    def post(self, request):
        service = ChartAnalysisService()

        # 1) 이미지 업로드 방식
        image_file = request.FILES.get("image")
        if image_file is not None:
            # 이미지 파일만으로 분석 호출 (symbol/period 없이)
            '''11/03 합병 주석처리
            try:
                # service.analyze_image(...) 메서드는 image_file만 받아서 처리하도록 가정
                result_image_path, pattern_label = service.analyze_image(image_file)

                # 미디어 URL 경로 처리: result_rel_path는 상대 경로
                result_url = request.build_absolute_uri(result_image_path)

                # Django에서 URL 경로가 올바르게 반환되도록 처리합니다.
                # 절대 경로가 아니라 상대 경로로 리턴되도록 확인합니다.
                result_url = result_url.replace('%5C', '/')  # 백슬래시가 있으면 슬래시로 변경
                # result_url 경로에서 불필요한 '/chart/analysis/image'를 제거하여 http://127.0.0.1:8000/media/로 시작하게 처리
                result_url = result_url.replace("/chart/analysis/image", "")
                return Response({
                    "result_url": result_url,
                    "pattern_label": pattern_label
                }, status=status.HTTP_200_OK,)
            '''          

            #수정 코드 시작 10/29
            try:
                # service.analyze_image(...) 메서드는 image_file만 받아서 처리하도록 가정
                result_image_path, pattern_labels_list = service.analyze_image(image_file, # 수정 10/29
                                                                               user=request.user if getattr(request, "user", None) and request.user.is_authenticated else None)

                # 미디어 URL 경로 처리: result_rel_path는 상대 경로
                result_url = request.build_absolute_uri(result_image_path)

                # Django에서 URL 경로가 올바르게 반환되도록 처리합니다.
                # 절대 경로가 아니라 상대 경로로 리턴되도록 확인합니다.
                result_url = result_url.replace('%5C', '/')  # 백슬래시가 있으면 슬래시로 변경
                # result_url 경로에서 불필요한 '/chart/analysis/image'를 제거하여 http://127.0.0.1:8000/media/로 시작하게 처리
                result_url = result_url.replace("/chart/analysis/image", "")
                return Response({
                    "result_url": result_url,
                    "pattern_labels": pattern_labels_list # 키 수정 10/29
                }, status=status.HTTP_200_OK,)
            #여기까지 10/29
            
            except Exception as e:
                print(traceback.format_exc())
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # 3) 위 두 가지 조건에 모두 해당하지 않으면 필수 파라미터 부족으로 간주
        return Response(
            {"error": "Provide either 'image' or both 'symbol' and 'period'."},
            status=status.HTTP_400_BAD_REQUEST,
        )


def build_media_url(request, rel_path_under_media: str) -> str:
    """MEDIA_URL + 상대경로 → 절대 URL. Windows 백슬래시 이슈 방지."""
    base = request.build_absolute_uri(settings.MEDIA_URL)  # e.g. http://127.0.0.1:8000/media/
    return urljoin(base, rel_path_under_media.replace("\\", "/"))

@method_decorator(csrf_exempt, name="dispatch")  # 개발단계: 필요시 유지, 운영에선 제거하고 CSRF 토큰 사용
class ChartAnalysisBySymbolAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # 1) JSON 또는 폼 모두 지원
        try:
            if (request.content_type or "").startswith("application/json"):
                payload = json.loads((request.body or b"{}").decode("utf-8"))
            else:
                payload = request.POST.dict()
        except ValueError as e:
            # 데이터 비어있음/형식오류 등 사용자 입력 문제
            return Response({"detail": str(e)}, status=400)
        except Exception as e:
            # 서버 내부 오류
            import traceback; traceback.print_exc()
            return Response({"detail": "내부 오류가 발생했습니다."}, status=500)
        except Exception:
            payload = {}

        # 2) 키 여러 형태 허용
        symbol = (payload.get("symbol") or "").strip()
        start_raw = payload.get("start_date") or payload.get("startDate") or payload.get("start")
        end_raw = payload.get("end_date") or payload.get("endDate") or payload.get("end")
        interval = (payload.get("interval") or "1d").strip()

        # ---- 디버그 로그 (서버 콘솔에서 값 확인)
        print(f"[BySymbolAPIView] payload={payload}")

        # 3) 날짜 문자열을 ISO(YYYY-MM-DD)로 정규화
        start_iso = parse_date_str(start_raw)
        end_iso = parse_date_str(end_raw)

        # 서비스 호출
        service = BySymbolAnalysisService()
        out = service.run(
            user=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
            symbol=symbol,
            start_date=start_iso,
            end_date=end_iso,
            interval=interval,
        )

        # 절대 URL 보정 (상대 경로가 온 경우)
        result_url = out.get("result_url", "")
        if result_url.startswith("/"):
            result_url = request.build_absolute_uri(result_url)
            out["result_url"] = result_url

        return JsonResponse(out, status=200)
