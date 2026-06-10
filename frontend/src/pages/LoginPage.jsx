import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Shield3D() {
  return (
    <div className="shield-3d-scene">
      <div className="shield-3d">
        <div className="shield-face shield-front">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <polyline points="9 12 11 14 15 10" strokeWidth="2" />
          </svg>
        </div>
        <div className="shield-orbit shield-orbit-1">
          <div className="orbit-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </div>
        </div>
        <div className="shield-orbit shield-orbit-2">
          <div className="orbit-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </div>
        </div>
        <div className="shield-orbit shield-orbit-3">
          <div className="orbit-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
          </div>
        </div>
        <div className="shield-ring" />
      </div>
    </div>
  );
}

export default function LoginPage() {
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState(null);
  const [info, setInfo] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const { login, signup } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from?.pathname || "/home";

  const switchMode = (next) => {
    setMode(next);
    setError(null);
    setInfo(null);
    setPassword("");
  };

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setInfo(null);
    setSubmitting(true);
    try {
      if (mode === "login") {
        const user = await login(email.trim(), password);
        navigate(user.role === "admin" ? "/admin" : redirectTo, { replace: true });
      } else {
        await signup(email.trim(), password, displayName.trim());
        setInfo("가입이 완료되었습니다. 로그인해 주세요.");
        switchMode("login");
        setEmail(email.trim());
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "요청을 처리하지 못했습니다.";
      // pydantic 검증 오류는 배열로 올 수 있음
      setError(Array.isArray(msg) ? msg.map((m) => m.msg).join(", ") : msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-page">
      <section className="hero-section">
        <div className="hero-grid">
          <div className="hero-content">
            <span className="hero-badge fade-up" style={{ animationDelay: "0.1s" }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              AI 기반 계약서 분석
            </span>
            <h1 className="hero-title fade-up" style={{ animationDelay: "0.25s" }}>
              계약서 속 <span className="hero-highlight">독소조항</span>을<br />
              찾아드립니다
            </h1>
            <p className="hero-desc fade-up" style={{ animationDelay: "0.4s" }}>
              로그인하고 관련 법률·판례 데이터 기반의 계약서 위험 분석을 시작하세요.
            </p>
          </div>
          <div className="hero-3d fade-up" style={{ animationDelay: "0.3s" }}>
            <Shield3D />
          </div>
        </div>

        <div className="hero-upload fade-up" style={{ animationDelay: "0.5s" }}>
          <div className="upload-card auth-card">
            <div className="auth-tabs" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={mode === "login"}
                className={`auth-tab${mode === "login" ? " active" : ""}`}
                onClick={() => switchMode("login")}
              >
                로그인
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={mode === "signup"}
                className={`auth-tab${mode === "signup" ? " active" : ""}`}
                onClick={() => switchMode("signup")}
              >
                회원가입
              </button>
            </div>

            <form className="auth-form" onSubmit={handleSubmit}>
              {mode === "signup" && (
                <label className="auth-field">
                  <span className="auth-label">이름</span>
                  <input
                    type="text"
                    className="auth-input"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="표시 이름 (선택)"
                    autoComplete="name"
                  />
                </label>
              )}
              <label className="auth-field">
                <span className="auth-label">이메일</span>
                <input
                  type="email"
                  className="auth-input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  autoComplete="username"
                  required
                />
              </label>
              <label className="auth-field">
                <span className="auth-label">비밀번호</span>
                <input
                  type="password"
                  className="auth-input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={mode === "signup" ? "최소 8자" : "비밀번호"}
                  autoComplete={mode === "signup" ? "new-password" : "current-password"}
                  required
                />
              </label>

              {error && (
                <div className="error-message">
                  <span className="error-icon">!</span>
                  <span>{error}</span>
                </div>
              )}
              {info && <div className="auth-info">{info}</div>}

              <button type="submit" className="auth-submit" disabled={submitting}>
                {submitting ? "처리 중..." : mode === "login" ? "로그인" : "회원가입"}
              </button>
            </form>

            <p className="auth-switch">
              {mode === "login" ? (
                <>
                  계정이 없으신가요?{" "}
                  <button type="button" className="auth-link" onClick={() => switchMode("signup")}>
                    회원가입
                  </button>
                </>
              ) : (
                <>
                  이미 계정이 있으신가요?{" "}
                  <button type="button" className="auth-link" onClick={() => switchMode("login")}>
                    로그인
                  </button>
                </>
              )}
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
