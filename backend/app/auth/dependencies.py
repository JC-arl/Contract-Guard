from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session as DBSession

from backend.app.auth import security
from backend.app.db.models import Session as SessionModel, User, UserRole
from backend.app.db.session import get_db


def get_current_session(request: Request, db: DBSession = Depends(get_db)) -> SessionModel:
    session_id = request.cookies.get(security.SESSION_COOKIE)
    session = security.get_valid_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return session


def get_current_user(
    session: SessionModel = Depends(get_current_session),
    db: DBSession = Depends(get_db),
) -> User:
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다.")
    return user


def require_csrf(
    request: Request,
    session: SessionModel = Depends(get_current_session),
) -> None:
    """변경 메서드(POST/PATCH/PUT/DELETE)에 대한 CSRF 검증.

    헤더 X-CSRF-Token == cg_csrf 쿠키 == DB 세션의 csrf_token 셋이 모두 일치해야 통과.
    """
    header_token = request.headers.get(security.CSRF_HEADER)
    cookie_token = request.cookies.get(security.CSRF_COOKIE)
    if not header_token or not cookie_token:
        raise HTTPException(status_code=403, detail="CSRF 토큰이 없습니다.")
    if not (header_token == cookie_token == session.csrf_token):
        raise HTTPException(status_code=403, detail="CSRF 토큰이 일치하지 않습니다.")


def require_role(*roles: UserRole):
    """지정한 role 중 하나여야 통과하는 의존성 팩토리."""

    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        return user

    return _checker
