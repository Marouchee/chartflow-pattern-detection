from django.urls import path
from .views_mypage import (
    MyPageSummaryAPI, MyPagePNLHistoryAPI,
    MyPagePNLCalendarAPI, MyPageTradeHistoryAPI,
    MyPageBalanceAPI, MyPageResetBalanceAPI, #잔액 api 임포트
)

urlpatterns = [
    path("summary/", MyPageSummaryAPI.as_view(), name="mypage-summary"),
    path("pnl-history/", MyPagePNLHistoryAPI.as_view(), name="mypage-pnl-history"),
    path("pnl-calendar/", MyPagePNLCalendarAPI.as_view(), name="mypage-pnl-calendar"),
    path("trade-history/", MyPageTradeHistoryAPI.as_view(), name="mypage-trade-history"),
    path("balance/", MyPageBalanceAPI.as_view(), name="mypage-balance"), #잔액 관련
    path("reset-balance/", MyPageResetBalanceAPI.as_view(), name="mypage-reset-balance"), #잔액 관련
]