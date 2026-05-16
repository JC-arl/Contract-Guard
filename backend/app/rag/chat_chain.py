"""변호사용 법률 Q&A 챗봇 체인.

분석 파이프라인(`chain.py`)과 분리. 입력은 자연어 질문이고 출력은 conclusion/answer 형식.
rule_filter는 우회한다 (계약서 조항이 아니므로 의미 없음).
"""

import asyncio
import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.models.chat import ChatMessage, ChatResponse, Citation
from backend.app.rag.chat_prompts import (
    CHAT_QA_SYSTEM,
    CHAT_QA_TEMPLATE,
    format_chat_history,
)
from backend.app.services.chat_retrieval_service import chat_retrieve
from backend.app.services.llm_service import get_llm

logger = logging.getLogger(__name__)

# 챗봇 LLM 호출 타임아웃 (초). 분석 PER_CLAUSE_TIMEOUT=120 대비 짧게.
# 답변이 너무 길어지지 않도록 num_predict 제약과 함께 빠른 응답 보장.
CHAT_LLM_TIMEOUT = 90


def _to_citation(ref: dict) -> Citation:
    md = ref.get("metadata") or {}
    return Citation(
        text=ref.get("text", "")[:1200],  # UI/payload 크기 제한
        source=md.get("source", ""),
        category=ref.get("category", "other"),
        similarity=float(ref.get("similarity", 0.0) or 0.0),
        article=md.get("article") or md.get("law_name") or None,
    )


def _format_references_for_chat(refs: list[dict]) -> str:
    """LLM 프롬프트용 참고문헌 텍스트. 분석용 format_references와 별도로 구성:
    - 변호사 톤이므로 라벨 가이드 불필요(이미 system prompt에 원칙 명시)
    - 각 항목에 [N] 번호 부여 → citation_indices 회수에 사용
    - source/article 메타 표시 → LLM이 조문번호·판례번호를 [참고]에서 직접 따올 수 있도록
    """
    if not refs:
        return "(참고 자료가 검색되지 않았습니다. 알고 있는 범위 밖이라고 답변하세요.)"
    lines = []
    for i, ref in enumerate(refs, 1):
        md = ref.get("metadata") or {}
        src = md.get("source", "")
        article = md.get("article") or md.get("law_name") or ""
        cat = ref.get("category", "other")
        header = f"[참고{i}][{cat}] source={src}"
        if article:
            header += f" / {article}"
        body = (ref.get("text") or "")[:500]
        lines.append(f"{header}\n{body}")
    return "\n\n".join(lines)


# JSON 파싱 — 챗봇은 단일 객체 응답. chain.py의 _extract_json_from_response(배열용)와 분리.
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_CODE_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_OUTER_OBJECT_RE = re.compile(r"\{[\s\S]*\}")


def _extract_chat_json(text: str) -> dict | None:
    """LLM 응답에서 단일 JSON 객체 추출. 3단계 폴백."""
    if not text:
        return None
    cleaned = _THINK_RE.sub("", text).strip()

    # 1. ```json ``` 코드블록
    m = _CODE_BLOCK_RE.search(cleaned)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 2. 가장 바깥 {...}
    m = _OUTER_OBJECT_RE.search(cleaned)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    # 3. 실패
    return None


def _fallback_response(refs: list[dict], domain: str | None, raw_text: str = "") -> ChatResponse:
    """LLM 파싱 실패 시 검색 결과만으로 최소 응답 구성. 변호사가 출처 카드로 직접 판단 가능."""
    return ChatResponse(
        conclusion="답변 생성에 실패했습니다. 우측의 참고 자료를 직접 확인해주세요.",
        answer=raw_text[:1500] if raw_text else "(LLM 응답 파싱 실패)",
        citations=[],
        all_references=[_to_citation(r) for r in refs],
        domain=domain,
        status="parse_failed",
    )


async def answer_question(
    question: str,
    history: list[ChatMessage],
    contract_type: str | None,
) -> ChatResponse:
    """변호사 질문에 대한 1차 리서치 보조 응답.

    절차: chat_retrieve → LLM 호출 → JSON 파싱 → citation 매핑.
    """
    refs, domain = chat_retrieve(question, contract_type)
    references_text = _format_references_for_chat(refs)
    # 직전 2턴까지만 컨텍스트로 사용 (Step 1: 서버 영속화 없음, 단순 멀티턴)
    history_text = format_chat_history(history[-2:] if history else [])

    user_prompt = CHAT_QA_TEMPLATE.format(
        references=references_text,
        history=history_text,
        question=question,
    )

    llm = get_llm()
    try:
        raw = await asyncio.wait_for(
            llm.ainvoke([
                SystemMessage(content=CHAT_QA_SYSTEM),
                HumanMessage(content=user_prompt),
            ]),
            timeout=CHAT_LLM_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning(f"챗봇 LLM 타임아웃 ({CHAT_LLM_TIMEOUT}s)")
        return ChatResponse(
            conclusion="요청 시간이 초과되었습니다.",
            answer="LLM 응답이 시간 내에 완료되지 않았습니다. 질문을 더 구체적으로 좁혀 다시 시도해주세요.",
            citations=[],
            all_references=[_to_citation(r) for r in refs],
            domain=domain,
            status="llm_error",
        )
    except Exception as e:
        logger.exception(f"챗봇 LLM 호출 실패: {e}")
        return ChatResponse(
            conclusion="LLM 호출에 실패했습니다.",
            answer=f"({type(e).__name__}: {e})",
            citations=[],
            all_references=[_to_citation(r) for r in refs],
            domain=domain,
            status="llm_error",
        )

    raw_text = raw.content if hasattr(raw, "content") else str(raw)
    parsed = _extract_chat_json(raw_text)
    if not parsed:
        logger.warning(f"챗봇 JSON 파싱 실패. raw 앞 300자: {raw_text[:300]}")
        return _fallback_response(refs, domain, raw_text)

    conclusion = (parsed.get("conclusion") or "").strip()
    answer = (parsed.get("answer") or "").strip()
    if not conclusion and not answer:
        return _fallback_response(refs, domain, raw_text)

    citation_indices = parsed.get("citation_indices") or []
    cited: list[Citation] = []
    for idx in citation_indices:
        try:
            i = int(idx)
        except (TypeError, ValueError):
            continue
        if 1 <= i <= len(refs):
            cited.append(_to_citation(refs[i - 1]))

    return ChatResponse(
        conclusion=conclusion or "(결론 없음)",
        answer=answer or "(상세 답변 없음)",
        citations=cited,
        all_references=[_to_citation(r) for r in refs],
        domain=domain,
        status="ok",
    )
