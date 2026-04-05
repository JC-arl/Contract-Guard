# Contract Guard

AI 기반 임대차 계약서 위험 조항 분석 서비스입니다.
LLM + RAG로 세입자에게 불리한 조항을 자동 탐지하고 개선안을 제시합니다.


---

## 동작 흐름

```
사용자 ─── PDF 업로드 ──→ [FastAPI 백엔드]
                              │
                              ├─ 1. PDF 텍스트 추출 (PyMuPDF)
                              ├─ 2. 조항 단위 분리 (제n조 패턴)
                              ├─ 3. 유사 법률/판례 검색 (ChromaDB + Ko-SBERT)
                              ├─ 4. LLM 배치 분석 (Ollama)
                              └─ 5. 위험도 분류 + 개선안 생성
                                        │
사용자 ←── 분석 결과 ────── [React UI]
```

각 조항에 대해 **위험도(high/medium/low/safe)**, 신뢰도 점수, 위험 유형, 설명, 개선 제안, 유사 참고 조항을 제공합니다.

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| PDF 업로드 & 즉시 분석 | 계약서 PDF를 올리면 조항별 위험도를 바로 확인 |
| 조항 자동 분리 | `제 n조` 패턴 인식 + 단락 기반 fallback |
| RAG 기반 분석 | 1,679건의 약관·판결문 지식베이스에서 유사 조항 검색 |
| 8가지 위험 유형 탐지 | 보증금 미반환, 일방적 해지, 수선의무 전가, 위약금 과다 등 |
| 분석 결과 시각화 | 위험도 게이지, 등급별 배지, 확장 가능한 조항 카드 |
| 분석 결과 저장 & 조회 | JSON 파일 저장 후 API로 재조회 가능 |

---

## 기술 스택

### Backend
- **FastAPI** + Uvicorn — REST API 서버
- **LangChain** + langchain-ollama — LLM 오케스트레이션
- **ChromaDB** — 벡터 데이터베이스 (persist: `data/chroma`)
- **HuggingFace** — 한국어 임베딩 (`jhgan/ko-sroberta-multitask`)
- **PyMuPDF** — PDF 텍스트 추출

### Frontend
- **React 18** + **Vite** — SPA
- **React Router** — 페이지 라우팅
- **Axios** — API 통신 (5분 타임아웃)

### LLM
- **Ollama** — 로컬 LLM 서버 (기본: `qwen3:8b`)

---

## 프로젝트 구조

```
Contract-Guard/
├── backend/
│   ├── app/
│   │   ├── api/            # 엔드포인트 (health, upload, analyses, kb)
│   │   ├── models/         # Pydantic 모델 (analysis, clause, risk)
│   │   ├── services/       # 비즈니스 로직 (pdf, clause, llm, chroma, retrieval, analysis)
│   │   ├── rag/            # 프롬프트 템플릿 + 배치 분석 체인
│   │   ├── utils/          # 파일 유틸리티
│   │   ├── config.py       # 환경변수 기반 설정
│   │   └── main.py         # FastAPI 앱 진입점
│   ├── scripts/            # KB 구축, 테스트 PDF 생성, 검증 스크립트
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/          # UploadPage, ResultPage
│   │   ├── components/     # FileUploader, ClauseCard, RiskBadge, ConfidenceBar
│   │   ├── api/            # Axios 클라이언트
│   │   └── styles/         # 글로벌 CSS (골드/블랙 테마)
│   ├── vite.config.js
│   └── package.json
├── data/
│   ├── chroma/             # ChromaDB 벡터 저장소
│   ├── uploads/            # 업로드된 PDF 원본
│   └── results/            # 분석 결과 JSON
├── docs/                   # 개발 일지
├── start.sh                # 전체 서비스 시작
├── stop.sh                 # 전체 서비스 종료
├── .env.example            # 환경변수 템플릿
└── README.md
```

---

## 빠른 시작

### 사전 준비

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.ai) 설치

```bash
# LLM 모델 다운로드
ollama pull qwen3:8b
```

### 방법 1: 스크립트로 한 번에 실행

```bash
cp .env.example .env        # 환경변수 설정
./start.sh                  # Ollama + 백엔드 + 프론트엔드 일괄 시작
```

종료:

```bash
./stop.sh
```

### 방법 2: 개별 실행

