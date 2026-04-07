from backend.app.services import chroma_service
from backend.app.config import settings


def retrieve_similar(
    text: str,
    top_k: int | None = None,
    contract_type: str | None = None,
) -> list[dict]:
    """텍스트와 유사한 법률 조항을 ChromaDB에서 검색."""
    k = top_k or settings.retrieval_top_k
    results = chroma_service.query(text, k=k, contract_type=contract_type)

    similar = []
    best = None
    for doc, score in results:
        entry = {
            "id": doc.metadata.get("id", ""),
            "text": doc.page_content,
            "similarity": round(score, 4),
            "metadata": doc.metadata,
        }
        # 최소 점수 이상이면 포함
        if score >= settings.retrieval_min_score:
            similar.append(entry)
        # 점수 미달이어도 가장 높은 1건은 후보로 보관
        elif best is None or score > best["similarity"]:
            best = entry

    # 결과가 0건이면 가장 유사한 1건이라도 반환
    if not similar and best:
        similar.append(best)

    return similar
