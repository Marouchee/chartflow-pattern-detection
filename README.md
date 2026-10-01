# ChartFlow — 캔들차트 패턴 탐지 웹 플랫폼

홍익대학교 컴퓨터공학과 졸업 프로젝트 (2025, 2인 팀)

종목·기간·봉 간격을 고르면 시세를 받아 캔들차트를 그리고, YOLOv8로 11개 가격 패턴을 탐지해 결과 이미지와 패턴별 매매 전략 가이드를 보여 줍니다. 차트 이미지를 직접 올려 분석할 수도 있습니다.

> 원본 레포는 비공개입니다. 이 레포는 공개용으로 정리한 사본입니다. DB 파일, 모델 가중치, IDE 설정은 빼고 올렸고 커밋 히스토리는 담지 않았습니다.

<!-- 스크린샷: docs/screenshot.png 를 추가한 뒤 아래 줄의 주석을 푸세요 -->
<!-- ![분석 결과 화면](docs/screenshot.png) -->

## 역할 분담

| 구성원 | 담당 |
|---|---|
| 송범규 | 시세 수집·정규화, OHLC 리샘플링, 차트 렌더링, YOLO 추론·오버레이, 분석 API와 분석 이력 저장, 차트 분석 화면, 모델 학습용 차트 이미지 수집 |
| 팀원 | 회원가입·JWT 인증, 모의투자(포지션·주문·TP/SL·청산), 마이페이지 화면 |

## 분석 흐름

```
종목 / 기간 / 봉 간격
 ↓
시세 수집      코인(…USDT)은 ccxt(바이낸스), 주식·ETF는 yfinance
 ↓
정규화         컬럼 평탄화 → 표준 OHLCV, 숫자 변환, 인덱스 UTC 고정, 모순된 봉 제거
 ↓
리샘플링       캔들이 3,500개를 넘으면 OHLC 집계 규칙으로 단계적 축소
 ↓
차트 렌더링    mplfinance (서버용 Agg 백엔드), 표시 시간대 Asia/Seoul
 ↓
YOLOv8 추론    conf 0.35 · IoU 0.50 · imgsz 960, 모델은 프로세스당 1회 로드
 ↓
결과           박스·라벨 오버레이 이미지 + 패턴 목록 응답, 분석 이력 저장
```

코드 위치: `chartapp/chart_data.py`(수집·정규화) → `chartapp/downsample.py`(리샘플링) → `chartapp/plotting.py`(렌더링) → `chartapp/services.py`(추론·저장)

## 설계 포인트

**출처가 달라도 같은 형태로 만든다**
yfinance는 MultiIndex 컬럼과 대소문자가 섞인 컬럼명을 돌려주고, ccxt는 밀리초 타임스탬프 배열을 돌려줍니다. 두 응답을 모두 `Open/High/Low/Close/Volume` 컬럼과 UTC 인덱스로 통일했습니다. 그래서 렌더링과 추론 단계는 데이터 출처를 몰라도 됩니다.

**봉 간격과 기간을 소스별 규칙에 맞춘다**
- 프런트의 봉 간격 값을 소스별 토큰으로 바꿉니다(예: `1h` → yfinance `60m`, ccxt `1h`).
- yfinance 분·시간봉은 날짜 범위 대신 기간 토큰(`1mo`, `3mo` …)으로 받은 뒤 요청 구간을 UTC 기준으로 잘라 냅니다.
- ccxt는 요청 기간 ÷ 봉 길이로 필요한 개수를 계산합니다(최대 5,000).

**패턴 모양을 지키며 줄인다**
캔들이 너무 많으면 차트가 뭉개져 탐지가 어렵습니다. 단순히 n개마다 하나씩 뽑으면 고가·저가를 놓쳐 패턴 모양이 바뀝니다. 그래서 `first / max / min / last / sum` 규칙으로 더 긴 봉으로 리샘플링하고(예: 15분 → 30분 → 1시간 …), 간격 추출은 최후 수단으로만 씁니다.

**잘못된 봉은 입력 단계에서 버린다**
`High < Low`이거나 시가·종가가 고가·저가 범위를 벗어난 봉은 정규화 단계에서 제거합니다. 이런 봉이 남으면 차트 모양이 틀어져 오탐으로 이어집니다.

**부가 기능의 실패가 분석을 막지 않는다**
분석 이력은 `transaction.atomic`으로 1건씩 저장합니다. 저장에 실패해도 로그만 남기고 분석 결과는 정상 반환합니다.

## 탐지 패턴 (11종)

| 유형 | 패턴 |
|---|---|
| 하락형 | 헤드 앤 숄더, 이중 천장, 삼중 천장, 상승 쐐기 |
| 상승형 | 리버스 헤드 앤 숄더, 이중 바닥, 삼중 바닥, 하락 쐐기, 컵 앤 핸들 |
| 복합형 | 삼각수렴, 직사각형 |

패턴별 설명과 매매 전략은 `react_app/src/data/strategyGuide.js`에 있습니다.

## 기술 스택

| 영역 | 기술 |
|---|---|
| Backend | Python 3.11, Django 5.2, Django REST Framework, SimpleJWT, SQLite |
| Data · ML | pandas, yfinance, ccxt, mplfinance, ultralytics YOLOv8 |
| Frontend | React (Create React App), React Router, Zustand, Recharts, Tailwind CSS |

## 디렉터리

```
ChartAnalysis/   Django 설정, URL
chartapp/        차트 수집·정규화·리샘플링·렌더링·YOLO 분석, 분석 이력, 마이페이지 API
accounts/        회원가입, JWT 인증
papertrade/      모의투자 API
react_app/       프런트엔드
models/          YOLO 가중치 위치 (레포 미포함, models/README.md 참고)
```

## 실행

```bash
# 백엔드
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
mkdir -p media/results
python manage.py migrate
python manage.py runserver            # http://localhost:8000

# 프런트엔드 (API는 8000번으로 프록시)
cd react_app && npm install && npm start   # http://localhost:3000
```

- YOLO 가중치 두 개를 `models/`에 두어야 분석 API가 동작합니다. 자세한 내용은 [models/README.md](models/README.md)에 있습니다.
- 환경변수 `DJANGO_SECRET_KEY`를 지정하지 않으면 실행할 때마다 임시 키가 만들어집니다. 이 경우 서버를 재시작하면 기존 로그인 토큰이 무효가 됩니다.

## 결과와 한계

- 졸업 전시회에서 3일간 시연했습니다. 배포는 하지 않았고 설정은 로컬 개발용입니다(DEBUG, SQLite, localhost CORS).
- 패턴 판별 정확도는 약 60%에 머물렀습니다. 학습용 차트 이미지가 부족했던 것이 주원인입니다. 종목 기반 차트 생성 흐름을 학습 데이터를 늘리는 데 쓰는 것이 다음 개선 방향입니다.
