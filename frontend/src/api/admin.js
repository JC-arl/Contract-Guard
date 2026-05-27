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
