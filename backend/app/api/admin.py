import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from backend.app.auth.dependencies import require_csrf, require_role
from backend.app.db.models import Team, User, UserRole
from backend.app.db.session import get_db
from backend.app.models.auth import (
    AdminStats,
    TeamCreate,
    TeamSummary,
    TeamUpdate,
    UserSummary,
    UserUpdate,
)

logger = logging.getLogger(__name__)

# 라우터 레벨: admin 또는 manager 모두 진입 가능 (개별 변경 엔드포인트에서 admin만으로 더 좁힘)
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_role(UserRole.admin, UserRole.manager))],
)

# 변경 메서드 전용 추가 가드
_admin_only = Depends(require_role(UserRole.admin))


def _iso(dt: datetime) -> str:
    return dt.replace(tzinfo=timezone.utc).isoformat(timespec="seconds")


def _current_user(me: User = Depends(require_role(UserRole.admin, UserRole.manager))) -> User:
    """라우터 데코레이터의 의존성을 핸들러 인자로 노출하기 위한 헬퍼."""
    return me


# ===== 대시보드 통계 =====

@router.get("/stats", response_model=AdminStats)
def get_stats(me: User = Depends(_current_user), db: DBSession = Depends(get_db)):
    """Admin: 시스템 전체 통계. Manager: 자기 팀으로 스코프."""
    week_ago = datetime.utcnow() - timedelta(days=7)

    total_teams = db.query(func.count(Team.id)).scalar() or 0  # 모든 role이 전체 팀 수 확인 가능

    if me.role == UserRole.admin:
        total_users = db.query(func.count(User.id)).scalar() or 0
        active_users = db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
        signups_7d = db.query(func.count(User.id)).filter(User.created_at >= week_ago).scalar() or 0
    else:
        # Manager: 사용자 관련 수치는 자기 팀원만 집계. 팀 수만 시스템 전체.
        if me.team_id is None:
            return AdminStats(
                total_users=0, active_users=0, total_teams=total_teams, signups_last_7_days=0,
            )
        team_users = db.query(User).filter(User.team_id == me.team_id)
        total_users = team_users.count()
        active_users = team_users.filter(User.is_active.is_(True)).count()
        signups_7d = team_users.filter(User.created_at >= week_ago).count()

    return AdminStats(
        total_users=total_users,
        active_users=active_users,
        total_teams=total_teams,
        signups_last_7_days=signups_7d,
    )


# ===== 사용자 관리 =====

def _user_to_summary(user: User, team_name: str | None) -> UserSummary:
    return UserSummary(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        team_id=user.team_id,
        team_name=team_name,
        is_active=user.is_active,
        created_at=_iso(user.created_at),
    )


@router.get("/users", response_model=list[UserSummary])
def list_users(me: User = Depends(_current_user), db: DBSession = Depends(get_db)):
    """Admin: 전체 사용자. Manager: 자기 팀원만."""
    q = (
        db.query(User, Team.name)
        .outerjoin(Team, User.team_id == Team.id)
    )
    if me.role == UserRole.manager:
        if me.team_id is None:
            return []
        q = q.filter(User.team_id == me.team_id)
    rows = q.order_by(User.created_at.desc()).all()
    return [_user_to_summary(u, name) for (u, name) in rows]


@router.patch(
    "/users/{user_id}",
    response_model=UserSummary,
    dependencies=[_admin_only, Depends(require_csrf)],
)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: DBSession = Depends(get_db),
    me: User = Depends(require_role(UserRole.admin)),
):
    """Admin 전용. 보낸 필드만 수정 (PATCH 시맨틱)."""
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    sent = body.model_fields_set

    if target.id == me.id:
        if "role" in sent and body.role != UserRole.admin:
            raise HTTPException(status_code=400, detail="자기 자신의 권한을 강등할 수 없습니다.")
        if "is_active" in sent and body.is_active is False:
            raise HTTPException(status_code=400, detail="자기 자신을 비활성화할 수 없습니다.")

    if "display_name" in sent and body.display_name is not None:
        target.display_name = body.display_name.strip()
    if "is_active" in sent and body.is_active is not None:
        target.is_active = body.is_active
    if "role" in sent and body.role is not None:
        target.role = body.role
    if "team_id" in sent:
        if body.team_id is not None:
            team = db.get(Team, body.team_id)
            if team is None:
                raise HTTPException(status_code=400, detail="존재하지 않는 팀입니다.")
        target.team_id = body.team_id

    # 매니저였던 사용자가 팀을 떠나거나 역할이 바뀌면 해당 팀의 manager_id 해제 (정합성)
    if target.role != UserRole.manager or target.team_id is None:
        former_team = db.query(Team).filter(Team.manager_id == target.id).first()
        if former_team is not None and (
            target.team_id != former_team.id or target.role != UserRole.manager
        ):
            former_team.manager_id = None

    db.commit()
    db.refresh(target)
    team_name = db.get(Team, target.team_id).name if target.team_id else None
    return _user_to_summary(target, team_name)


