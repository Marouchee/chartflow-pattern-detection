"""
URL configuration for ChartAnalysis project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve
from django.middleware.csrf import get_token
# 1105추가
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from accounts.views import UserCreateAPIView # 1105추가
from django.urls import include, path # 1112추가


class IndexView(TemplateView):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        # 요청이 들어올 때 CSRF 쿠키를 강제로 생성/설정
        get_token(request)
        return super().get(request, *args, **kwargs)


urlpatterns = [
    path("admin/", admin.site.urls),
    path('chart/', include('chartapp.urls')),
    path("mypage/", include("chartapp.mypage_urls")),
    path("papertrade/", include("papertrade.urls")), # 1112추가 (모의투자)

    # 1105추가 사용자 인증 API
    # 1. 회원가입 (POST /api/users/register/)
    path('api/accounts/register/', UserCreateAPIView.as_view(), name='register'),

    # 2. 로그인 (POST /api/users/token/) - simplejwt 기본 뷰
    path('api/accounts/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    # 3. 토큰 재발급 (POST /api/users/token/refresh/) - simplejwt 기본 뷰
    path('api/accounts/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # 1105추가 사용자 인증 API

    #path("chart/api/", include("chartapp.urls")),

    # SPA 진입점
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
]

# React build 산출물 중 JSON/아이콘 파일은 정적 서빙으로 직접 매핑 (DEBUG 여부 무관하게)
# settings.py에 REACT_BUILD_DIR 설정(아래 2절 참고)
urlpatterns += [
    re_path(r"^manifest\.json$", static_serve, {
        "path": "manifest.json",
        "document_root": settings.REACT_BUILD_DIR
    }),
    re_path(r"^asset-manifest\.json$", static_serve, {
        "path": "asset-manifest.json",
        "document_root": settings.REACT_BUILD_DIR
    }),
    re_path(r"^favicon\.ico$", static_serve, {
        "path": "favicon.ico",
        "document_root": settings.REACT_BUILD_DIR
    }),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 루트와 SPA fallback (API/정적/미디어/관리자 제외)
urlpatterns += [
    path("", IndexView.as_view(), name="home"),
    re_path(r"^(?!api/|chart/|admin/|media/|static/).*$", IndexView.as_view(), name="spa"),
]