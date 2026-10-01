import pandas as pd
import ccxt
import yfinance as yf
import pytz

def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """MultiIndex/중복 컬럼을 일렬(str)로 평탄화합니다."""
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [
            "_".join([str(x) for x in col if str(x) != ""]).strip()
            for col in df.columns
        ]
    else:
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
    return df

def _pick_one_column(df: pd.DataFrame, name: str):
    """
    'Open','High','Low','Close','Volume' 중 하나에 해당하는 단일 컬럼명을 찾아 반환.
    - 우선순위: 완전 일치 > 접두/접미/토큰 일치
    - 반환: 컬럼명 문자열 (없으면 None)
    """
    target = name.lower()
    cols = list(df.columns)

    # 1) 완전 일치
    for c in cols:
        if c.lower() == target:
            return c

    # 2) 접두/접미/토큰 일치 (예: 'AAPL_Open' / 'Open_AAPL' / 'BTCUSD_Open' 등)
    for c in cols:
        cl = c.lower()
        tokens = cl.replace("-", "_").split("_")
        if (cl.startswith(target + "_") or cl.endswith("_" + target)
            or cl == target or target in tokens):
            return c
    return None

def sanitize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError("빈 데이터프레임입니다.")

    # 0) 컬럼 평탄화
    df = _flatten_columns(df)

    # 1) 필요한 컬럼 고르기
    col_map = {}
    for nm in ["Open", "High", "Low", "Close", "Volume"]:
        c = _pick_one_column(df, nm)
        if c is not None:
            col_map[nm] = c

    # Open/High/Low/Close는 필수
    for req in ["Open", "High", "Low", "Close"]:
        if req not in col_map:
            raise ValueError(f"필수 칼럼 누락: {req}. 실제 컬럼: {list(df.columns)[:10]} ...")

    # 2) 숫자화 (쉼표/공백 제거 후 to_numeric)
    def _to_numeric_series(obj):
        s = obj
        if isinstance(s, pd.DataFrame):
            # 중복 라벨로 DataFrame이 왔다면 첫 열 사용
            s = s.iloc[:, 0]
        s = s.astype(str).str.replace(",", "", regex=False).str.replace(" ", "", regex=False)
        return pd.to_numeric(s, errors="coerce")

    out = pd.DataFrame({
        "Open":  _to_numeric_series(df[col_map["Open"]]),
        "High":  _to_numeric_series(df[col_map["High"]]),
        "Low":   _to_numeric_series(df[col_map["Low"]]),
        "Close": _to_numeric_series(df[col_map["Close"]]),
    })
    if "Volume" in col_map:
        out["Volume"] = _to_numeric_series(df[col_map["Volume"]]).fillna(0)

    # 3) 인덱스를 DatetimeIndex로
    if not isinstance(df.index, pd.DatetimeIndex):
        out.index = pd.to_datetime(df.index, errors="coerce", utc=True)
    else:
        out.index = pd.to_datetime(df.index, errors="coerce", utc=True)
    out = out[~out.index.isna()]

    # 4) NaN/이상치 제거
    out = out.dropna(subset=["Open", "High", "Low", "Close"])
    bad = (
        (out["High"] < out["Low"]) |
        (out["Open"] > out["High"]) | (out["Open"] < out["Low"]) |
        (out["Close"] > out["High"]) | (out["Close"] < out["Low"])
    )
    out = out[~bad]

    return out.sort_index()

def parse_date_str(s: str):
    ts = pd.to_datetime(str(s), errors="coerce")
    if pd.isna(ts):
        return None
    return ts.date().isoformat()

def map_interval(interval: str, source: str = "yf") -> str:
    """
    프런트에서 오는 interval을 각 소스별 토큰으로 매핑.
    - source="ccxt" : 바이낸스가 지원하는 문자열 그대로 반환 (15m, 1h, 1d ...)
    - source="yf"   : yfinance 토큰으로 매핑 (1h -> 60m 등)
    """
    iv = (interval or "1d").strip().lower()

    if source == "ccxt":
        ccxt_map = {
            "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h",
            "1d": "1d", "3d": "3d", "1w": "1w", "1mo": "1M", "1mth": "1M",
        }
        return ccxt_map.get(iv, iv)

    # source == "yf"
    yf_map = {
        "1m": "1m", "2m": "2m", "5m": "5m", "15m": "15m", "30m": "30m",
        "60m": "60m", "90m": "90m", "1h": "60m",
        "1d": "1d", "5d": "5d", "1wk": "1wk", "1w": "1wk", "1mo": "1mo",
    }
    return yf_map.get(iv, iv)

# yfinance
# 프런트 인터벌 → yfinance 인터벌 토큰
_YF_INTERVAL_MAP = {
    "1d":  "1d",
    "1h":  "60m",   # ← 1시간봉은 60m
    "15m": "15m",
}
# intraday 판정에 '60m' 포함!
_INTRADAY = {"1m","2m","5m","15m","30m","60m","90m","1h"}

