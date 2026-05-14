from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    # Ollama 설정
    ollama_base_url: str = "http://localhost:11434"
    ollama_model_name: str = "exaone3.5:7.8b"
    ollama_timeout: int = 180

    # 임베딩 모델 — nlpai-lab/KURE-v1: 한국어 retrieval SOTA (고려대 NLPAI Lab, 2024-12)
    # bge-m3 기반으로 한국어 코퍼스 추가 finetune. 동일 1024차원, 8192 컨텍스트라 drop-in 호환.
    # MTEB Korean Retrieval에서 bge-m3 대비 +5~10점.
    embedding_model: str = "nlpai-lab/KURE-v1"
    embedding_device: str = "auto"

    # Reranker — bge-m3와 호환되는 cross-encoder. 1차 hybrid retrieval 풀을 정밀 재정렬.
    # 기본 비활성화 — 12GB VRAM에서 EXAONE+bge-m3와 병행 시 GPU swap 또는 CPU rerank 비용
    # 으로 검증/분석 시간이 5-10배 증가. 정확도 향상 +1~3%p 대비 비용 큼. 필요 시 toggle.
    reranker_enabled: bool = False
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    reranker_max_length: int = 512
    reranker_device: str = "cpu"

    # ChromaDB 설정
    chroma_persist_dir: str = str(DATA_DIR / "chroma")
    chroma_collection: str = "contract_kb"

    # 탐지 설정
    rule_score_threshold: float = 0.3
    retrieval_top_k: int = 8
    retrieval_min_score: float = 0.5

    # 파일 경로
    upload_dir: str = str(DATA_DIR / "uploads")
    documents_dir: str = str(DATA_DIR / "documents")
    results_dir: str = str(DATA_DIR / "results")

    # OCR (PaddleOCR) — 사진/스캔본 계약서에서 텍스트를 추출하기 위한 검증용 파이프라인.
    # device: "gpu" | "cpu" — paddlepaddle-gpu 단일 설치를 전제로 하되, CUDA 미가용 환경에서는
    # OCR_DEVICE=cpu 로 바꿔 use_gpu=False 로 강제할 수 있다.
    ocr_device: str = "gpu"
    ocr_lang: str = "korean"
    ocr_use_angle_cls: bool = True
    # 큰 이미지(예: 4000px 이상)는 비율 유지 다운샘플 — 정확도 손실 적고 속도/메모리 안정.
    ocr_max_image_dim: int = 5120
    # 업로드 원본/오버레이 PNG 저장 위치. 미가공 폴더와 분리해 정리·삭제가 쉽도록 함.
    ocr_dir: str = str(DATA_DIR / "ocr")
    # 한국어 라벨 합성용 폰트. OpenCV putText는 한글 미지원이라 PIL+TrueType 사용.
    ocr_font_path: str = str(BASE_DIR / "backend" / "app" / "assets" / "fonts" / "NotoSansKR-Regular.ttf")
    # 업로드 단계 게이트 (Pillow decompression bomb 방지)
    ocr_max_upload_mb: int = 10
    # autocontrast 전처리 — 사진 그림자/명암 불균일 영역에서 옅은 글씨 detection 회복.
    # 양 끝 cutoff% 히스토그램을 잘라낸 뒤 전체 명암을 0~255 로 재선형화.
    # 부작용 거의 없음. 도장 색은 보존된다 (히스토그램 양 끝만 건드림).
    ocr_autocontrast: bool = True
    ocr_autocontrast_cutoff: int = 2  # 0~10 범위, 클수록 강한 대비 보정
    # PP-Structure 레이아웃 분석 — 제목/본문/표/그림 영역을 분리해 박스별 region_type 부여.
    # 한국어 fine-tune 이 없어 영문(PubLayNet) 또는 중문(CDLA) 모델로 동작한다.
    # 결과 품질이 떨어지면 OCR_USE_LAYOUT=false 로 끄고 raw 박스만 사용한다.
    ocr_use_layout: bool = False
    # 레이아웃 모델 언어 — 'ch'(CDLA, 중문 학술/공문서) 또는 'en'(PubLayNet, 영문 학술).
    # 한국어 계약서는 CDLA 가 본문/제목/표 구분에 더 유리(PubLayNet 은 figure 로 몰아붙이는 경향).
    # CDLA 라벨: text/title/figure/figure_caption/table/table_caption/header/footer/reference/equation
    # PubLayNet 라벨: text/title/list/table/figure
    ocr_layout_lang: str = "ch"
    # 세이프가드 — 검출된 region 중 figure 비율이 이 임계값 이상이면 레이아웃 실패로 간주.
    # 결과를 통째로 버리고 raw 박스로 폴백한다 (region_type=None, regions=[]).
    # 0~1 사이; 1.0 이면 비활성. 0.7 이면 70% 초과가 figure 일 때 폴백.
    ocr_layout_figure_max_ratio: float = 0.7

    model_config = {"env_file": str(BASE_DIR / ".env"), "extra": "ignore"}


settings = Settings()
