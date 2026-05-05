import { motion } from 'framer-motion'
import { TrendingUp, Target, AlertTriangle, Lightbulb, Flame } from 'lucide-react'
import type { ViralScoreData } from '../lib/api'

interface Props {
  score: ViralScoreData
}

function ScoreRing({ value, max = 100 }: { value: number; max?: number }) {
  const pct = Math.min(value / max, 1)
  const color = pct >= 0.8 ? '#10b981' : pct >= 0.6 ? '#f59e0b' : '#ef4444'

  return (
    <div className="relative w-20 h-20">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
        <path
          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none" stroke="#e5e7eb" strokeWidth="3"
        />
        <motion.path
          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none" stroke={color} strokeWidth="3"
          strokeDasharray={`${pct * 100}, 100`}
          initial={{ strokeDasharray: '0, 100' }}
          animate={{ strokeDasharray: `${pct * 100}, 100` }}
          transition={{ duration: 1, ease: 'easeOut' }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-bold" style={{ color }}>{value}</span>
      </div>
    </div>
  )
}

function DimensionBar({ name, score, max }: { name: string; score: number; max: number }) {
  const pct = (score / max) * 100
  const color = pct >= 80 ? 'bg-emerald-500' : pct >= 60 ? 'bg-amber-500' : 'bg-red-400'

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-16 text-slate-600 dark:text-slate-400 truncate">{name}</span>
      <div className="flex-1 h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />
      </div>
      <span className="w-8 text-right font-medium text-slate-700 dark:text-slate-300 tabular-nums">
        {score}/{max}
      </span>
    </div>
  )
}

export default function ViralScorePanel({ score }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-4 rounded-xl border border-violet-100 dark:border-violet-900/40 bg-gradient-to-br from-white to-violet-50/30 dark:from-slate-900 dark:to-violet-950/10 p-4 shadow-sm"
    >
      <div className="flex items-center gap-2 mb-3">
        <Flame className="w-4 h-4 text-orange-500" />
        <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">CES 爆款潜力评分</h3>
        <span className="ml-auto text-[10px] px-2 py-0.5 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 rounded-full">
          {score.engagement_formula}
        </span>
      </div>

      <div className="flex gap-4 mb-4">
        <ScoreRing value={score.total_score} />
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-1.5 text-xs">
            <Target className="w-3 h-3 text-blue-500" />
            <span className="text-slate-600 dark:text-slate-400">预测流量池:</span>
            <span className="font-semibold text-slate-800 dark:text-slate-200">{score.predicted_pool}</span>
          </div>
          {score.pool_probability && (
            <div className="text-[11px] text-slate-500 dark:text-slate-400 pl-[18px]">
              {score.pool_probability}
            </div>
          )}
          {score.ces_analysis && (
            <div className="text-[11px] text-slate-600 dark:text-slate-400 mt-1 pl-[18px] line-clamp-2">
              {score.ces_analysis}
            </div>
          )}
        </div>
      </div>

      {score.dimensions && score.dimensions.length > 0 && (
        <div className="space-y-1.5 mb-3">
          {score.dimensions.map(d => (
            <DimensionBar key={d.id} name={d.name} score={d.score} max={d.max} />
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 text-xs">
        {score.strengths && score.strengths.length > 0 && (
          <div>
            <div className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium mb-1">
              <TrendingUp className="w-3 h-3" />
              <span>优势</span>
            </div>
            <ul className="space-y-0.5 text-slate-600 dark:text-slate-400">
              {score.strengths.map((s, i) => (
                <li key={i} className="flex items-start gap-1">
                  <span className="text-emerald-400 mt-0.5">+</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {score.weaknesses && score.weaknesses.length > 0 && (
          <div>
            <div className="flex items-center gap-1 text-amber-600 dark:text-amber-400 font-medium mb-1">
              <AlertTriangle className="w-3 h-3" />
              <span>不足</span>
            </div>
            <ul className="space-y-0.5 text-slate-600 dark:text-slate-400">
              {score.weaknesses.map((w, i) => (
                <li key={i} className="flex items-start gap-1">
                  <span className="text-amber-400 mt-0.5">-</span>
                  <span>{w}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {score.optimization_tips && score.optimization_tips.length > 0 && (
        <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-700/50">
          <div className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 font-medium mb-1">
            <Lightbulb className="w-3 h-3" />
            <span>优化建议</span>
          </div>
          <ul className="space-y-0.5 text-xs text-slate-600 dark:text-slate-400">
            {score.optimization_tips.map((tip, i) => (
              <li key={i}>💡 {tip}</li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  )
}
