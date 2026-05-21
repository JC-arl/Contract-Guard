import api from "./client";

// 회원가입 — 기본 role=lawyer. 자동 로그인은 하지 않는다.
export async function signup(email, password, displayName) {
  const res = await api.post("/api/auth/signup", {
    email,
    password,
    display_name: displayName || "",
  });
  return res.data;
}

// 로그인 — 성공 시 세션/CSRF 쿠키가 설정되고 { user, csrf_token } 반환.
export async function login(email, password) {
  const res = await api.post("/api/auth/login", { email, password });
  return res.data;
}

export async function logout() {
  await api.post("/api/auth/logout");
}

// 현재 세션의 사용자. 미로그인(401)이면 예외를 던진다.
export async function fetchMe() {
  const res = await api.get("/api/auth/me");
  return res.data;
}
