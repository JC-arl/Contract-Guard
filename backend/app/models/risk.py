from enum import Enum
from pydantic import BaseModel


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SAFE = "safe"


class RiskDetail(BaseModel):
    risk_type: str
    description: str
    suggestion: str
