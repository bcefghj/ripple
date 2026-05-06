import { motion } from 'framer-motion'
import { Search, BookOpen, PenTool, Check } from 'lucide-react'
import type { ThinkingStep } from '../lib/api'

interface Props {
  stats?: any
  steps?: ThinkingStep[]
  isActive?: boolean
}

const PHASES = [
  { key: 'searching', label: '搜索中', icon: Search, color: 'text-blue-400' },
  { key: 'reading', label: '阅读分析', icon: BookOpen, color: 'text-amber-400' },
  { key: 'writing', label: '生成报告', icon: PenTool, color: 'text-emerald-400' },
]

function getCurrentPhase(steps?: ThinkingStep[]): number {
  if (!steps || steps.length === 0) return 0
  const lastStep = steps[steps.length - 1]
  if (lastStep.step?.includes('报告') || lastStep.step?.includes('综合')) return 2
  if (lastStep.step?.includes('图谱') || lastStep.step?.includes('分析') || lastStep.step?.includes('关联')) return 1
  return 0
}

export default function SearchRadar({ stats, steps, isActive }: Props) {
  if (!isActive && (!steps || steps.length === 0)) return null

  const currentPhase = isActive ? getCurrentPhase(steps) : 3

  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-4 px-4 py-3 rounded-xl bg-slate-800/60 border border-slate-700/40"
    >
      <div className="flex items-center gap-6">
        {PHASES.map((phase, i) => {
          const Icon = phase.icon
          const isDone = currentPhase > i
          const isCurrent = currentPhase === i && isActive
          
          return (
            <div key={phase.key} className="flex items-center gap-2">
              <div className={`relative flex items-center justify-center w-7 h-7 rounded-lg ${
                isDone ? 'bg-emerald-500/20' : isCurrent ? 'bg-slate-700' : 'bg-slate-800/50'
              }`}>
                {isDone ? (
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Icon className={`w-3.5 h-3.5 ${isCurrent ? phase.color : 'text-slate-500'}`} />
                )}
                {isCurrent && (
                  <motion.div
                    className="absolute inset-0 rounded-lg border border-current opacity-50"
                    style={{ color: phase.color.replace('text-', '').includes('blue') ? '#60a5fa' : phase.color.includes('amber') ? '#fbbf24' : '#34d399' }}
                    animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0, 0.5] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  />
                )}
              </div>
              <div className="flex flex-col">
                <span className={`text-xs font-medium ${isDone ? 'text-emerald-400' : isCurrent ? 'text-slate-200' : 'text-slate-500'}`}>
                  {phase.label}
                </span>
                {isCurrent && (
                  <span className="flex gap-0.5 mt-0.5">
                    {[0, 1, 2].map(dot => (
                      <motion.span
                        key={dot}
                        className="w-1 h-1 rounded-full bg-current"
                        style={{ color: phase.color.includes('blue') ? '#60a5fa' : phase.color.includes('amber') ? '#fbbf24' : '#34d399' }}
                        animate={{ opacity: [0.3, 1, 0.3] }}
                        transition={{ duration: 1, repeat: Infinity, delay: dot * 0.2 }}
                      />
                    ))}
                  </span>
                )}
              </div>
              {i < PHASES.length - 1 && (
                <div className={`w-8 h-px mx-1 ${isDone ? 'bg-emerald-500/50' : 'bg-slate-700'}`} />
              )}
            </div>
          )
        })}
      </div>

      {/* Show active agents */}
      {isActive && steps && steps.length > 0 && steps[steps.length - 1].agents && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-2.5 pt-2.5 border-t border-slate-700/40 flex flex-wrap gap-1.5"
        >
          {steps[steps.length - 1].agents!.map((agent, i) => (
            <span
              key={i}
              className={`text-[10px] px-2 py-0.5 rounded-full border ${
                agent.status === 'running'
                  ? 'border-blue-600/40 bg-blue-500/10 text-blue-300'
                  : agent.status === 'done'
                  ? 'border-emerald-600/40 bg-emerald-500/10 text-emerald-300'
                  : 'border-slate-700 bg-slate-800 text-slate-500'
              }`}
            >
              {agent.status === 'running' && (
                <motion.span
                  className="inline-block w-1.5 h-1.5 rounded-full bg-blue-400 mr-1"
                  animate={{ opacity: [1, 0.3, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                />
              )}
              {agent.name}
              {agent.count !== undefined && ` (${agent.count})`}
            </span>
          ))}
        </motion.div>
      )}

      {/* Progress summary */}
      {steps && steps.length > 0 && (
        <div className="mt-2 text-[11px] text-slate-400">
          {steps[steps.length - 1].detail}
        </div>
      )}
    </motion.div>
  )
}
