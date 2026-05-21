import secrets
from datetime import datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy.orm import Session as DBSession

from backend.app.config import settings
from backend.app.db.models import Session as SessionModel, User

SESSION_COOKIE = "cg_session"
CSRF_COOKIE = "cg_csrf"
CSRF_HEADER = "x-csrf-token"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_session(db: DBSession, user: User) -> SessionModel:
    """새 세션 row 발급. session id와 csrf 토큰을 각각 랜덤 생성."""
    now = datetime.utcnow()
    session = SessionModel(
        id=secrets.token_urlsafe(32),
        user_id=user.id,
        csrf_token=secrets.token_urlsafe(32),
        created_at=now,
        expires_at=now + timedelta(days=settings.session_ttl_days),
        last_seen_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_valid_session(db: DBSession, session_id: str) -> SessionModel | None:
    """세션 조회. 없거나 만료됐으면 None. 만료 row는 삭제한다."""
    if not session_id:
        return None
    session = db.get(SessionModel, session_id)
    if session is None:
        return None
    if session.expires_at < datetime.utcnow():
        db.delete(session)
        db.commit()
        return None
    return session


def delete_session(db: DBSession, session_id: str) -> None:
    session = db.get(SessionModel, session_id)
    if session is not None:
        db.delete(session)
        db.commit()


def set_session_cookies(response, session: SessionModel) -> None:
    """로그인 응답에 세션/CSRF 쿠키를 설정.

    cg_session: HTTPOnly (JS 접근 불가) — 세션 탈취 방지
    cg_csrf:    JS 가독 — 프론트가 읽어 X-CSRF-Token 헤더에 실어 보냄 (double-submit)
    """
    max_age = settings.session_ttl_days * 86400  # 일 → 초 (86400 = 24h*60m*60s). 쿠키 max_age는 초 단위
    response.set_cookie(
        SESSION_COOKIE,
        session.id,
        max_age=max_age,
        httponly=True,
        secure=settings.secure_cookie,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        session.csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.secure_cookie,
        samesite="lax",
        path="/",
    )


def clear_session_cookies(response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")
