import { createContext, useCallback, useContext, useEffect, useState } from "react";
import * as authApi from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true); // 부팅 시 세션 복구 진행 중

  // 마운트 시 1회: /auth/me로 세션 복구. 미로그인이면 조용히 null.
  const refresh = useCallback(async () => {
    try {
      const user = await authApi.fetchMe();
      setCurrentUser(user);
      return user;
    } catch {
      setCurrentUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = useCallback(async (email, password) => {
    const data = await authApi.login(email, password);
    setCurrentUser(data.user);
    return data.user;
  }, []);

  const signup = useCallback(async (email, password, displayName) => {
    return authApi.signup(email, password, displayName);
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setCurrentUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ currentUser, loading, refresh, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth는 AuthProvider 하위에서만 사용 가능합니다.");
  }
  return ctx;
}
