import type { Phase } from '../App'

interface Props {
  phase: Phase
  pendingStart: [number, number] | null
  onOpen: () => void
  onSetPoints: () => void
  onStart: () => void
  onReset: () => void
}

export function Controls({ phase, pendingStart, onOpen, onSetPoints, onStart, onReset }: Props) {
  const isSettingPoints = phase === 'setting_points'

  let hint: { label: string; text: string; accent?: boolean } | null = null
  if (isSettingPoints && !pendingStart) {
    hint = { label: 'Step 1 / 2', text: 'Click the start point on the image', accent: true }
  } else if (isSettingPoints && pendingStart) {
    hint = { label: 'Step 2 / 2', text: 'Click the end point on the image', accent: true }
  } else if (phase === 'ready') {
    hint = { label: 'Ready', text: 'Press Solve to find the path' }
  } else if (phase === 'solving') {
    hint = { label: 'Solving', text: 'Drawing path…' }
  }

  return (
    <>
      <button className="btn btn-secondary" onClick={onOpen} disabled={phase === 'solving'}>
        Open
      </button>

      <button
        className={`btn ${isSettingPoints ? 'btn-active' : 'btn-secondary'}`}
        onClick={onSetPoints}
        disabled={phase === 'idle' || phase === 'solving'}
      >
        Set Points
      </button>

      <button
        className="btn btn-primary"
        onClick={onStart}
        disabled={phase !== 'ready'}
      >
        Solve
      </button>

      <button
        className="btn btn-secondary"
        onClick={onReset}
        disabled={phase === 'idle' || phase === 'solving'}
      >
        Reset
      </button>

      {hint && (
        <div className={`hint${hint.accent ? ' hint-step' : ''}`}>
          <strong>{hint.label}</strong>
          {hint.text}
        </div>
      )}
    </>
  )
}
