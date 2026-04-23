import asyncio
import logging

from langchain_ollama import ChatOllama

from backend.app.config import SUPPORTED_QUANTIZATIONS, settings

logger = logging.getLogger(__name__)

_llm: ChatOllama | None = None
_llm_lock = asyncio.Lock()


def get_llm() -> ChatOllama:
    global _llm
    if _llm is None:
        _llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model_name,
            temperature=0,
            seed=42,
            num_predict=4096,
            num_ctx=16384,
            timeout=settings.ollama_timeout,
        )
    return _llm


def reset_llm():
    """LLM 인스턴스를 초기화한다 (설정 변경 시 사용)."""
    global _llm
    _llm = None


async def switch_quantization_if_needed(tag: str | None) -> str:
    """요청된 양자화 태그와 현재 설정이 다르면 LLM 싱글턴을 교체한다.

    - tag가 None 또는 빈 문자열이면 현재 설정 유지.
    - settings.ollama_model_name_override가 지정된 경우, 사용자 지정 모델명을 우선하므로 교체를 건너뛴다.
    - 지원 목록 밖의 값은 ValueError.
    """
    if not tag:
        return settings.ollama_model_name
    if settings.ollama_model_name_override:
        # 사용자가 OLLAMA_MODEL_NAME을 직접 고정했다면 런타임 교체는 의미가 없다.
        return settings.ollama_model_name
    if tag not in SUPPORTED_QUANTIZATIONS:
        raise ValueError(
            f"지원하지 않는 양자화 수준: {tag}. 허용 값: {SUPPORTED_QUANTIZATIONS}"
        )
    if tag == settings.llm_quantization:
        return settings.ollama_model_name

    async with _llm_lock:
        if tag == settings.llm_quantization:
            return settings.ollama_model_name
        previous = settings.ollama_model_name
        settings.llm_quantization = tag
        reset_llm()
        get_llm()
        logger.info("LLM 양자화 교체: %s -> %s", previous, settings.ollama_model_name)
        return settings.ollama_model_name


async def check_health() -> bool:
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False
