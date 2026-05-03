import { useState } from "react";

// 3-tab: SVG 오버레이 / 백엔드가 합성한 PNG / raw JSON
// SVG 오버레이는 원본 좌표계(viewBox)를 유지해서 이미지 크기와 박스 좌표가 정합되도록 한다.
function SvgOverlay({ result, imageUrl }) {
  const { width, height, boxes } = result;
  return (
    <div className="ocr-svg-wrap">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
        style={{ width: "100%", height: "auto", display: "block" }}
      >
        <image href={imageUrl} x="0" y="0" width={width} height={height} />
        {boxes.map((box, i) => {
          const xs = box.poly.map((p) => p[0]);
          const ys = box.poly.map((p) => p[1]);
          const minX = Math.min(...xs);
          const minY = Math.min(...ys);
          // 텍스트 라벨은 박스 위쪽에 — 화면 위 잘리면 박스 안쪽으로 폴백.
          // 폰트 크기는 box 높이에 비례 (최소 12 / 최대 28). overlay PNG와 톤 맞춤.
          const boxH = Math.max(...ys) - minY;
          const fontSize = Math.max(12, Math.min(28, Math.round(boxH * 0.6)));
          const labelY = minY - 4 < fontSize ? minY + fontSize : minY - 4;

          const points = box.poly.map((p) => p.join(",")).join(" ");
          return (
            <g key={i}>
              <polygon
                points={points}
                fill="rgba(231, 76, 60, 0.08)"
                stroke="#e74c3c"
                strokeWidth={Math.max(1, width / 800)}
              />
              <text
                x={minX}
                y={labelY}
                fontSize={fontSize}
                fill="#fff"
                stroke="rgba(0,0,0,0.6)"
                strokeWidth={Math.max(1, fontSize / 12)}
                paintOrder="stroke"
                style={{ fontFamily: "sans-serif" }}
              >
                {box.text}
                <title>{`score: ${box.score.toFixed(3)}`}</title>
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function JsonView({ data }) {
  return (
    <pre className="ocr-json">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

const TABS = [
  { id: "svg", label: "SVG 오버레이" },
  { id: "overlay", label: "백엔드 PNG" },
  { id: "json", label: "Raw JSON" },
];

export default function OcrViewer({ response }) {
  const [tab, setTab] = useState("svg");
  if (!response) return null;
  const { image_url, overlay_url, result } = response;

  return (
    <div className="ocr-viewer">
      <div className="ocr-meta">
        <span>{result.boxes.length} 박스</span>
        <span className="ocr-meta-dot">·</span>
        <span>{result.width}×{result.height}</span>
        <span className="ocr-meta-dot">·</span>
        <span>{result.elapsed_ms} ms</span>
      </div>

      <div className="ocr-tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`ocr-tab${tab === t.id ? " active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="ocr-tab-content">
        {tab === "svg" && <SvgOverlay result={result} imageUrl={image_url} />}
        {tab === "overlay" && (
          <img src={overlay_url} alt="overlay" style={{ width: "100%", display: "block" }} />
        )}
        {tab === "json" && <JsonView data={response} />}
      </div>
    </div>
  );
}
