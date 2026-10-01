from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

urlpatterns = [
    path('analyze/', analyze_chart, name='analyze_chart'),
    path("analysis/image/", ChartAnalysisAPIView.as_view(), name="chart-image-api"),  # 기존: 업로드 이미지 분석 1106 오류로 수정 image/ -> analysis/image/ (views.py, )
    path("by-symbol/", ChartAnalysisBySymbolAPIView.as_view(), name="analysis_by_symbol"),  # 신규: 종목+기간 분석
]