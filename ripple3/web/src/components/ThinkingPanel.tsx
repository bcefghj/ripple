import { motion, AnimatePresence } from 'framer-motion'
import { Brain, CheckCircle2, Loader2, Clock, Zap, Search, Database } from 'lucide-react'
import type { ThinkingStep, AgentStatus } from '../lib/api'

interface Props {
  steps: ThinkingStep[]
  collapsed?: boolean
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'done') return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
  if (status === 'running') return (
    <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}>
      <Loader2 className="w-3.5 h-3.5 text-blue-500" />
    </motion.div>
  )
  return <Clock className="w-3.5 h-3.5 text-slate-400" />
}

function AgentRow({ agent, index }: { agent: AgentStatus; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="flex items-center gap-2 text-xs py-1 pl-6"
    >
      <StatusIcon status={agent.status} />
      <span className={`flex-1 ${
        agent.status === 'done' ? 'text-slate-600 dark:text-slate-400' :
        agent.status === 'running' ? 'text-blue-600 dark:text-blue-400 font-medium' :
        'text-slate-400 dark:text-slate-600'
      }`}>
        {agent.name}
      </span>
      {agent.count !== undefined && agent.status === 'done' && (
        <motion.span
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-emerald-600 dark:text-emerald-400 font-semibold tabular-nums bg-emerald-50 dark:bg-emerald-900/20 px-1.5 py-0.5 rounded-full"
        >
          {agent.count}条
        </motion.span>
      )}
      {agent.status === 'running' && (
        <motion.div
          className="flex gap-0.5"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {[0, 1, 2].map(i => (
            <motion.span
              key={i}
              className="w-1 h-1 rounded-full bg-blue-400"
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ repeat: Infinity, duration: 1.2, delay: i * 0.2 }}
            />
          ))}
        </motion.div>
      )}
    </motion.div>
  )
}

function NeuralPulse() {
  return (
    <svg className="w-full h-6" viewBox="0 0 200 20" preserveAspectRatio="none">
      <motion.path
        d="M0,10 Q25,2 50,10 Q75,18 100,10 Q125,2 150,10 Q175,18 200,10"
        fill="none"
        stroke="url(#pulse-gradient)"
        strokeWidth="1.5"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: [0, 1, 0.5] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
      />
      <defs>
        <linearGradient id="pulse-gradient" x1="0" x2="1">
          <stop offset="0" stopColor="#3B82F6" stopOpacity="0" />
          <stop offset="0.5" stopColor="#8B5CF6" stopOpacity="1" />
          <stop offset="1" stopColor="#3B82F6" stopOpacity="0" />
        </linearGradient>
      </defs>
    </svg>
  )
}

export default function ThinkingPanel({ steps }: Props) {
  if (!steps.length) return null

  const lastStep = steps[steps.length - 1]
  const progress = lastStep.progress || 0
  const totalAgentsDone = steps.reduce((acc, s) => {
    return acc + (s.agents?.filter(a => a.status === 'done').length || 0)
  }, 0)

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="mb-3 rounded-xl border border-indigo-100 dark:border-indigo-900/50 bg-gradient-to-br from-indigo-50/50 to-violet-50/50 dark:from-indigo-950/20 dark:to-violet-950/20 overflow-hidden shadow-sm"
    >
      {/* Progress bar with glow */}
      <div className="h-1 bg-indigo-100 dark:bg-indigo-900/30 relative overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-500 via-violet-500 to-indigo-500"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
        <motion.div
          className="absolute top-0 h-full w-20 bg-gradient-to-r from-transparent via-white/30 to-transparent"
          animate={{ left: ['-20%', '120%'] }}
          transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
        />
      </div>

      <div className="p-3">
        {/* Header with neural pulse */}
        <div className="flex items-center gap-2 text-xs font-semibold text-indigo-700 dark:text-indigo-300 mb-1">
          <motion.div
            animate={{ rotate: [0, 15, -15, 0] }}
            transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
          >
            <Brain className="w-4 h-4" />
          </motion.div>
          <span>Ripple 神经网络</span>
          <span className="text-[10px] font-normal text-indigo-400 ml-auto tabular-nums">{progress}%</span>
        </div>

        <NeuralPulse />

        <AnimatePresence>
          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="mb-1.5"
            >
              <div className="flex items-center gap-2 text-xs">
                {i < steps.length - 1 ? (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 500 }}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                  </motion.div>
                ) : (
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ repeat: Infinity, duration: 1.5 }}
                  >
                    {step.detail.includes('搜索') ? (
                      <Search className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                    ) : step.detail.includes('图谱') ? (
                      <Database className="w-3.5 h-3.5 text-violet-500 shrink-0" />
                    ) : (
                      <Zap className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                    )}
                  </motion.div>
                )}
                <span className={`flex-1 ${i < steps.length - 1 ? 'text-slate-500 dark:text-slate-500' : 'text-slate-700 dark:text-slate-300 font-medium'}`}>
                  {step.detail}
                </span>
              </div>

              {/* Connector line between steps */}
              {i < steps.length - 1 && (
                <div className="ml-[7px] w-px h-2 bg-gradient-to-b from-emerald-300 to-transparent dark:from-emerald-700" />
              )}

              {step.agents && (
                <div className="mt-1 space-y-0">
                  {step.agents.map((agent, j) => (
                    <AgentRow key={j} agent={agent} index={j} />
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
