import { useState } from "react";

// 라벨 소스 — SVG 텍스트로 표시할 값을 결정.
//   text:      원본 OCR
//   corrected: LLM 보정 결과 (없으면 원본 폴백)
//   diff:      LLM 이 바꾼 박스만 보정된 텍스트로, 나머지는 원본
const LABEL_SOURCES = [
  { id: "text", label: "원본" },
  { id: "corrected", label: "LLM 보정" },
  { id: "diff", label: "변경분만" },
];

function pickLabel(box, source) {
  const corrected = box.corrected_text ?? box.text;
  if (source === "corrected") return corrected;
  if (source === "diff") return corrected !== box.text ? corrected : box.text;
  return box.text;
}

function isChanged(box) {
  return box.corrected_text != null && box.corrected_text !== box.text;
}

// SVG 오버레이는 원본 좌표계(viewBox)를 유지해서 이미지 크기와 박스 좌표가 정합되도록 한다.
function SvgOverlay({ result, imageUrl, labelSource, hasCorrection }) {
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
          const boxH = Math.max(...ys) - minY;
          const fontSize = Math.max(12, Math.min(28, Math.round(boxH * 0.6)));
          const labelY = minY - 4 < fontSize ? minY + fontSize : minY - 4;

          const points = box.poly.map((p) => p.join(",")).join(" ");
          const changed = hasCorrection && isChanged(box);
          // LLM 이 바꾼 박스는 파란 톤으로 강조, 그대로면 빨간 톤(기존 OCR 박스 톤 유지)
          const stroke = changed ? "#2563eb" : "#e74c3c";
          const fill = changed ? "rgba(37, 99, 235, 0.12)" : "rgba(231, 76, 60, 0.08)";
          const label = pickLabel(box, labelSource);
          // 호버 시 원본/보정 둘 다 보이도록 title 구성
          const title = changed
            ? `원본: ${box.text}\n보정: ${box.corrected_text}\nscore: ${box.score.toFixed(3)}`
            : `${box.text}\nscore: ${box.score.toFixed(3)}`;
          return (
            <g key={i}>
              <polygon
                points={points}
                fill={fill}
                stroke={stroke}
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
                {label}
                <title>{title}</title>
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

// LLM 변경 내역만 표 형태로 — 정성 검증에 가장 빠른 형태
function DiffTable({ boxes }) {
  const changed = boxes.filter(isChanged);
  if (changed.length === 0) {
    return <div className="ocr-status">LLM 보정 결과: 변경된 박스가 없습니다.</div>;
  }
  return (
    <table className="ocr-diff-table">
      <thead>
        <tr>
          <th style={{ width: 36 }}>#</th>
          <th>원본 OCR</th>
          <th>LLM 보정</th>
          <th style={{ width: 64 }}>score</th>
        </tr>
      </thead>
      <tbody>
        {changed.map((b, i) => (
          <tr key={i}>
            <td>{i + 1}</td>
            <td className="diff-orig">{b.text}</td>
            <td className="diff-fixed">{b.corrected_text}</td>
            <td>{b.score.toFixed(3)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

const BASE_TABS = [
  { id: "svg", label: "SVG 오버레이" },
  { id: "overlay", label: "백엔드 PNG" },
  { id: "json", label: "Raw JSON" },
];

export default function OcrViewer({ response }) {
  const [tab, setTab] = useState("svg");
  const [labelSource, setLabelSource] = useState("text");
  if (!response) return null;
  const { image_url, overlay_url, result } = response;
  const hasCorrection = result.boxes.some((b) => b.corrected_text != null);
  const changedCount = result.boxes.filter(isChanged).length;

  // LLM 보정 결과가 있을 때만 diff 탭 활성화
  const tabs = hasCorrection
    ? [...BASE_TABS, { id: "diff", label: `변경 표 (${changedCount})` }]
    : BASE_TABS;

  return (
    <div className="ocr-viewer">
      <div className="ocr-meta">
        <span>{result.boxes.length} 박스</span>
        <span className="ocr-meta-dot">·</span>
        <span>{result.width}×{result.height}</span>
        <span className="ocr-meta-dot">·</span>
        <span>{result.elapsed_ms} ms</span>
        {hasCorrection && (
          <>
            <span className="ocr-meta-dot">·</span>
            <span style={{ color: "#2563eb" }}>LLM 보정 {changedCount}건</span>
          </>
        )}
      </div>

      <div className="ocr-tabs">
        {tabs.map((t) => (
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

      {/* SVG 탭에서만 라벨 소스 토글 노출 */}
      {tab === "svg" && hasCorrection && (
        <div className="ocr-label-toggle">
          <span style={{ color: "#666", fontSize: 12 }}>라벨:</span>
          {LABEL_SOURCES.map((s) => (
            <button
              key={s.id}
              type="button"
              className={`ocr-label-btn${labelSource === s.id ? " active" : ""}`}
              onClick={() => setLabelSource(s.id)}
            >
              {s.label}
            </button>
          ))}
        </div>
      )}

      <div className="ocr-tab-content">
        {tab === "svg" && (
          <SvgOverlay
            result={result}
            imageUrl={image_url}
            labelSource={labelSource}
            hasCorrection={hasCorrection}
          />
        )}
        {tab === "overlay" && (
          <img src={overlay_url} alt="overlay" style={{ width: "100%", display: "block" }} />
        )}
        {tab === "json" && <JsonView data={response} />}
        {tab === "diff" && <DiffTable boxes={result.boxes} />}
      </div>
    </div>
  );
}
