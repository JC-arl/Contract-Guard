import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import FileUploader from "../components/FileUploader";
import { uploadDocument } from "../api/client";

function Shield3D() {
  return (
    <div className="shield-3d-scene">
      <div className="shield-3d">
        {/* 방패 면 */}
        <div className="shield-face shield-front">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <polyline points="9 12 11 14 15 10" strokeWidth="2" />
          </svg>
        </div>
        {/* 문서 아이콘들 */}
        <div className="shield-orbit shield-orbit-1">
          <div className="orbit-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </div>
        </div>
        <div className="shield-orbit shield-orbit-2">
          <div className="orbit-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </div>
        </div>
        <div className="shield-orbit shield-orbit-3">
          <div className="orbit-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
          </div>
        </div>
        {/* 링 */}
        <div className="shield-ring" />
      </div>
    </div>
  );
}

function TiltCard({ children, className, style }) {
  const ref = useRef(null);

  const handleMouseMove = useCallback((e) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    el.style.transform = `perspective(600px) rotateY(${x * 8}deg) rotateX(${-y * 8}deg) translateY(-4px)`;
  }, []);

  const handleMouseLeave = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    el.style.transform = "perspective(600px) rotateY(0) rotateX(0) translateY(0)";
  }, []);

  return (
    <div
      ref={ref}
      className={className}
      style={style}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {children}
    </div>
  );
}

