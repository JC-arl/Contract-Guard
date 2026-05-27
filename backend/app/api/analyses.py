import io
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session as DBSession

from backend.app.auth.dependencies import (
    get_current_user,
    require_analysis_access,
    require_csrf,
)
from backend.app.config import settings
from backend.app.db.models import AnalysisMeta, User, UserRole
from backend.app.db.session import get_db
from backend.app.models.analysis import AnalysisResponse, AnalysisResult, ClauseAnalysis
from backend.app.services.export_service import export_analysis, supported_formats

logger = logging.getLogger(__name__)
router = APIRouter()


def _result_path(analysis_id: str) -> Path:
    return Path(settings.results_dir) / f"{analysis_id}.json"


def _load_result(analysis_id: str) -> AnalysisResult:
    """저장된 분석 결과 본문(JSON)을 모델로 복원. 권한 검사는 호출자가 책임."""
    result_file = _result_path(analysis_id)
    if not result_file.exists():
        # DB에 메타는 있는데 파일이 없는 비정상 상태
        raise HTTPException(status_code=404, detail="분석 결과 본문을 찾을 수 없습니다.")
    with open(result_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return AnalysisResult(**data)


def _save_result(result: AnalysisResult) -> None:
    """수정된 분석 결과를 원자적으로 저장."""
    target = _result_path(result.id)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
    tmp.replace(target)


class AnalysisSummary(BaseModel):
    """사이드바 이력 목록용 요약 모델."""
    id: str
    filename: str
    contract_type: str | None = None
    created_at: str
    total_clauses: int
    risky_clauses: int


@router.get("/analyses", response_model=list[AnalysisSummary])
async def list_analyses(
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """현재 사용자가 볼 수 있는 분석 목록.

    - Lawyer/Admin: 본인이 만든 것만
    - Manager: 본인 것 + 같은 팀원이 만든 것
    """
    q = db.query(AnalysisMeta)
    if user.role == UserRole.manager and user.team_id is not None:
        q = q.filter(
            or_(AnalysisMeta.owner_id == user.id, AnalysisMeta.team_id == user.team_id)
        )
    else:
        q = q.filter(AnalysisMeta.owner_id == user.id)

    rows = q.order_by(AnalysisMeta.created_at.desc()).all()
    return [
        AnalysisSummary(
            id=m.id,
            filename=m.filename,
            contract_type=m.contract_type,
            # DB에 naive UTC로 저장 → UTC tz 부여 후 ISO8601
            created_at=m.created_at.replace(tzinfo=timezone.utc).isoformat(timespec="seconds"),
            total_clauses=m.total_clauses,
            risky_clauses=m.risky_clauses,
        )
        for m in rows
    ]


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    meta: AnalysisMeta = Depends(require_analysis_access("view")),
):
    result = _load_result(meta.id)
    return AnalysisResponse(status="completed", result=result)


@router.delete(
    "/analyses/{analysis_id}",
    status_code=204,
    dependencies=[Depends(require_csrf)],
)
async def delete_analysis(
    meta: AnalysisMeta = Depends(require_analysis_access("delete")),
    db: DBSession = Depends(get_db),
):
    """소유자만. DB 메타 + 본문 JSON 함께 정리. manager_comments는 FK cascade."""
    # 파일 먼저 (DB 삭제 전에 실패해도 권한이 있으니 재시도 가능)
    _result_path(meta.id).unlink(missing_ok=True)
    db.delete(meta)
    db.commit()
    return None


class ClauseOverrideUpdate(BaseModel):
    text: str | None = None  # null이면 사용자 수정안 제거(원안/권고안으로 회귀)


@router.patch(
    "/analyses/{analysis_id}/clauses/{clause_index}",
    response_model=ClauseAnalysis,
    dependencies=[Depends(require_csrf)],
)
async def update_clause_override(
    clause_index: int,
    body: ClauseOverrideUpdate,
    meta: AnalysisMeta = Depends(require_analysis_access("modify")),
):
    """위험 조항에 대한 사용자 수정안을 저장하거나 제거. 소유자만."""
    result = _load_result(meta.id)
    target = next(
        (c for c in result.clause_analyses if c.clause_index == clause_index),
        None,
    )
    if target is None:
        raise HTTPException(status_code=404, detail="해당 조항을 찾을 수 없습니다.")

    new_text = (body.text or "").strip()
    if new_text:
        target.user_override = new_text
        target.user_override_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    else:
        target.user_override = None
        target.user_override_at = None

    _save_result(result)
    return target


@router.get("/analyses/{analysis_id}/export")
async def export_contract(
    format: str = "docx",
    meta: AnalysisMeta = Depends(require_analysis_access("view")),
):
    """분석 결과로 수정안이 반영된 계약서를 다운로드. format: docx | pdf | hwpx"""
    fmt = (format or "").lower().strip()
    if fmt not in supported_formats():
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 형식입니다: {format} (지원: {', '.join(supported_formats())})",
        )
    result = _load_result(meta.id)
    try:
        data, mime, filename = export_analysis(result, fmt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 생성 실패: {e}")

    # 한글 파일명을 위해 RFC 5987 인코딩 사용
    encoded_name = quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}",
    }
    return StreamingResponse(io.BytesIO(data), media_type=mime, headers=headers)
