interface Props {
  status: 'idle' | 'wait' | 'ac' | 'wa'
  solveTime: number | null
}

const STATUS_LABELS: Record<Props['status'], string> = {
  idle: '—',
  wait: 'Solving...',
  ac: 'Solved',
  wa: 'No path found',
}

export function StatusBar({ status, solveTime }: Props) {
  return (
    <div className="status-bar">
      <span className="status-label">Status</span>
      <span className={`status-value status-${status}`}>{STATUS_LABELS[status]}</span>

      <span className="status-label" style={{ marginTop: 8 }}>Solve time</span>
      <span className="time-value">
        {solveTime !== null ? `${solveTime.toFixed(4)} s` : '—'}
      </span>
    </div>
  )
}
