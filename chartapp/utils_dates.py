import re
import pandas as pd

def parse_date_str(s: str | None) -> str | None:
    """다양한 표기(YYYY-MM-DD, YYYY. MM. DD., YYYY/..., YYYY년 MM월 DD일 등)를 YYYY-MM-DD로 정규화."""
    if not s:
        return None
    s = str(s).strip()
    s = (s.replace("년", "-")
         .replace("월", "-")
         .replace("일", "")
         .replace("/", "-")
         .replace(".", "-"))
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    # 가장 흔한 포맷 우선
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # 마지막 보정
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return None