import axios from "axios";

const api = axios.create({
  baseURL: "/",
  timeout: 600000, // 10분 (조항별 개별 LLM 분석 시간 고려)
  withCredentials: true, // 세션/CSRF 쿠키 동봉 (RBAC)
});

// double-submit CSRF: 변경 메서드 요청에 cg_csrf 쿠키 값을 X-CSRF-Token 헤더로 동봉.
function readCookie(name) {
  const m = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
  return m ? decodeURIComponent(m[1]) : null;
}

api.interceptors.request.use((config) => {
  const method = (config.method || "get").toLowerCase();
  if (["post", "put", "patch", "delete"].includes(method)) {
    const csrf = readCookie("cg_csrf");
    if (csrf) {
      config.headers = config.headers || {};
      config.headers["X-CSRF-Token"] = csrf;
    }
  }
  return config;
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

// 지식베이스 통계 조회 (홈 화면 카운트업 애니메이션용)
export async function fetchKbStatus() {
  const response = await api.get("/api/kb/status");
  return response.data;
}

// 분석 결과 기반 수정 계약서 다운로드 URL
// 형식: docx | pdf | hwpx
export function buildExportUrl(analysisId, format) {
  return `/api/analyses/${encodeURIComponent(analysisId)}/export?format=${encodeURIComponent(format)}`;
}

// URL 새로고침/직접 접근 시 결과를 서버에서 복원
export async function fetchAnalysis(analysisId) {
  const response = await api.get(`/api/analyses/${encodeURIComponent(analysisId)}`);
  return response.data;
}

// 사이드바 이력 목록 — 최신순 AnalysisSummary[] 반환
export async function listAnalyses() {
  const response = await api.get("/api/analyses");
  return response.data;
}

// 사이드바에서 분석 항목 삭제
export async function deleteAnalysis(analysisId) {
  await api.delete(`/api/analyses/${encodeURIComponent(analysisId)}`);
}

// 위험 조항에 대해 사용자가 직접 입력한 수정안을 저장(또는 제거)
// text가 null/공백이면 사용자 수정안을 제거하여 권고안으로 회귀
export async function updateClauseOverride(analysisId, clauseIndex, text) {
  const response = await api.patch(
    `/api/analyses/${encodeURIComponent(analysisId)}/clauses/${clauseIndex}`,
    { text },
  );
  return response.data;
}

export default api;
