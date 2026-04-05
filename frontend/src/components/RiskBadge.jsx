const RISK_CONFIG = {
  high: { label: "고위험", className: "risk-high" },
  medium: { label: "중위험", className: "risk-medium" },
  low: { label: "저위험", className: "risk-low" },
  safe: { label: "안전", className: "risk-safe" },
};

export default function RiskBadge({ level }) {
  const config = RISK_CONFIG[level] || RISK_CONFIG.safe;
  return <span className={`risk-badge ${config.className}`}>{config.label}</span>;
}
