from fastapi import APIRouter
from backend.app.services import chroma_service

router = APIRouter()


@router.get("/kb/status")
async def kb_status():
    status = chroma_service.collection_status()
    return {
        "status": "ready" if status["count"] > 0 else "empty",
        "collection": status["name"],
        "document_count": status["count"],
    }
