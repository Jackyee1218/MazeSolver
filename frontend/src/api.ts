// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface UploadResponse {
  session_id: string
  display_image: string  // base64 PNG
  maze_image: string     // base64 PNG
  width: number
  height: number
}

export interface ImagesResponse {
  display_image: string
  maze_image: string
}

export interface SSEVisitedEvent {
  nodes: [number, number][]  // [y, x]
  start_index: number
  total: number
}

export interface SSEPathEvent {
  nodes: [number, number][]  // [y, x]
}

export interface SSECompleteEvent {
  status: 'ac' | 'wa'
  solve_time: number
}

// ---------------------------------------------------------------------------
// Fetch wrapper
// ---------------------------------------------------------------------------

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, options)
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error((data as { detail?: string }).detail || `Request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export async function uploadMaze(file: File): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)
  return request<UploadResponse>('/api/maze/upload', { method: 'POST', body: form })
}

export async function setPoints(
  sessionId: string,
  start: [number, number],
  end: [number, number],
): Promise<ImagesResponse> {
  return request<ImagesResponse>('/api/maze/set-points', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, start, end }),
  })
}

export async function resetMaze(sessionId: string): Promise<ImagesResponse> {
  return request<ImagesResponse>('/api/maze/reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  })
}

// ---------------------------------------------------------------------------
// SSE solve — returns a cleanup function
// ---------------------------------------------------------------------------

export interface SolveCallbacks {
  onVisited: (event: SSEVisitedEvent) => void
  onPath: (event: SSEPathEvent) => void
  onComplete: (event: SSECompleteEvent) => void
  onError?: (err: Error) => void
}

export function startSolve(sessionId: string, callbacks: SolveCallbacks): () => void {
  const es = new EventSource(`/api/maze/solve?session_id=${sessionId}`)

  es.addEventListener('visited', (e: MessageEvent) => {
    callbacks.onVisited(JSON.parse(e.data) as SSEVisitedEvent)
  })

  es.addEventListener('path', (e: MessageEvent) => {
    callbacks.onPath(JSON.parse(e.data) as SSEPathEvent)
  })

  es.addEventListener('complete', (e: MessageEvent) => {
    callbacks.onComplete(JSON.parse(e.data) as SSECompleteEvent)
    es.close()
  })

  es.onerror = () => {
    callbacks.onError?.(new Error('SSE connection error'))
    es.close()
  }

  return () => es.close()
}
