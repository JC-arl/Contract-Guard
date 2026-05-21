import logging
from pathlib import Path

from backend.app.config import settings
from backend.app.db.session import Base, SessionLocal, engine
from backend.app.db import models  # noqa: F401  - 모델 클래스 등록을 위한 import

logger = logging.getLogger(__name__)


def init_db() -> None:
    """앱 부팅 시 1회 호출. 시크릿 검증 + SQLite 파일 디렉토리 보장 + 스키마 생성 + Admin 시드."""
    if not settings.session_secret_key:
        raise RuntimeError(
            "SESSION_SECRET_KEY가 설정되지 않았습니다. "
            ".env에 다음 줄을 추가하세요:\n"
            "  SESSION_SECRET_KEY=$(python -c \"import secrets; print(secrets.token_urlsafe(32))\")"
        )

    if settings.database_url.startswith("sqlite:///"):
        db_path = Path(settings.database_url.replace("sqlite:///", "", 1))
        db_path.parent.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)
    _seed_admin()


def _seed_admin() -> None:
    """.env의 ADMIN_EMAIL/ADMIN_PASSWORD가 채워져 있고 해당 계정이 없으면 Admin을 생성.

    이미 같은 이메일이 존재하면 아무것도 하지 않는다(멱등). 비밀번호 변경은 갱신하지 않으므로
    의도치 않은 매 부팅 비밀번호 덮어쓰기를 막는다.
    """
    email = settings.admin_email.strip().lower()
    password = settings.admin_password
    if not email or not password:
        return

    # 지연 import — passlib 로딩을 시드가 필요할 때로 미룬다.
    from backend.app.auth import security
    from backend.app.db.models import User, UserRole

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first() is not None:
            return
        db.add(
            User(
                email=email,
                password_hash=security.hash_password(password),
                display_name=settings.admin_name.strip() or "관리자",
                role=UserRole.admin,
                is_active=True,
            )
        )
        db.commit()
        logger.info(f"[seed] Admin 계정 생성: {email}")
    finally:
        db.close()
