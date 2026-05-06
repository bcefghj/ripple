import { motion } from 'framer-motion'

interface Props {
  engines?: Record<string, number>
  totalResults?: number
  isActive?: boolean
  count?: number
}

export default function DataUniverseParticles({ engines, totalResults, isActive, count }: Props) {
  const total = totalResults || count || 0
  if (total === 0 && !engines) return null

  const engineEntries = Object.entries(engines || {})
  const maxCount = Math.max(...engineEntries.map(([, c]) => c), 1)

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-slate-700/50 bg-slate-900/80 p-4 mb-3 overflow-hidden relative"
    >
      {/* Ambient glow */}
      {isActive && (
        <motion.div
          animate={{ opacity: [0.1, 0.3, 0.1] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-transparent to-violet-500/5 pointer-events-none"
        />
      )}

      <div className="flex items-center gap-2 mb-3 relative">
        <motion.div
          animate={isActive ? { scale: [1, 1.2, 1] } : {}}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="w-2 h-2 rounded-full bg-cyan-400"
        />
        <span className="text-xs font-medium text-slate-300">数据收集</span>
        <motion.span
          key={total}
          initial={{ scale: 1.3, color: '#22d3ee' }}
          animate={{ scale: 1, color: '#94a3b8' }}
          className="text-xs text-slate-400 ml-auto font-mono"
        >
          {total} 条
        </motion.span>
      </div>

      {/* Engine bars */}
      {engineEntries.length > 0 && (
        <div className="space-y-1.5 relative">
          {engineEntries.map(([name, cnt], idx) => (
            <motion.div
              key={name}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1, type: 'spring', stiffness: 200 }}
              className="flex items-center gap-2"
            >
              <span className="text-[10px] text-slate-500 w-20 truncate">{name}</span>
              <div className="flex-1 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(cnt / maxCount) * 100}%` }}
                  transition={{ delay: idx * 0.1 + 0.2, duration: 0.6, ease: 'easeOut' }}
                  className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-violet-500"
                />
              </div>
              <span className="text-[10px] text-cyan-400 font-mono w-6 text-right">{cnt}</span>
            </motion.div>
          ))}
        </div>
      )}

      {/* Particle dots animation */}
      {isActive && (
        <div className="flex justify-center gap-1 mt-3 pt-2 border-t border-slate-800/50">
          {[...Array(7)].map((_, i) => (
            <motion.span
              key={i}
              animate={{
                y: [0, -4, 0],
                opacity: [0.3, 1, 0.3],
              }}
              transition={{ duration: 1.2, delay: i * 0.1, repeat: Infinity }}
              className="w-1 h-1 rounded-full bg-cyan-400"
            />
          ))}
        </div>
      )}
    </motion.div>
  )
}
