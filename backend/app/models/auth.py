import re

from pydantic import BaseModel, field_validator

from backend.app.db.models import UserRole

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupRequest(BaseModel):
    email: str
    password: str
    display_name: str = ""

    @field_validator("email")
    @classmethod
    def _valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("유효한 이메일 형식이 아닙니다.")
        return v

    @field_validator("password")
    @classmethod
    def _valid_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("비밀번호는 최소 8자 이상이어야 합니다.")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("비밀번호가 너무 깁니다 (bcrypt 72바이트 제한).")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class UserPublic(BaseModel):
    id: int
    email: str
    display_name: str
    role: UserRole
    team_id: int | None = None
    team_name: str | None = None
    is_active: bool


class LoginResponse(BaseModel):
    user: UserPublic
    csrf_token: str


# ===== Admin 페이지 =====

class AdminStats(BaseModel):
    total_users: int
    active_users: int
    total_teams: int
    signups_last_7_days: int
    pending_feedback: int = 0  # 승인 대기 피드백 수 (manager=팀, admin=전체)
    approved_rules: int = 0  # 승인된 활성 룰 수


class UserSummary(BaseModel):
    id: int
    email: str
    display_name: str
    role: UserRole
    team_id: int | None = None
    team_name: str | None = None
    is_active: bool
    created_at: str  # ISO8601 UTC


class UserUpdate(BaseModel):
    # 보낸 필드만 수정. team_id는 명시적 null 허용(팀 해제 의미) → 별도 처리 필요해 raw dict 활용.
    role: UserRole | None = None
    team_id: int | None = None
    is_active: bool | None = None
    display_name: str | None = None


class TeamSummary(BaseModel):
    id: int
    name: str
    manager_id: int | None = None
    manager_name: str | None = None
    member_count: int
    created_at: str


class TeamCreate(BaseModel):
    name: str
    manager_id: int | None = None


class TeamUpdate(BaseModel):
    name: str | None = None
    manager_id: int | None = None
