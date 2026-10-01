from django.urls import path
from .views import PaperPositionsAPI, PaperOrderAPI, PaperTpSlAPI, PaperCloseAPI, PendingOrdersAPI, CancelOrderAPI, RealTimePriceAPI

urlpatterns = [
    path("positions/", PaperPositionsAPI.as_view(), name="paper-positions"), # /papertrade/positions/
    path("order/", PaperOrderAPI.as_view(), name="paper-order"), # /papertrade/order/
    path("tpsl/", PaperTpSlAPI.as_view(), name="paper-tpsl"), # /papertrade/tpsl/
    path("close/", PaperCloseAPI.as_view(), name="paper-close"), # /papertrade/close/
    path("pending/", PendingOrdersAPI.as_view(), name="paper-pending"),
    path("cancel/", CancelOrderAPI.as_view(), name="paper-cancel"),
    path('price/', RealTimePriceAPI.as_view(), name='realtime_price'),
]