import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// 인증/권한 가드. PR4에서 라우트에 적용 예정.
// roles를 주면 해당 role만 통과. 미충족 시 로그인 화면("/")으로 보낸다.
export default function ProtectedRoute({ children, roles }) {
  const { currentUser, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="auth-loading">불러오는 중...</div>;
  }
  if (!currentUser) {
    return <Navigate to="/" replace state={{ from: location }} />;
  }
  if (roles && roles.length > 0 && !roles.includes(currentUser.role)) {
    return <Navigate to="/home" replace />;
  }
  return children;
}
