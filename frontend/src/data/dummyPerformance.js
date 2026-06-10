// ⚠️ 데모용 더미 데이터 — 실데이터/API 연동 시 이 파일과 PerformancePanel.jsx를 통째로 삭제하면 됩니다.
//
// 시간축 없이 "현재 성능 스냅샷"을 막대그래프로 보여줍니다. 값은 자유롭게 조정 가능합니다.

// ① 위험 등급별 판정 분포 (건) — 라벨/색상은 앱 위험도 분류(RiskBadge)와 동일
export const RISK_DISTRIBUTION = [
  { label: "법률 위반", value: 38, color: "var(--risk-high, #e74c3c)" },
  { label: "계약자 불리", value: 52, color: "var(--risk-medium, #e67e22)" },
  { label: "검토 권장", value: 31, color: "var(--risk-low, #b8a024)" },
  { label: "안전", value: 124, color: "var(--risk-safe, #27ae60)" },
];

// ② 성능 지표 (%)
export const METRICS = [
  { label: "정답률", value: 86 },
  { label: "정밀도", value: 84 },
  { label: "재현율", value: 89 },
  { label: "F1", value: 86 },
];
