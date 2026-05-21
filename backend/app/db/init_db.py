from pathlib import Path

from backend.app.config import settings
from backend.app.db.session import Base, engine
from backend.app.db import models  # noqa: F401  - 모델 클래스 등록을 위한 import


def init_db() -> None:
    """앱 부팅 시 1회 호출. 시크릿 검증 + SQLite 파일 디렉토리 보장 + 스키마 생성."""
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
