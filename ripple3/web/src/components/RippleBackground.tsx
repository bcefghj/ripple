import { useEffect, useRef } from 'react'

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  r: number
  color: string
  alpha: number
  life: number
  maxLife: number
}

interface Ripple {
  x: number
  y: number
  r: number
  maxR: number
  alpha: number
}

const COLORS = [
  'rgba(99, 102, 241,',   // indigo
  'rgba(139, 92, 246,',    // violet
  'rgba(59, 130, 246,',    // blue
  'rgba(236, 72, 153,',    // pink
  'rgba(16, 185, 129,',    // emerald
]

export default function RippleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!

    let w = canvas.width = window.innerWidth
    let h = canvas.height = window.innerHeight
    let animId: number
    let mouseX = -100
    let mouseY = -100

    const particles: Particle[] = []
    const ripples: Ripple[] = []
    const connections: [number, number][] = []

    function createParticle(): Particle {
      return {
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        r: 1 + Math.random() * 2,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        alpha: 0.1 + Math.random() * 0.3,
        life: 0,
        maxLife: 300 + Math.random() * 600,
      }
    }

    const PARTICLE_COUNT = Math.min(60, Math.floor((w * h) / 25000))
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push(createParticle())
    }

    function addRipple(x?: number, y?: number) {
      ripples.push({
        x: x ?? Math.random() * w,
        y: y ?? Math.random() * h,
        r: 0,
        maxR: 60 + Math.random() * 140,
        alpha: 0.06 + Math.random() * 0.04,
      })
    }

    const interval = setInterval(() => addRipple(), 3000)
    addRipple()

    function draw() {
      ctx.clearRect(0, 0, w, h)

      for (let i = ripples.length - 1; i >= 0; i--) {
        const rp = ripples[i]
        rp.r += 0.4
        const progress = rp.r / rp.maxR
        const a = rp.alpha * (1 - progress)
        if (a <= 0.001) { ripples.splice(i, 1); continue }
        ctx.beginPath()
        ctx.arc(rp.x, rp.y, rp.r, 0, Math.PI * 2)
        ctx.strokeStyle = `rgba(99, 102, 241, ${a})`
        ctx.lineWidth = 1
        ctx.stroke()
      }

      connections.length = 0
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 120) {
            connections.push([i, j])
            const alpha = (1 - dist / 120) * 0.08
            ctx.beginPath()
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.strokeStyle = `rgba(99, 102, 241, ${alpha})`
            ctx.lineWidth = 0.5
            ctx.stroke()
          }
        }
      }

      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i]
        p.life++
        if (p.life > p.maxLife) {
          particles[i] = createParticle()
          continue
        }

        const mdx = mouseX - p.x
        const mdy = mouseY - p.y
        const mdist = Math.sqrt(mdx * mdx + mdy * mdy)
        if (mdist < 100 && mdist > 0) {
          p.vx -= (mdx / mdist) * 0.05
          p.vy -= (mdy / mdist) * 0.05
        }

        p.x += p.vx
        p.y += p.vy

        if (p.x < 0) p.x = w
        if (p.x > w) p.x = 0
        if (p.y < 0) p.y = h
        if (p.y > h) p.y = 0

        const fadeIn = Math.min(1, p.life / 60)
        const fadeOut = Math.max(0, 1 - (p.life - p.maxLife + 60) / 60)
        const alpha = p.alpha * fadeIn * fadeOut

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r + 3, 0, Math.PI * 2)
        ctx.fillStyle = `${p.color} ${alpha * 0.3})`
        ctx.fill()

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fillStyle = `${p.color} ${alpha})`
        ctx.fill()
      }

      animId = requestAnimationFrame(draw)
    }
    draw()

    const onResize = () => { w = canvas.width = window.innerWidth; h = canvas.height = window.innerHeight }
    const onMouseMove = (e: MouseEvent) => { mouseX = e.clientX; mouseY = e.clientY }
    const onMouseLeave = () => { mouseX = -100; mouseY = -100 }

    window.addEventListener('resize', onResize)
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseleave', onMouseLeave)

    return () => {
      cancelAnimationFrame(animId)
      clearInterval(interval)
      window.removeEventListener('resize', onResize)
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseleave', onMouseLeave)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none opacity-50 dark:opacity-25"
      style={{ zIndex: 0 }}
    />
  )
}
