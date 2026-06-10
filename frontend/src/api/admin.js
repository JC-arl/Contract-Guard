import api from "./client";

// 대시보드 상단 4개 카드용 통계
export async function fetchAdminStats() {
  const res = await api.get("/api/admin/stats");
  return res.data;
}

// 사용자 관리
export async function listUsers() {
  const res = await api.get("/api/admin/users");
  return res.data;
}

// patch: 보낸 필드만 수정 (role / team_id / is_active / display_name)
export async function updateUser(userId, changes) {
  const res = await api.patch(`/api/admin/users/${userId}`, changes);
  return res.data;
}

// 팀 관리
export async function listTeams() {
  const res = await api.get("/api/admin/teams");
  return res.data;
}

export async function createTeam(name, managerId = null) {
  const res = await api.post("/api/admin/teams", { name, manager_id: managerId });
  return res.data;
}

export async function updateTeam(teamId, changes) {
  const res = await api.patch(`/api/admin/teams/${teamId}`, changes);
  return res.data;
}

export async function deleteTeam(teamId) {
  await api.delete(`/api/admin/teams/${teamId}`);
}

// 피드백 승인 (팀장 전용)
// 자기 팀원이 제출한 승인 대기 피드백 목록
export async function listPendingFeedback() {
  const res = await api.get("/api/admin/feedback/pending");
  return res.data;
}

export async function approveFeedback(feedbackId) {
  const res = await api.post(`/api/admin/feedback/${encodeURIComponent(feedbackId)}/approve`);
  return res.data;
}

export async function rejectFeedback(feedbackId) {
  const res = await api.post(`/api/admin/feedback/${encodeURIComponent(feedbackId)}/reject`);
  return res.data;
}

// 승인 대기 피드백 내용 수정 (raw 재파싱). status는 그대로 유지(pending/approved).
export async function editFeedback(feedbackId, raw) {
  const res = await api.patch(`/api/admin/feedback/${encodeURIComponent(feedbackId)}`, { raw });
  return res.data;
}

// 승인된 활성 룰 목록 (조회)
export async function listActiveRules() {
  const res = await api.get("/api/admin/feedback/active");
  return res.data;
}

// 활성 룰 비활성화 (분석 적용 중단)
export async function deactivateFeedback(feedbackId) {
  const res = await api.post(`/api/admin/feedback/${encodeURIComponent(feedbackId)}/deactivate`);
  return res.data;
}
