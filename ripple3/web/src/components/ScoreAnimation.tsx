import { motion, useMotionValue, useTransform, animate } from 'framer-motion'
import { useEffect, useState } from 'react'
import { Star, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface ScoreDimension {
  name: string
  score: number
  maxScore?: number
}

interface Props {
  totalScore: number
  dimensions: ScoreDimension[]
  hkrrDimensions?: ScoreDimension[]
  verdict?: string
}

function ScoreRing({ score, size = 140, strokeWidth = 10 }: { score: number; size?: number; strokeWidth?: number }) {
  const mv = useMotionValue(0)
  const [displayed, setDisplayed] = useState(0)
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius

  useEffect(() => {
    const controls = animate(mv, score, { duration: 2, ease: [0.34, 1.56, 0.64, 1] })
    const unsub = mv.on('change', v => setDisplayed(Math.round(v)))
    return () => { controls.stop(); unsub() }
  }, [score, mv])

  const strokeDashoffset = useTransform(mv, [0, 100], [circumference, 0])

  const getColor = (s: number) => {
    if (s >= 80) return '#10b981'
    if (s >= 60) return '#f59e0b'
    if (s >= 40) return '#f97316'
    return '#ef4444'
  }

  const getGlow = (s: number) => {
    if (s >= 80) return '0 0 20px rgba(16,185,129,0.3)'
    if (s >= 60) return '0 0 20px rgba(245,158,11,0.3)'
    return '0 0 20px rgba(239,68,68,0.3)'
  }

  return (
    <motion.div
      className="relative flex items-center justify-center"
      style={{ width: size, height: size }}
      initial={{ scale: 0, rotate: -180 }}
      animate={{ scale: 1, rotate: 0 }}
      transition={{ type: 'spring', damping: 12, stiffness: 100, delay: 0.2 }}
    >
      <svg width={size} height={size} className="-rotate-90" style={{ filter: `drop-shadow(${getGlow(score)})` }}>
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="currentColor"
          className="text-slate-200 dark:text-slate-700" strokeWidth={strokeWidth} />
        <motion.circle cx={size / 2} cy={size / 2} r={radius} fill="none"
          stroke={getColor(score)} strokeWidth={strokeWidth} strokeLinecap="round"
          strokeDasharray={circumference} style={{ strokeDashoffset }} />
        {/* Glow circle */}
        <motion.circle cx={size / 2} cy={size / 2} r={radius} fill="none"
          stroke={getColor(score)} strokeWidth={strokeWidth + 4} strokeLinecap="round"
          strokeDasharray={circumference} style={{ strokeDashoffset }}
          opacity={0.15} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          className="text-4xl font-black"
          style={{ fontVariantNumeric: 'tabular-nums', color: getColor(score) }}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          {displayed}
        </motion.span>
        <span className="text-[10px] text-slate-400 font-medium">/ 100</span>
      </div>
    </motion.div>
  )
}

function DimensionBar({ dim, delay }: { dim: ScoreDimension; delay: number }) {
  const max = dim.maxScore || 100
  const pct = dim.score / max * 100

  const getColor = (s: number) => {
    if (s >= 80) return 'from-emerald-400 to-emerald-500'
    if (s >= 60) return 'from-amber-400 to-amber-500'
    if (s >= 40) return 'from-orange-400 to-orange-500'
    return 'from-red-400 to-red-500'
  }

  const getGlowColor = (s: number) => {
    if (s >= 80) return 'rgba(16,185,129,0.3)'
    if (s >= 60) return 'rgba(245,158,11,0.3)'
    return 'rgba(239,68,68,0.3)'
  }

  return (
    <motion.div
      className="flex items-center gap-2 text-xs"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay, duration: 0.3 }}
    >
      <span className="w-20 text-right text-slate-600 dark:text-slate-400 shrink-0 truncate text-[11px]">{dim.name}</span>
      <div className="flex-1 h-6 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden relative">
        <motion.div
          className={`h-full rounded-full bg-gradient-to-r ${getColor(pct)} relative overflow-hidden`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, delay: delay + 0.2, ease: [0.34, 1.56, 0.64, 1] }}
          style={{ boxShadow: `0 0 8px ${getGlowColor(pct)}` }}
        >
          {/* Charging shimmer */}
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/25 to-transparent"
            animate={{ x: ['-100%', '200%'] }}
            transition={{ repeat: Infinity, duration: 2, delay: delay + 1, ease: 'easeInOut' }}
          />
        </motion.div>
        <motion.span
          className="absolute inset-y-0 right-2 flex items-center text-[11px] font-bold text-slate-700 dark:text-slate-300"
          style={{ fontVariantNumeric: 'tabular-nums' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: delay + 0.8 }}
        >
          {dim.score}
        </motion.span>
      </div>
    </motion.div>
  )
}

