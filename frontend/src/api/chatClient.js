import api from "./client";

// 변호사용 법률 Q&A 챗봇 요청.
// history는 직전 2턴까지만 백엔드가 사용하지만, 클라이언트는 전체 메시지를 전송해도 무방.
// 백엔드가 끝에서 2개만 잘라 쓴다.
export async function postChatMessage({ message, history = [], contractType = null }) {
  const payload = {
    message,
    history: history.map((m) => ({ role: m.role, content: m.content })),
    contract_type: contractType,
  };
  const response = await api.post("/api/chat", payload);
  return response.data;
}