```bash
# 1. 백엔드
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000

# 2. 프론트엔드
cd frontend
npm install
npm run dev
```

### 접속 URL

| 서비스 | URL |
|--------|-----|
| Frontend | `http://localhost:5173` |
| Backend API | `http://localhost:8000` |
| Swagger Docs | `http://localhost:8000/docs` |

---

## 지식베이스(KB) 구축

분석 품질 향상을 위해 초기 인덱싱을 권장합니다.

```bash
# 기본 법률/실무 데이터로 구축
python -m backend.scripts.build_kb

# AI Hub 원천 데이터 포함 시
python -m backend.scripts.build_kb --data-dir data/raw/aihub

# KB 상태 확인
curl http://localhost:8000/api/kb/status
```

---

## 환경 변수

`.env.example`을 복사하여 `.env`를 생성하세요.

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `OLLAMA_MODEL_NAME` | `qwen3:8b` | Ollama LLM 모델 |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 서버 주소 |
| `OLLAMA_TIMEOUT` | `300` | LLM 호출 타임아웃 (초) |
| `OLLAMA_NUM_PARALLEL` | `2` | Ollama 병렬 처리 수 |
| `EMBEDDING_DEVICE` | `auto` | 임베딩 디바이스 (`auto`/`cpu`/`cuda`) |
| `CHROMA_COLLECTION` | `lease_kb` | ChromaDB 컬렉션명 |
| `RETRIEVAL_TOP_K` | `5` | 유사 조항 검색 개수 |
| `RETRIEVAL_MIN_SCORE` | `0.5` | 최소 유사도 점수 |

---

## API

| Method | Endpoint | 설명 |
|--------|----------|------|
| `GET` | `/health` | Ollama 연결 상태 + KB 문서 수 |
| `POST` | `/api/documents/upload` | PDF 업로드 및 분석 (multipart/form-data) |
| `GET` | `/api/analyses/{id}` | 저장된 분석 결과 조회 |
| `GET` | `/api/kb/status` | KB 컬렉션 상태 |

### 응답 예시

```json
{
  "status": "completed",
  "result": {
    "id": "analysis-uuid",
    "filename": "contract.pdf",
    "total_clauses": 11,
    "risky_clauses": 6,
    "summary": "총 11개 조항 중 6개 조항에서 위험 요소가 발견되었습니다...",
    "clause_analyses": [
      {
        "clause_index": 3,
        "clause_title": "제4조 (보증금 반환)",
        "risk_level": "high",
        "confidence": 0.88,
        "risks": [
          {
            "risk_type": "보증금_미반환_위험",
            "description": "보증금 반환 시기를 과도하게 지연...",
            "suggestion": "반환 시점과 공제 기준을 명확히..."
          }
        ],
        "similar_references": [
          "주택임대차보호법 제3조의2 ... (유사도: 0.78)"
        ],
        "explanation": "임차인에게 불리한 보증금 반환 제한 조항입니다."
      }
    ]
  }
}
```

---

## 유틸리티 스크립트

```bash
# 지식베이스 구축
python -m backend.scripts.build_kb

# 확장 KB 인덱싱 (대용량 샘플 데이터)
python -m backend.scripts.index_kb

# 테스트용 계약서 PDF 생성
pip install fpdf2
python -m backend.scripts.generate_test_pdf

# 분석 정확도 검증
python -m backend.scripts.validate
```

---

## 분석 정확도

AI Hub 임대차 약관 데이터를 활용한 검증 결과:

- KB 규모: 약관 538건 + 판결문 1,089건 = **1,679건**
- 불리 조항 탐지율(Recall): **100%**
- 전체 정확도: **85%**
- 거짓 경보(False Positive): 3건

> 상세 검증 방법 및 결과는 [docs/devlog-2026-04-02.md](docs/devlog-2026-04-02.md) 참고

---

## 알려진 제한 사항

- 분석 정확도는 LLM 모델 성능, 프롬프트, KB 품질에 의존합니다.
- 프론트엔드 결과는 라우팅 state 기반으로, 새로고침 시 사라질 수 있습니다.
- 인증/인가, 파일 크기 제한, 비동기 작업 큐, 결과 DB 저장소 등은 미구현 상태입니다.
- 자동화 테스트는 아직 준비되지 않았습니다.

---

**K&H2** — Legal Contract Review Project Team
