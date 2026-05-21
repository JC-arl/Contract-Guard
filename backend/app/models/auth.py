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
