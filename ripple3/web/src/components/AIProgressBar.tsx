import { motion } from 'framer-motion'
import { Search, GitBranch, FileText } from 'lucide-react'

interface Props {
  phase: 'idle' | 'searching' | 'graphing' | 'reporting' | 'done'
  progress?: number
}

const PHASES = [
  { key: 'searching', label: '搜索中', icon: Search, color: 'from-cyan-500 to-blue-500' },
  { key: 'graphing', label: '构建图谱', icon: GitBranch, color: 'from-violet-500 to-purple-500' },
  { key: 'reporting', label: '生成报告', icon: FileText, color: 'from-emerald-500 to-teal-500' },
] as const

export default function AIProgressBar({ phase, progress = 0 }: Props) {
  if (phase === 'idle' || phase === 'done') return null

  const phaseIndex = PHASES.findIndex(p => p.key === phase)

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="px-4 py-2 border-b border-slate-800/50"
    >
      <div className="max-w-3xl mx-auto">
        {/* Phase indicators */}
        <div className="flex items-center gap-1 mb-2">
          {PHASES.map((p, i) => {
            const Icon = p.icon
            const isActive = i === phaseIndex
            const isDone = i < phaseIndex

            return (
              <div key={p.key} className="flex items-center gap-1 flex-1">
                <motion.div
                  animate={isActive ? { scale: [1, 1.1, 1] } : {}}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-[10px] font-medium transition-all ${
                    isActive
                      ? 'bg-slate-800 border border-slate-700/50 text-slate-200'
                      : isDone
                        ? 'text-emerald-400'
                        : 'text-slate-600'
                  }`}
                >
                  <Icon className="w-3 h-3" />
                  <span>{p.label}</span>
                  {isDone && <span className="text-emerald-400">✓</span>}
                </motion.div>
                {i < PHASES.length - 1 && (
                  <div className={`flex-1 h-px ${isDone ? 'bg-emerald-500/50' : 'bg-slate-800'}`} />
                )}
              </div>
            )
          })}
        </div>

        {/* Progress bar with shimmer */}
        <div className="relative h-0.5 rounded-full bg-slate-800 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className={`absolute inset-y-0 left-0 rounded-full bg-gradient-to-r ${PHASES[phaseIndex]?.color || 'from-cyan-500 to-blue-500'}`}
          />
          <motion.div
            animate={{ x: ['-100%', '200%'] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            className="absolute inset-y-0 w-1/4 bg-gradient-to-r from-transparent via-white/30 to-transparent"
          />
        </div>
      </div>
    </motion.div>
  )
}
