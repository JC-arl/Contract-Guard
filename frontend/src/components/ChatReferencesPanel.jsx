import { useState, useEffect } from "react";

// 챗봇 답변의 출처 카드 패널.
// ResultPage의 GroupedReferencesPanel과 시각적으로 동일한 CSS 클래스를 사용해
// 사용자 학습 비용 없이 같은 룩앤필을 유지한다.
// 백엔드 Citation 모델은 이미 category 필드를 가지므로 프론트에서 재분류하지 않는다.

const CHAT_REF_CATEGORIES = [
  { key: "law", label: "법률", icon: "法" },
  { key: "judgment", label: "판례", icon: "判" },
  { key: "safe_clause", label: "표준약관", icon: "標" },
  { key: "unfair_clause", label: "불공정약관", icon: "違" },
];

function stripMdMarks(text) {
  if (!text) return "";
  return String(text).replace(/\*\*([^*]+)\*\*/g, "$1");
}

function CitationDetailModal({ reference, onClose }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  if (!reference) return null;
  const sim = Math.round((reference.similarity || 0) * 100);
  return (
    <div className="ref-modal-overlay" onClick={onClose}>
      <div className="ref-modal kb-detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="ref-modal-header">
          <h2 className="ref-modal-title">참고 자료 전문</h2>
          <button type="button" className="ref-modal-close" onClick={onClose} aria-label="닫기">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
        <div className="kb-detail-meta">
          <span className="kb-detail-meta-item">
            <span className="kb-detail-meta-label">출처</span> {reference.source || "unknown"}
          </span>
          <span className="kb-detail-meta-item">
            <span className="kb-detail-meta-label">유사도</span> {sim}%
          </span>
          {reference.article && (
            <span className="kb-detail-meta-item">
              <span className="kb-detail-meta-label">조문</span> {reference.article}
            </span>
          )}
        </div>
        <div className="ref-modal-body">
          <div className="kb-detail-text">{stripMdMarks(reference.text || "")}</div>
        </div>
      </div>
    </div>
  );
}

// references: 백엔드 Citation[] (category 필드 포함)
// cited: 답변에 인용된 출처. 시각적으로 강조 표시.
export default function ChatReferencesPanel({ references, citedKeys }) {
  const [activeRef, setActiveRef] = useState(null);
  if (!references || references.length === 0) return null;

  // 카테고리별 그룹
  const grouped = { law: [], judgment: [], safe_clause: [], unfair_clause: [] };
  for (const ref of references) {
    const cat = grouped[ref.category] ? ref.category : "law";
    grouped[cat].push(ref);
  }
  for (const k of Object.keys(grouped)) {
    grouped[k].sort((a, b) => (b.similarity || 0) - (a.similarity || 0));
  }

  const total = Object.values(grouped).reduce((s, arr) => s + arr.length, 0);
  if (total === 0) return null;

  return (
    <>
      <div className="ref-grouped chat-ref-grouped">
        {CHAT_REF_CATEGORIES.map((cat) => {
          const items = grouped[cat.key];
          if (!items || items.length === 0) return null;
          return (
            <div key={cat.key} className={`ref-grouped-cat ref-grouped-cat-${cat.key}`}>
              <div className="ref-grouped-header">
                <span className="ref-grouped-icon">{cat.icon}</span>
                <span className="ref-grouped-label">{cat.label}</span>
                <span className="ref-grouped-count">{items.length}건</span>
              </div>
              <ul className="ref-grouped-list">
                {items.map((ref, i) => {
                  const sim = Math.round((ref.similarity || 0) * 100);
                  const text = (ref.text || "").replace(/^\[[^\]]+\]\s*/, "");
                  const preview = text.slice(0, 200);
                  const refKey = `${ref.source}|${(ref.article || "")}|${text.slice(0, 40)}`;
                  const isCited = citedKeys && citedKeys.has(refKey);
                  return (
                    <li key={i} className={`ref-grouped-item${isCited ? " ref-grouped-item-cited" : ""}`}>
                      <button
                        type="button"
                        className="ref-grouped-item-btn"
                        onClick={() => setActiveRef(ref)}
                        title="클릭하여 전문 보기"
                      >
                        <div className="ref-grouped-bar-wrap" title={`유사도 ${sim}%`}>
                          <div className="ref-grouped-bar-track">
                            <div className="ref-grouped-bar" style={{ width: `${Math.max(2, sim)}%` }} />
                          </div>
                          <span className="ref-grouped-pct">{sim}%</span>
                          {isCited && <span className="chat-ref-cited-badge">인용</span>}
                        </div>
                        {ref.article && <p className="chat-ref-article">{ref.article}</p>}
                        <p className="ref-grouped-text">
                          {stripMdMarks(preview)}
                          {text.length > 200 ? "…" : ""}
                        </p>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </div>
      {activeRef && <CitationDetailModal reference={activeRef} onClose={() => setActiveRef(null)} />}
    </>
  );
}

// Citation 한 건의 고유 키 — `citedKeys` Set 생성용 헬퍼.
export function citationKey(c) {
  return `${c.source}|${c.article || ""}|${(c.text || "").slice(0, 40)}`;
}
