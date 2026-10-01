import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class DataFetcher:
    """Yahoo Finance에서 구간/간격 데이터를 받아옵니다."""

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """프론트 기호 → yfinance 티커 변환(BTCUSDT → BTC-USD 등). 필요 시 확장."""
        s = symbol.upper().strip()
        mapping = {
            "BTCUSDT": "BTC-USD",
            "ETHUSDT": "ETH-USD",
        }
        return mapping.get(s, s)  # 매핑 없으면 그대로

    def get(self, symbol: str, start_date: str, end_date: str, interval: str = "1d") -> pd.DataFrame:
        """
        start_date / end_date: 'YYYY-MM-DD'
        yfinance의 end는 'exclusive'라서 하루 더해줍니다.
        """
        tkr = self._normalize_symbol(symbol)
        start = datetime.fromisoformat(start_date)
        end   = datetime.fromisoformat(end_date) + timedelta(days=1)

        df = yf.download(
            tkr, start=start, end=end, interval=interval,
            auto_adjust=False, progress=False
        )
        if df is None or df.empty:
            raise ValueError(f"No data for {symbol} ({start_date}~{end_date}, interval={interval})")

        # mplfinance 표준 컬럼명 보장 (대소문자 포함)
        df = df.rename(columns={
            "Open":"Open", "High":"High", "Low":"Low", "Close":"Close", "Adj Close":"Adj Close", "Volume":"Volume"
        })
        return df