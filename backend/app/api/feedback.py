"""변호사 피드백 등록 API.

변호사가 권고안 편집 옆 피드백란에 가이드라인 형식으로 입력 → jsonl 누적.
4개 필드 모두 충족 + [일반화]=O면 활성 룰 자격으로 표시 (is_rule=True).
"""

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from backend.app.auth.dependencies import get_current_user, require_csrf
from backend.app.config import DATA_DIR, settings
from backend.app.db.models import User
from backend.app.models.feedback import (
    FeedbackEntry,
    FeedbackPayload,
    FeedbackResponse,
)
from backend.app.services.feedback_parser import (
    is_complete_rule,
    parse_feedback,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_FEEDBACK_DIR = Path(DATA_DIR) / "verified_rules"
_ANALYSIS_ID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
# contract_type을 파일명에 쓰기 전에 영문·하이픈만 허용 (path traversal 방지)
_CT_SAFE_RE = re.compile(r"[^A-Za-z0-9_-]")


def _feedback_path(contract_type: str) -> Path:
    safe = _CT_SAFE_RE.sub("", contract_type or "")[:32]
    if not safe:
        safe = "unknown"
    return _FEEDBACK_DIR / f"{safe}.jsonl"


def _load_clause_context(analysis_id: str, clause_index: int) -> tuple[str, str]:
    """저장된 분석 결과에서 (clause_text, contract_type) 반환."""
    result_path = Path(settings.results_dir) / f"{analysis_id}.json"
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
    try:
        with open(result_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"분석 결과 로드 실패: {e}")
        raise HTTPException(status_code=500, detail="분석 결과 파일을 읽을 수 없습니다.")
    contract_type = data.get("contract_type") or "unknown"
    for clause in data.get("clause_analyses", []):
        if clause.get("clause_index") == clause_index:
            return clause.get("clause_content", ""), contract_type
    raise HTTPException(status_code=404, detail="해당 조항을 찾을 수 없습니다.")


def _append_jsonl(path: Path, entry: FeedbackEntry) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry.model_dump_json() + "\n")


@router.post(
    "/analyses/{analysis_id}/clauses/{clause_index}/feedback",
    response_model=FeedbackResponse,
    dependencies=[Depends(get_current_user), Depends(require_csrf)],
)
async def register_feedback(
    analysis_id: str,
    clause_index: int,
    payload: FeedbackPayload,
    current_user: User = Depends(get_current_user),
) -> FeedbackResponse:
    """변호사 피드백을 jsonl에 누적 저장. 가이드라인 형식이면 활성 룰로 표시."""
    if not _ANALYSIS_ID_RE.match(analysis_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 분석 ID입니다.")
    if clause_index < 1 or clause_index > 9999:
        raise HTTPException(status_code=400, detail="유효하지 않은 조항 번호입니다.")
    if not payload.raw or not payload.raw.strip():
        raise HTTPException(status_code=400, detail="피드백 내용이 비어 있습니다.")
    if len(payload.raw) > 5000:
        raise HTTPException(
            status_code=400, detail="피드백이 너무 깁니다 (최대 5000자)."
        )

    clause_text, contract_type = _load_clause_context(analysis_id, clause_index)
    parsed, warnings = parse_feedback(payload.raw)
    rule_registered = is_complete_rule(parsed)

    # parsed에 어떤 필드라도 채워졌으면 보존 — 부분 정보도 다음 단계 룰 추출에 가치 있음
    has_any_parsed = any(
        [parsed.condition, parsed.judgment, parsed.reason, parsed.generalize is not None]
    )

    entry = FeedbackEntry(
        id=str(uuid.uuid4()),
        analysis_id=analysis_id,
        clause_index=clause_index,
        contract_type=contract_type,
        clause_text=clause_text,
        raw=payload.raw.strip(),
        parsed=parsed if has_any_parsed else None,
        is_rule=rule_registered,
        lawyer_id=str(current_user.id) if current_user.id is not None else None,
        lawyer_name=current_user.display_name or current_user.email,
        registered_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )

    try:
        _append_jsonl(_feedback_path(contract_type), entry)
    except OSError as e:
        logger.exception(f"피드백 저장 실패: {e}")
        raise HTTPException(status_code=500, detail="피드백 저장에 실패했습니다.")

    logger.info(
        f"피드백 등록: analysis={analysis_id} clause={clause_index} "
        f"contract_type={contract_type} rule={rule_registered}"
    )

    return FeedbackResponse(
        entry=entry,
        rule_registered=rule_registered,
        parse_warnings=warnings,
    )
