from django.conf import settings
from django.db import models
from django.utils import timezone
import decimal

User = settings.AUTH_USER_MODEL

class PaperTrade(models.Model):
    class Side(models.TextChoices):
        LONG = "LONG", "Long"
        SHORT = "SHORT", "Short"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"
    
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name="paper_trades")
    symbol      = models.CharField(max_length=32)
    side        = models.CharField(max_length=5, choices=Side.choices, default=Side.LONG)
    qty         = models.DecimalField(max_digits=20, decimal_places=8) # 총 포지션 수량
    margin      = models.DecimalField(max_digits=20, decimal_places=8, default=0) # 이 포지션에 사용된 증거금
    leverage    = models.PositiveIntegerField(default=10) # 레버리지
    order_type  = models.CharField(max_length=10, default='market') # 'market' 또는 'limit'

    entry_price = models.DecimalField(max_digits=20, decimal_places=8)
    entry_at    = models.DateTimeField(default=timezone.now)

    exit_price  = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    exit_at     = models.DateTimeField(null=True, blank=True)
    status      = models.CharField(max_length=6, choices=Status.choices, default=Status.OPEN)
    
    pnl         = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    note        = models.TextField(blank=True, default="")
    
    # TP/SL 가격
    tp_price    = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    sl_price    = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    # 강제 청산 가격 ---
    liq_price   = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    def compute_pnl(self, exit_price=None): 
        """pnl 필드가 비었을 때 계산"""
        close_price = exit_price or self.exit_price 
        if self.status != self.Status.CLOSED and not close_price:
            return None
        mult = 1 if self.side == self.Side.LONG else -1
        return mult * (float(close_price) - float(self.entry_price)) * float(self.qty)

    def __str__(self):
        return f"{self.user} {self.symbol} {self.side} {self.status}"

# '미체결 주문(대기열)' 모델
class PendingOrder(models.Model):
    class OrderType(models.TextChoices):
        LIMIT = "LIMIT", "Limit" # 지정가 진입

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pending_orders")
    symbol      = models.CharField(max_length=32)
    side        = models.CharField(max_length=5, choices=PaperTrade.Side.choices)
    order_type  = models.CharField(max_length=5, choices=OrderType.choices, default=OrderType.LIMIT)
    
    qty         = models.DecimalField(max_digits=20, decimal_places=8) # 총 포지션 수량
    margin      = models.DecimalField(max_digits=20, decimal_places=8) # 차감될 증거금
    leverage    = models.PositiveIntegerField(default=10)
    
    trigger_price = models.DecimalField(max_digits=20, decimal_places=8) # 이 가격에 도달하면 실행
    
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[PENDING] {self.user} {self.symbol} @ {self.trigger_price}"

class ChartAnalysisHistory(models.Model):
    """분석 기록(마이페이지 리스트/통계 용)"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="chart_analyses"
    )
    symbol = models.CharField(max_length=40)
    interval = models.CharField(max_length=16)
    start_dt = models.DateTimeField(null=True, blank=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    # 렌더링한 이미지의 MEDIA_ROOT 상대경로 (예: results/aaa.png)
    image_rel = models.CharField(max_length=512, blank=True)
    # 프론트가 바로 띄울 수 있는 절대 URL (캐시버스터 포함)
    result_url = models.CharField(max_length=1024, blank=True)

    # YOLO 등 감지 결과
    patterns = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.symbol} {self.interval}] {self.created_at:%Y-%m-%d %H:%M}"