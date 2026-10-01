# YOLO 가중치

용량 문제로 가중치 파일은 레포에 포함하지 않았습니다. 아래 두 파일을 이 폴더에 두어야 분석 API가 동작합니다.

| 파일 | 사용처 |
|---|---|
| `best.pt` | 종목·기간 기반 분석 (`ChartAnalysis/settings.py`의 `YOLO_MODEL_PATH`) |
| `model_0608.pt` | 업로드 이미지 분석 (`chartapp/services.py`의 `YOLODetector`) |
