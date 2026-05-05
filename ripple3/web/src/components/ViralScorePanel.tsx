import { motion } from 'framer-motion'
import { useState, useEffect, useRef } from 'react'
import { Flame, TrendingUp, AlertTriangle, Lightbulb, ChevronDown, ChevronUp } from 'lucide-react'
import type { ViralScoreData } from '../lib/api'

interface Props {
  data: ViralScoreData
}

function GaugeRing({ score, maxScore = 100, size = 180 }: { score: number; maxScore?: number; size?: number }) {
  const radius = size / 2 - 16
  const circumference = 2 * Math.PI * radius
  const progress = (score / maxScore) * circumference
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const getColor = (s: number) => {
    if (s >= 80) return { main: '#10b981', glow: '#10b98140' }
    if (s >= 60) return { main: '#6366f1', glow: '#6366f140' }
    if (s >= 40) return { main: '#f59e0b', glow: '#f59e0b40' }
    return { main: '#ef4444', glow: '#ef444440' }
  }

  const color = getColor(score)

  useEffect(() => {
    if (!canvasRef.current) return
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')!
    canvas.width = size * 2
    canvas.height = size * 2
    ctx.scale(2, 2)

    const cx = size / 2
    const cy = size / 2
    let frame = 0
    let currentScore = 0

    const draw = () => {
      ctx.clearRect(0, 0, size, size)
      currentScore += (score - currentScore) * 0.05
      const currentProgress = (currentScore / maxScore) * circumference

      ctx.beginPath()
      ctx.arc(cx, cy, radius, 0, Math.PI * 2)
      ctx.strokeStyle = 'rgba(148, 163, 184, 0.1)'
      ctx.lineWidth = 8
      ctx.stroke()

      for (let i = 0; i < 40; i++) {
        const angle = (Math.PI * 2 / 40) * i - Math.PI / 2
        const len = i % 5 === 0 ? 8 : 4
        const x1 = cx + Math.cos(angle) * (radius - 14)
        const y1 = cy + Math.sin(angle) * (radius - 14)
        const x2 = cx + Math.cos(angle) * (radius - 14 - len)
        const y2 = cy + Math.sin(angle) * (radius - 14 - len)
        ctx.beginPath()
        ctx.moveTo(x1, y1)
        ctx.lineTo(x2, y2)
        ctx.strokeStyle = i < (currentScore / maxScore * 40) ? color.main + '80' : 'rgba(148,163,184,0.15)'
        ctx.lineWidth = i % 5 === 0 ? 2 : 1
        ctx.stroke()
      }

      const startAngle = -Math.PI / 2
      const endAngle = startAngle + (currentScore / maxScore) * Math.PI * 2
      ctx.beginPath()
      ctx.arc(cx, cy, radius, startAngle, endAngle)
      ctx.strokeStyle = color.main
      ctx.lineWidth = 8
      ctx.lineCap = 'round'
      ctx.stroke()

      ctx.beginPath()
      ctx.arc(cx, cy, radius, startAngle, endAngle)
      ctx.strokeStyle = color.glow
      ctx.lineWidth = 16
      ctx.stroke()

      const particleAngle = endAngle
      const px = cx + Math.cos(particleAngle) * radius
      const py = cy + Math.sin(particleAngle) * radius
      ctx.beginPath()
      ctx.arc(px, py, 4, 0, Math.PI * 2)
      ctx.fillStyle = color.main
      ctx.fill()
      ctx.beginPath()
      ctx.arc(px, py, 8, 0, Math.PI * 2)
      ctx.fillStyle = color.glow
      ctx.fill()

      frame++
      if (Math.abs(currentScore - score) > 0.5 || frame < 60) {
        requestAnimationFrame(draw)
      }
    }
    draw()
  }, [score, size])

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <canvas ref={canvasRef} className="w-full h-full" />
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', delay: 0.5 }}
          className="text-4xl font-bold"
          style={{ color: color.main }}
        >
          {score}
        </motion.span>
        <span className="text-xs text-slate-500 mt-0.5">/ {maxScore}</span>
      </div>
    </div>
  )
}

function DimensionBar({ name, score, max, delay }: { name: string; score: number; max: number; delay: number }) {
  const pct = (score / max) * 100
  const getBarColor = () => {
    if (pct >= 80) return 'from-emerald-500 to-emerald-400'
    if (pct >= 60) return 'from-indigo-500 to-indigo-400'
    if (pct >= 40) return 'from-amber-500 to-amber-400'
    return 'from-red-500 to-red-400'
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
      className="flex items-center gap-2"
    >
      <span className="text-xs text-slate-600 dark:text-slate-400 w-16 text-right truncate">{name}</span>
      <div className="flex-1 h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, delay: delay + 0.2, ease: 'easeOut' }}
          className={`h-full rounded-full bg-gradient-to-r ${getBarColor()}`}
          style={{ boxShadow: `0 0 8px ${pct >= 60 ? 'rgba(99,102,241,0.3)' : 'rgba(245,158,11,0.3)'}` }}
        />
      </div>
      <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 w-8">{score}</span>
    </motion.div>
  )
}

