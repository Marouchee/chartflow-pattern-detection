from django.contrib import admin
from .models import PaperTrade, ChartAnalysisHistory

@admin.register(PaperTrade)
class PaperTradeAdmin(admin.ModelAdmin):
    list_display = ("user", "symbol", "side", "status", "entry_at", "exit_at", "pnl")
    list_filter  = ("side", "status", "symbol",)
    search_fields = ("user__username", "symbol")

@admin.register(ChartAnalysisHistory)
class ChartAnalysisHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "symbol", "interval", "created_at")
    list_filter  = ("symbol", "interval")
    search_fields = ("user__username", "symbol")