import ChatReferencesPanel, { citationKey } from "./ChatReferencesPanel";

// 사용자 메시지 — 짧은 버블 형태
export function UserMessage({ content }) {
  return (
    <div className="chat-msg chat-msg-user">
      <div className="chat-msg-bubble">{content}</div>
    </div>
  );
}

// 어시스턴트 메시지 — 결론(항상 노출) + 펼침 답변 + 출처 패널
// C(하이브리드) UI: 결론과 출처 카드는 항상 보이고, 상세 답변만 접힘.
export function AssistantMessage({ data }) {
  const {
    conclusion,
    answer,
    citations = [],
    all_references = [],
    domain,
    status,
  } = data;

  const citedKeys = new Set(citations.map(citationKey));
  const domainLabel = DOMAIN_LABELS[domain] || (domain ? domain : "자동(전체)");

  return (
    <div className="chat-msg chat-msg-assistant">
      <div className="chat-msg-body">
        <div className="chat-msg-meta">
          <span className="chat-msg-domain">분류: {domainLabel}</span>
          {status && status !== "ok" && (
            <span className={`chat-msg-status chat-msg-status-${status}`}>
              {STATUS_LABEL[status] || status}
            </span>
          )}
        </div>

        <div className="chat-msg-conclusion">{conclusion}</div>

        <details className="chat-msg-details">
          <summary>상세 답변 펼치기</summary>
          <pre className="chat-msg-answer">{answer}</pre>
        </details>

        <div className="chat-msg-refs">
          <div className="chat-msg-refs-title">참고 자료 ({all_references.length}건)</div>
          <ChatReferencesPanel references={all_references} citedKeys={citedKeys} />
        </div>
      </div>
    </div>
  );
}

const DOMAIN_LABELS = {
  lease: "임대차",
  sales: "매매",
  employment: "근로",
  service: "용역·도급",
  loan: "금전소비대차",
};

const STATUS_LABEL = {
  parse_failed: "답변 파싱 실패",
  llm_error: "LLM 오류",
};
