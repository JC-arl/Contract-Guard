from pydantic import BaseModel


class OcrBox(BaseModel):
    # PaddleOCR 의 검출 박스는 4점 다각형(시계방향 좌상→우상→우하→좌하).
    # 회전된 텍스트도 다루기 위해 사각형이 아닌 polygon 으로 보존한다.
    poly: list[list[float]]
    text: str
    score: float


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
