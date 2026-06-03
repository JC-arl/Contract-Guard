import re
from typing import Literal

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session as DBSession

from backend.app.auth import security
from backend.app.db.models import AnalysisMeta, Session as SessionModel, User, UserRole
from backend.app.db.session import get_db

# UUID4 형식만 허용 — 잘못된 ID가 DB/파일시스템으로 가지 않게 한 곳에서 필터
_ANALYSIS_ID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


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


def require_analysis_access(action: Literal["view", "modify", "delete"]):
    """분석 단위 권한 검사 의존성 팩토리.

    권한 매트릭스 (Admin은 분석 데이터에 접근 불가 — 변호사·의뢰인 비밀유지):
      view  : 소유자 또는 같은 팀의 Manager
      modify: 소유자만
      delete: 소유자만

    통과하면 AnalysisMeta 객체를 반환 → 라우터에서 meta.id로 본문 JSON 로드.
    조회 권한 없음은 404로 응답해 '존재 사실'도 숨긴다.
    """

    def _checker(
        analysis_id: str,
        user: User = Depends(get_current_user),
        db: DBSession = Depends(get_db),
    ) -> AnalysisMeta:
        if not _ANALYSIS_ID_RE.match(analysis_id):
            raise HTTPException(status_code=400, detail="유효하지 않은 분석 ID입니다.")

        meta = db.get(AnalysisMeta, analysis_id)
        if meta is None:
            raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")

        is_owner = meta.owner_id == user.id
        is_team_manager = (
            user.role == UserRole.manager
            and user.team_id is not None
            and meta.team_id == user.team_id
        )

        if action == "view":
            if not (is_owner or is_team_manager):
                # 정보 노출 방지를 위해 403 대신 404
                raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
        else:  # modify, delete — 소유자만
            if not is_owner:
                raise HTTPException(status_code=403, detail="권한이 없습니다.")

        return meta

    return _checker
