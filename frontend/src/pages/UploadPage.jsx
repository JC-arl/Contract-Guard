import { useState } from "react";
import { useNavigate } from "react-router-dom";
import FileUploader from "../components/FileUploader";
import { uploadDocument } from "../api/client";

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
      { msg: "관련 법률 및 판례 검색 중...", delay: 8000 },
      { msg: "AI 분석 진행 중... (잠시만 기다려주세요)", delay: 15000 },
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
            탐지합니다
          </h1>
          <p className="hero-desc fade-up" style={{ animationDelay: "0.4s" }}>
            관련 법률과 판례 데이터를 기반으로
            계약서의 위험 조항을 자동 탐지하고 개선안을 제안합니다.
          </p>
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

      {/* 지원 계약 유형 */}
      <section className="features-section">
        <h2 className="section-title fade-up" style={{ animationDelay: "0.6s" }}>
          <span className="section-title-line" />
          지원 계약 유형
          <span className="section-title-line" />
        </h2>
        <div className="features-grid">
          <div className="feature-card fade-up" style={{ animationDelay: "0.7s" }}>
            <div className="feature-icon-wrap feature-icon-lease">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                <polyline points="9 22 9 12 15 12 15 22" />
              </svg>
            </div>
            <h3>임대차 계약</h3>
            <p>주택·상가 임대차보호법, 판례 기반으로 보증금 반환, 수선의무, 계약해지 등 위험 조항을 분석합니다</p>
          </div>
          <div className="feature-card fade-up" style={{ animationDelay: "0.8s" }}>
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
          </div>
          <div className="feature-card fade-up" style={{ animationDelay: "0.9s" }}>
            <div className="feature-icon-wrap feature-icon-employ">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                <path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" />
              </svg>
            </div>
            <h3>근로 계약</h3>
            <p>근로기준법 기반으로 임금, 근무시간, 퇴직금, 해고 조건 등 근로자에게 불리한 조항을 검토합니다</p>
          </div>
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
              <p>업로드한 문서에서 조항을 자동 인식하여 개별 분석합니다</p>
            </div>
          </div>
          <div className="process-connector" />
          <div className="process-step fade-up" style={{ animationDelay: "1.2s" }}>
            <div className="step-num">2</div>
            <div className="step-body">
              <h4>법률 기반 분석</h4>
              <p>계약 유형별 관련 법률과 판례 기준을 적용합니다</p>
            </div>
          </div>
          <div className="process-connector" />
          <div className="process-step fade-up" style={{ animationDelay: "1.3s" }}>
            <div className="step-num">3</div>
            <div className="step-body">
              <h4>위험 조항 탐지</h4>
              <p>불리한 조항을 4단계로 분류하고 개선안을 제시합니다</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
