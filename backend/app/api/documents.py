import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession

from backend.app.auth.dependencies import get_current_user, require_csrf
from backend.app.config import settings
from backend.app.db.models import AnalysisMeta, User
from backend.app.db.session import get_db
from backend.app.models.analysis import AnalysisResponse
from backend.app.services import document_service, clause_service, analysis_service
from backend.app.utils.file_utils import save_upload

router = APIRouter()


@router.post(
    "/documents/upload",
    response_model=AnalysisResponse,
    dependencies=[Depends(require_csrf)],
)
async def upload_and_analyze(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다.")

    ext = Path(file.filename).suffix.lower()
    if ext not in document_service.SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(document_service.SUPPORTED_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {supported}",
        )

    document_id = str(uuid.uuid4())

    file_path = await save_upload(file, document_id)

    text, _page_count = document_service.extract_text(file_path)
    if not text.strip():
        raise HTTPException(status_code=422, detail="문서에서 텍스트를 추출할 수 없습니다.")

    contract_type = clause_service.detect_contract_type(text)
    parties = clause_service.detect_parties(text, contract_type)
    sub_type = (
        clause_service.detect_lease_subtype(text)
        if contract_type == "lease"
        else None
    )

    clauses = clause_service.split_clauses(text)
    if not clauses:
        raise HTTPException(status_code=422, detail="계약 조항을 분리할 수 없습니다.")

    result = await analysis_service.run_analysis(
        document_id=document_id,
        filename=file.filename,
        clauses=clauses,
        contract_type=contract_type,
        parties=parties,
        sub_type=sub_type,
    )

    # 분석 본문(JSON)은 analysis_service가 이미 저장. 여기선 권한 판정용 메타만 DB에 기록.
    meta = AnalysisMeta(
        id=result.id,
        document_id=result.document_id,
        filename=result.filename,
        contract_type=result.contract_type,
        total_clauses=result.total_clauses,
        risky_clauses=result.risky_clauses,
        owner_id=current_user.id,
        team_id=current_user.team_id,
    )
    try:
        db.add(meta)
        db.commit()
    except Exception:
        # 메타 INSERT 실패 → 본문 JSON만 남는 고아 파일 방지
        db.rollback()
        (Path(settings.results_dir) / f"{result.id}.json").unlink(missing_ok=True)
        raise

    return AnalysisResponse(status="completed", result=result)
