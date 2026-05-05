import { motion, AnimatePresence } from 'framer-motion'
import { useState, useEffect, useRef, useCallback } from 'react'
import { Radar, Zap } from 'lucide-react'
import gsap from 'gsap'
import type { SearchStats, ThinkingStep } from '../lib/api'
import AnimatedCounter from './AnimatedCounter'

interface Props {
  stats?: SearchStats
  steps: ThinkingStep[]
  isActive: boolean
}

const SEARCH_LAYERS = [
  { id: 'llm', name: 'LLM联网', color: '#818cf8', icon: '🧠' },
  { id: 'api', name: 'API搜索', color: '#34d399', icon: '🔌' },
  { id: 'serp', name: 'SERP引擎', color: '#fbbf24', icon: '🔍' },
  { id: 'semantic', name: '语义搜索', color: '#f472b6', icon: '🎯' },
  { id: 'free', name: '免费引擎', color: '#22d3ee', icon: '🆓' },
  { id: 'platform', name: '平台API', color: '#a78bfa', icon: '📱' },
  { id: 'hot', name: '热搜聚合', color: '#fb923c', icon: '🔥' },
  { id: 'scrape', name: '深度抓取', color: '#4ade80', icon: '🕷️' },
  { id: 'validate', name: '质量验证', color: '#f87171', icon: '✅' },
] as const

// ---- Canvas particles & ring pulse types ----

interface CanvasParticle {
  x: number
  y: number
  vx: number
  vy: number
  color: string
  life: number
  size: number
}

interface RingPulse {
  cx: number
  cy: number
  radius: number
  maxRadius: number
  color: string
  life: number
}

interface BurstParticle {
  x: number
  y: number
  vx: number
  vy: number
  color: string
  life: number
  size: number
}

