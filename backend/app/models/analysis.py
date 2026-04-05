from pydantic import BaseModel
from backend.app.models.risk import RiskLevel, RiskDetail


class ClauseAnalysis(BaseModel):
    clause_index: int
    clause_title: str
    clause_content: str
    risk_level: RiskLevel
    confidence: float
    risks: list[RiskDetail]
    similar_references: list[str] = []
    explanation: str = ""


class AnalysisResult(BaseModel):
    id: str
    document_id: str
    filename: str
    total_clauses: int
    risky_clauses: int
    clause_analyses: list[ClauseAnalysis]
    summary: str = ""


class AnalysisResponse(BaseModel):
    status: str
    result: AnalysisResult | None = None
    error: str | None = None
