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
    setProgress("PDF 업로드 및 분석 중...");

    const steps = [
      { msg: "PDF 텍스트 추출 중...", delay: 3000 },
      { msg: "조항 분리 중...", delay: 5000 },
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
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <span className="hero-badge fade-up" style={{ animationDelay: "0.1s" }}>AI 기반 계약서 분석</span>
          <h1 className="hero-title fade-up" style={{ animationDelay: "0.3s" }}>
            임대차 계약,<br />
            <span className="hero-highlight">불리한 조항</span>을 놓치지 마세요
          </h1>
          <p className="hero-desc fade-up" style={{ animationDelay: "0.5s" }}>
            주택임대차보호법과 판례 데이터를 기반으로<br />
            임차인에게 불리한 조항을 자동 탐지하고 개선안을 제안합니다.
          </p>
        </div>
      </section>

      {/* Upload Section */}
      <section className="upload-section">
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
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon-wrap">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
              </svg>
            </div>
            <h3>조항 자동 분리</h3>
            <p>PDF에서 조항을 자동 인식하여 개별 분석합니다</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon-wrap">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
                <line x1="4" y1="22" x2="4" y2="15" />
              </svg>
            </div>
            <h3>법률 기반 분석</h3>
            <p>주택임대차보호법, 판례, 약관심사 기준 적용</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon-wrap">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <polyline points="9 12 11 14 15 10" />
              </svg>
            </div>
            <h3>위험 조항 탐지</h3>
            <p>임차인에게 불리한 조항을 4단계로 분류합니다</p>
          </div>
        </div>
      </section>

    </div>
  );
}
