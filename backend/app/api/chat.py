import logging

from fastapi import APIRouter, HTTPException, Depends

from backend.app.auth.dependencies import get_current_user, require_csrf
from backend.app.models.chat import ChatRequest, ChatResponse
from backend.app.rag import chat_chain

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[Depends(get_current_user), Depends(require_csrf)],
)
async def chat_endpoint(req: ChatRequest):
    """변호사용 법률 Q&A 챗봇. 직전 2턴까지의 history를 컨텍스트로 사용한다."""
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="질문이 비어 있습니다.")
    if len(req.message) > 2000:
        raise HTTPException(status_code=400, detail="질문이 너무 깁니다 (최대 2000자).")
    try:
        return await chat_chain.answer_question(
            question=req.message.strip(),
            history=req.history or [],
            contract_type=req.contract_type,
        )
    except Exception as e:
        logger.exception(f"챗봇 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"챗봇 처리 실패: {e}")
