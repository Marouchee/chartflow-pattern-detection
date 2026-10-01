import matplotlib.pyplot as plt
from typing import List, Dict
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO
from django.conf import settings
from django.db import transaction
import os, uuid, math, logging
from django.utils import timezone

from .chart_data import (
    fetch_yf, fetch_ccxt, sanitize_ohlcv, map_interval
)
from .plotting import render_candlestick
from .downsample import auto_downsample
from .utils_dates import parse_date_str

from .data_fetcher import DataFetcher
from .chart_generator import ChartGenerator

from .models import ChartAnalysisHistory

'''
class DataFetcher:
    def get_data(self, symbol, period):
        import yfinance as yf
        data = yf.download(symbol, period=period)
        return data


class ChartGenerator:
    def generate_chart(self, data):
        fig, ax = plt.subplots()
        ax.plot(data.index, data['Close'])
        fig.savefig('chart.png')
        plt.close(fig)
        return 'chart.png'
'''

class ImagePreprocessor:
    def preprocess(self, image_path):
        img = Image.open(image_path)
        # 이미지 전처리 (크기 조정 등)
        img = img.resize((640, 640))
        return img


class YOLODetector:
    def __init__(self, model_name="model_0608.pt"):
        model_path = os.path.join(settings.BASE_DIR, "models", "model_0608.pt")
        self.model = YOLO(model_path)

    def predict(self, image_input):
        """
        image_input:
         - PIL.Image or numpy array 를 넘기는 대신
         - 파일 경로(str)도 넘겨서 inference 하면,
           내부적으로 원본 크기 기준 좌표를 리턴해 줍니다.
        """
        # 만약 image_input이 파일 경로(str)라면, 아래처럼 호출:
        if isinstance(image_input, str):
            results = self.model(image_input)
        else:
            # 기존 넘파이/배열을 넘기고 싶다면 기존 코드를 사용
            results = self.model(image_input)

        return results


