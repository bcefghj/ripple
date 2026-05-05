import { motion, AnimatePresence } from 'framer-motion'
import { Brain, CheckCircle2, Loader2, Clock } from 'lucide-react'
import type { ThinkingStep, AgentStatus } from '../lib/api'

interface Props {
  steps: ThinkingStep[]
  collapsed?: boolean
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'done') return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
  if (status === 'running') return <Loader2 className="w-3.5 h-3.5 text-blue-500 animate-spin" />
  return <Clock className="w-3.5 h-3.5 text-slate-400" />
}

function AgentRow({ agent }: { agent: AgentStatus }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-center gap-2 text-xs py-0.5 pl-6"
    >
      <StatusIcon status={agent.status} />
      <span className={agent.status === 'done' ? 'text-slate-600 dark:text-slate-400' : 'text-slate-500 dark:text-slate-500'}>
        {agent.name}
      </span>
      {agent.count !== undefined && agent.status === 'done' && (
        <span className="text-emerald-600 dark:text-emerald-400 font-medium">({agent.count}条)</span>
      )}
    </motion.div>
  )
}

export default function ThinkingPanel({ steps }: Props) {
  if (!steps.length) return null

  const lastStep = steps[steps.length - 1]
  const progress = lastStep.progress || 0

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="mb-3 rounded-xl border border-blue-100 dark:border-blue-900/50 bg-blue-50/50 dark:bg-blue-950/20 overflow-hidden"
    >
      {/* Progress bar */}
      <div className="h-0.5 bg-blue-100 dark:bg-blue-900/30">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-500 to-violet-500"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>

      <div className="p-3">
        <div className="flex items-center gap-2 text-xs font-medium text-blue-700 dark:text-blue-300 mb-2">
          <Brain className="w-3.5 h-3.5" />
          <span>Ripple 正在思考</span>
        </div>

        <AnimatePresence>
          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="mb-1"
            >
              <div className="flex items-center gap-2 text-xs">
                {i < steps.length - 1 ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                ) : (
                  <Loader2 className="w-3.5 h-3.5 text-blue-500 animate-spin shrink-0" />
                )}
                <span className={`${i < steps.length - 1 ? 'text-slate-500 dark:text-slate-500' : 'text-slate-700 dark:text-slate-300 font-medium'}`}>
                  {step.detail}
                </span>
              </div>
              {step.agents && (
                <div className="mt-1 space-y-0.5">
                  {step.agents.map((agent, j) => (
                    <AgentRow key={j} agent={agent} />
                  ))}
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