# ===== 팀 관리 =====

def _team_to_summary(team: Team, manager_name: str | None, member_count: int) -> TeamSummary:
    return TeamSummary(
        id=team.id,
        name=team.name,
        manager_id=team.manager_id,
        manager_name=manager_name,
        member_count=member_count,
        created_at=_iso(team.created_at),
    )


@router.get("/teams", response_model=list[TeamSummary])
def list_teams(db: DBSession = Depends(get_db)):
    """Admin/Manager 모두 전체 팀 구조를 조회 가능. 변경 권한은 admin 전용."""
    member_counts = dict(
        db.query(User.team_id, func.count(User.id))
        .filter(User.team_id.isnot(None))
        .group_by(User.team_id)
        .all()
    )
    rows = db.query(Team).order_by(Team.created_at.desc()).all()
    out: list[TeamSummary] = []
    for t in rows:
        mgr_name = None
        if t.manager_id is not None:
            mgr = db.get(User, t.manager_id)
            mgr_name = mgr.display_name if mgr else None
        out.append(_team_to_summary(t, mgr_name, member_counts.get(t.id, 0)))
    return out


def _validate_manager_assignment(db: DBSession, team_id: int, manager_id: int | None) -> None:
    if manager_id is None:
        return
    user = db.get(User, manager_id)
    if user is None:
        raise HTTPException(status_code=400, detail="존재하지 않는 사용자입니다.")
    if user.team_id != team_id:
        raise HTTPException(
            status_code=400,
            detail="매니저로 임명하려면 해당 사용자가 먼저 그 팀에 소속되어야 합니다.",
        )


@router.post(
    "/teams",
    response_model=TeamSummary,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_admin_only, Depends(require_csrf)],
)
def create_team(body: TeamCreate, db: DBSession = Depends(get_db)):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="팀 이름이 비어 있습니다.")
    if db.query(Team).filter(Team.name == name).first() is not None:
        raise HTTPException(status_code=409, detail="이미 존재하는 팀 이름입니다.")

    team = Team(name=name)
    db.add(team)
    db.flush()

    if body.manager_id is not None:
        _validate_manager_assignment(db, team.id, body.manager_id)
        team.manager_id = body.manager_id
        mgr = db.get(User, body.manager_id)
        if mgr is not None and mgr.role != UserRole.admin:
            mgr.role = UserRole.manager

    db.commit()
    db.refresh(team)
    mgr_name = db.get(User, team.manager_id).display_name if team.manager_id else None
    member_count = (
        db.query(func.count(User.id)).filter(User.team_id == team.id).scalar() or 0
    )
    return _team_to_summary(team, mgr_name, member_count)


@router.patch(
    "/teams/{team_id}",
    response_model=TeamSummary,
    dependencies=[_admin_only, Depends(require_csrf)],
)
def update_team(team_id: int, body: TeamUpdate, db: DBSession = Depends(get_db)):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")

    sent = body.model_fields_set
    if "name" in sent and body.name is not None:
        new_name = body.name.strip()
        if not new_name:
            raise HTTPException(status_code=400, detail="팀 이름이 비어 있습니다.")
        if db.query(Team).filter(Team.name == new_name, Team.id != team.id).first() is not None:
            raise HTTPException(status_code=409, detail="이미 존재하는 팀 이름입니다.")
        team.name = new_name

    if "manager_id" in sent:
        _validate_manager_assignment(db, team.id, body.manager_id)
        if team.manager_id is not None and team.manager_id != body.manager_id:
            old_mgr = db.get(User, team.manager_id)
            if old_mgr is not None and old_mgr.role == UserRole.manager:
                old_mgr.role = UserRole.lawyer
        team.manager_id = body.manager_id
        if body.manager_id is not None:
            new_mgr = db.get(User, body.manager_id)
            if new_mgr is not None and new_mgr.role != UserRole.admin:
                new_mgr.role = UserRole.manager

    db.commit()
    db.refresh(team)
    mgr_name = db.get(User, team.manager_id).display_name if team.manager_id else None
    member_count = (
        db.query(func.count(User.id)).filter(User.team_id == team.id).scalar() or 0
    )
    return _team_to_summary(team, mgr_name, member_count)


@router.delete(
    "/teams/{team_id}",
    status_code=204,
    dependencies=[_admin_only, Depends(require_csrf)],
)
def delete_team(team_id: int, db: DBSession = Depends(get_db)):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")

    db.query(User).filter(User.team_id == team.id).update({User.team_id: None})
    db.delete(team)
    db.commit()
    return None
