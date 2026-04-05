export default function ConfidenceBar({ value, label }) {
  const percentage = Math.round(value * 100);
  const barClass =
    percentage >= 70 ? "bar-high" : percentage >= 40 ? "bar-medium" : "bar-low";

  return (
    <div className="confidence-bar">
      {label && <span className="confidence-label">{label}</span>}
      <div className="confidence-track">
        <div
          className={`confidence-fill ${barClass}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="confidence-value">{percentage}%</span>
    </div>
  );
}
