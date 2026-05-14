"""OCR 검증 전용 엔드포인트.

분석 파이프라인(`/api/documents/upload`)과 분리되어 있다 — 이미지에서 텍스트가
얼마나 정확히 추출되는지 시각적으로 확인하는 단계까지만 책임진다.
정확도 검증이 끝난 뒤 별도 작업으로 분석 파이프라인에 통합한다.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.app.config import settings
from backend.app.models.ocr import OcrCorrectRequest, OcrCorrectResponse, OcrResponse
from backend.app.services import ocr_service

router = APIRouter()

SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def _ocr_dir() -> Path:
    p = Path(settings.ocr_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


@router.post("/ocr/test", response_model=OcrResponse)
async def ocr_test(file: UploadFile = File(...)) -> OcrResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다.")

    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_IMAGE_EXTS:
        supported = ", ".join(sorted(SUPPORTED_IMAGE_EXTS))
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 이미지 형식입니다. 지원 형식: {supported}",
        )

    content = await file.read()
    max_bytes = settings.ocr_max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"이미지가 너무 큽니다. 최대 {settings.ocr_max_upload_mb}MB",
        )

    document_id = str(uuid.uuid4())
    raw_path = _ocr_dir() / f"{document_id}_raw{ext}"
    raw_path.write_bytes(content)

    try:
        result, prepared = await ocr_service.run_ocr(str(raw_path))
    except Exception as e:  # PaddleOCR 호출 실패 (모델 로딩, GPU 메모리 등)
        raise HTTPException(status_code=500, detail=f"OCR 실행 실패: {e}") from e

    orig_path = _ocr_dir() / f"{document_id}_orig.png"
    overlay_path = _ocr_dir() / f"{document_id}_overlay.png"
    ocr_service.save_prepared(prepared, str(orig_path))
    ocr_service.render_overlay(prepared, result, str(overlay_path))

    # 원본 raw 파일은 정합성 검증 후 삭제 — orig.png 가 OCR 입력과 동일한 표시본.
    try:
        raw_path.unlink()
    except OSError:
        pass

    return OcrResponse(
        document_id=document_id,
        image_url=f"/api/ocr/image/{document_id}",
        overlay_url=f"/api/ocr/overlay/{document_id}",
        result=result,
    )


def _safe_file(document_id: str, suffix: str) -> Path:
    # path traversal 방지: uuid 형식만 허용
    try:
        uuid.UUID(document_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="잘못된 document_id") from e
    path = _ocr_dir() / f"{document_id}_{suffix}.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="파일이 없습니다.")
    return path


@router.get("/ocr/image/{document_id}")
async def get_image(document_id: str):
    return FileResponse(_safe_file(document_id, "orig"), media_type="image/png")


@router.get("/ocr/overlay/{document_id}")
async def get_overlay(document_id: str):
    return FileResponse(_safe_file(document_id, "overlay"), media_type="image/png")


@router.post("/ocr/correct", response_model=OcrCorrectResponse)
async def correct(payload: OcrCorrectRequest) -> OcrCorrectResponse:
    """OCR 결과 박스들을 LLM 으로 후보정.

    백엔드에 OCR 결과를 영속화하지 않으므로 클라이언트가 직전 응답의 boxes 를 그대로
    다시 보낸다. 결과는 corrected_text 가 채워진 boxes 와 소요 시간.
    """
    import time
    started = time.perf_counter()
    corrected = await ocr_service.correct_with_llm(payload.boxes)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return OcrCorrectResponse(boxes=corrected, elapsed_ms=elapsed_ms)
