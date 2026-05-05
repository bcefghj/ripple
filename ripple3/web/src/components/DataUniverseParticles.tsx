import { useRef, useEffect, useCallback, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Atom } from 'lucide-react'

interface Props {
  engines: Record<string, number>
  totalResults: number
  isActive: boolean
}

const ENGINE_COLORS: Record<string, string> = {
  minimax: '#a78bfa',
  serper: '#34d399',
  ddgs: '#60a5fa',
  tavily: '#fbbf24',
  exa: '#f472b6',
  jina: '#22d3ee',
  google: '#fb923c',
  bing: '#818cf8',
  baidu: '#f87171',
  default: '#94a3b8',
}

function getEngineColor(name: string): string {
  const lower = name.toLowerCase()
  for (const [key, color] of Object.entries(ENGINE_COLORS)) {
    if (lower.includes(key)) return color
  }
  const hash = [...lower].reduce((h, c) => (h * 31 + c.charCodeAt(0)) | 0, 0)
  const palette = Object.values(ENGINE_COLORS)
  return palette[Math.abs(hash) % (palette.length - 1)]
}

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  color: string
  alpha: number
  size: number
  trail: { x: number; y: number; alpha: number }[]
}

interface EngineLabel {
  name: string
  count: number
  displayCount: number
  angle: number
  color: string
}