def _period_token_for_intraday(start_utc: pd.Timestamp, end_utc: pd.Timestamp) -> str:
    days = max(1, int((end_utc - start_utc).total_seconds() // 86400) + 1)
    if days <= 30:   return "1mo"
    if days <= 90:   return "3mo"
    if days <= 180:  return "6mo"
    if days <= 365:  return "1y"
    if days <= 730:  return "2y"
    return "5y"

def _to_utc(ts: pd.Timestamp | None) -> pd.Timestamp | None:
    if ts is None: return None
    if ts.tz is None: return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")

def _flatten_ohlcv_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    yfinance가 MultiIndex(튜플) 컬럼을 반환할 때 OHLCV 레벨로 평탄화.
    """
    cols = []
    for c in df.columns:
        if isinstance(c, tuple):
            # 오른쪽(마지막)에서 OHLCV에 해당하는 문자열을 고릅니다.
            pick = None
            for part in reversed(c):
                if isinstance(part, str) and part.lower().replace(" ", "") in (
                    "open","high","low","close","adjclose","adjclose","volume"):
                    pick = part
                    break
            if pick is None:
                pick = next((str(part) for part in reversed(c) if isinstance(part, (str,int,float))), str(c))
            cols.append(pick)
        else:
            cols.append(c)
    df.columns = pd.Index(cols)
    return df

def fetch_yf(symbol: str, start_iso: str | None, end_iso: str | None, interval_raw: str = "1d") -> pd.DataFrame:
    """
    symbol: 'AAPL'|'QQQ'|'BTC-USD' 등
    start_iso/end_iso: 'YYYY-MM-DD' 또는 None
    interval_raw: 프런트 값 그대로 ('1d'|'1h'|'15m')
    """
    yf_iv = _YF_INTERVAL_MAP.get(interval_raw, interval_raw)
    is_intraday = yf_iv in _INTRADAY

    start = pd.to_datetime(start_iso) if start_iso else None
    end   = pd.to_datetime(end_iso) if end_iso else None

    print(f"[fetch_yf] raw={interval_raw} yf_iv={yf_iv} is_intraday={is_intraday} start={start_iso} end={end_iso}")

    if is_intraday:
        # intraday는 period 기반이 안전. 날짜가 없으면 1mo로 기본 제공.
        if start is not None and end is not None:
            s_utc = _to_utc(start); e_utc = _to_utc(end)
            period = _period_token_for_intraday(s_utc, e_utc)
        else:
            period = "1mo"  # 날짜 없을 때 기본 1개월

        df = yf.Ticker(symbol).history(period=period, interval=yf_iv, auto_adjust=False, prepost=False)
    else:
        df = yf.download(
            tickers=symbol,
            start=start_iso or None,
            end=end_iso or None,
            interval=yf_iv,
            auto_adjust=False,
            progress=False,
            threads=False,
            group_by="column",  # 단일 컬럼 그룹화 유도
        )

    if df is None or df.empty:
        return pd.DataFrame(columns=["Open","High","Low","Close","Volume"])

    # 인덱스/컬럼 정규화
    if isinstance(df.columns, pd.MultiIndex) or any(isinstance(c, tuple) for c in df.columns):
        df = _flatten_ohlcv_columns(df)

    # yfinance가 소문자/대문자 섞여 줄 수 있음 → 보정
    rename_map = {}
    for c in df.columns:
        key = str(c).strip().lower().replace(" ", "")
        if key == "adjclose" or key == "adjclose": rename_map[c] = "AdjClose"
        elif key == "open":   rename_map[c] = "Open"
        elif key == "high":   rename_map[c] = "High"
        elif key == "low":    rename_map[c] = "Low"
        elif key == "close":  rename_map[c] = "Close"
        elif key == "volume": rename_map[c] = "Volume"
    if rename_map:
        df = df.rename(columns=rename_map)

    needed = ["Open","High","Low","Close","Volume"]
    df = df[[c for c in needed if c in df.columns]].copy()

    # 숫자형 강제
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(how="any")

    # 인덱스 UTC
    idx = pd.to_datetime(df.index)
    idx = idx.tz_localize("UTC") if getattr(idx, "tz", None) is None else idx.tz_convert("UTC")
    df.index = idx

    # intraday + 날짜 지정 시 정확 슬라이스
    if is_intraday and (start is not None or end is not None):
        s_utc = _to_utc(start) if start is not None else None
        e_utc = _to_utc(end)   if end   is not None else None
        if s_utc is not None: df = df[df.index >= s_utc]
        if e_utc is not None: df = df[df.index <= e_utc]

    return df

# ccxt (바이낸스)
_binance = ccxt.binance()

def fetch_ccxt(symbol: str, timeframe: str, since_ms: int = None, limit: int = 1000) -> pd.DataFrame:
    """
    symbol: 'BTC/USDT' 형태
    timeframe: '15m' | '1h' | '1d' ...
    since_ms:  UTC ms
    limit:    개수 (서비스에서 기간으로 계산해서 넘겨줌)
    """
    tf = timeframe.lower()

    # 바이낸스가 지원하는 timeframes 확인(안전장치)
    if hasattr(_binance, "timeframes") and tf not in _binance.timeframes:
        raise ValueError(f"Unsupported timeframe '{tf}'. Allowed: {sorted(_binance.timeframes.keys())[:12]} ...")

    rows = _binance.fetch_ohlcv(symbol, timeframe=tf, since=since_ms, limit=limit)
    if not rows:
        return pd.DataFrame(columns=["Open","High","Low","Close","Volume"])

    df = pd.DataFrame(rows, columns=["ts", "Open", "High", "Low", "Close", "Volume"])
    df["Date"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.set_index("Date").drop(columns=["ts"])
    df.index.name = "Date"

    # 분해상도 유지 + 컬럼/인덱스 정리
    return sanitize_ohlcv(df)