class ResultVisualizer:
    def overlay_results(self, image_path, results, save_path=None):
        """
        image_path : str
            ➤ YOLO가 탐지한 원본 차트 이미지의 경로(절대경로 or 프로젝트 루트 기준 상대경로).
        results : ultralytics.yolo.engine.results.Results
            ➤ YOLO 추론 결과 객체. 이 안에 .boxes, .names, .boxes.conf(신뢰도) 등이 포함되어 있음.
        save_path : str, optional
            ➤ 결과 이미지를 저장할 경로. None이면 현재 작업 폴더에 'result.png' 로 저장.
        """

        # 1) 원본 이미지를 열어서 RGB 모드로 변환
        img = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(img)

        # 2) 글꼴(Font) 설정 (테스트 환경에 따라 폰트 경로를 실제 시스템 경로로 바꿔야 할 수 있음)
        #    - Windows: "C:/Windows/Fonts/arial.ttf" 같은 경로가 일반적
        #    - Linux/Mac: "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" 등이 있음
        try:
            font = ImageFont.truetype("arial.ttf", size=24)
        except IOError:
            # 운영체제에 따라 해당 폰트 파일이 없을 수 있으므로, 기본 폰트로 대체
            font = ImageFont.load_default()

        # 3) YOLO 결과 객체에서 "boxes", "conf", "cls", "names" 정보 읽어오기
        #    - results[0].boxes.xyxy : 각 바운딩 박스 좌표 리스트 (Tensor Nx4)
        #    - results[0].boxes.conf : 각 바운딩 박스의 신뢰도 리스트 (Tensor N)
        #    - results[0].boxes.cls  : 각 바운딩 박스의 클래스 인덱스 리스트 (Tensor N)
        #    - results[0].names     : 클래스 인덱스 → 이름 매핑 딕셔너리

        # YOLOv8 기준: 결과 첫 번째 객체(한 장의 이미지 결과)만 처리
        det = results[0]

        boxes = det.boxes.xyxy.cpu().numpy()    # shape: (N, 4) → [[x1,y1,x2,y2], ...]
        confidences = det.boxes.conf.cpu().numpy()  # shape: (N,)
        class_idxs = det.boxes.cls.cpu().numpy().astype(int)  # shape: (N,)
        names = det.names  # 예: {0: "Head-Shoulders", 1: "Double Top", ...}

        filtered_idxs = []
        for idx in range(len(boxes)):
            x1, y1, x2, y2 = boxes[idx]
            w = x2 - x1
            h = y2 - y1
            area_box = w * h
            img_area = img.width * img.height

            # ■ 예시 필터: 박스가 이미지의 80% 이상을 차지하면 스킵
            #   (너무 큰 박스는 가독성을 해치므로 제외)
            if area_box > 0.8 * img_area:
                continue

            # ■ 예시 필터: 신뢰도가 0.4 미만인 박스는 스킵
            if confidences[idx] < 0.40:
                continue

            filtered_idxs.append(idx)

        # 4) 바운딩 박스마다 초록색 테두리 + "클래스 이름 신뢰도" 텍스트를 그리기
        for idx in filtered_idxs:
            x1_m, y1_m, x2_m, y2_m = boxes[idx]
            # YOLO가 반환한 좌표는 “원본 해상도 기준”이라고 가정 (이미 pre-scaling 을 거침)
            x1, y1, x2, y2 = int(x1_m), int(y1_m), int(x2_m), int(y2_m)

            # 클래스 이름과 신뢰도(소수점 두 자리)
            cls_idx = class_idxs[idx]
            pattern_name = names[cls_idx]
            confidence = confidences[idx]
            label = f"{pattern_name} {confidence:.2f}"

            # 텍스트 크기 계산 (textbbox 사용)
            # textbbox는 (x, y, text) 형태로 호출하면 텍스트가 차지하는 사각형을 반환합니다.
            # 반환값은 (left, top, right, bottom)
            bbox = draw.textbbox((x1, y1), label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # 4-1) 바운딩 박스 그리기 (초록색, 두께=3)
            draw.rectangle([x1, y1, x2, y2], outline="lime", width=3)

            # 4-2) 텍스트 배경(초록색)
            # 텍스트를 바운딩 박스 위쪽에 붙여 그리려면 y1 - text_height - 4 만큼 위로 빼줍니다.
            text_bg_top = y1 - text_height - 4
            if text_bg_top < 0:
                text_bg_top = y1 + 4  # 위로 공간이 없으면 박스 아래쪽에 그리도록 조정
            text_background = [
                x1,
                text_bg_top,
                x1 + text_width + 4,
                text_bg_top + text_height + 4,
            ]
            draw.rectangle(text_background, fill="lime")

            # 4-3) 텍스트 그리기 (검정색)
            text_x = x1 + 2
            text_y = text_bg_top + 2
            draw.text((text_x, text_y), label, fill="black", font=font)

        # 5) 결과 저장 경로 처리
        if save_path is None:
            save_path = "result.png"  # 기본값
        else:
            # 상위 디렉토리가 없으면 자동 생성
            dir_name = os.path.dirname(save_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)

        img.save(save_path)
        return save_path


class ChartAnalysisService:
    """
    아래 작업을 수행하기 위한 서비스:
    # 이미지 파일을 받아서 바로 YOLO 분석
    """
    def __init__(self):
        self.fetcher = DataFetcher()
        self.generator = ChartGenerator()
        self.preprocessor = ImagePreprocessor()
        self.detector = YOLODetector()
        self.visualizer = ResultVisualizer()

    def analyze_image(self, image_file, user):
        """
        1) 업로드된 차트 이미지를 받아서 전처리 → YOLO 추론 → 시각화
        image_file: Django InMemoryUploadedFile 또는 파일 객체
        리턴: (result_image_path, pattern_label)
        """
        # 1) 업로드된 이미지를 로컬에 임시 저장 (예: media/temp.png)
        temp_filename = f"temp_{image_file.name}"
        temp_path = os.path.join(settings.MEDIA_ROOT, temp_filename)
        with open(temp_path, "wb+") as f:
            for chunk in image_file.chunks():
                f.write(chunk)

        # 2) 이미지 전처리
        #processed_img = self.preprocessor.preprocess(temp_path)

        # 3) YOLO 추론
        results = self.detector.predict(temp_path)

        # 4) 결과 시각화 → result_filename 반환
        result_filename = f"result_{image_file.name}"
        result_path = os.path.join("media", result_filename)
        abs_result_path = os.path.join(settings.BASE_DIR, result_path)
        self.visualizer.overlay_results(temp_path, results, abs_result_path)

        # 5) 패턴 레이블(가장 높은 confidence로 분류된 클래스 이름) 리턴
        ''' 11/03 합병 주석처리
        if results and results[0].boxes:
            top_box = results[0].boxes[0]
            cls_idx = int(top_box.cls[0])  # 클래스 인덱스
            pattern_label = results[0].names[cls_idx]  # 클래스 이름
        else:
            pattern_label = "No Pattern Detected"
        '''

        '''
        rec = ChartAnalysisHistory.objects.create(
            user=user,  # 로그인 안했으면 None
            request_type="upload",  # or "symbol"
            original_image=result_path,  # 업로드일 때만 실제 파일
            symbol=sym,
            start_date=pd.to_datetime(start_iso).date() if start_iso else None,
            end_date=pd.to_datetime(end_iso).date() if end_iso else None,
            interval=interval,  # "1d" / "1h" / "15m"
            patterns=patterns,  # [{"label":..., "conf":...}]
            result_image=result_rel,  # MEDIA_ROOT 기준 상대경로
        )
        '''
        ''' 11/03 합병 주석처리
        return (result_path, pattern_label)
        '''
        #여기부터 수정코드 10/29
        pattern_labels = [] # 기본값 (빈 리스트)
        if results and results[0].boxes and len(results[0].boxes) > 0:
            detected_names = set() # 중복 제거를 위해 set 사용
            for box in results[0].boxes:
                cls_idx = int(box.cls[0])
                detected_names.add(results[0].names[cls_idx])
            pattern_labels = list(detected_names) # JSON으로 보내기 위해 list로 변환

        # 11.12 수정코드, DB 저장 로직 추가
        history_id = _save_analysis_history(
            user=user, sym="IMAGE_UPLOAD", interval="N/A",
            start_dt=None, end_dt=None,
            result_rel=result_path, result_url=abs_result_path, patterns=pattern_labels
        )
        #out["history_id"] = history_id
        # 여기까지 11.12 수정코드

        return (result_path, pattern_labels)
        #여기까지 수정코드 10/29


# -------- YOLO 로더(프로세스당 1회 로드) --------
_YOLO = None
def get_yolo():
    global _YOLO
    if _YOLO is None:
        model_path = getattr(settings, "YOLO_MODEL_PATH", None)
        if not model_path or not os.path.exists(model_path):
            return None
        from ultralytics import YOLO
        _YOLO = YOLO(model_path)
    return _YOLO


# -------- YOLO 오버레이 --------
def overlay_yolo(image_path: str, yolo_result, out_path: str, class_names: Dict[int, str]) -> str:
    im = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(im)
    try:
        # 시스템에 없는 경우 자동 기본 폰트 사용
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=26)
    except Exception:
        font = ImageFont.load_default()

    boxes = yolo_result.boxes
    if boxes is None or len(boxes) == 0:
        im.save(out_path)
        return out_path

    xyxy = boxes.xyxy.cpu().numpy()
    cls  = boxes.cls.cpu().numpy().astype(int)
    conf = boxes.conf.cpu().numpy()

    W, H = im.size
    for i, (x1, y1, x2, y2) in enumerate(xyxy):
        x1 = max(0, int(x1)); y1 = max(0, int(y1))
        x2 = min(W-1, int(x2)); y2 = min(H-1, int(y2))
        label = class_names.get(cls[i], str(cls[i]))
        score = float(conf[i])
        text  = f"{label} {score:.2f}"

        # 박스
        draw.rectangle([x1, y1, x2, y2], outline=(0, 255, 0), width=3)

        # 라벨 배경
        tb = draw.textbbox((0, 0), text, font=font)
        tw, th = tb[2]-tb[0], tb[3]-tb[1]
        tx, ty = x1, max(0, y1 - th - 6)
        draw.rectangle([tx, ty, tx + tw + 10, ty + th + 4], fill=(0, 255, 0))
        draw.text((tx + 5, ty + 2), text, font=font, fill=(0, 0, 0))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im.save(out_path)
    return out_path

