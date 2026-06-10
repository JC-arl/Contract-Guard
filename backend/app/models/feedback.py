from typing import Literal

from pydantic import BaseModel


class FeedbackPayload(BaseModel):
    """변호사 피드백 입력. raw는 자유 텍스트(가이드 따른 형식이면 룰 등록).

    가이드라인:
        [조건] 어떤 상황에 적용되는지
        [판단] safe / low / medium / high
        [근거] 법령·판례·실무 이유
        [일반화] O(자동 적용) / X(케이스별)
    """
    raw: str


class ParsedFeedback(BaseModel):
    """가이드라인 따른 형식에서 추출된 구조화 필드.

    4개 필드 모두 채워지고 generalize=True면 활성 룰로 등록 가능.
    """
    condition: str | None = None
    judgment: Literal["safe", "low", "medium", "high"] | None = None
    reason: str | None = None
    generalize: bool | None = None
    condition_keywords: list[str] = []  # 룰 매칭 가속을 위한 키워드 자동 추출


class FeedbackEntry(BaseModel):
    """jsonl 저장 단위 + API 응답 본문.

    is_rule=True이고 status="approved"여야 chain.py의 _check_verified_rules에서
    활용되는 활성 룰이 된다. 변호사 제출은 status="pending"으로 팀장 승인을 거친다.
    """
    id: str  # uuid4
    analysis_id: str
    clause_index: int
    contract_type: str
    clause_text: str
    raw: str  # 변호사 원본 피드백 (가공 없이 보존)
    parsed: ParsedFeedback | None = None  # 가이드 형식 따랐을 때만
    is_rule: bool  # parsed 완성 + generalize=True
    # 승인 워크플로우: 변호사 제출=pending, 팀장/관리자 제출=approved.
    # 기본값 approved — status 필드가 없던 레거시 jsonl 항목을 grandfather 처리한다.
    status: Literal["pending", "approved", "rejected"] = "approved"
    team_id: int | None = None  # 작성 시점 작성자 팀 (승인 권한 스코프용)
    reviewed_by: str | None = None  # 승인/반려한 팀장 user id (문자열)
    reviewer_name: str | None = None
    reviewed_at: str | None = None  # ISO8601 UTC
    lawyer_id: str | None = None
    lawyer_name: str | None = None
    registered_at: str  # ISO8601 UTC


class PendingFeedbackItem(BaseModel):
    """팀장 승인 큐 조회용 항목."""
    id: str
    contract_type: str
    clause_index: int
    clause_text: str
    raw: str
    parsed: ParsedFeedback | None = None
    is_rule: bool
    status: str
    lawyer_id: str | None = None
    lawyer_name: str | None = None
    registered_at: str


class FeedbackResponse(BaseModel):
    """저장 확인 + 룰 등록 여부 + 가이드라인 미준수 경고."""
    entry: FeedbackEntry
    rule_registered: bool
    status: str = "approved"  # pending이면 프론트에서 "승인 요청" 메시지 분기
    parse_warnings: list[str] = []
