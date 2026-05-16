"""변호사용 Q&A 챗봇 retrieval 어댑터.

핵심:
- 도메인 자동 분류 (키워드 룰). LLM 호출 없이 결정적 매칭.
- 분석 파이프라인과 동일한 retrieve_similar()를 mode="chat"으로 호출.
- query expansion은 의도적으로 생략 — 변호사는 이미 법률 용어로 질의하므로
  자연어 사용자 대상 확장이 오히려 의도 왜곡을 유발할 수 있다.
"""

import logging

from backend.app.services.retrieval_service import retrieve_similar

logger = logging.getLogger(__name__)


# 도메인별 키워드. 동일 키워드가 여러 도메인에 출현하지 않도록 가급적 도메인 고유 용어 선정.
# 일반화 원칙: 한 도메인에 편중 매칭되지 않도록 5개 도메인 모두 풍부히 정의.
_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "lease": [
        "임차인", "임대인", "차임", "월세", "보증금", "전세", "임대차",
        "주택임대차보호법", "주임법", "상가임대차", "상임법", "갱신요구권",
        "묵시적 갱신", "원상복구", "전대",
    ],
    "sales": [
        "매도인", "매수인", "매매대금", "계약금", "잔금", "소유권 이전",
        "등기", "하자담보", "동시이행", "매매계약",
    ],
    "employment": [
        "근로자", "사용자", "임금", "해고", "퇴직금", "연차", "근로계약",
        "근로기준법", "근기법", "통상임금", "최저임금", "가산수당",
        "산재", "취업규칙",
    ],
    "service": [
        "용역", "도급", "수급인", "발주자", "하도급", "하도급법",
        "공사대금", "검수", "용역계약",
    ],
    "loan": [
        "차주", "대주", "대여금", "차용금", "이자", "변제", "기한이익",
        "근보증", "이자제한법", "대부업법", "보증인보호",
    ],
}

# 도메인 매핑 검증용 상수 (contract_types.py의 키와 동일해야 함)
_VALID_DOMAINS = set(_DOMAIN_KEYWORDS.keys())


def classify_domain(question: str) -> str | None:
    """질문에서 5개 도메인 중 가장 강하게 매칭되는 1개 반환.

    Returns:
      도메인 키 ("lease"/"sales"/"employment"/"service"/"loan") 또는 None.
      매칭 없음 또는 동률이면 None을 반환하여 retrieve_similar가 전 도메인을 검색.
    """
    if not question:
        return None

    hits: dict[str, int] = {}
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in question)
        if count > 0:
            hits[domain] = count

    if not hits:
        return None

    max_count = max(hits.values())
    top = [d for d, c in hits.items() if c == max_count]
    if len(top) > 1:
        # 동률이면 모호한 도메인 — 전 도메인 검색이 안전
        logger.debug(f"도메인 동률 매칭({top}), 자동 분류 보류")
        return None
    return top[0]


def chat_retrieve(question: str, contract_type: str | None = None) -> tuple[list[dict], str | None]:
    """챗봇용 검색. classify_domain 결과를 기본으로 사용하되 contract_type이 지정되면 그것을 우선.

    Returns:
      (검색 결과 리스트, 실제 사용된 contract_type 또는 None).
    """
    if contract_type and contract_type in _VALID_DOMAINS:
        domain = contract_type
    elif contract_type:
        logger.warning(f"알 수 없는 contract_type: {contract_type!r} — 자동 분류로 폴백")
        domain = classify_domain(question)
    else:
        domain = classify_domain(question)

    logger.info(f"[chat_retrieve] domain={domain!r} query={question[:80]!r}")
    results = retrieve_similar(question, contract_type=domain, mode="chat")
    return results, domain
