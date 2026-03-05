import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react'

interface Props {
  imageSrc: string | null   // base64 PNG
  label: string
  clickable?: boolean
  onCanvasClick?: (x: number, y: number) => void
}

export interface MazeCanvasHandle {
  drawMarker: (x: number, y: number, color: string) => void
  drawPath: (nodes: [number, number][]) => void
}

// Target ~6 seconds for path animation regardless of path length
const ANIM_FRAMES = 360

export const MazeCanvas = forwardRef<MazeCanvasHandle, Props>(
  ({ imageSrc, label, clickable, onCanvasClick }, ref) => {
    const canvasRef = useRef<HTMLCanvasElement>(null)

    // Draw base image whenever src changes
    useEffect(() => {
      const canvas = canvasRef.current
      if (!canvas) return
      const ctx = canvas.getContext('2d')!

      if (!imageSrc) {
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        return
      }

      const img = new Image()
      img.onload = () => {
        canvas.width = img.naturalWidth
        canvas.height = img.naturalHeight
        ctx.drawImage(img, 0, 0)
      }
      img.src = `data:image/png;base64,${imageSrc}`
    }, [imageSrc])

    // Expose drawing methods to parent via ref
    useImperativeHandle(ref, () => ({
      drawMarker(x: number, y: number, color: string) {
        const ctx = canvasRef.current?.getContext('2d')
        if (!ctx) return
        const r = 10
        ctx.strokeStyle = color
        ctx.lineWidth = 4
        ctx.lineCap = 'round'
        ctx.beginPath()
        ctx.moveTo(x - r, y - r)
        ctx.lineTo(x + r, y + r)
        ctx.moveTo(x + r, y - r)
        ctx.lineTo(x - r, y + r)
        ctx.stroke()
      },

      drawPath(nodes: [number, number][]) {
        const ctx = canvasRef.current?.getContext('2d')
        if (!ctx || nodes.length < 2) return

        const nodesPerFrame = Math.max(1, Math.ceil(nodes.length / ANIM_FRAMES))
        let index = 1

        ctx.strokeStyle = '#cc2200'
        ctx.lineWidth = 4
        ctx.lineJoin = 'round'
        ctx.lineCap = 'round'

        const step = () => {
          if (index >= nodes.length) return

          ctx.beginPath()
          const [py, px] = nodes[index - 1]
          ctx.moveTo(px, py)

          for (let i = 0; i < nodesPerFrame && index < nodes.length; i++, index++) {
            const [y, x] = nodes[index]
            ctx.lineTo(x, y)
          }
          ctx.stroke()

          requestAnimationFrame(step)
        }

        requestAnimationFrame(step)
      },
    }))

    function handleClick(e: React.MouseEvent<HTMLCanvasElement>) {
      if (!onCanvasClick) return
      const rect = (e.target as HTMLCanvasElement).getBoundingClientRect()
      const scaleX = canvasRef.current!.width / rect.width
      const scaleY = canvasRef.current!.height / rect.height
      const x = Math.round((e.clientX - rect.left) * scaleX)
      const y = Math.round((e.clientY - rect.top) * scaleY)
      onCanvasClick(x, y)
    }

    return (
      <div className="canvas-wrapper">
        <span className="canvas-label">{label}</span>
        <canvas
          ref={canvasRef}
          width={512}
          height={512}
          className={clickable ? 'clickable' : undefined}
          onClick={clickable ? handleClick : undefined}
        />
      </div>
    )
  },
)