def _secs_per(tf: str) -> int:
    tf = tf.lower()
    return {
        "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
        "1h": 3600, "4h": 14400, "1d": 86400, "1w": 604800
    }.get(tf, 86400)

class BySymbolAnalysisService:
    """
    프런트에서 symbol/startDate/endDate/interval이 오면:
      1) 데이터 수집 (yfinance 또는 ccxt)
      2) sanitize_ohlcv 적용
      3) 캔들 이미지 생성
      4) (선택) YOLO 추론 및 결과 오버레이
      5) result_url 반환
    """
    def run(self, *, user, symbol: str, start_date: str, end_date: str, interval: str):
        start_iso = parse_date_str(start_date) if start_date else None
        end_iso   = parse_date_str(end_date) if end_date else None

        sym = symbol.strip().upper()

        # ---- 1) 데이터 수집 ---------------------------------------------------
        if sym.endswith("USDT"):  # 코인(CCXT)
            tf = map_interval(interval, source="ccxt")
            start_dt = pd.to_datetime(start_iso) if start_iso else None
            end_dt   = pd.to_datetime(end_iso)   if end_iso   else None
            since_ms = int(start_dt.tz_localize("UTC").timestamp() * 1000) if start_dt is not None else None

            limit = 1000
            if start_dt is not None and end_dt is not None:
                secs = max(1, (end_dt - start_dt).total_seconds())
                limit = min(5000, int(secs / _secs_per(tf)) + 10)

            df = fetch_ccxt(f"{sym[:-4]}/USDT", timeframe=tf, since_ms=since_ms, limit=limit)

            # 정확히 기간 슬라이스(UTC)
            if start_dt is not None:
                df = df[df.index >= start_dt.tz_localize("UTC")]
            if end_dt is not None:
                df = df[df.index <= end_dt.tz_localize("UTC")]
        else:  # 주식/ETF 등(Yahoo)
            yf_symbol = sym if not sym.endswith("USDT") else f"{sym[:-4]}-USD"

            print(f"[BySymbol] sym={yf_symbol} interval={interval} start={start_iso} end={end_iso}")
            df = fetch_yf(yf_symbol, start_iso, end_iso, interval)  # '1d' / '1h' / '15m' 그대로 전달

        # ---- 2) 정제 & UTC 일관성 ---------------------------------------------
        df = sanitize_ohlcv(df)  # (기존 함수 그대로)
        if df.index.tz is None:                          # ★ UTC tz-aware 보장
            df.index = pd.to_datetime(df.index, utc=True)
        else:
            df.index = df.index.tz_convert("UTC")

        # ---- 2-1) 과도한 포인트 자동 축소(OHLC 리샘플링) -----------------------
        df = auto_downsample(df, base_interval=interval, max_points=3500)   # ★ 추가

        if df.empty:
            # 프론트가 빈 이미지도 잘 처리할 수 있게 pattern 없이 URL만 돌려줌
            filename_base = f"symbol_{uuid.uuid4().hex}"
            chart_rel = os.path.join("results", f"{filename_base}.png").replace("\\", "/")
            chart_abs = os.path.join(settings.MEDIA_ROOT, chart_rel)
            render_candlestick(df, chart_abs, interval=interval,
                               display_tz=getattr(settings, "DISPLAY_TZ", "Asia/Seoul"),
                               title=f"{sym} ({interval})")
            # ... URL 구성 후 반환
            # (이 경우 patterns는 []이므로 프론트에 "없음" 표시)

        # ---- 3) 차트 PNG 생성 -------------------------------------------------
        else:
            # 정상 렌더
            filename_base = f"symbol_{uuid.uuid4().hex}"
            chart_rel = os.path.join("results", f"{filename_base}.png").replace("\\", "/")
            chart_abs = os.path.join(settings.MEDIA_ROOT, chart_rel)

            render_candlestick(
                df, chart_abs,
                interval=interval,
                display_tz=getattr(settings, "DISPLAY_TZ", "Asia/Seoul"),
                title=f"{sym} ({interval})",
            )

        # ---- 4) YOLO 감지 & 오버레이 -----------------------------------------
        patterns: List[Dict] = []
        result_rel, result_abs = chart_rel, chart_abs

        yolo = get_yolo()
        if yolo is not None:
            conf_th = float(getattr(settings, "YOLO_CONF", 0.35))
            iou_th  = float(getattr(settings, "YOLO_IOU", 0.50))
            imgsz   = int(getattr(settings, "YOLO_IMGSZ", 960))

            yres = yolo.predict(
                source=chart_abs, conf=conf_th, iou=iou_th,
                imgsz=imgsz, max_det=100, verbose=False
            )[0]

            names = getattr(yolo, "names", None) or getattr(getattr(yolo, "model", None), "names", {}) or {}

            ov_rel = os.path.join("results", f"{filename_base}_det.png").replace("\\", "/")
            ov_abs = os.path.join(settings.MEDIA_ROOT, ov_rel)
            overlay_yolo(chart_abs, yres, ov_abs, names)

            result_rel, result_abs = ov_rel, ov_abs

            if yres.boxes is not None and len(yres.boxes) > 0:
                for i in range(len(yres.boxes)):
                    cls_i  = int(yres.boxes.cls[i].item())
                    conf_i = float(yres.boxes.conf[i].item())
                    patterns.append({"label": names.get(cls_i, str(cls_i)), "conf": round(conf_i, 3)})

            # ---- 절대 URL + 캐시버스터
            media_url = f"{settings.MEDIA_URL}{result_rel}"
            cb = uuid.uuid4().hex
            if getattr(settings, "EXTERNAL_BASE_URL", ""):
                base = settings.EXTERNAL_BASE_URL.rstrip("/")
                result_url = f"{base}{media_url}?cb={cb}"
            else:
                result_url = f"{media_url}?cb={cb}"

            # ---- 저장 (여기 추가)
            # start_dt / end_dt가 위에서 분기별로 다르게 계산되었다면 통일:
            try:
                sdt = pd.to_datetime(start_date) if start_date else None
                edt = pd.to_datetime(end_date) if end_date else None
                if sdt is not None:
                    sdt = (sdt.tz_localize("UTC") if sdt.tz is None else sdt.tz_convert("UTC")).to_pydatetime()
                if edt is not None:
                    edt = (edt.tz_localize("UTC") if edt.tz is None else edt.tz_convert("UTC")).to_pydatetime()
            except Exception:
                sdt = edt = None

            history_id = _save_analysis_history(
                user=user, sym=sym, interval=interval,
                start_dt=sdt, end_dt=edt,
                result_rel=result_rel, result_url=result_url, patterns=patterns
            )

        return {
            "result_url": result_url,
            "result_rel": result_rel,
            "symbol": sym,
            "patterns": patterns,
            "history_id": history_id,  # ← 프론트로 id도 내려주면 추후 개별 조회/공유가 수월
        }


logger = logging.getLogger(__name__)

def _save_analysis_history(*, user, sym, interval, start_dt, end_dt,
                           result_rel, result_url, patterns) -> int | None:
    """ChartAnalysisHistory 1건을 저장하고 PK를 반환. 실패 시 None."""
    try:
        from .models import ChartAnalysisHistory
    except Exception as e:
        logger.exception("ChartAnalysisHistory import 실패: %s", e)
        return None

    try:
        with transaction.atomic():
            obj = ChartAnalysisHistory.objects.create(
                user=user if (getattr(user, "is_authenticated", False)) else None,
                symbol=sym,
                interval=interval,
                start_dt=start_dt,
                end_dt=end_dt,
                image_rel=result_rel,
                result_url=result_url,
                patterns=patterns or [],
            )
            return obj.pk
    except Exception as e:
        logger.exception("ChartAnalysisHistory 저장 실패: %s", e)
        return None