export default function ViralScorePanel({ data }: Props) {
  const [showDetails, setShowDetails] = useState(false)

  const getVerdict = () => {
    if (data.total_score >= 80) return { text: '爆款潜力极高', icon: Flame, color: 'text-emerald-500' }
    if (data.total_score >= 60) return { text: '有较好潜力', icon: TrendingUp, color: 'text-indigo-500' }
    if (data.total_score >= 40) return { text: '需要优化', icon: Lightbulb, color: 'text-amber-500' }
    return { text: '建议大幅调整', icon: AlertTriangle, color: 'text-red-500' }
  }

  const verdict = getVerdict()
  const VerdictIcon = verdict.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-3 rounded-2xl border border-slate-200 dark:border-slate-700/50 bg-gradient-to-br from-white to-slate-50 dark:from-slate-900 dark:to-slate-950 overflow-hidden shadow-lg"
    >
      {/* Header with gauge */}
      <div className="px-4 pt-4 pb-2">
        <div className="flex items-start gap-4">
          <GaugeRing score={data.total_score} />
          <div className="flex-1 pt-4">
            <div className={`flex items-center gap-2 mb-2 ${verdict.color}`}>
              <VerdictIcon className="w-5 h-5" />
              <span className="font-bold text-lg">{verdict.text}</span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
              预测流量池: <span className="font-semibold text-slate-700 dark:text-slate-200">{data.predicted_pool}</span>
              <span className="ml-2 text-indigo-500">({data.pool_probability})</span>
            </p>

            {/* Quick dimensions */}
            <div className="space-y-2">
              {data.dimensions.slice(0, 5).map((dim, i) => (
                <DimensionBar key={dim.id} name={dim.name} score={dim.score} max={dim.max} delay={i * 0.1} />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Expand details */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="w-full flex items-center justify-center gap-1 py-2 text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors border-t border-slate-100 dark:border-slate-800"
      >
        {showDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        {showDetails ? '收起详情' : '展开完整分析'}
      </button>

      <AnimatePresence>
        {showDetails && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-4">
              {/* CES Analysis */}
              {data.ces_analysis && (
                <div className="p-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/50">
                  <h4 className="text-xs font-semibold text-indigo-700 dark:text-indigo-300 mb-1">CES 分析</h4>
                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{data.ces_analysis}</p>
                </div>
              )}

              {/* Traffic pools */}
              {data.traffic_pools?.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">流量池阶梯</h4>
                  <div className="space-y-1">
                    {data.traffic_pools.map((pool, i) => (
                      <motion.div
                        key={pool.name}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="flex items-center gap-2 text-xs px-2 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800/50"
                      >
                        <span className="font-medium text-slate-700 dark:text-slate-300">{pool.name}</span>
                        <span className="text-slate-400">→</span>
                        <span className="text-indigo-600 dark:text-indigo-400">{pool.exposure}</span>
                        <span className="ml-auto text-slate-400">门槛: {pool.threshold}</span>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}

              {/* Strengths & Weaknesses */}
              <div className="grid grid-cols-2 gap-3">
                {data.strengths?.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 mb-1.5">优势</h4>
                    <ul className="space-y-1">
                      {data.strengths.map((s, i) => (
                        <li key={i} className="text-[11px] text-slate-600 dark:text-slate-400 flex gap-1">
                          <span className="text-emerald-500 flex-shrink-0">✓</span> {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {data.weaknesses?.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-amber-600 dark:text-amber-400 mb-1.5">待优化</h4>
                    <ul className="space-y-1">
                      {data.weaknesses.map((w, i) => (
                        <li key={i} className="text-[11px] text-slate-600 dark:text-slate-400 flex gap-1">
                          <span className="text-amber-500 flex-shrink-0">△</span> {w}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Optimization tips */}
              {data.optimization_tips?.length > 0 && (
                <div className="p-3 rounded-xl bg-gradient-to-r from-violet-50 to-indigo-50 dark:from-violet-950/30 dark:to-indigo-950/30 border border-violet-100 dark:border-violet-900/50">
                  <h4 className="text-xs font-semibold text-violet-700 dark:text-violet-300 mb-1.5 flex items-center gap-1">
                    <Lightbulb className="w-3 h-3" /> 优化建议
                  </h4>
                  <ul className="space-y-1">
                    {data.optimization_tips.map((tip, i) => (
                      <li key={i} className="text-[11px] text-slate-600 dark:text-slate-400">{i + 1}. {tip}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
