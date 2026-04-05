import axios from "axios";

const api = axios.create({
  baseURL: "/",
  timeout: 300000, // 5분 (LLM 분석 시간 고려)
});

// PDF 업로드 및 분석 요청
export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post("/api/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export default api;
