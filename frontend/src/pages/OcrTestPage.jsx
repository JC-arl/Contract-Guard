import { useEffect, useRef, useState } from "react";
import { uploadOcrImage } from "../api/client";
import OcrViewer from "../components/OcrViewer";

const ACCEPTED_EXT = [".png", ".jpg", ".jpeg", ".webp"];
const ACCEPTED_MIME = ["image/png", "image/jpeg", "image/webp"];

function isImage(file) {
  if (!file) return false;
  if (ACCEPTED_MIME.includes(file.type)) return true;
  const name = file.name?.toLowerCase() || "";
  return ACCEPTED_EXT.some((ext) => name.endsWith(ext));
}

// 분석 파이프라인과 분리된 OCR 정확도 검증 페이지.
// URL `/ocr-test` 직접 접근 전용 (Sidebar/Header 진입점 없음).
export default function OcrTestPage() {
  const [file, setFile] = useState(null);
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [elapsedMs, setElapsedMs] = useState(0);
  const startedAtRef = useRef(0);
  const inputRef = useRef(null);

  useEffect(() => {
    if (!loading) return;
    startedAtRef.current = performance.now();
    setElapsedMs(0);
    const id = setInterval(() => {
      setElapsedMs(performance.now() - startedAtRef.current);
    }, 100);
    return () => clearInterval(id);
  }, [loading]);

  const pick = () => inputRef.current?.click();

  async function handleFile(f) {
    if (!isImage(f)) {
      setError(`이미지 형식만 지원합니다 (${ACCEPTED_EXT.join(", ")})`);
      return;
    }
    setFile(f);
    setError("");
    setResponse(null);
    setLoading(true);
    try {
      const data = await uploadOcrImage(f);
      setResponse(data);
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "OCR 실패";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="ocr-page">
      <header className="ocr-page-header">
        <h1>OCR 정확도 검증</h1>
        <p className="ocr-page-sub">
          이미지 계약서를 업로드하면 PaddleOCR이 추출한 텍스트와 박스를 시각화합니다.
          이 페이지는 분석 파이프라인과 연결되어 있지 않습니다.
        </p>
      </header>

      <section className="ocr-uploader" onClick={pick} role="button" tabIndex={0}>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXT.join(",")}
          style={{ display: "none" }}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />
        {file ? (
          <div>
            <strong>{file.name}</strong>
            <span style={{ marginLeft: 8, color: "#888" }}>
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </span>
          </div>
        ) : (
          <div>이미지(PNG / JPG / JPEG / WEBP)를 클릭해 선택</div>
        )}
      </section>

      {loading && (
        <div className="ocr-status">
          <span>OCR 실행 중... (첫 호출은 모델 로딩으로 수십 초 걸릴 수 있습니다)</span>
          <span className="ocr-timer">{(elapsedMs / 1000).toFixed(1)}s</span>
        </div>
      )}
      {!loading && !error && response && elapsedMs > 0 && (
        <div className="ocr-status ocr-done">
          완료 — 소요 시간 {(elapsedMs / 1000).toFixed(2)}s
        </div>
      )}
      {error && <div className="ocr-status ocr-error">{error}</div>}

      {response && <OcrViewer response={response} />}

      <style>{`
        .ocr-page { max-width: 1100px; margin: 0 auto; padding: 24px; }
        .ocr-page-header h1 { margin: 0 0 6px; font-size: 22px; }
        .ocr-page-sub { color: #666; font-size: 13px; margin: 0 0 20px; }
        .ocr-uploader {
          border: 2px dashed #cfd6e0; border-radius: 8px; padding: 28px;
          text-align: center; cursor: pointer; background: #fafbfc;
          transition: background .15s;
        }
        .ocr-uploader:hover { background: #f1f4f8; }
        .ocr-status {
          margin-top: 16px; padding: 10px 14px; border-radius: 6px;
          background: #eef3fb; color: #36506e; font-size: 13px;
          display: flex; justify-content: space-between; align-items: center; gap: 12px;
        }
        .ocr-timer {
          font-variant-numeric: tabular-nums; font-weight: 600;
          background: #dbe6f6; color: #1f3a5f; padding: 2px 10px; border-radius: 999px;
        }
        .ocr-done { background: #e6f5ec; color: #1f5d3a; }
        .ocr-error { background: #fde8e8; color: #9b1c1c; }
        .ocr-viewer { margin-top: 20px; }
        .ocr-meta { display: flex; gap: 8px; align-items: center; color: #666; font-size: 12px; margin-bottom: 8px; }
        .ocr-meta-dot { color: #ccc; }
        .ocr-tabs { display: flex; gap: 4px; border-bottom: 1px solid #e3e7ec; }
        .ocr-tab {
          background: transparent; border: none; padding: 8px 14px; cursor: pointer;
          color: #666; font-size: 13px; border-bottom: 2px solid transparent;
        }
        .ocr-tab.active { color: #1f2937; border-bottom-color: #2563eb; font-weight: 600; }
        .ocr-tab-content { margin-top: 12px; border: 1px solid #eef0f3; border-radius: 6px; overflow: hidden; }
        .ocr-svg-wrap { background: #f7f8fa; }
        .ocr-json {
          margin: 0; padding: 12px; background: #0f172a; color: #e2e8f0;
          font-size: 12px; line-height: 1.5; max-height: 600px; overflow: auto;
        }
      `}</style>
    </div>
  );
}
