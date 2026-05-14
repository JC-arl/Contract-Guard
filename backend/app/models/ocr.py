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
    # PP-Structure 레이아웃 분석으로 부여한 영역 타입.
    # PubLayNet 라벨: text / title / list / table / figure. 어디에도 속하지 않으면 'unclassified'.
    # None 이면 레이아웃 분석을 건너뛴(비활성·실패) 상태.
    region_type: str | None = None
    # 서명/도장/그림 영역 후보 — 분석 단위에서 제외해야 하는 박스.
    # 현재 region_type == 'figure' 이거나 신뢰도 낮은 unclassified 박스에 부여.
    is_decoration: bool = False


class OcrRegion(BaseModel):
    """PP-Structure 가 검출한 레이아웃 영역.

    bbox 는 [x1, y1, x2, y2] 사각형. region_type 은 PubLayNet 라벨(소문자).
    영역 단위로 색상을 다르게 그리거나 후속 처리(셀 단위 OCR 등)에 라우팅한다.
    """
    bbox: list[float]
    region_type: str
    score: float = 0.0


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
    # 레이아웃 분석 결과. 미사용(설정 off / 모델 실패) 시 빈 리스트.
    regions: list[OcrRegion] = []


class OcrResponse(BaseModel):
    document_id: str
    image_url: str    # 원본(EXIF 회전 적용본) PNG 서빙 경로
    overlay_url: str  # 박스+한글 라벨 합성 PNG 서빙 경로
    result: OcrResult
