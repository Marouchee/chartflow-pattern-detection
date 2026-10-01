# --- 반드시 최상단에서 Agg 백엔드 고정(서버에서 GUI 백엔드 금지) ---
import os
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("Agg")

from io import BytesIO
import mplfinance as mpf
import pandas as pd
import pytz

def _fmt_by_interval(interval: str) -> tuple[str, int]:
    iv = (interval or "").lower()
    # 일/주봉은 날짜만, 시/분봉은 날짜+시각
    if iv in ("1d", "1일", "1일봉", "daily", "1wk", "1주", "1주봉", "weekly"):
        return "%Y-%m-%d", 20
    return "%m-%d %H:%M", 30


def render_candlestick(
    df_utc: pd.DataFrame,
    out_path: str,
    interval: str = "1h",
    display_tz: str = "Asia/Seoul",
    title: str | None = None,
    warn_limit: int = 10**9,
):
    if df_utc is None or df_utc.empty:
        # 빈 그림이라도 저장해 두면 프론트에서 에러 안 남
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_title(title or "No data")
        fig.savefig(out_path, dpi=140, bbox_inches="tight")
        plt.close(fig)
        return

    # ✅ UTC 가정 → 표시용 타임존으로만 변환 (축/Formatter 직접 만지지 않음)
    df = df_utc.copy()
    if df.index.tz is None:
        df.index = pd.to_datetime(df.index, utc=True)
    tz = pytz.timezone(display_tz) if display_tz != "UTC" else pytz.UTC
    df.index = df.index.tz_convert(tz)

    fig, axes = mpf.plot(
        df,
        type="candle",
        volume=True,
        style="yahoo",
        returnfig=True,
        datetime_format="%Y-%m-%d %H:%M",
        xrotation=30,
        figsize=(12, 6),
        title=title or "",
        warn_too_much_data=warn_limit,  # 경고 억제
    )

    # tight_layout 경고를 피하려면 생략하거나, bbox_inches만 사용
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)