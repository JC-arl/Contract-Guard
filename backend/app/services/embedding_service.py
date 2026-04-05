from langchain_huggingface import HuggingFaceEmbeddings
from backend.app.config import settings

_embeddings: HuggingFaceEmbeddings | None = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """임베딩 모델 싱글턴 인스턴스 반환."""
    global _embeddings
    if _embeddings is None:
        model_kwargs = {}
        if settings.embedding_device != "auto":
            model_kwargs["device"] = settings.embedding_device
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs=model_kwargs,
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings
