// ⚠️ 데모용 성능 지표 패널 — 전부 더미 데이터(dummyPerformance.js).
// 실데이터 연동/제거 시: 이 파일 + dummyPerformance.js 삭제, AdminPage에서 <PerformancePanel /> 1줄 제거.

import BarChart from "./BarChart";
import { RISK_DISTRIBUTION, METRICS } from "../data/dummyPerformance";

// 성능 지표 하단 설명
const METRIC_DEFS = [
  [
    "정답률",
    "전체 판정 중 올바르게 맞춘 비율입니다. 위험한 조항을 위험으로, 안전한 조항을 안전으로 맞춘 건수를 모두 더해 전체 건수로 나눈 값입니다.",
  ],
  [
    "정밀도",
    "AI가 ‘위험’이라고 판정한 조항 중 실제로 위험이었던 비율입니다. 높을수록 거짓 경보(안전한 조항을 위험이라 한 경우)가 적습니다.",
  ],
  [
    "재현율",
    "실제로 위험한 조항 중 AI가 위험으로 잡아낸 비율입니다. 높을수록 놓친 위험(위험한 조항을 안전이라 한 경우)이 적습니다.",
  ],
  [
    "F1",
    "정밀도와 재현율을 함께 반영한 종합 점수(조화평균)입니다. 둘 중 하나라도 낮으면 점수가 떨어져, 정밀도와 재현율의 균형을 평가합니다.",
  ],
];

function ChartCard({ title, help, footer, children }) {
  return (
    <div className="perf-chart-card">
      <div className="perf-chart-head">
        <h3 className="perf-chart-title">{title}</h3>
        {help && (
          <span className="perf-help" tabIndex={0} role="button" aria-label={`${title} 설명`}>
            ?
            <span className="perf-help-tip" role="tooltip">{help}</span>
          </span>
        )}
      </div>
      {children}
      {footer && <div className="perf-chart-desc">{footer}</div>}
    </div>
  );
}

export default function PerformancePanel() {
  const totalJudged = RISK_DISTRIBUTION.reduce((s, d) => s + d.value, 0);
  const riskyJudged = RISK_DISTRIBUTION.filter((d) => d.label !== "안전").reduce((s, d) => s + d.value, 0);

  return (
    <section className="adm-panel perf-panel">
      <div className="adm-panel-head">
        <h2 className="adm-panel-title">AI 분석 성능 지표</h2>
      </div>
      <p className="perf-panel-sub">검증 데이터 기준 현재 분석 성능 스냅샷입니다.</p>

      <div className="perf-grid">
        <ChartCard
          title="위험 등급별 분포"
        >
          <BarChart
            data={RISK_DISTRIBUTION}
            unit="건"
            caption={`전체 ${totalJudged}건 · 위험 ${riskyJudged}건 / 안전 ${totalJudged - riskyJudged}건`}
          />
        </ChartCard>

        <ChartCard
          title="성능 지표"
          footer={
            <dl className="perf-metric-defs">
              {METRIC_DEFS.map(([term, desc]) => (
                <div key={term}>
                  <dt>{term}</dt>
                  <dd>{desc}</dd>
                </div>
              ))}
            </dl>
          }
        >
          <BarChart data={METRICS} yMax={100} unit="%" barColor="#2563eb" />
        </ChartCard>
      </div>
    </section>
  );
}