export default function DataUniverseParticles({ engines, totalResults, isActive }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animRef = useRef(0)
  const particlesRef = useRef<Particle[]>([])
  const timeRef = useRef(0)
  const coreRadiusRef = useRef(12)
  const displayTotalRef = useRef(0)
  const labelsRef = useRef<EngineLabel[]>([])
  const prevEnginesRef = useRef<Record<string, number>>({})
  const [displayTotal, setDisplayTotal] = useState(0)

  const spawnParticle = useCallback((w: number, h: number, color: string) => {
    const edge = Math.random() * 4
    let x: number, y: number
    if (edge < 1) { x = Math.random() * w; y = -8 }
    else if (edge < 2) { x = w + 8; y = Math.random() * h }
    else if (edge < 3) { x = Math.random() * w; y = h + 8 }
    else { x = -8; y = Math.random() * h }

    const cx = w / 2, cy = h / 2
    const dx = cx - x, dy = cy - y
    const dist = Math.sqrt(dx * dx + dy * dy)
    const speed = 0.8 + Math.random() * 1.2
    const spread = (Math.random() - 0.5) * 0.3

    return {
      x, y,
      vx: (dx / dist) * speed + spread,
      vy: (dy / dist) * speed + spread,
      color,
      alpha: 0.7 + Math.random() * 0.3,
      size: 1.5 + Math.random() * 2,
      trail: [] as { x: number; y: number; alpha: number }[],
    }
  }, [])

  useEffect(() => {
    const entries = Object.entries(engines)
    const angleStep = (Math.PI * 2) / Math.max(entries.length, 1)
    labelsRef.current = entries.map(([name, count], i) => ({
      name,
      count,
      displayCount: prevEnginesRef.current[name] || 0,
      angle: -Math.PI / 2 + i * angleStep,
      color: getEngineColor(name),
    }))
    prevEnginesRef.current = { ...engines }
  }, [engines])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const rect = canvas.getBoundingClientRect()
    const W = rect.width
    const H = rect.height
    canvas.width = W * dpr
    canvas.height = H * dpr
    const ctx = canvas.getContext('2d')!
    ctx.scale(dpr, dpr)

    const cx = W / 2, cy = H / 2
    const maxOrbitR = Math.min(W, H) * 0.32

    const draw = () => {
      const dt = 1
      timeRef.current += 0.016

      ctx.clearRect(0, 0, W, H)

      const t = timeRef.current

      if (isActive) {
        const colors = labelsRef.current.map(l => l.color)
        if (colors.length === 0) colors.push(ENGINE_COLORS.default)
        for (let i = 0; i < 3; i++) {
          const color = colors[Math.floor(Math.random() * colors.length)]
          particlesRef.current.push(spawnParticle(W, H, color))
        }
      }

      // --- gravitational lens distortion rings ---
      for (let r = 20; r <= 60; r += 15) {
        const pulseR = r + Math.sin(t * 2 + r * 0.1) * 3
        ctx.beginPath()
        ctx.arc(cx, cy, pulseR, 0, Math.PI * 2)
        ctx.strokeStyle = `rgba(129, 140, 248, ${0.04 + Math.sin(t * 1.5 + r) * 0.02})`
        ctx.lineWidth = 1
        ctx.stroke()
      }

      // --- update & draw particles ---
      for (let i = particlesRef.current.length - 1; i >= 0; i--) {
        const p = particlesRef.current[i]
        const dx = cx - p.x, dy = cy - p.y
        const dist = Math.sqrt(dx * dx + dy * dy)

        p.trail.push({ x: p.x, y: p.y, alpha: p.alpha * 0.5 })
        if (p.trail.length > 12) p.trail.shift()

        if (dist < coreRadiusRef.current + 5) {
          if (isActive) {
            coreRadiusRef.current = Math.min(coreRadiusRef.current + 0.05, 30)
          }
          particlesRef.current.splice(i, 1)
          continue
        }

        if (isActive) {
          const gravity = 80 / (dist * dist + 100)
          p.vx += (dx / dist) * gravity * dt
          p.vy += (dy / dist) * gravity * dt
        } else {
          const targetDist = maxOrbitR * (0.4 + (i % 5) * 0.12)
          const orbitAngle = t * 0.3 + (i * 2.399)
          const tx = cx + Math.cos(orbitAngle) * targetDist
          const ty = cy + Math.sin(orbitAngle) * targetDist
          p.vx += (tx - p.x) * 0.01
          p.vy += (ty - p.y) * 0.01
          p.vx *= 0.96
          p.vy *= 0.96
        }

        const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy)
        const maxSpeed = 4
        if (speed > maxSpeed) {
          p.vx = (p.vx / speed) * maxSpeed
          p.vy = (p.vy / speed) * maxSpeed
        }

        p.x += p.vx * dt
        p.y += p.vy * dt

        // gravitational lens warp near center
        if (dist < 80 && dist > coreRadiusRef.current) {
          const warpStrength = (1 - dist / 80) * 0.15
          const perpX = -dy / dist
          const perpY = dx / dist
          p.vx += perpX * warpStrength
          p.vy += perpY * warpStrength
        }

        // draw trail
        for (let j = 0; j < p.trail.length; j++) {
          const tp = p.trail[j]
          const trailAlpha = (j / p.trail.length) * tp.alpha * 0.4
          ctx.beginPath()
          ctx.arc(tp.x, tp.y, p.size * 0.6, 0, Math.PI * 2)
          ctx.fillStyle = p.color + Math.floor(trailAlpha * 255).toString(16).padStart(2, '0')
          ctx.fill()
        }

        // draw particle
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx.fillStyle = p.color + Math.floor(p.alpha * 255).toString(16).padStart(2, '0')
        ctx.fill()

        // glow
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size * 2.5, 0, Math.PI * 2)
        ctx.fillStyle = p.color + '12'
        ctx.fill()
      }

      // --- core pulse ---
      const corePulse = Math.sin(t * 3) * 3
      const coreR = coreRadiusRef.current + corePulse

      const coreGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR * 2.5)
      coreGrad.addColorStop(0, 'rgba(129, 140, 248, 0.4)')
      coreGrad.addColorStop(0.4, 'rgba(139, 92, 246, 0.15)')
      coreGrad.addColorStop(1, 'rgba(139, 92, 246, 0)')
      ctx.beginPath()
      ctx.arc(cx, cy, coreR * 2.5, 0, Math.PI * 2)
      ctx.fillStyle = coreGrad
      ctx.fill()

      ctx.beginPath()
      ctx.arc(cx, cy, coreR, 0, Math.PI * 2)
      const innerGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR)
      innerGrad.addColorStop(0, '#c4b5fd')
      innerGrad.addColorStop(1, '#7c3aed')
      ctx.fillStyle = innerGrad
      ctx.fill()

      if (!isActive) {
        coreRadiusRef.current = Math.max(coreRadiusRef.current - 0.02, 12)
      }

      // --- engine labels around perimeter ---
      const labelRadius = Math.min(W, H) * 0.42
      for (const label of labelsRef.current) {
        const lerpSpeed = 0.06
        label.displayCount += (label.count - label.displayCount) * lerpSpeed

        const lx = cx + Math.cos(label.angle) * labelRadius
        const ly = cy + Math.sin(label.angle) * labelRadius

        ctx.save()
        ctx.font = '600 11px ui-sans-serif, system-ui, sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillStyle = label.color
        ctx.fillText(label.name, lx, ly - 8)

        ctx.font = '700 13px ui-monospace, monospace'
        ctx.fillStyle = label.color + 'cc'
        ctx.fillText(Math.round(label.displayCount).toString(), lx, ly + 8)
        ctx.restore()

        // connector line to center
        ctx.beginPath()
        ctx.moveTo(lx, ly)
        const innerEnd = coreR * 3
        ctx.lineTo(
          cx + Math.cos(label.angle) * innerEnd,
          cy + Math.sin(label.angle) * innerEnd,
        )
        ctx.strokeStyle = label.color + '18'
        ctx.lineWidth = 1
        ctx.setLineDash([3, 4])
        ctx.stroke()
        ctx.setLineDash([])
      }

      // --- total counter at center ---
      displayTotalRef.current += (totalResults - displayTotalRef.current) * 0.08
      const shown = Math.round(displayTotalRef.current)
      ctx.save()
      ctx.font = '700 16px ui-monospace, monospace'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = '#e0e7ff'
      ctx.fillText(shown.toLocaleString(), cx, cy - 1)

      ctx.font = '500 9px ui-sans-serif, system-ui, sans-serif'
      ctx.fillStyle = '#a5b4fc'
      ctx.fillText('结果汇聚', cx, cy + 14)
      ctx.restore()

      animRef.current = requestAnimationFrame(draw)
    }

    draw()
    return () => cancelAnimationFrame(animRef.current)
  }, [isActive, totalResults, spawnParticle])

  useEffect(() => {
    const id = setInterval(() => {
      setDisplayTotal(Math.round(displayTotalRef.current))
    }, 100)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const handleResize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const rect = canvas.getBoundingClientRect()
      canvas.width = rect.width * dpr
      canvas.height = rect.height * dpr
      const ctx = canvas.getContext('2d')
      if (ctx) ctx.scale(dpr, dpr)
    }
    const observer = new ResizeObserver(handleResize)
    observer.observe(canvas)
    return () => observer.disconnect()
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.5 }}
      className="relative w-full h-[300px] rounded-2xl overflow-hidden bg-slate-950 border border-slate-800/60 shadow-xl"
    >
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
        style={{ imageRendering: 'auto' }}
      />

      <AnimatePresence>
        {isActive && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 backdrop-blur-sm"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
            >
              <Atom className="w-3.5 h-3.5 text-indigo-400" />
            </motion.div>
            <span className="text-[11px] font-medium text-indigo-300">数据汇聚中</span>
            <motion.div
              className="flex gap-0.5"
            >
              {[0, 1, 2].map(i => (
                <motion.span
                  key={i}
                  className="w-1 h-1 rounded-full bg-indigo-400"
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ repeat: Infinity, duration: 1.2, delay: i * 0.2 }}
                />
              ))}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="absolute bottom-3 right-3 flex items-center gap-2">
        {Object.entries(engines).slice(0, 5).map(([name]) => (
          <div key={name} className="flex items-center gap-1">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: getEngineColor(name) }}
            />
            <span className="text-[10px] text-slate-500">{name}</span>
          </div>
        ))}
        {Object.keys(engines).length > 5 && (
          <span className="text-[10px] text-slate-600">+{Object.keys(engines).length - 5}</span>
        )}
      </div>
    </motion.div>
  )
}
