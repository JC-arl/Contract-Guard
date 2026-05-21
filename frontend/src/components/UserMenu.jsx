import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ROLE_LABELS = {
  admin: "관리자",
  manager: "팀장",
  lawyer: "변호사",
};

export default function UserMenu() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  if (!currentUser) {
    return (
      <button type="button" className="user-menu-login" onClick={() => navigate("/")}>
        로그인
      </button>
    );
  }

  const handleLogout = async (e) => {
    e.stopPropagation();
    await logout();
    navigate("/");
  };

  return (
    <div className="user-menu" onClick={(e) => e.stopPropagation()}>
      <div className="user-menu-info">
        <span className="user-menu-name">{currentUser.display_name || currentUser.email}</span>
        <span className="user-menu-role">{ROLE_LABELS[currentUser.role] || currentUser.role}</span>
      </div>
      {currentUser.role === "admin" && (
        <button type="button" className="user-menu-admin" onClick={() => navigate("/admin")}>
          관리자
        </button>
      )}
      <button type="button" className="user-menu-logout" onClick={handleLogout}>
        로그아웃
      </button>
    </div>
  );
}
