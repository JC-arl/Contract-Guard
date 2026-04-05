import { useLocation, useNavigate } from "react-router-dom";
import ClauseCard from "../components/ClauseCard";

function RiskGauge({ total, risky }) {
  const safe = total - risky;
  const riskyPct = total > 0 ? (risky / total) * 100 : 0;
  const safePct = total > 0 ? (safe / total) * 100 : 0;

  let gradeClass = "grade-safe";
  let gradeText = "양호";
  if (riskyPct >= 50) {
    gradeClass = "grade-danger";
    gradeText = "위험";
  } else if (riskyPct >= 25) {
    gradeClass = "grade-caution";
    gradeText = "주의";
  }

  return (
    <div className="risk-gauge">
      <div className={`gauge-circle ${gradeClass}`}>
        <span className="gauge-number">{risky}</span>
        <span className="gauge-label">위험 조항</span>
      </div>
      <div className="gauge-info">
        <div className="gauge-bar">
          <div className="gauge-bar-risky" style={{ width: `${riskyPct}%` }} />
          <div className="gauge-bar-safe" style={{ width: `${safePct}%` }} />
        </div>
        <div className="gauge-legend">
          <span className="legend-risky">위험 {risky}건</span>
          <span className="legend-safe">안전 {safe}건</span>
        </div>
      </div>
    </div>
  );
}

export default function ResultPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const result = location.state?.result;

  if (!result) {
    return (
      <div className="result-page">
        <div className="no-result">
          <h3>분석 결과가 없습니다</h3>
          <p>계약서를 먼저 업로드해주세요.</p>
          <button onClick={() => navigate("/")}>계약서 분석하기</button>
        </div>
      </div>
    );
  }

  const sortedAnalyses = [...result.clause_analyses].sort((a, b) => {
    const order = { high: 0, medium: 1, low: 2, safe: 3 };
    return (order[a.risk_level] ?? 3) - (order[b.risk_level] ?? 3);
  });

  const highCount = result.clause_analyses.filter((a) => a.risk_level === "high").length;
  const mediumCount = result.clause_analyses.filter((a) => a.risk_level === "medium").length;
  const lowCount = result.clause_analyses.filter((a) => a.risk_level === "low").length;
  const safeCount = result.clause_analyses.filter((a) => a.risk_level === "safe").length;

  return (
    <div className="result-page">
      <div className="result-top-bar">
        <button className="back-button" onClick={() => navigate("/")}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          새 분석
        </button>
        <h2 className="result-filename">{result.filename}</h2>
      </div>

      <div className="result-summary-card">
        <RiskGauge total={result.total_clauses} risky={result.risky_clauses} />

        <div className="summary-chips">
          {highCount > 0 && (
            <div className="stat-chip stat-high">
              <span className="stat-count">{highCount}</span>
              <span>고위험</span>
            </div>
          )}
          {mediumCount > 0 && (
            <div className="stat-chip stat-medium">
              <span className="stat-count">{mediumCount}</span>
              <span>중위험</span>
            </div>
          )}
          {lowCount > 0 && (
            <div className="stat-chip stat-low">
              <span className="stat-count">{lowCount}</span>
              <span>저위험</span>
            </div>
          )}
          <div className="stat-chip stat-safe-chip">
            <span className="stat-count">{safeCount}</span>
            <span>안전</span>
          </div>
        </div>

        {result.summary && <p className="summary-text">{result.summary}</p>}
      </div>

      <div className="clause-list">
        <div className="clause-list-header">
          <h3>조항별 분석 결과</h3>
          <span className="clause-count">총 {result.total_clauses}개 조항</span>
        </div>
        {sortedAnalyses.map((analysis) => (
          <ClauseCard key={analysis.clause_index} analysis={analysis} />
        ))}
      </div>
    </div>
  );
}
