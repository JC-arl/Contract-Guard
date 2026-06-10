"""변호사 피드백 등록 API.

변호사가 권고안 편집 옆 피드백란에 가이드라인 형식으로 입력 → jsonl 누적.
4개 필드 모두 충족 + [일반화]=O면 활성 룰 자격으로 표시 (is_rule=True).
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from backend.app.auth.dependencies import get_current_user, require_csrf
from backend.app.config import settings
from backend.app.db.models import User, UserRole
from backend.app.models.feedback import (
    FeedbackEntry,
    FeedbackPayload,
    FeedbackResponse,
)
from backend.app.services import feedback_store
from backend.app.services.feedback_parser import (
    is_complete_rule,
    parse_feedback,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_ANALYSIS_ID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


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
    """변호사 피드백을 jsonl에 누적 저장.

    변호사(lawyer) 제출은 status="pending"으로 자기 팀 팀장 승인을 거쳐야 활성 룰이 된다.
    팀장/관리자 제출은 즉시 status="approved".
    """
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

    # 변호사 제출은 팀장 승인 대기. 팀장/관리자 제출은 즉시 승인.
    is_lawyer = current_user.role == UserRole.lawyer
    status = "pending" if is_lawyer else "approved"

    # 팀 미소속 변호사는 승인할 팀장이 없음 — 보류 안내
    if is_lawyer and current_user.team_id is None:
        warnings = [
            *warnings,
            "소속 팀이 없어 승인 담당 팀장이 없습니다 — 팀 배정 후 검토됩니다.",
        ]

    entry = FeedbackEntry(
        id=feedback_store.new_id(),
        analysis_id=analysis_id,
        clause_index=clause_index,
        contract_type=contract_type,
        clause_text=clause_text,
        raw=payload.raw.strip(),
        parsed=parsed if has_any_parsed else None,
        is_rule=rule_registered,
        status=status,
        team_id=current_user.team_id,
        lawyer_id=str(current_user.id) if current_user.id is not None else None,
        lawyer_name=current_user.display_name or current_user.email,
        registered_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )

    try:
        feedback_store.append_entry(entry)
    except OSError as e:
        logger.exception(f"피드백 저장 실패: {e}")
        raise HTTPException(status_code=500, detail="피드백 저장에 실패했습니다.")

    logger.info(
        f"피드백 등록: analysis={analysis_id} clause={clause_index} "
        f"contract_type={contract_type} rule={rule_registered} status={status}"
    )

    return FeedbackResponse(
        entry=entry,
        rule_registered=rule_registered,
        status=status,
        parse_warnings=warnings,
    )