function RadarChart({ dimensions, size = 200 }: { dimensions: ScoreDimension[]; size?: number }) {
  const n = dimensions.length
  if (n < 3) return null

  const cx = size / 2
  const cy = size / 2
  const maxR = size / 2 - 30

  const angleStep = (2 * Math.PI) / n
  const levels = [0.25, 0.5, 0.75, 1.0]

  const getPoint = (i: number, r: number) => ({
    x: cx + r * Math.sin(i * angleStep),
    y: cy - r * Math.cos(i * angleStep),
  })

  const dataPoints = dimensions.map((d, i) => {
    const r = (d.score / (d.maxScore || 100)) * maxR
    return getPoint(i, r)
  })
  const dataPath = dataPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z'

  return (
    <svg width={size} height={size} className="mx-auto">
      {levels.map(l => {
        const pts = Array.from({ length: n }, (_, i) => getPoint(i, maxR * l))
        const path = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z'
        return <path key={l} d={path} fill="none" stroke="currentColor" className="text-slate-200 dark:text-slate-700" strokeWidth={0.5} />
      })}

      {dimensions.map((d, i) => {
        const end = getPoint(i, maxR)
        return (
          <g key={i}>
            <line x1={cx} y1={cy} x2={end.x} y2={end.y} stroke="currentColor" className="text-slate-200 dark:text-slate-700" strokeWidth={0.5} />
            <text x={getPoint(i, maxR + 14).x} y={getPoint(i, maxR + 14).y}
              textAnchor="middle" dominantBaseline="central"
              className="fill-slate-500 dark:fill-slate-400 text-[9px]">
              {d.name}
            </text>
          </g>
        )
      })}

      {/* Animated fill with pulse */}
      <motion.path
        d={dataPath}
        fill="rgba(59,130,246,0.12)"
        stroke="none"
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: [0, 1, 0.8], scale: [0, 1.05, 1] }}
        transition={{ duration: 1.5, ease: 'easeOut' }}
        style={{ transformOrigin: `${cx}px ${cy}px` }}
      />
      <motion.path
        d={dataPath}
        fill="none"
        stroke="#3B82F6"
        strokeWidth={2.5}
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 2, ease: 'easeOut' }}
      />
      {/* Inner glow pulse */}
      <motion.path
        d={dataPath}
        fill="none"
        stroke="#3B82F6"
        strokeWidth={6}
        opacity={0.1}
        initial={{ scale: 0 }}
        animate={{ scale: [1, 1.02, 1] }}
        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
        style={{ transformOrigin: `${cx}px ${cy}px` }}
      />

      {dataPoints.map((p, i) => (
        <motion.circle key={i} cx={p.x} cy={p.y} r={3} fill="#3B82F6"
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 + i * 0.1 }}
        />
      ))}
    </svg>
  )
}

function StarRating({ score }: { score: number }) {
  const stars = Math.round(score / 20)
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map(i => (
        <motion.div
          key={i}
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 + i * 0.15 }}
        >
          <Star
            className={`w-5 h-5 ${i <= stars ? 'text-amber-400 fill-amber-400' : 'text-slate-300 dark:text-slate-600'}`}
          />
        </motion.div>
      ))}
    </div>
  )
}

function VerdictBadge({ verdict }: { verdict: string }) {
  const isPositive = verdict.includes('推荐') || verdict.includes('值得')
  const isNegative = verdict.includes('不建议')

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ delay: 1.5, type: 'spring', stiffness: 400, damping: 15 }}
      className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-bold shadow-lg ${
        isPositive ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-emerald-200/50 dark:shadow-emerald-900/30' :
        isNegative ? 'bg-gradient-to-r from-red-500 to-rose-500 text-white shadow-red-200/50 dark:shadow-red-900/30' :
        'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-amber-200/50 dark:shadow-amber-900/30'
      }`}
    >
      {isPositive ? <TrendingUp className="w-5 h-5" /> :
       isNegative ? <TrendingDown className="w-5 h-5" /> :
       <Minus className="w-5 h-5" />}
      {verdict}
    </motion.div>
  )
}

export default function ScoreAnimation({ totalScore, dimensions, hkrrDimensions, verdict }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6 py-4"
    >
      {/* Top: ring + stars + verdict */}
      <div className="flex flex-col items-center gap-3">
        <ScoreRing score={totalScore} />
        <StarRating score={totalScore} />
        {verdict && <VerdictBadge verdict={verdict} />}
      </div>

      {/* Basic dimensions bar chart */}
      {dimensions.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wider">基础维度</h4>
          <div className="space-y-1.5">
            {dimensions.map((d, i) => (
              <DimensionBar key={d.name} dim={d} delay={0.3 + i * 0.08} />
            ))}
          </div>
        </div>
      )}

      {/* HKRR radar */}
      {hkrrDimensions && hkrrDimensions.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wider">HKRR 模型</h4>
          <RadarChart dimensions={hkrrDimensions} size={180} />
        </div>
      )}
    </motion.div>
  )
}

export { ScoreRing, DimensionBar, RadarChart, StarRating, VerdictBadge }
export type { ScoreDimension }
