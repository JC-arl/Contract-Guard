import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import ResultPage from "./pages/ResultPage";

function Header() {
  const navigate = useNavigate();

  return (
    <header className="app-header" onClick={() => navigate("/")} style={{ cursor: "pointer" }}>
      <div className="header-inner">
        <img src="/logo.png" alt="K&H2" className="header-logo" />
      </div>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Header />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/result" element={<ResultPage />} />
          </Routes>
        </main>
        <footer className="app-footer">
          <div className="footer-inner">
            <span>K&H<sup>2</sup> Legal Contract Review Project</span>
            <span className="footer-dot">&middot;</span>
            <span>AI Hub 데이터 기반 분석</span>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}
