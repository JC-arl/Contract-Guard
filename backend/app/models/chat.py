from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class Citation(BaseModel):
    text: str
    source: str
    category: str  # "law" | "judgment" | "safe_clause" | "unfair_clause" | "other"
    similarity: float
    article: str | None = None


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    contract_type: str | None = None  # 사용자가 도메인 토글로 직접 지정. None이면 자동 분류


class ChatResponse(BaseModel):
    conclusion: str
    answer: str
    citations: list[Citation] = []      # LLM이 답변에 실제 인용한 출처
    all_references: list[Citation] = [] # 검색된 전체 근거(인용 안 된 것 포함). 변호사가 직접 평가
    domain: str | None = None           # 실제로 사용된 contract_type ("lease" 등 또는 None)
    status: str = "ok"                  # "ok" | "parse_failed" | "llm_error"
