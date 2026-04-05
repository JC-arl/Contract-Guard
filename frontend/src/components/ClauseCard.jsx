import { useState } from "react";
import RiskBadge from "./RiskBadge";
import ConfidenceBar from "./ConfidenceBar";

export default function ClauseCard({ analysis }) {
  const [expanded, setExpanded] = useState(analysis.risk_level !== "safe");

  return (
    <div className={`clause-card clause-${analysis.risk_level}`}>
      <div className="clause-header" onClick={() => setExpanded(!expanded)}>
        <div className="clause-title-row">
          <RiskBadge level={analysis.risk_level} />
          <h3 className="clause-title">{analysis.clause_title}</h3>
          <span className="expand-icon">{expanded ? "\u25B2" : "\u25BC"}</span>
        </div>
        <ConfidenceBar value={analysis.confidence} label="신뢰도" />
      </div>

      {expanded && (
        <div className="clause-body">
          <div className="clause-content">
            <h4>조항 내용</h4>
            <p>{analysis.clause_content}</p>
          </div>

          {analysis.explanation && (
            <div className="clause-explanation">
              <h4>분석 결과</h4>
              <p>{analysis.explanation}</p>
            </div>
          )}

          {analysis.risks.length > 0 && (
            <div className="clause-risks">
              <h4>발견된 위험 요소</h4>
              {analysis.risks.map((risk, i) => (
                <div key={i} className="risk-item">
                  <div className="risk-type">{risk.risk_type}</div>
                  <p className="risk-description">{risk.description}</p>
                  {risk.suggestion && (
                    <p className="risk-suggestion">
                      <strong>개선 제안:</strong> {risk.suggestion}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {analysis.similar_references.length > 0 && (
            <div className="clause-references">
              <h4>참고 법률 조항</h4>
              <ul>
                {analysis.similar_references.map((ref, i) => (
                  <li key={i}>{ref}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
