from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# 런타임에 전환 가능한 Ollama 양자화 태그 목록.
# Ollama 레지스트리의 exaone3.5:7.8b-instruct-<tag> 형식을 그대로 사용한다.
SUPPORTED_QUANTIZATIONS: tuple[str, ...] = (
    "q2_K",
    "q3_K_M",
    "q4_K_M",
    "q5_K_M",
    "q8_0",
)
DEFAULT_QUANTIZATION = "q4_K_M"


class Settings(BaseSettings):
    # LLM 모델 (양자화 수준별 태그 조합)
    llm_base_model: str = "exaone3.5:7.8b"
    llm_quantization: str = DEFAULT_QUANTIZATION
    # 하위호환: 환경변수 OLLAMA_MODEL_NAME이 지정되면 조합 규칙을 무시하고 그대로 사용
    ollama_model_name_override: str | None = Field(default=None, alias="OLLAMA_MODEL_NAME")

    # Ollama 연결
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout: int = 180

    # 임베딩 모델
    embedding_model: str = "jhgan/ko-sroberta-multitask"
    embedding_device: str = "auto"

    # ChromaDB 설정
    chroma_persist_dir: str = str(DATA_DIR / "chroma")
    chroma_collection: str = "contract_kb"

    # 탐지 설정
    rule_score_threshold: float = 0.3
    retrieval_top_k: int = 5
    retrieval_min_score: float = 0.5

    # 파일 경로
    upload_dir: str = str(DATA_DIR / "uploads")
    documents_dir: str = str(DATA_DIR / "documents")
    results_dir: str = str(DATA_DIR / "results")

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "extra": "ignore",
        "populate_by_name": True,
    }

    @property
    def ollama_model_name(self) -> str:
        if self.ollama_model_name_override:
            return self.ollama_model_name_override
        tag = (self.llm_quantization or "").strip()
        if not tag or tag.lower() == "default":
            return self.llm_base_model
        return f"{self.llm_base_model}-instruct-{tag}"


settings = Settings()
