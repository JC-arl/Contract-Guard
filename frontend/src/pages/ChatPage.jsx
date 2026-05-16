import { useState, useRef, useEffect } from "react";
import { postChatMessage } from "../api/chatClient";
import { UserMessage, AssistantMessage } from "../components/ChatMessage";
import "../styles/chat.css";

const DOMAIN_OPTIONS = [
  { key: null, label: "자동" },
  { key: "lease", label: "임대차" },
  { key: "sales", label: "매매" },
  { key: "employment", label: "근로" },
  { key: "service", label: "용역·도급" },
  { key: "loan", label: "금전소비대차" },
];

// 변호사용 법률 Q&A 챗봇 페이지.
// - 상태는 페이지 로컬 useState로만 관리 (Step 1: 서버 영속화 없음, 새로고침 시 소실)
// - 멀티턴: 직전 2턴을 백엔드에 전송 (백엔드가 잘라 사용)
// - UI: C(하이브리드) — 결론·출처는 항상, 상세 답변은 접힘
export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [contractType, setContractType] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const listRef = useRef(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setError("");
    const userMsg = { role: "user", content: text };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);

    try {
      // 백엔드가 직전 2턴까지만 사용하지만, 클라이언트는 user 메시지를 추가하기 전 상태를 전달.
      // history에는 직전 어시스턴트의 텍스트만 들어가도록 변환 (Citation 등 메타는 제외).
      const historyForApi = messages.map((m) => ({
        role: m.role,
        content: m.role === "assistant" ? `${m.data?.conclusion || ""}\n${m.data?.answer || ""}` : m.content,
      }));

      const response = await postChatMessage({
        message: text,
        history: historyForApi,
        contractType,
      });

      setMessages([...nextMessages, { role: "assistant", data: response }]);
    } catch (err) {
      const detail = err?.response?.data?.detail || err?.message || "요청 실패";
      setError(`요청 실패: ${detail}`);
      // 사용자 메시지는 남기고 마지막 어시스턴트 응답만 누락
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    if (messages.length === 0) return;
    if (!confirm("대화를 모두 비우시겠습니까?")) return;
    setMessages([]);
    setError("");
  };

  return (
    <div className="chat-page">
      <div className="chat-header">
        <div className="chat-header-title">
          <h1>법률 Q&amp;A 챗봇</h1>
          <p className="chat-header-sub">법령·판례·표준약관 1차 리서치 보조 (변호사 전용)</p>
        </div>
        <div className="chat-header-actions">
          <div className="chat-domain-toggle">
            {DOMAIN_OPTIONS.map((opt) => (
              <button
                key={opt.key || "auto"}
                type="button"
                className={`chat-domain-btn${contractType === opt.key ? " active" : ""}`}
                onClick={() => setContractType(opt.key)}
                disabled={loading}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="chat-clear-btn"
            onClick={handleClear}
            disabled={loading || messages.length === 0}
          >
            대화 비우기
          </button>
        </div>
      </div>

      <div className="chat-list" ref={listRef}>
        {messages.length === 0 && !loading && (
          <div className="chat-empty">
            <p>변호사용 법률 Q&amp;A 챗봇입니다.</p>
            <p className="chat-empty-sub">
              법령·판례·표준약관 기반 1차 리서치를 보조합니다.<br />
              인용된 조문·판례 번호는 검색된 참고 자료에 한정됩니다.
            </p>
            <ul className="chat-empty-examples">
              <li>예) 민법 제640조 2기 차임 연체 해지권 행사 시 최고 절차 필요 여부에 대한 판례 동향?</li>
              <li>예) 주임법 제10조 강행규정에 위반한 약정의 효력?</li>
              <li>예) 근기법 제23조 정당한 이유 없는 해고에 대한 판단 기준?</li>
            </ul>
          </div>
        )}

        {messages.map((m, i) =>
          m.role === "user" ? (
            <UserMessage key={i} content={m.content} />
          ) : (
            <AssistantMessage key={i} data={m.data} />
          ),
        )}

        {loading && (
          <div className="chat-msg chat-msg-assistant">
            <div className="chat-msg-body">
              <div className="chat-loading">
                <span className="chat-loading-dot" />
                <span className="chat-loading-dot" />
                <span className="chat-loading-dot" />
                <span className="chat-loading-text">참고 자료 검색 후 답변 생성 중…</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {error && <div className="chat-error">{error}</div>}

      <form className="chat-input-row" onSubmit={handleSubmit}>
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="법령·판례·표준약관에 대해 질문하세요. (Enter 전송, Shift+Enter 줄바꿈)"
          rows={2}
          disabled={loading}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <button
          type="submit"
          className="chat-submit"
          disabled={loading || !input.trim()}
        >
          전송
        </button>
      </form>
    </div>
  );
}
