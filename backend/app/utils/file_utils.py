from pathlib import Path
from fastapi import UploadFile
from backend.app.config import settings


async def save_upload(file: UploadFile, document_id: str) -> str:
    """업로드된 파일을 저장하고 경로를 반환."""
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix.lower() if file.filename else ""
    file_path = upload_dir / f"{document_id}{ext}"

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return str(file_path)
