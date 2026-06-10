import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  createTeam,
  deleteTeam,
  fetchAdminStats,
  listTeams,
  listUsers,
  updateTeam,
  updateUser,
} from "../api/admin";
import { listAnalyses } from "../api/client";
import PerformancePanel from "../components/PerformancePanel";
import "../styles/admin.css";

const ROLE_LABELS = { admin: "시스템 관리자", manager: "팀장", lawyer: "변호사" };

// ─── 헤더 ─────────────────────────────────────
function AdminHeader() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <header className="adm-header">
      <div className="adm-header-brand">
        <img src="/logo.png" alt="K&H2" className="adm-header-logo" />
        <span className="adm-header-title">AI 기반 독소조항 탐색</span>
      </div>
      <nav className="adm-header-nav">
        <button className="adm-nav-link" onClick={() => navigate("/home")}>홈</button>
        <button className="adm-nav-link adm-nav-link--active">관리</button>
        {currentUser && (
          <div className="adm-user-info">
            <span className="adm-user-name">{currentUser.display_name || currentUser.email}</span>
            <span className="adm-user-role">{ROLE_LABELS[currentUser.role] || currentUser.role}</span>
          </div>
        )}
        <button className="adm-header-cta" onClick={handleLogout}>로그아웃</button>
      </nav>
    </header>
  );
}

// ─── 사이드바 ─────────────────────────────────
function AdminSidebar({ active, onSelect, items }) {
  return (
    <aside className="adm-sidebar">
      <div className="adm-sidebar-label">MENU</div>
      {items.map(({ key, label, icon: Icon }) => (
        <button
          key={key}
          className={`adm-sidebar-item${active === key ? " active" : ""}`}
          onClick={() => onSelect(key)}
        >
          <span className="adm-sidebar-icon"><Icon /></span>
          {label}
        </button>
      ))}
    </aside>
  );
}

// ─── 통계 카드 ────────────────────────────────
function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="adm-stat-card">
      <div className="adm-stat-icon"><Icon /></div>
      <div className="adm-stat-label">{label}</div>
      <div className="adm-stat-number">
        {(value ?? 0).toLocaleString()}<span className="adm-stat-suffix">건</span>
      </div>
    </div>
  );
}

