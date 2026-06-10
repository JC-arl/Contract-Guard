// 세로 막대 차트 — 외부 차트 라이브러리 없이 SVG로 직접 그린다 (폐쇄망 대응, RiskPieChart와 동일 방침).
// 카테고리별(가로축) 값을 막대로 표시한다. 막대는 아래→위로 자라나는 애니메이션.

const VB_W = 360;
const VB_H = 200;
const PAD = { l: 36, r: 14, t: 22, b: 30 };
const PLOT_W = VB_W - PAD.l - PAD.r;
const PLOT_H = VB_H - PAD.t - PAD.b;
const Y_BOTTOM = VB_H - PAD.b;

// 데이터 최댓값을 보기 좋은 눈금 상한으로 올림 (예: 12 → 15, 161 → 180)
function niceCeil(max) {
  if (max <= 0) return 1;
  const pow = Math.pow(10, Math.floor(Math.log10(max)));
  const norm = max / pow;
  const step = norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 5 ? 5 : 10;
  return step * pow * (max / (step * pow) > 0.9 ? 1.2 : 1);
}

export default function BarChart({
  data = [],
  yMax: yMaxProp = null,
  unit = "",
  barColor = "var(--primary, #1a1a1a)",
  caption = "",
}) {
  const n = data.length;
  const dataMax = Math.max(1, ...data.map((d) => d.value));
  const yMax = yMaxProp ?? niceCeil(dataMax);

  const slot = n > 0 ? PLOT_W / n : PLOT_W;
  const barW = slot * 0.5;

  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => ({
    v: Math.round(yMax * f),
    y: Y_BOTTOM - f * PLOT_H,
  }));

  return (
    <div className="bar-chart">
      <svg viewBox={`0 0 ${VB_W} ${VB_H}`} className="bar-svg" role="img">
        {/* Y축 눈금선 + 라벨 */}
        {ticks.map((t) => (
          <g key={`tick-${t.v}`}>
            <line x1={PAD.l} y1={t.y} x2={VB_W - PAD.r} y2={t.y} className="bar-grid" />
            <text x={PAD.l - 6} y={t.y} className="bar-axis-label" textAnchor="end" dominantBaseline="central">
              {t.v}
            </text>
          </g>
        ))}

        {/* 막대 + 값/카테고리 라벨 */}
        {data.map((d, i) => {
          const cx = PAD.l + slot * (i + 0.5);
          const h = (d.value / yMax) * PLOT_H;
          return (
            <g key={`bar-${d.label}`}>
              <rect
                x={cx - barW / 2}
                y={Y_BOTTOM - h}
                width={barW}
                height={h}
                rx="3"
                className="bar-rect"
                style={{ fill: d.color || barColor, "--bar-delay": `${i * 0.08}s` }}
              />
              <text x={cx} y={Y_BOTTOM - h - 6} className="bar-value" textAnchor="middle">
                {d.value}
                {unit}
              </text>
              <text x={cx} y={VB_H - 10} className="bar-axis-label" textAnchor="middle">
                {d.label}
              </text>
            </g>
          );
        })}
      </svg>

      {caption && <p className="bar-caption">{caption}</p>}
    </div>
  );
}
