import axios from "axios";

const api = axios.create({
  baseURL: "/",
  timeout: 600000, // 10분 (조항별 개별 LLM 분석 시간 고려)
});

// 계약서 파일 업로드 및 분석 요청 (PDF, DOCX)
export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post("/api/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export default api;
