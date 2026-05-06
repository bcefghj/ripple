import { motion, AnimatePresence } from 'framer-motion'
import type { ThinkingStep } from '../lib/api'

interface Props {
  stats?: { total_raw: number; total_deduped: number; engines: Record<string, number> }
  steps?: ThinkingStep[]
  isActive?: boolean
}

export default function SearchRadar({ stats, steps, isActive }: Props) {
  if (!stats && (!steps || steps.length === 0)) return null

  const engines = Object.entries(stats?.engines || {})
  const currentStep = steps?.[steps.length - 1]
  const progress = currentStep?.progress || 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-slate-700/50 bg-slate-900/80 p-4 mb-4 overflow-hidden"
    >
      {/* Progress bar */}
      <div className="relative h-1 rounded-full bg-slate-800 mb-3 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-violet-500 via-cyan-500 to-emerald-500"
        />
        {isActive && (
          <motion.div
            animate={{ x: ['0%', '200%'] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
            className="absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-white/20 to-transparent"
          />
        )}
      </div>

      {/* Current phase */}
      <div className="flex items-center gap-2 mb-3">
        {isActive ? (
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        ) : (
          <div className="w-2 h-2 rounded-full bg-emerald-400" />
        )}
        <span className="text-xs font-medium text-slate-300">
          {currentStep?.step || '搜索引擎矩阵'}
        </span>
        {stats && (
          <span className="text-xs text-slate-500 ml-auto">
            {stats.total_deduped} 条数据
          </span>
        )}
      </div>

      {/* Engine status list */}
      <AnimatePresence>
        {engines.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="flex flex-wrap gap-1.5"
          >
            {engines.map(([name, count], idx) => (
              <motion.span
                key={name}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: idx * 0.08, type: 'spring', stiffness: 300 }}
                className="px-2 py-1 rounded-md text-[10px] bg-slate-800 border border-slate-700/50 text-slate-400 flex items-center gap-1"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                {name}
                <span className="text-emerald-400 font-medium">{count}</span>
              </motion.span>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Thinking steps timeline */}
      {steps && steps.length > 1 && (
        <div className="mt-3 pt-3 border-t border-slate-800/50 space-y-1">
          {steps.slice(-4).map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-center gap-2 text-[10px]"
            >
              <span className={`w-1 h-1 rounded-full ${
                i === steps.slice(-4).length - 1 && isActive
                  ? 'bg-violet-400 animate-pulse'
                  : 'bg-slate-600'
              }`} />
              <span className="text-slate-500">{step.step}</span>
              <span className="text-slate-600 truncate">{step.detail}</span>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  )
}
