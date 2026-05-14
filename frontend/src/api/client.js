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

// OCR 검증 — 이미지에서 텍스트와 박스 좌표를 추출. 분석 파이프라인과 분리된 엔드포인트.
// 응답: { document_id, image_url, overlay_url, result: { width, height, elapsed_ms, boxes:[{poly,text,score}] } }
export async function uploadOcrImage(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post("/api/ocr/test", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

// OCR 결과를 LLM 으로 후보정. 직전 OCR 응답의 boxes 를 그대로 다시 보내고,
// corrected_text 가 채워진 boxes 를 받음. 텍스트와 corrected_text 비교로 LLM 이 어디를
// 어떻게 고쳤는지 시각적으로 확인하기 위한 검증 도구.
export async function correctOcrBoxes(boxes) {
  const response = await api.post("/api/ocr/correct", { boxes });
  return response.data;  // { boxes:[{poly,text,score,corrected_text}], elapsed_ms }
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
