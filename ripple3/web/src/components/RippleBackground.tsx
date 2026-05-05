import { useEffect, useRef } from 'react'

export default function RippleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!

    let w = canvas.width = window.innerWidth
    let h = canvas.height = window.innerHeight
    let animId: number

    const ripples: { x: number; y: number; r: number; maxR: number; alpha: number }[] = []

    function addRipple() {
      ripples.push({
        x: Math.random() * w,
        y: Math.random() * h,
        r: 0,
        maxR: 80 + Math.random() * 120,
        alpha: 0.08 + Math.random() * 0.04,
      })
    }

    let interval = setInterval(addRipple, 2000)
    addRipple()

    function draw() {
      ctx.clearRect(0, 0, w, h)
      for (let i = ripples.length - 1; i >= 0; i--) {
        const rp = ripples[i]
        rp.r += 0.5
        const progress = rp.r / rp.maxR
        const a = rp.alpha * (1 - progress)
        if (a <= 0.001) { ripples.splice(i, 1); continue }
        ctx.beginPath()
        ctx.arc(rp.x, rp.y, rp.r, 0, Math.PI * 2)
        ctx.strokeStyle = `rgba(99, 102, 241, ${a})`
        ctx.lineWidth = 1.5
        ctx.stroke()
      }
      animId = requestAnimationFrame(draw)
    }
    draw()

    const onResize = () => { w = canvas.width = window.innerWidth; h = canvas.height = window.innerHeight }
    window.addEventListener('resize', onResize)

    return () => {
      cancelAnimationFrame(animId)
      clearInterval(interval)
      window.removeEventListener('resize', onResize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none opacity-40 dark:opacity-20"
      style={{ zIndex: 0 }}
    />
  )
}
