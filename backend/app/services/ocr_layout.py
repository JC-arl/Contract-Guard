"""PP-Structure 기반 레이아웃 분석 — 제목/본문/표/그림 영역 분리.

목적은 PaddleOCR 의 박스 단위 출력을 영역 단위로 분류해 후속 처리(영역별 OCR 단위 결정,
표 셀 그룹화, 서명/도장 분리)에 라우팅하는 것. 모델 자체의 OCR/표 인식 기능은 비활성화하고
**레이아웃 영역 좌표만** 가져온다 — 텍스트 인식은 이미 튜닝된 PaddleOCR(ocr_service) 이 담당.

한국어 fine-tune 모델이 없어 PubLayNet(영문) 모델로 동작한다. 분류 정확도가 일정치 않으니
ocr_use_layout=False 로 끄는 폴백 경로를 항상 유지한다.
"""
from __future__ import annotations

from backend.app.config import settings
from backend.app.models.ocr import OcrBox, OcrRegion

_layout = None  # type: ignore[var-annotated]

# PubLayNet 라벨 — PP-Structure 가 반환하는 type 문자열(소문자).
# 'figure' 는 보통 그림/로고/서명 박스. text 분석에서 제외해 노이즈를 줄인다.
_DECORATION_TYPES = frozenset({"figure"})


def get_layout():
    """PPStructure 싱글턴. lazy init — 첫 호출 시 ~수백MB 모델 다운로드.

    옵션:
    - layout=True, ocr=False, table=False — 레이아웃 영역만 검출, 내부 OCR/표 추론 비활성.
    - lang — 레이아웃 모델 사전은 'en'(PubLayNet) / 'ch'(CDLA) 만 존재.
      한국어는 사전에 없어 'korean' 을 넘기면 paddleocr 의 get_model_config 가 sys.exit 한다.
      한국어 계약서에선 CDLA(ch) 가 PubLayNet(en) 보다 본문/표 구분이 안정적이다 — 후자는
      한국어 본문을 'figure' 로 몰아붙이는 경향이 있어 모델 자체를 폴백시키는 일이 잦다.
    """
    global _layout
    if _layout is None:
        from paddleocr import PPStructure  # 지연 import — 모듈 로딩 비용 격리

        use_gpu = settings.ocr_device.lower() == "gpu"
        lang = settings.ocr_layout_lang if settings.ocr_layout_lang in ("ch", "en") else "ch"
        _layout = PPStructure(
            layout=True,
            ocr=False,         # 내부 text_system 비활성 — ocr_service 의 PaddleOCR 사용
            table=False,       # 표 구조 인식은 Phase C 에서 별도 싱글턴
            formula=False,
            show_log=False,
            lang=lang,
            use_gpu=use_gpu,
        )
    return _layout


def reset_layout() -> None:
    """설정 변경 후 강제 재초기화 (embedding_service/llm_service 와 같은 패턴)."""
    global _layout
    _layout = None


def _normalize_bbox(bbox) -> list[float] | None:
    """PP-Structure bbox 는 [x1, y1, x2, y2] (int). None 일 수 있음(전체 이미지)."""
    if bbox is None:
        return None
    try:
        x1, y1, x2, y2 = (float(v) for v in bbox)
        return [x1, y1, x2, y2]
    except (TypeError, ValueError):
        return None


def detect_regions(np_image) -> list[OcrRegion]:
    """이미지에서 레이아웃 영역 리스트를 검출. 실패 또는 신뢰 불가 시 빈 리스트.

    PP-Structure 가 반환하는 dict 중 type/bbox/score 만 추출. img(ndarray)/res 는 버린다
    (응답 페이로드 비대화 방지).

    세이프가드: figure 비율이 ocr_layout_figure_max_ratio 초과면 결과를 통째로 버린다.
    PubLayNet/CDLA 가 한국어 계약서를 거의 전부 'figure' 로 오분류하는 사례가 흔해서,
    이런 경우 raw 박스만으로 처리하는 편이 잘못된 색 분류보다 사용자에게 정직하다.
    """
    try:
        raw = get_layout()(np_image)
    except Exception:
        # 모델 로딩/추론 실패는 무음 폴백 — raw 박스만으로 동작하도록.
        return []

    regions: list[OcrRegion] = []
    for item in raw or []:
        try:
            bbox = _normalize_bbox(item.get("bbox"))
            if bbox is None:
                continue
            region_type = str(item.get("type", "")).lower() or "unclassified"
            score = float(item.get("score", 0.0) or 0.0)
            regions.append(OcrRegion(bbox=bbox, region_type=region_type, score=score))
        except (AttributeError, TypeError, ValueError):
            continue

    # figure 비율 세이프가드 — 임계값 초과면 레이아웃 결과 자체를 버림.
    threshold = settings.ocr_layout_figure_max_ratio
    if regions and 0 < threshold < 1.0:
        figure_count = sum(1 for r in regions if r.region_type == "figure")
        if figure_count / len(regions) > threshold:
            return []

    return regions


def _box_center(poly: list[list[float]]) -> tuple[float, float]:
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _bbox_area(bbox: list[float]) -> float:
    x1, y1, x2, y2 = bbox
    return max(0.0, (x2 - x1)) * max(0.0, (y2 - y1))


def assign_regions(
    boxes: list[OcrBox],
    regions: list[OcrRegion],
) -> list[OcrBox]:
    """각 박스 중심점이 포함되는 region 을 찾아 region_type/is_decoration 부여.

    두 개 이상의 region 이 중심점을 포함하면 **더 작은 면적의 region** 을 우선한다
    (큰 영역이 작은 영역을 감싸는 경우 작은 쪽이 더 구체적이라고 가정).

    어떤 region 에도 속하지 않는 박스의 처리:
      - regions 가 비어 있음 (레이아웃 off/실패/세이프가드 발동): region_type=None
      - regions 가 있지만 매칭 실패: region_type='text' 로 기본 처리
        (CDLA 가 표/제목/그림만 명시 라벨링하고 본문은 묵시 처리하는 경향이 있어,
         "특수 영역 밖 = 본문" 으로 가정하는 편이 'unclassified' 보다 사용자에게 유용하다.
         잘못 분류된 케이스는 색만 빨강으로 보일 뿐 OCR 결과 자체는 그대로 보존됨.)
    """
    if not regions:
        return [
            b.model_copy(update={"region_type": None, "is_decoration": False})
            for b in boxes
        ]

    # 면적 오름차순으로 정렬해 작은 region 이 먼저 매칭되게 함.
    sorted_regions = sorted(regions, key=lambda r: _bbox_area(r.bbox))

    result: list[OcrBox] = []
    for box in boxes:
        cx, cy = _box_center(box.poly)
        matched_type: str | None = None
        for region in sorted_regions:
            x1, y1, x2, y2 = region.bbox
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                matched_type = region.region_type
                break

        region_type = matched_type or "text"
        is_decoration = region_type in _DECORATION_TYPES
        result.append(
            box.model_copy(update={"region_type": region_type, "is_decoration": is_decoration})
        )
    return result


def warmup() -> None:
    """startup 워밍업 — 첫 요청 지연 감소. 실패는 무시(첫 실제 요청에서 재시도)."""
    if not settings.ocr_use_layout:
        return
    try:
        import numpy as np

        get_layout()
        dummy = np.zeros((64, 64, 3), dtype=np.uint8)
        get_layout()(dummy)
    except Exception:
        pass
