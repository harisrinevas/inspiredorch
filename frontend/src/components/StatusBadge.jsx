const COLORS = {
  pending:           { bg: '#374151', color: '#9ca3af' },
  running:           { bg: '#1d3a6e', color: '#60a5fa' },
  input_validation:  { bg: '#1e3a5f', color: '#93c5fd' },
  output_validation: { bg: '#1e3a5f', color: '#93c5fd' },
  success:           { bg: '#14532d', color: '#4ade80' },
  failed:            { bg: '#450a0a', color: '#f87171' },
  skipped:           { bg: '#2d2d2d', color: '#6b7280' },
  cancelled:         { bg: '#3d1f00', color: '#fb923c' },
}

export default function StatusBadge({ status }) {
  const style = COLORS[status] || { bg: '#2d2d2d', color: '#9ca3af' }
  return (
    <span className="tag" style={{ background: style.bg, color: style.color }}>
      {status}
    </span>
  )
}