export default function UploadPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState("");
  const navigate = useNavigate();

  async function handleFileSelect(file) {
    setLoading(true);
    setError(null);
    setProgress("문서 업로드 및 분석 중...");

    const steps = [
      { msg: "문서 텍스트 추출 중...", delay: 3000 },
      { msg: "계약 유형 자동 감지 중...", delay: 5000 },
      { msg: "관련 법률 및 판례 하이브리드 검색 중...", delay: 8000 },
      { msg: "AI 위험 분석 진행 중... (잠시만 기다려주세요)", delay: 15000 },
    ];

    const timers = steps.map(({ msg, delay }) =>
      setTimeout(() => setProgress(msg), delay)
    );

    try {
      const data = await uploadDocument(file);
      if (data.status === "completed" && data.result) {
        navigate("/result", { state: { result: data.result } });
      } else {
        setError(data.error || "분석에 실패했습니다.");
      }
    } catch (err) {
      const msg =
        err.response?.data?.detail || err.message || "서버 오류가 발생했습니다.";
      setError(msg);
    } finally {
      timers.forEach(clearTimeout);
      setLoading(false);
      setProgress("");
    }
  }

  return (
    <div className="upload-page">
      {/* Hero + Upload */}
      <section className="hero-section">
        <div className="hero-grid">
          <div className="hero-content">
            <span className="hero-badge fade-up" style={{ animationDelay: "0.1s" }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              AI 기반 계약서 분석
            </span>
            <h1 className="hero-title fade-up" style={{ animationDelay: "0.25s" }}>
              계약서 속{" "}
              <span className="hero-highlight">독소조항</span>을<br />
              찾아드립니다
            </h1>
            <p className="hero-desc fade-up" style={{ animationDelay: "0.4s" }}>
              관련 법률과 판례 데이터를 기반으로
              계약서의 위험 조항을 자동으로 분석하고 개선안을 제안해 드립니다.
            </p>
          </div>
          <div className="hero-3d fade-up" style={{ animationDelay: "0.3s" }}>
            <Shield3D />
          </div>
        </div>

        <div className="hero-upload fade-up" style={{ animationDelay: "0.5s" }}>
          <div className="upload-card">
            <FileUploader onFileSelect={handleFileSelect} disabled={loading} />

            {loading && (
              <div className="loading-indicator">
                <div className="loading-bar">
                  <div className="loading-bar-fill" />
                </div>
                <p>{progress}</p>
              </div>
            )}

            {error && (
              <div className="error-message">
                <span className="error-icon">!</span>
                <span>{error}</span>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 핵심 강점 */}
      <section className="strengths-section">
        <h2 className="section-title fade-up" style={{ animationDelay: "0.6s" }}>
          <span className="section-title-line" />
          왜 Contract Guard인가
          <span className="section-title-line" />
        </h2>
        <div className="strengths-grid">
          <TiltCard className="strength-card fade-up" style={{ animationDelay: "0.65s" }}>
            <div className="strength-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0110 0v4" />
              </svg>
            </div>
            <h3>완전한 로컬 처리</h3>
            <p>외부 서버 전송 없이 모든 분석이 로컬에서 수행됩니다. 계약서 데이터가 외부로 유출될 걱정이 없습니다.</p>
          </TiltCard>
          <TiltCard className="strength-card fade-up" style={{ animationDelay: "0.75s" }}>
            <div className="strength-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="10" />
                <path d="M8 12l2 2 4-4" />
              </svg>
            </div>
            <h3>하이브리드 검색</h3>
            <p>BM25 키워드 매칭과 벡터 유사도 검색을 RRF로 결합하여, 단일 검색보다 정확한 법률 근거를 제공합니다.</p>
          </TiltCard>
          <TiltCard className="strength-card fade-up" style={{ animationDelay: "0.85s" }}>
            <div className="strength-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z" />
                <path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z" />
              </svg>
            </div>
            <h3>법률 데이터 기반</h3>
            <p>표준약관, 판결문, 관련 법령 등 실제 법률 데이터를 학습하여 근거 있는 분석 결과를 제공합니다.</p>
          </TiltCard>
        </div>
      </section>

      {/* 지원 계약 유형 */}
      <section className="features-section">
        <h2 className="section-title fade-up" style={{ animationDelay: "0.6s" }}>
          <span className="section-title-line" />
          지원 계약 유형
          <span className="section-title-line" />
        </h2>
        <div className="features-grid">
          <TiltCard className="feature-card fade-up" style={{ animationDelay: "0.7s" }}>
            <div className="feature-icon-wrap feature-icon-lease">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                <polyline points="9 22 9 12 15 12 15 22" />
              </svg>
            </div>
            <h3>임대차 계약</h3>
            <p>주택·상가 임대차보호법, 판례 기반으로 보증금 반환, 수선의무, 계약해지 등 위험 조항을 분석합니다</p>
          </TiltCard>
          <TiltCard className="feature-card fade-up" style={{ animationDelay: "0.8s" }}>
            <div className="feature-icon-wrap feature-icon-sales">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="12" y1="18" x2="12" y2="12" />
                <line x1="9" y1="15" x2="15" y2="15" />
              </svg>
            </div>
            <h3>매매 계약</h3>
            <p>부동산 매매 시 소유권이전, 계약금·잔금 조건, 하자담보 책임 등 매수인에게 불리한 조항을 탐지합니다</p>
          </TiltCard>
          <TiltCard className="feature-card fade-up" style={{ animationDelay: "0.9s" }}>
            <div className="feature-icon-wrap feature-icon-employ">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                <path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" />
              </svg>
            </div>
            <h3>근로 계약</h3>
            <p>근로기준법 기반으로 임금, 근무시간, 퇴직금, 해고 조건 등 근로자에게 불리한 조항을 검토합니다</p>
          </TiltCard>
        </div>
      </section>

      {/* 분석 프로세스 */}
      <section className="process-section">
        <h2 className="section-title fade-up" style={{ animationDelay: "1.0s" }}>
          <span className="section-title-line" />
          분석 프로세스
          <span className="section-title-line" />
        </h2>
        <div className="process-steps">
          <div className="process-step fade-up" style={{ animationDelay: "1.1s" }}>
            <div className="step-num">1</div>
            <div className="step-body">
              <h4>조항 자동 분리</h4>
              <p>업로드한 문서에서 조항을 자동 인식하고 계약 유형을 감지합니다</p>
            </div>
          </div>
          <div className="process-connector" />
          <div className="process-step fade-up" style={{ animationDelay: "1.2s" }}>
            <div className="step-num">2</div>
            <div className="step-body">
              <h4>하이브리드 검색</h4>
              <p>BM25 키워드 검색과 벡터 유사도 검색을 결합하여 관련 법률·판례를 탐색합니다</p>
            </div>
          </div>
          <div className="process-connector" />
          <div className="process-step fade-up" style={{ animationDelay: "1.3s" }}>
            <div className="step-num">3</div>
            <div className="step-body">
              <h4>AI 위험 분석</h4>
              <p>검색된 법률 근거를 바탕으로 위험 조항을 4단계로 분류하고 개선안을 제시합니다</p>
            </div>
          </div>
        </div>
      </section>

      {/* 기술 스택 */}
      <section className="tech-section">
        <h2 className="section-title fade-up">
          <span className="section-title-line" />
          기술 스택
          <span className="section-title-line" />
        </h2>
        <div className="tech-grid fade-up">
          <div className="tech-item">
            <div className="tech-icon-wrap">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 2a4 4 0 014 4c0 1.95-2 4-4 6-2-2-4-4.05-4-6a4 4 0 014-4z" />
                <path d="M12 12c2 2 4 4.05 4 6a4 4 0 01-8 0c0-1.95 2-4 4-6z" />
                <circle cx="12" cy="12" r="2" />
              </svg>
            </div>
            <span className="tech-label">Qwen3 8B</span>
            <span className="tech-desc">로컬 LLM 추론</span>
          </div>
          <div className="tech-divider" />
          <div className="tech-item">
            <div className="tech-icon-wrap">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="3" />
                <circle cx="12" cy="12" r="8" strokeDasharray="3 3" />
                <line x1="12" y1="1" x2="12" y2="4" />
                <line x1="12" y1="20" x2="12" y2="23" />
                <line x1="1" y1="12" x2="4" y2="12" />
                <line x1="20" y1="12" x2="23" y2="12" />
              </svg>
            </div>
            <span className="tech-label">ChromaDB</span>
            <span className="tech-desc">벡터 유사도 검색</span>
          </div>
          <div className="tech-divider" />
          <div className="tech-item">
            <div className="tech-icon-wrap">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
                <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
              </svg>
            </div>
            <span className="tech-label">BM25 + RRF</span>
            <span className="tech-desc">하이브리드 검색</span>
          </div>
          <div className="tech-divider" />
          <div className="tech-item">
            <div className="tech-icon-wrap">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <polyline points="16 18 22 12 16 6" />
                <polyline points="8 6 2 12 8 18" />
                <line x1="14" y1="4" x2="10" y2="20" />
              </svg>
            </div>
            <span className="tech-label">FastAPI + React</span>
            <span className="tech-desc">풀스택 아키텍처</span>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section fade-up">
        <div className="cta-inner">
          <h2>지금 바로 계약서를 분석해 보세요</h2>
          <p>PDF, DOCX, HWP 파일을 업로드하면 즉시 위험 조항을 찾아드립니다.</p>
          <button className="cta-button" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            계약서 업로드하기
          </button>
        </div>
      </section>
    </div>
  );
}