export default function SearchRadar({ stats, steps, isActive }: Props) {
  const [activeLayers, setActiveLayers] = useState<Set<number>>(new Set())
  const [collapsed, setCollapsed] = useState(false)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animRef = useRef<number>(0)
  const sweepRef = useRef({ angle: 0 })
  const prevActiveRef = useRef<Set<number>>(new Set())
  const prevStatsRef = useRef<SearchStats | undefined>(undefined)
  const ringPulsesRef = useRef<RingPulse[]>([])
  const burstParticlesRef = useRef<BurstParticle[]>([])

  // ---- Determine active layers from steps ----
  useEffect(() => {
    if (!isActive) return

    const stepText = steps.map(s => s.step + ' ' + s.detail).join(' ').toLowerCase()
    const newActive = new Set<number>()

    if (stepText.includes('minimax') || stepText.includes('混元') || stepText.includes('llm'))
      newActive.add(0)
    if (stepText.includes('api') || stepText.includes('tavily') || stepText.includes('exa'))
      newActive.add(1)
    if (stepText.includes('serper') || stepText.includes('google') || stepText.includes('serp'))
      newActive.add(2)
    if (stepText.includes('语义') || stepText.includes('semantic'))
      newActive.add(3)
    if (stepText.includes('duckduck') || stepText.includes('ddg') || stepText.includes('免费'))
      newActive.add(4)
    if (stepText.includes('平台') || stepText.includes('小红书') || stepText.includes('b站'))
      newActive.add(5)
    if (stepText.includes('热搜') || stepText.includes('trending') || stepText.includes('热门'))
      newActive.add(6)
    if (stepText.includes('jina') || stepText.includes('抓取') || stepText.includes('crawl'))
      newActive.add(7)
    if (stepText.includes('验证') || stepText.includes('质量') || stepText.includes('filter'))
      newActive.add(8)

    if (newActive.size === 0 && isActive) {
      const idx = Math.floor(steps.length / 2) % 9
      for (let i = 0; i <= idx; i++) newActive.add(i)
    }

    // Detect newly activated layers → emit ring pulses
    newActive.forEach(layerIdx => {
      if (!prevActiveRef.current.has(layerIdx) && canvasRef.current) {
        const W = 280
        const centerX = W / 2
        const centerY = W / 2
        const maxR = W / 2 - 20
        const r = (maxR / 9) * (layerIdx + 1)
        ringPulsesRef.current.push({
          cx: centerX,
          cy: centerY,
          radius: r,
          maxRadius: r + 30,
          color: SEARCH_LAYERS[layerIdx].color,
          life: 1,
        })
      }
    })

    prevActiveRef.current = newActive
    setActiveLayers(newActive)
  }, [steps, isActive])

  // ---- Detect new results arriving → burst particles ----
  useEffect(() => {
    if (!stats || !canvasRef.current) return
    const prevTotal = prevStatsRef.current?.total_raw ?? 0
    const newTotal = stats.total_raw

    if (newTotal > prevTotal && prevTotal > 0) {
      const W = 280
      const cx = W / 2
      const cy = W / 2
      const count = Math.min(Math.max((newTotal - prevTotal) * 2, 8), 30)
      for (let i = 0; i < count; i++) {
        const angle = (Math.PI * 2 / count) * i + Math.random() * 0.3
        const speed = 1.5 + Math.random() * 2.5
        burstParticlesRef.current.push({
          x: cx,
          y: cy,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          color: SEARCH_LAYERS[i % SEARCH_LAYERS.length].color,
          life: 1,
          size: 2 + Math.random() * 2,
        })
      }
    }

    prevStatsRef.current = stats
  }, [stats])

  // ---- GSAP-powered sweep angle + Canvas rendering ----
  useEffect(() => {
    if (!isActive || !canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')!
    const W = 280
    const H = 280
    canvas.width = W * 2
    canvas.height = H * 2
    ctx.scale(2, 2)

    const centerX = W / 2
    const centerY = H / 2
    const maxR = W / 2 - 20

    // GSAP-driven sweep angle for smoother rotation
    sweepRef.current.angle = 0
    const sweepTween = gsap.to(sweepRef.current, {
      angle: Math.PI * 2,
      duration: 3,
      repeat: -1,
      ease: 'none',
    })

    let t = 0
    const trailParticles: CanvasParticle[] = []

    const draw = () => {
      t += 0.02
      ctx.clearRect(0, 0, W, H)

      // ---- Dark background with subtle grid ----
      ctx.fillStyle = 'rgba(10, 14, 23, 0.95)'
      ctx.fillRect(0, 0, W, H)

      const gridSize = 20
      ctx.strokeStyle = 'rgba(148, 163, 184, 0.04)'
      ctx.lineWidth = 0.5
      for (let gx = 0; gx <= W; gx += gridSize) {
        ctx.beginPath()
        ctx.moveTo(gx, 0)
        ctx.lineTo(gx, H)
        ctx.stroke()
      }
      for (let gy = 0; gy <= H; gy += gridSize) {
        ctx.beginPath()
        ctx.moveTo(0, gy)
        ctx.lineTo(W, gy)
        ctx.stroke()
      }

      // ---- Concentric layer rings ----
      for (let i = 0; i < 9; i++) {
        const r = (maxR / 9) * (i + 1)
        const active = activeLayers.has(i)

        ctx.beginPath()
        ctx.arc(centerX, centerY, r, 0, Math.PI * 2)
        ctx.strokeStyle = active
          ? SEARCH_LAYERS[i].color + '50'
          : 'rgba(148, 163, 184, 0.06)'
        ctx.lineWidth = active ? 1.5 : 0.5
        ctx.stroke()

        if (active) {
          const pulseR = r + Math.sin(t * 2 + i) * 2
          ctx.beginPath()
          ctx.arc(centerX, centerY, pulseR, 0, Math.PI * 2)
          ctx.strokeStyle = SEARCH_LAYERS[i].color + '18'
          ctx.lineWidth = 3
          ctx.stroke()
        }
      }

      // ---- Cross-hair lines ----
      for (let i = 0; i < 4; i++) {
        const angle = (Math.PI * 2 / 4) * i + t * 0.3
        ctx.beginPath()
        ctx.moveTo(centerX, centerY)
        ctx.lineTo(
          centerX + Math.cos(angle) * maxR,
          centerY + Math.sin(angle) * maxR,
        )
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.05)'
        ctx.lineWidth = 0.5
        ctx.stroke()
      }

      // ---- GSAP-driven sweep wedge ----
      const sweepAngle = sweepRef.current.angle
      const sweepArc = 0.4

      const grad = ctx.createConicGradient?.(sweepAngle, centerX, centerY)
      if (grad) {
        grad.addColorStop(0, 'rgba(99, 102, 241, 0.15)')
        grad.addColorStop(sweepArc / (Math.PI * 2), 'rgba(99, 102, 241, 0)')
        grad.addColorStop(1, 'rgba(99, 102, 241, 0)')
        ctx.beginPath()
        ctx.arc(centerX, centerY, maxR, 0, Math.PI * 2)
        ctx.fillStyle = grad
        ctx.fill()
      } else {
        ctx.beginPath()
        ctx.moveTo(centerX, centerY)
        ctx.arc(centerX, centerY, maxR, sweepAngle, sweepAngle + sweepArc)
        ctx.closePath()
        ctx.fillStyle = 'rgba(99, 102, 241, 0.1)'
        ctx.fill()
      }

      // Bright sweep leading edge
      ctx.beginPath()
      ctx.moveTo(centerX, centerY)
      ctx.lineTo(
        centerX + Math.cos(sweepAngle) * maxR,
        centerY + Math.sin(sweepAngle) * maxR,
      )
      ctx.strokeStyle = 'rgba(99, 102, 241, 0.35)'
      ctx.lineWidth = 1.5
      ctx.stroke()

      // ---- Active layer dots ----
      activeLayers.forEach(layerIdx => {
        const r = (maxR / 9) * (layerIdx + 1)
        const dotAngle = t * (1 + layerIdx * 0.3) + layerIdx * 0.7
        const x = centerX + Math.cos(dotAngle) * r
        const y = centerY + Math.sin(dotAngle) * r

        ctx.beginPath()
        ctx.arc(x, y, 3, 0, Math.PI * 2)
        ctx.fillStyle = SEARCH_LAYERS[layerIdx].color
        ctx.fill()

        ctx.beginPath()
        ctx.arc(x, y, 7, 0, Math.PI * 2)
        ctx.fillStyle = SEARCH_LAYERS[layerIdx].color + '25'
        ctx.fill()

        if (Math.random() < 0.04) {
          trailParticles.push({
            x, y,
            vx: (centerX - x) * 0.018,
            vy: (centerY - y) * 0.018,
            color: SEARCH_LAYERS[layerIdx].color,
            life: 1,
            size: 1.5 + Math.random() * 2,
          })
        }
      })

      // ---- Trail particles ----
      for (let i = trailParticles.length - 1; i >= 0; i--) {
        const p = trailParticles[i]
        p.x += p.vx
        p.y += p.vy
        p.life -= 0.015
        if (p.life <= 0) {
          trailParticles.splice(i, 1)
          continue
        }
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2)
        ctx.fillStyle = p.color + alphaHex(p.life * 0.8)
        ctx.fill()
      }

      // ---- Ring pulses (layer activation) ----
      const rings = ringPulsesRef.current
      for (let i = rings.length - 1; i >= 0; i--) {
        const rp = rings[i]
        rp.life -= 0.02
        if (rp.life <= 0) {
          rings.splice(i, 1)
          continue
        }
        const currentR = rp.radius + (rp.maxRadius - rp.radius) * (1 - rp.life)
        ctx.beginPath()
        ctx.arc(rp.cx, rp.cy, currentR, 0, Math.PI * 2)
        ctx.strokeStyle = rp.color + alphaHex(rp.life * 0.5)
        ctx.lineWidth = 2 * rp.life
        ctx.stroke()
      }

      // ---- Burst particles (data incoming) ----
      const bursts = burstParticlesRef.current
      for (let i = bursts.length - 1; i >= 0; i--) {
        const bp = bursts[i]
        bp.x += bp.vx
        bp.y += bp.vy
        bp.vx *= 0.97
        bp.vy *= 0.97
        bp.life -= 0.02
        if (bp.life <= 0) {
          bursts.splice(i, 1)
          continue
        }
        ctx.beginPath()
        ctx.arc(bp.x, bp.y, bp.size * bp.life, 0, Math.PI * 2)
        ctx.fillStyle = bp.color + alphaHex(bp.life * 0.7)
        ctx.fill()
      }

      // ---- Center dot ----
      ctx.beginPath()
      ctx.arc(centerX, centerY, 8, 0, Math.PI * 2)
      const centerGlow = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, 14)
      centerGlow.addColorStop(0, 'rgba(99, 102, 241, 0.9)')
      centerGlow.addColorStop(0.5, 'rgba(99, 102, 241, 0.3)')
      centerGlow.addColorStop(1, 'rgba(99, 102, 241, 0)')
      ctx.fillStyle = centerGlow
      ctx.fill()

      ctx.beginPath()
      ctx.arc(centerX, centerY, 5, 0, Math.PI * 2)
      ctx.fillStyle = '#818cf8'
      ctx.fill()

      animRef.current = requestAnimationFrame(draw)
    }

    draw()
    return () => {
      cancelAnimationFrame(animRef.current)
      sweepTween.kill()
    }
  }, [isActive, activeLayers])

  if (!isActive && !stats) return null

  const engineCount = stats ? Object.keys(stats.engines).length : 0

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="mb-3 rounded-2xl border border-slate-200 dark:border-slate-700/50 bg-gradient-to-br from-slate-50 to-white dark:from-slate-900 dark:to-slate-950 overflow-hidden shadow-lg"
    >
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300"
      >
        <div className="flex items-center gap-2">
          <motion.div
            animate={isActive ? { rotate: 360 } : {}}
            transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
          >
            <Radar className="w-4 h-4 text-indigo-500" />
          </motion.div>
          <span className="bg-gradient-to-r from-indigo-600 to-violet-600 dark:from-indigo-400 dark:to-violet-400 bg-clip-text text-transparent font-semibold">
            9层搜索矩阵
          </span>
          {stats && (
            <span className="text-xs text-slate-400 tabular-nums">
              <AnimatedCounter value={stats.total_deduped} size="sm" className="!text-xs !font-normal text-slate-400" /> 条结果 ·{' '}
              <AnimatedCounter value={engineCount} size="sm" className="!text-xs !font-normal text-slate-400" /> 引擎
            </span>
          )}
          {isActive && (
            <motion.span
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
              className="flex items-center gap-1 text-xs text-emerald-500"
            >
              <Zap className="w-3 h-3" /> 搜索中
            </motion.span>
          )}
        </div>
      </button>

      <AnimatePresence>
        {!collapsed && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="flex flex-col md:flex-row items-center gap-4 px-4 pb-4">
              {/* Radar canvas */}
              <div className="relative flex-shrink-0 rounded-xl overflow-hidden">
                <canvas
                  ref={canvasRef}
                  className="w-[280px] h-[280px]"
                  style={{ imageRendering: 'auto' }}
                />
              </div>

              {/* Layer list */}
              <div className="flex-1 space-y-1.5 min-w-0">
                {SEARCH_LAYERS.map((layer, i) => {
                  const isLayerActive = activeLayers.has(i)
                  const layerCount = stats?.engines
                    ? Object.entries(stats.engines)
                        .filter(([k]) =>
                          k.toLowerCase().includes(layer.id) || layer.name.includes(k),
                        )
                        .reduce((sum, [, v]) => sum + v, 0)
                    : 0

                  return (
                    <motion.div
                      key={layer.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{
                        opacity: 1,
                        x: 0,
                        boxShadow: isLayerActive
                          ? `0 0 12px ${layer.color}20`
                          : '0 0 0px transparent',
                      }}
                      transition={{ delay: i * 0.05 }}
                      className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs transition-all ${
                        isLayerActive
                          ? 'bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/50'
                          : 'opacity-50'
                      }`}
                    >
                      <span className="text-base">{layer.icon}</span>
                      <span
                        className="w-2 h-2 rounded-full transition-shadow duration-500"
                        style={{
                          backgroundColor: layer.color,
                          boxShadow: isLayerActive ? `0 0 8px ${layer.color}` : 'none',
                        }}
                      />
                      <span
                        className={`flex-1 ${
                          isLayerActive
                            ? 'text-slate-700 dark:text-slate-200 font-medium'
                            : 'text-slate-400'
                        }`}
                      >
                        第{i + 1}层: {layer.name}
                      </span>
                      {isLayerActive && (
                        <motion.span
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="text-emerald-600 dark:text-emerald-400 font-semibold tabular-nums"
                        >
                          {layerCount > 0 ? (
                            <AnimatedCounter value={layerCount} suffix="条" size="sm" className="!text-xs" />
                          ) : (
                            '●'
                          )}
                        </motion.span>
                      )}
                    </motion.div>
                  )
                })}
              </div>
            </div>

            {/* Stats summary with animated counters */}
            {stats && (
              <div className="px-4 pb-3 pt-2 border-t border-slate-100 dark:border-slate-800">
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div>
                    <AnimatedCounter
                      value={stats.total_raw}
                      size="lg"
                      className="text-indigo-600 dark:text-indigo-400"
                    />
                    <div className="text-[10px] text-slate-500">原始结果</div>
                  </div>
                  <div>
                    <AnimatedCounter
                      value={stats.total_deduped}
                      size="lg"
                      className="text-emerald-600 dark:text-emerald-400"
                    />
                    <div className="text-[10px] text-slate-500">去重后</div>
                  </div>
                  <div>
                    <AnimatedCounter
                      value={engineCount}
                      size="lg"
                      className="text-violet-600 dark:text-violet-400"
                    />
                    <div className="text-[10px] text-slate-500">搜索引擎</div>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function alphaHex(alpha: number): string {
  return Math.round(Math.min(1, Math.max(0, alpha)) * 255)
    .toString(16)
    .padStart(2, '0')
}
