from pydantic import BaseModel


class OcrBox(BaseModel):
    # PaddleOCR 의 검출 박스는 4점 다각형(시계방향 좌상→우상→우하→좌하).
    # 회전된 텍스트도 다루기 위해 사각형이 아닌 polygon 으로 보존한다.
    poly: list[list[float]]
    text: str
    score: float
    # LLM 보정 후 채워지는 교정 텍스트. None 이면 보정 안 한 상태.
    # 프론트에서 원본/보정/diff 토글로 비교 가능.
    corrected_text: str | None = None


class OcrCorrectRequest(BaseModel):
    """LLM 보정 요청 — 클라이언트가 직전 OCR 응답의 boxes 를 그대로 다시 보낸다.
    백엔드에 결과를 영속화하지 않아 클라이언트가 상태를 들고 있는 단순한 구조.
    """
    boxes: list[OcrBox]


class OcrCorrectResponse(BaseModel):
    boxes: list[OcrBox]
    elapsed_ms: int


class OcrResult(BaseModel):
    width: int
    height: int
    elapsed_ms: int
    boxes: list[OcrBox]


class OcrResponse(BaseModel):
    document_id: str
    image_url: str    # 원본(EXIF 회전 적용본) PNG 서빙 경로
    overlay_url: str  # 박스+한글 라벨 합성 PNG 서빙 경로
    result: OcrResult
