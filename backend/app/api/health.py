from fastapi import APIRouter
from backend.app.services import llm_service, chroma_service

router = APIRouter()


@router.get("/health")
async def health_check():
    ollama_ok = await llm_service.check_health()
    try:
        kb_status = chroma_service.collection_status()
    except Exception:
        kb_status = {"name": "lease_kb", "count": 0}
    return {
        "status": "ok",
        "ollama": "connected" if ollama_ok else "disconnected",
        "knowledge_base": kb_status,
    }
