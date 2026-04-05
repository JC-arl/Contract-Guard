from langchain_ollama import ChatOllama
from backend.app.config import settings

_llm: ChatOllama | None = None


def get_llm() -> ChatOllama:
    global _llm
    if _llm is None:
        _llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model_name,
            temperature=0.3,
            num_predict=4096,
            num_ctx=8192,
            timeout=settings.ollama_timeout,
        )
    return _llm


def reset_llm():
    """LLM 인스턴스를 초기화한다 (설정 변경 시 사용)."""
    global _llm
    _llm = None


async def generate(prompt: str, system: str = "") -> str:
    from langchain_core.messages import SystemMessage, HumanMessage

    llm = get_llm()
    messages = []
    if system:
        messages.append(SystemMessage(content=system))
    messages.append(HumanMessage(content=prompt))
    response = await llm.ainvoke(messages)
    return response.content


async def check_health() -> bool:
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False
