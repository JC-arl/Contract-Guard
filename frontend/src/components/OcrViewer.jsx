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

// 레이아웃 영역 색 — backend 와 의미 일치.
// PubLayNet 라벨(title/text/list/table/figure) + CDLA 추가 라벨(figure_caption/
// table_caption/header/footer/reference/equation) 양쪽 커버.
// LLM 보정 강조용 파랑(#2563eb) 과의 충돌을 피하려고 title 은 backend 의 파랑 대신 주황 사용.
// 미부여(레이아웃 off · unclassified) 박스는 stroke 기본값(빨강) 유지 → 기존 시각화 호환.
const REGION_COLORS = {
  title: { stroke: "#f59e0b", fill: "rgba(245, 158, 11, 0.10)" },
  text: { stroke: "#e74c3c", fill: "rgba(231, 76, 60, 0.08)" },
  list: { stroke: "#a855f7", fill: "rgba(168, 85, 247, 0.10)" },
  table: { stroke: "#10b981", fill: "rgba(16, 185, 129, 0.10)" },
  table_caption: { stroke: "#34d399", fill: "rgba(52, 211, 153, 0.10)" },
  figure: { stroke: "#9ca3af", fill: "rgba(156, 163, 175, 0.10)" },
  figure_caption: { stroke: "#cbd5e1", fill: "rgba(203, 213, 225, 0.10)" },
  header: { stroke: "#0ea5e9", fill: "rgba(14, 165, 233, 0.10)" },
  footer: { stroke: "#0ea5e9", fill: "rgba(14, 165, 233, 0.10)" },
  reference: { stroke: "#c084fc", fill: "rgba(192, 132, 252, 0.10)" },
  equation: { stroke: "#dc2626", fill: "rgba(220, 38, 38, 0.10)" },
};
const DEFAULT_REGION_COLOR = { stroke: "#e74c3c", fill: "rgba(231, 76, 60, 0.08)" };

function colorForRegion(regionType) {
  if (!regionType) return DEFAULT_REGION_COLOR;
  return REGION_COLORS[regionType] || DEFAULT_REGION_COLOR;
}

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
// showRegions 가 켜져 있으면 PP-Structure 가 검출한 레이아웃 영역도 박스 뒤에 점선으로 그린다.
function SvgOverlay({ result, imageUrl, labelSource, hasCorrection, showRegions }) {
  const { width, height, boxes, regions = [] } = result;
  return (
    <div className="ocr-svg-wrap">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
        style={{ width: "100%", height: "auto", display: "block" }}
      >
        <image href={imageUrl} x="0" y="0" width={width} height={height} />
        {/* 레이아웃 영역 — 박스 뒤에 점선 사각형 + 좌상단 라벨 */}
        {showRegions && regions.map((region, i) => {
          const [x1, y1, x2, y2] = region.bbox;
          const { stroke, fill } = colorForRegion(region.region_type);
          const labelSize = Math.max(14, Math.min(32, Math.round((y2 - y1) * 0.04)));
          return (
            <g key={`r${i}`}>
              <rect
                x={x1}
                y={y1}
                width={x2 - x1}
                height={y2 - y1}
                fill={fill}
                stroke={stroke}
                strokeWidth={Math.max(2, width / 600)}
                strokeDasharray={`${width / 120},${width / 240}`}
              />
              <text
                x={x1 + 4}
                y={y1 + labelSize + 2}
                fontSize={labelSize}
                fill={stroke}
                stroke="rgba(255,255,255,0.7)"
                strokeWidth={Math.max(1, labelSize / 8)}
                paintOrder="stroke"
                style={{ fontFamily: "sans-serif", fontWeight: 700 }}
              >
                {region.region_type}
              </text>
            </g>
          );
        })}
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
          // 우선순위: LLM 변경(파랑) > region_type 색 > 기본(빨강).
          // region 색은 backend render_overlay 와 의미 일치(title/text/list/table/figure).
          const regionColor = colorForRegion(box.region_type);
          const stroke = changed ? "#2563eb" : regionColor.stroke;
          const fill = changed ? "rgba(37, 99, 235, 0.12)" : regionColor.fill;
          const label = pickLabel(box, labelSource);
          // 호버 시 원본/보정/region_type 모두 보이도록 title 구성
          const regionLine = box.region_type ? `\nregion: ${box.region_type}` : "";
          const title = changed
            ? `원본: ${box.text}\n보정: ${box.corrected_text}\nscore: ${box.score.toFixed(3)}${regionLine}`
            : `${box.text}\nscore: ${box.score.toFixed(3)}${regionLine}`;
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

// region_type → 한국어 라벨. CDLA + PubLayNet 양쪽 라벨을 모두 커버.
const REGION_LABELS_KO = {
  title: "제목",
  text: "본문",
  list: "리스트",
  table: "표",
  table_caption: "표 캡션",
  figure: "그림/서명",
  figure_caption: "그림 캡션",
  header: "머리말",
  footer: "꼬리말",
  reference: "참고",
  equation: "수식",
};

// 레이아웃 영역 색 범례 — 실제 검출된 region_type 만 동적으로 표시.
// PubLayNet / CDLA / 기타 모델이 무엇을 뱉었는지 한눈에 보이게 함.
function RegionLegend({ regions }) {
  const presentTypes = Array.from(new Set(regions.map((r) => r.region_type))).sort();
  if (presentTypes.length === 0) return null;
  return (
    <div style={{ display: "flex", gap: 12, fontSize: 12, color: "#555", flexWrap: "wrap" }}>
      {presentTypes.map((type) => {
        const c = REGION_COLORS[type] || DEFAULT_REGION_COLOR;
        const label = REGION_LABELS_KO[type] || type;
        return (
          <span key={type} style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
            <span
              style={{
                display: "inline-block",
                width: 12,
                height: 12,
                background: c.fill,
                border: `2px solid ${c.stroke}`,
              }}
            />
            {label}
          </span>
        );
      })}
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
  const [showRegions, setShowRegions] = useState(true);
  if (!response) return null;
  const { image_url, overlay_url, result } = response;
  const hasCorrection = result.boxes.some((b) => b.corrected_text != null);
  const changedCount = result.boxes.filter(isChanged).length;
  const regionCount = (result.regions || []).length;

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
        {regionCount > 0 && (
          <>
            <span className="ocr-meta-dot">·</span>
            <span>레이아웃 {regionCount} 영역</span>
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

      {/* 레이아웃 영역이 검출된 경우만 영역 표시 토글 + 범례 노출 */}
      {tab === "svg" && regionCount > 0 && (
        <div className="ocr-label-toggle" style={{ alignItems: "center" }}>
          <label style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 12, color: "#666" }}>
            <input
              type="checkbox"
              checked={showRegions}
              onChange={(e) => setShowRegions(e.target.checked)}
            />
            레이아웃 영역 표시
          </label>
          <RegionLegend regions={result.regions || []} />
        </div>
      )}

      <div className="ocr-tab-content">
        {tab === "svg" && (
          <SvgOverlay
            result={result}
            imageUrl={image_url}
            labelSource={labelSource}
            hasCorrection={hasCorrection}
            showRegions={showRegions}
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
