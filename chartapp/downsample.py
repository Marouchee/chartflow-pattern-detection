import math
import pandas as pd

def _resample_ohlc(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    ohlc = {'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}
    out = df.resample(freq).agg(ohlc).dropna()
    return out

def auto_downsample(df: pd.DataFrame, base_interval: str, max_points: int = 4000) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if len(df) <= max_points:
        return df

    steps = {
        '15m': ['30min','1H','2H','4H','1D'],
        '1h' : ['2H','4H','6H','12H','1D'],
        '1d' : ['2D','3D','1W','2W','1M'],
    }.get(base_interval, ['1H','2H','4H','1D'])

    for freq in steps:
        out = _resample_ohlc(df, freq)
        if len(out) <= max_points:
            return out

    # 최후의 보루: 간격 샘플링(OHLC 왜곡 가능 → 되도록 위에서 걸리도록)
    factor = math.ceil(len(df) / max_points)
    return df.iloc[::factor]