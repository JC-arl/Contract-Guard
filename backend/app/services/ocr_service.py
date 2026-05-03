"""PaddleOCR 기반 한국어 텍스트 추출 + 박스 오버레이 렌더링.

구조는 embedding_service.py / llm_service.py 의 모듈 전역 싱글턴 패턴을 따른다.
첫 호출 시 ~200MB 모델 다운로드가 일어나므로 startup 워밍업과 함께 사용 권장.
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

from backend.app.config import settings
from backend.app.models.ocr import OcrBox, OcrResult

# decompression bomb 보호 (DoS 방지). Pillow 기본 ~89M 픽셀.
Image.MAX_IMAGE_PIXELS = 50_000_000

_ocr = None  # type: ignore[var-annotated]
_font_cache: dict[int, ImageFont.FreeTypeFont] = {}


def get_ocr():
    """PaddleOCR 싱글턴. lazy init — 첫 호출 시 모델 다운로드."""
    global _ocr
    if _ocr is None:
        # 지연 import — paddleocr 가 무거워서 모듈 import 단계에서 끌어오지 않는다.
        from paddleocr import PaddleOCR

        use_gpu = settings.ocr_device.lower() == "gpu"
        # 휴대폰 촬영 계약서처럼 미세 흐림·종이 굴곡이 있는 입력에서 detection 누락을 줄이기 위한 튜닝.
        # 기본값(0.5 / 1.6 / 0.3)은 깔끔한 스캔 기준이라 사진 입력에선 본문 작은 글씨를 자주 놓친다.
        # 임계 완화 → 박스 검출 증가(트레이드오프: false positive 약간 증가).
        # det_limit_side_len: PaddleOCR 가 detection 단계에서 입력 이미지를 내부적으로 재축소하는 상한.
        # 기본 960 이라 ocr_max_image_dim 을 4096 으로 올려도 detection 단에서 다시 960 으로 줄어들어
        # 본문 작은 글씨가 픽셀 단위로 뭉개진다. 사진 입력 계약서는 2048~2560 권장.
        # 트레이드오프: detection 시간이 (값/960)^2 비례로 증가 (GPU 면 견딜 만, CPU 면 페이지당 10~20초).
        _ocr = PaddleOCR(
            use_angle_cls=settings.ocr_use_angle_cls,
            lang=settings.ocr_lang,
            use_gpu=use_gpu,
            show_log=False,
            det_db_thresh=0.2,         # 픽셀 임계 (default 0.3)
            det_db_box_thresh=0.3,     # 박스 채택 임계 (default 0.5)
            det_db_unclip_ratio=2.0,   # 박스 확장 비율 (default 1.6)
            det_db_score_mode='slow',  # 점수 계산 방식 (default 'fast', 'slow' 는 작은 글씨 인식 개선)
            det_limit_side_len=2560,   # detection 입력 상한 (default 960) — 작은 글씨 누락 핵심 해결
            det_limit_type='max',      # 긴 변 기준 ('min' 이면 짧은 변 기준)
        )
    return _ocr


def reset_ocr() -> None:
    """설정 변경 후 강제 재초기화."""
    global _ocr
    _ocr = None


# 한글 합성용 폰트 후보 — settings.ocr_font_path 가 없을 때 운영체제 기본 폰트를 시도.
# OpenCV putText 는 한글 미지원이고 PIL load_default 도 라틴만 그릴 수 있어
# 한글이 들어오면 □ 로 깨지므로 시스템 한글 폰트를 폴백으로 둔다.
_FONT_FALLBACKS = (
    r"C:\Windows\Fonts\malgun.ttf",                            # Windows 맑은 고딕
    r"C:\Windows\Fonts\NanumGothic.ttf",                       # Windows 나눔고딕
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",         # Ubuntu
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",              # macOS
)


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """폰트 객체 캐시. truetype 로딩이 비싸므로 size 별로 보관."""
    if size not in _font_cache:
        for path in (settings.ocr_font_path, *_FONT_FALLBACKS):
            try:
                _font_cache[size] = ImageFont.truetype(path, size)
                break
            except OSError:
                continue
        else:
            _font_cache[size] = ImageFont.load_default()  # 한글 깨짐 가능
    return _font_cache[size]


def _prepare_image(image_path: str) -> Image.Image:
    """EXIF 회전 적용 + RGB 변환 + 다운샘플."""
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)  # 좌표가 화면 표시와 어긋나는 사고 방지
    if img.mode != "RGB":
        img = img.convert("RGB")

    max_dim = settings.ocr_max_image_dim
    if max(img.size) > max_dim:
        img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    return img


def _run_paddle(np_image: np.ndarray) -> list[tuple[list[list[float]], str, float]]:
    """PaddleOCR 호출 — 동기. 결과를 (poly, text, score) 튜플 리스트로 정규화.

    PaddleOCR 의 반환 포맷은 버전에 따라 약간씩 다른데 보통:
      [[ [poly, (text, score)], [poly, (text, score)], ... ]]   # 페이지 단위
    또는 빈 페이지면 [None] / [] 가 올 수 있다.
    """
    raw = get_ocr().ocr(np_image, cls=settings.ocr_use_angle_cls)
    if not raw:
        return []
    page = raw[0] if isinstance(raw, list) else raw
    if not page:
        return []

    out: list[tuple[list[list[float]], str, float]] = []
    for item in page:
        # item: [poly, (text, score)]
        try:
            poly_raw, txt_score = item[0], item[1]
            text, score = txt_score[0], float(txt_score[1])
            poly = [[float(p[0]), float(p[1])] for p in poly_raw]
            out.append((poly, text, score))
        except (IndexError, TypeError, ValueError):
            continue
    return out


async def run_ocr(image_path: str) -> tuple[OcrResult, Image.Image]:
    """이미지 경로를 받아 OCR 결과와 (다운샘플·EXIF 적용된) PIL 이미지를 반환.

    호출자가 prepared 이미지를 그대로 _orig.png 로 저장하면 박스 좌표와 표시 이미지가 정합한다.
    """
    started = time.perf_counter()
    img = _prepare_image(image_path)
    np_image = np.array(img)  # RGB; PaddleOCR 는 RGB/BGR 모두 동작

    raw_boxes = await asyncio.to_thread(_run_paddle, np_image)
    boxes = [OcrBox(poly=p, text=t, score=s) for (p, t, s) in raw_boxes]

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    result = OcrResult(
        width=img.width,
        height=img.height,
        elapsed_ms=elapsed_ms,
        boxes=boxes,
    )
    return result, img


def render_overlay(prepared_image: Image.Image, result: OcrResult, out_path: str) -> str:
    """박스 polygon + 한국어 라벨을 합성해 PNG 로 저장. 저장 경로를 반환.

    OpenCV 로 polygon 외곽선만 그리고, 텍스트는 PIL ImageDraw + TrueType 으로 합성한다
    (cv2.putText 는 한글 미지원).
    """
    # OpenCV 는 BGR 을 기대하므로 일시 변환
    bgr = cv2.cvtColor(np.array(prepared_image), cv2.COLOR_RGB2BGR)
    for box in result.boxes:
        pts = np.array(box.poly, dtype=np.int32).reshape(-1, 1, 2)
        cv2.polylines(bgr, [pts], isClosed=True, color=(0, 0, 255), thickness=2)
    annotated = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))

    draw = ImageDraw.Draw(annotated, "RGBA")
    for box in result.boxes:
        xs = [p[0] for p in box.poly]
        ys = [p[1] for p in box.poly]
        min_x, min_y = min(xs), min(ys)
        max_y = max(ys)
        # 박스 높이 기반 폰트 크기 (최소 12, 최대 28). 박스가 작은 OCR 결과의 가독성 확보.
        font_size = max(12, min(28, int((max_y - min_y) * 0.6)))
        font = _get_font(font_size)

        # textbbox 로 라벨 배경 사각형 너비 계산
        tb = draw.textbbox((0, 0), box.text, font=font)
        tw, th = tb[2] - tb[0], tb[3] - tb[1]
        label_x = int(min_x)
        label_y = int(min_y) - th - 4
        # 화면 위쪽을 벗어나면 박스 안쪽 위로 폴백
        if label_y < 0:
            label_y = int(min_y) + 2

        # 반투명 배경
        draw.rectangle(
            [label_x, label_y, label_x + tw + 6, label_y + th + 4],
            fill=(255, 0, 0, 160),
        )
        draw.text((label_x + 3, label_y + 1), box.text, fill=(255, 255, 255, 255), font=font)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    annotated.save(out_path, format="PNG", optimize=False)
    return out_path


def save_prepared(prepared_image: Image.Image, out_path: str) -> str:
    """OCR 입력으로 사용한 (EXIF 회전 + 다운샘플) 이미지를 PNG 로 저장.

    프론트가 이 이미지를 띄우고 SVG 오버레이를 그려야 박스 좌표가 정확히 맞는다.
    """
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    prepared_image.save(out_path, format="PNG", optimize=False)
    return out_path


def warmup() -> None:
    """startup 이벤트에서 호출 — 첫 요청 응답 지연을 줄이기 위한 모델 로딩 트리거."""
    try:
        get_ocr()
        # 1x1 픽셀 dummy 이미지로 가중치 워밍업 (선택)
        dummy = np.zeros((32, 32, 3), dtype=np.uint8)
        _run_paddle(dummy)
    except Exception:
        # 워밍업 실패는 치명적이지 않음 — 첫 실제 요청에서 다시 시도된다.
        pass
