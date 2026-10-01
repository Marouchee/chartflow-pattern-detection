import os
import mplfinance as mpf

class ChartGenerator:
    """OHLC DataFrame으로 캔들차트 이미지 생성."""

    def generate(self, df, save_abs_path: str, style: str = "yahoo"):
        os.makedirs(os.path.dirname(save_abs_path), exist_ok=True)
        mpf.plot(
            df, type='candle', volume=True, mav=(5, 20),
            style=style,
            savefig=dict(fname=save_abs_path, dpi=180, bbox_inches='tight')
        )
        return save_abs_path