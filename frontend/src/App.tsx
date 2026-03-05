import { useRef, useState, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Controls } from './components/Controls'
import { MazeCanvas, type MazeCanvasHandle } from './components/MazeCanvas'
import { StatusBar } from './components/StatusBar'
import { uploadMaze, setPoints, resetMaze, startSolve } from './api'

// ---------------------------------------------------------------------------
// State machine
// ---------------------------------------------------------------------------

export type Phase =
  | 'idle'
  | 'image_loaded'
  | 'setting_points'
  | 'ready'
  | 'solving'
  | 'solved'

interface AppState {
  phase: Phase
  sessionId: string | null
  originalImage: string | null   // original without any markers, never changes after upload
  displayImage: string | null   // updated with markers after set-points
  mazeImage: string | null
  pendingStart: [number, number] | null
  solveStatus: 'idle' | 'wait' | 'ac' | 'wa'
  solveTime: number | null
}

const INITIAL_STATE: AppState = {
  phase: 'idle',
  sessionId: null,
  originalImage: null,
  displayImage: null,
  mazeImage: null,
  pendingStart: null,
  solveStatus: 'idle',
  solveTime: null,
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

export default function App() {
  const [state, setState] = useState<AppState>(INITIAL_STATE)
  const displayCanvasRef = useRef<MazeCanvasHandle>(null)
  const mazeCanvasRef = useRef<MazeCanvasHandle>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const cleanupSSERef = useRef<(() => void) | null>(null)

  // Mutations
  const uploadMutation = useMutation({
    mutationFn: uploadMaze,
    onSuccess: (data) => {
      setState({
        ...INITIAL_STATE,
        phase: 'image_loaded',
        sessionId: data.session_id,
        originalImage: data.display_image,
        displayImage: data.display_image,
        mazeImage: data.maze_image,
      })
    },
  })

  const setPointsMutation = useMutation({
    mutationFn: ({ sessionId, start, end }: { sessionId: string; start: [number, number]; end: [number, number] }) =>
      setPoints(sessionId, start, end),
    onSuccess: (data) => {
      setState((s) => ({
        ...s,
        phase: 'ready',
        displayImage: data.display_image,
        mazeImage: data.maze_image,
        pendingStart: null,
      }))
    },
  })

  const resetMutation = useMutation({
    mutationFn: (sessionId: string) => resetMaze(sessionId),
    onSuccess: (data) => {
      cleanupSSERef.current?.()
      setState((s) => ({
        ...s,
        phase: 'image_loaded',
        displayImage: data.display_image,
        mazeImage: data.maze_image,
        pendingStart: null,
        solveStatus: 'idle',
        solveTime: null,
      }))
    },
  })

  // Handlers
  const handleOpen = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    uploadMutation.mutate(file)
    e.target.value = ''
  }, [uploadMutation])

  const handleSetPoints = useCallback(() => {
    setState((s) => ({ ...s, phase: 'setting_points', pendingStart: null }))
  }, [])

  const handleCanvasClick = useCallback((x: number, y: number) => {
    if (state.phase !== 'setting_points') return

    if (!state.pendingStart) {
      // First click → draw start marker optimistically, wait for second click
      setState((s) => ({ ...s, pendingStart: [x, y] }))
      displayCanvasRef.current?.drawMarker(x, y, 'rgb(20,140,40)')
    } else {
      // Second click → end point, send both to backend
      const start = state.pendingStart
      const end: [number, number] = [x, y]
      setPointsMutation.mutate({ sessionId: state.sessionId!, start, end })
    }
  }, [state.phase, state.pendingStart, state.sessionId, setPointsMutation])

  const handleStart = useCallback(() => {
    if (!state.sessionId || state.phase !== 'ready') return

    setState((s) => ({ ...s, phase: 'solving', solveStatus: 'wait', solveTime: null }))

    const cleanup = startSolve(state.sessionId, {
      onVisited() {
        // BFS visited nodes not visualized; path animation shown instead
      },
      onPath(event) {
        mazeCanvasRef.current?.drawPath(event.nodes)
      },
      onComplete(event) {
        setState((s) => ({
          ...s,
          phase: 'solved',
          solveStatus: event.status,
          solveTime: event.solve_time,
        }))
      },
      onError() {
        setState((s) => ({ ...s, phase: 'ready', solveStatus: 'idle' }))
      },
    })

    cleanupSSERef.current = cleanup
  }, [state.sessionId, state.phase])

  const handleReset = useCallback(() => {
    if (!state.sessionId) return
    resetMutation.mutate(state.sessionId)
  }, [state.sessionId, resetMutation])

  const isSettingPoints = state.phase === 'setting_points'

  return (
    <div className="app">
      <input
        ref={fileInputRef}
        type="file"
        accept=".jpg,.jpeg,.png,.tif,.tiff"
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />

      <header className="top-bar">
        <span className="top-bar-title">MazeSolver</span>
      </header>

      <div className="main">
        <aside className="sidebar">
          <Controls
            phase={state.phase}
            pendingStart={state.pendingStart}
            onOpen={handleOpen}
            onSetPoints={handleSetPoints}
            onStart={handleStart}
            onReset={handleReset}
          />
          <StatusBar status={state.solveStatus} solveTime={state.solveTime} />
        </aside>

        <section className="canvas-area">
          {state.phase === 'idle' && !uploadMutation.isPending ? (
            <div className="upload-area">
              <div className="upload-prompt">
                <p>Open a maze image to get started.</p>
                <button className="btn btn-primary" style={{ width: 'auto' }} onClick={handleOpen}>
                  Open Image
                </button>
              </div>
            </div>
          ) : (
            <>
              <MazeCanvas
                ref={displayCanvasRef}
                label="Original"
                imageSrc={isSettingPoints ? state.originalImage : state.displayImage}
                clickable={isSettingPoints}
                onCanvasClick={handleCanvasClick}
              />
              <MazeCanvas
                ref={mazeCanvasRef}
                label="Solution"
                imageSrc={state.displayImage}
              />
            </>
          )}
        </section>
      </div>
    </div>
  )
}