// ─── 팀 생성 패널 ─────────────────────────────
function CreateTeamPanel({ onCreated }) {
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    const trimmed = name.trim();
    if (!trimmed) {
      setError("팀 이름을 입력해 주세요.");
      return;
    }
    setSubmitting(true);
    try {
      await createTeam(trimmed);
      setName("");
      onCreated?.();
    } catch (err) {
      setError(err.response?.data?.detail || "팀 생성에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="adm-panel">
      <h2 className="adm-panel-title">팀 생성</h2>
      <form className="adm-create-team-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="adm-input"
          placeholder="새 팀 이름을 입력하세요"
          value={name}
          onChange={(e) => setName(e.target.value)}
          disabled={submitting}
        />
        <button type="submit" className="adm-btn-primary" disabled={submitting}>
          {submitting ? "생성 중..." : "팀 생성"}
        </button>
      </form>
      <p className="adm-helper">
        생성 후 사용자 관리에서 팀 배정과 팀장 지정을 할 수 있습니다.
      </p>
      {error && <div className="adm-error">{error}</div>}
    </section>
  );
}

// ─── 사용자 테이블 ────────────────────────────
function UsersTable({ users, teams, onUpdate, readOnly = false }) {
  const teamOptions = useMemo(
    () => [{ id: "", name: "미소속" }, ...teams.map((t) => ({ id: t.id, name: t.name }))],
    [teams],
  );
  const teamNameById = useMemo(
    () => Object.fromEntries(teams.map((t) => [t.id, t.name])),
    [teams],
  );

  return (
    <section className="adm-panel">
      <div className="adm-panel-head">
        <h2 className="adm-panel-title">{readOnly ? "팀원" : "사용자 관리"}</h2>
        <span className="adm-panel-count">{users.length}명</span>
      </div>
      <div className="adm-table">
        <div className="adm-table-head">
          <span>이메일</span>
          <span>역할</span>
          <span>팀</span>
          <span>상태</span>
        </div>
        <div className="adm-table-body">
          {users.map((u) => (
            <div key={u.id} className="adm-table-row">
              <div className="adm-user-cell">
                <div className="adm-user-name">{u.display_name || u.email}</div>
                <div className="adm-user-email">{u.email}</div>
              </div>
              {readOnly ? (
                <span className="adm-text-cell">{ROLE_LABELS[u.role] || u.role}</span>
              ) : (
                <select
                  className="adm-select"
                  value={u.role}
                  onChange={(e) => onUpdate(u.id, { role: e.target.value })}
                >
                  <option value="admin">시스템 관리자</option>
                  <option value="manager">팀장</option>
                  <option value="lawyer">변호사</option>
                </select>
              )}
              {readOnly ? (
                <span className="adm-text-cell">{teamNameById[u.team_id] || "미소속"}</span>
              ) : (
                <select
                  className="adm-select"
                  value={u.team_id ?? ""}
                  onChange={(e) =>
                    onUpdate(u.id, { team_id: e.target.value === "" ? null : Number(e.target.value) })
                  }
                >
                  {teamOptions.map((t) => (
                    <option key={String(t.id)} value={t.id}>{t.name}</option>
                  ))}
                </select>
              )}
              {readOnly ? (
                <span className={`adm-toggle${u.is_active ? " on" : ""}`}>
                  {u.is_active ? "활성" : "비활성"}
                </span>
              ) : (
                <button
                  type="button"
                  className={`adm-toggle${u.is_active ? " on" : ""}`}
                  onClick={() => onUpdate(u.id, { is_active: !u.is_active })}
                  aria-label={u.is_active ? "활성 상태" : "비활성 상태"}
                >
                  {u.is_active ? "활성" : "비활성"}
                </button>
              )}
            </div>
          ))}
          {users.length === 0 && <div className="adm-empty">등록된 사용자가 없습니다.</div>}
        </div>
      </div>
    </section>
  );
}

// ─── 분석 이력 패널 (매니저 전용) ──────────────
const CONTRACT_LABELS = {
  lease: "임대차", sales: "매매", employment: "근로", service: "용역", loan: "금전소비대차",
};
function formatDate(iso) {
  if (!iso) return "-";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "-";
  return d.toLocaleDateString("ko-KR", { year: "2-digit", month: "2-digit", day: "2-digit" });
}

function AnalysisHistoryPanel({ analyses, loading, currentUser, onOpen }) {
  return (
    <section className="adm-panel">
      <div className="adm-panel-head">
        <h2 className="adm-panel-title">팀 분석 이력</h2>
        <span className="adm-panel-count">{analyses.length}건</span>
      </div>
      <div className="adm-history-table">
        <div className="adm-history-head">
          <span>파일명</span>
          <span>작성자</span>
          <span>계약유형</span>
          <span>위험 조항</span>
          <span>분석일</span>
        </div>
        <div className="adm-history-body">
          {loading && <div className="adm-empty">불러오는 중...</div>}
          {!loading && analyses.length === 0 && (
            <div className="adm-empty">표시할 분석 이력이 없습니다.</div>
          )}
          {!loading && analyses.map((a) => {
            const isMine = currentUser && a.owner_id === currentUser.id;
            return (
              <div
                key={a.id}
                className="adm-history-row"
                onClick={() => onOpen(a.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onOpen(a.id); }
                }}
              >
                <span className="adm-history-file" title={a.filename}>{a.filename}</span>
                <span className={`adm-history-owner${isMine ? " mine" : ""}`}>
                  {isMine ? "나" : (a.owner_name || "-")}
                </span>
                <span>{CONTRACT_LABELS[a.contract_type] || a.contract_type || "기타"}</span>
                <span className="adm-history-risk">
                  {a.risky_clauses > 0 ? (
                    <span className="adm-risk-pill">{a.risky_clauses}건</span>
                  ) : (
                    <span className="adm-risk-safe">0건</span>
                  )}
                </span>
                <span className="adm-history-date">{formatDate(a.created_at)}</span>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}


// ─── 팀 리스트 ────────────────────────────────
function TeamsPanel({ teams, users, onUpdate, onDelete, readOnly = false }) {
  return (
    <section className="adm-panel">
      <div className="adm-panel-head">
        <h2 className="adm-panel-title">{readOnly ? "팀 구성도" : "팀 관리"}</h2>
        <span className="adm-panel-count">{teams.length}팀</span>
      </div>
      <ul className="adm-team-list">
        {teams.map((t) => {
          const teamMembers = users.filter((u) => u.team_id === t.id);
          return (
            <li key={t.id} className="adm-team-item">
              <div className="adm-team-main">
                <div className="adm-team-name">{t.name}</div>
                <div className="adm-team-meta">
                  팀장: <strong>{t.manager_name || "미지정"}</strong> · 멤버 {t.member_count}명
                </div>
              </div>
              {!readOnly && (
                <div className="adm-team-actions">
                  <select
                    className="adm-select"
                    value={t.manager_id ?? ""}
                    onChange={(e) =>
                      onUpdate(t.id, {
                        manager_id: e.target.value === "" ? null : Number(e.target.value),
                      })
                    }
                    title="팀장 지정 (먼저 해당 사용자를 이 팀에 배정해야 함)"
                  >
                    <option value="">팀장 미지정</option>
                    {teamMembers.map((m) => (
                      <option key={m.id} value={m.id}>{m.display_name || m.email}</option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="adm-btn-danger"
                    onClick={() => {
                      if (window.confirm(`'${t.name}' 팀을 삭제하시겠습니까? 멤버는 미소속으로 변경됩니다.`)) {
                        onDelete(t.id);
                      }
                    }}
                  >
                    삭제
                  </button>
                </div>
              )}
            </li>
          );
        })}
        {teams.length === 0 && <div className="adm-empty">{readOnly ? "소속된 팀이 없습니다." : "등록된 팀이 없습니다. 위에서 팀을 생성해 보세요."}</div>}
      </ul>
    </section>
  );
}

// ─── 메인 페이지 ──────────────────────────────
export default function AdminPage() {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const isAdmin = currentUser?.role === "admin";
  const isManager = currentUser?.role === "manager";

  const [active, setActive] = useState("dashboard");
  const [stats, setStats] = useState({ total_users: 0, active_users: 0, total_teams: 0, signups_last_7_days: 0 });
  const [users, setUsers] = useState([]);
  const [teams, setTeams] = useState([]);
  const [error, setError] = useState(null);

  // 분석 이력 (매니저 전용 탭)
  const [analyses, setAnalyses] = useState([]);
  const [analysesLoading, setAnalysesLoading] = useState(false);

  const sidebarItems = useMemo(() => {
    const base = [
      { key: "dashboard", label: "대시보드", icon: HomeIcon },
      { key: "users", label: "사용자 관리", icon: UsersIcon },
      { key: "teams", label: "팀 관리", icon: TeamIcon },
    ];
    if (isManager) {
      base.push({ key: "history", label: "분석 이력", icon: HistoryIcon });
    }
    return base;
  }, [isManager]);

  const refreshAll = useCallback(async () => {
    setError(null);
    try {
      const [s, u, t] = await Promise.all([fetchAdminStats(), listUsers(), listTeams()]);
      setStats(s);
      setUsers(u);
      setTeams(t);
    } catch (err) {
      setError(err.response?.data?.detail || "데이터를 불러오지 못했습니다.");
    }
  }, []);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  // 분석 이력 탭 진입 시 그때 한 번 로드 — 대시보드 첫 진입 비용 최소화
  useEffect(() => {
    if (active !== "history") return;
    setAnalysesLoading(true);
    listAnalyses()
      .then((data) => setAnalyses(Array.isArray(data) ? data : []))
      .catch(() => setAnalyses([]))
      .finally(() => setAnalysesLoading(false));
  }, [active]);

  const handleUserUpdate = async (id, changes) => {
    try {
      await updateUser(id, changes);
      await refreshAll();
    } catch (err) {
      window.alert(err.response?.data?.detail || "사용자 수정에 실패했습니다.");
    }
  };

  const handleTeamUpdate = async (id, changes) => {
    try {
      await updateTeam(id, changes);
      await refreshAll();
    } catch (err) {
      window.alert(err.response?.data?.detail || "팀 수정에 실패했습니다.");
    }
  };

  const handleTeamDelete = async (id) => {
    try {
      await deleteTeam(id);
      await refreshAll();
    } catch (err) {
      window.alert(err.response?.data?.detail || "팀 삭제에 실패했습니다.");
    }
  };

  return (
    <div className="adm-shell">
      <AdminHeader />
      <div className="adm-body">
        <AdminSidebar active={active} onSelect={setActive} items={sidebarItems} />
        <main className="adm-main">
          <h1 className="adm-page-title">
            {active === "users"
              ? (isAdmin ? "사용자 관리" : "팀원")
              : active === "teams"
              ? (isAdmin ? "팀 관리" : "팀 구성도")
              : active === "history"
              ? "분석 이력"
              : (isAdmin ? "시스템 관리자 대시보드" : "팀 구성도")}
          </h1>
          <p className="adm-page-sub">
            {active === "users"
              ? (isAdmin ? "전체 사용자 목록과 역할·소속을 관리합니다" : "내 팀 구성원을 확인합니다")
              : active === "teams"
              ? (isAdmin ? "팀 생성·구성·팀장 지정을 관리합니다" : "조직 전체의 팀 구성을 확인합니다")
              : active === "history"
              ? "팀원이 분석한 계약서 내역을 확인합니다"
              : (isAdmin ? "사용자 및 팀 운영 현황" : "내 팀과 조직 구성 현황을 확인합니다")}
          </p>

          {error && <div className="adm-error">{error}</div>}

          <div className="adm-stats-grid">
            <StatCard icon={UsersIcon} label={isAdmin ? "전체 사용자" : "팀원 수"} value={stats.total_users} />
            <StatCard icon={ShieldIcon} label={isAdmin ? "활성 사용자" : "활성 팀원"} value={stats.active_users} />
            <StatCard icon={TeamIcon} label="전체 팀" value={stats.total_teams} />
            <StatCard icon={ClockIcon} label={isAdmin ? "최근 7일 신규 가입" : "최근 7일 신규 팀원"} value={stats.signups_last_7_days} />
          </div>

          {active === "dashboard" && (
            <>
              <PerformancePanel />
              {isAdmin && <CreateTeamPanel onCreated={refreshAll} />}
              <div className="adm-grid-2">
                <UsersTable users={users} teams={teams} onUpdate={handleUserUpdate} readOnly={!isAdmin} />
                <TeamsPanel
                  teams={teams}
                  users={users}
                  onUpdate={handleTeamUpdate}
                  onDelete={handleTeamDelete}
                  readOnly={!isAdmin}
                />
              </div>
            </>
          )}

          {active === "users" && (
            <UsersTable users={users} teams={teams} onUpdate={handleUserUpdate} readOnly={!isAdmin} />
          )}

          {active === "teams" && (
            <>
              {isAdmin && <CreateTeamPanel onCreated={refreshAll} />}
              <TeamsPanel
                teams={teams}
                users={users}
                onUpdate={handleTeamUpdate}
                onDelete={handleTeamDelete}
                readOnly={!isAdmin}
              />
            </>
          )}

          {active === "history" && (
            <AnalysisHistoryPanel
              analyses={analyses}
              loading={analysesLoading}
              currentUser={currentUser}
              onOpen={(id) => navigate(`/result/${encodeURIComponent(id)}`)}
            />
          )}
        </main>
      </div>
    </div>
  );
}

// ─── 인라인 SVG 아이콘 (외부 의존성 회피) ─────
function HomeIcon() { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>; }
function UsersIcon() { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>; }
function TeamIcon() { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>; }
function ShieldIcon() { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>; }
function ClockIcon() { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>; }
function HistoryIcon() { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 12a9 9 0 1 0 3-6.7"/><polyline points="3 4 3 10 9 10"/><polyline points="12 7 12 12 15 14"/></svg>; }
