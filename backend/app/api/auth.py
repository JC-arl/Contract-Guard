import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session as DBSession

from backend.app.auth import security
from backend.app.auth.dependencies import get_current_session, get_current_user, require_csrf
from backend.app.db.models import Session as SessionModel, User, UserRole
from backend.app.db.session import get_db
from backend.app.models.auth import LoginRequest, LoginResponse, SignupRequest, UserPublic

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def _to_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        team_id=user.team_id,
        team_name=user.team.name if user.team is not None else None,
        is_active=user.is_active,
    )


@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def signup(req: SignupRequest, db: DBSession = Depends(get_db)):
    """자체 회원가입. 기본 role=lawyer, 팀 미소속. 자동 로그인은 하지 않는다."""
    exists = db.query(User).filter(User.email == req.email).first()
    if exists is not None:
        raise HTTPException(status_code=409, detail="이미 등록된 이메일입니다.")

    user = User(
        email=req.email,
        password_hash=security.hash_password(req.password),
        display_name=req.display_name.strip() or req.email.split("@")[0],
        role=UserRole.lawyer,
        team_id=None,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _to_public(user)


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, response: Response, db: DBSession = Depends(get_db)):
    email = req.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    # timing 노출 최소화를 위해 동일한 메시지로 응답
    if user is None or not security.verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다.")

    session = security.create_session(db, user)
    security.set_session_cookies(response, session)
    return LoginResponse(user=_to_public(user), csrf_token=session.csrf_token)


@router.post("/logout", status_code=204, dependencies=[Depends(require_csrf)])
def logout(
    response: Response,
    session: SessionModel = Depends(get_current_session),
    db: DBSession = Depends(get_db),
):
    security.delete_session(db, session.id)
    security.clear_session_cookies(response)
    return None


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)):
    return _to_public(user)
