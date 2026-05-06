import { motion } from 'framer-motion'
import type { ThinkingStep } from '../lib/api'

interface Props {
  steps: ThinkingStep[]
}

export default function ThinkingPanel({ steps }: Props) {
  if (!steps || steps.length === 0) return null

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="mb-4"
    >
      <div className="space-y-1.5">
        {steps.map((step, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50"
          >
            <div className={`w-1.5 h-1.5 rounded-full ${i === steps.length - 1 ? 'bg-violet-400 animate-pulse' : 'bg-emerald-400'}`} />
            <span className="text-xs text-slate-400">{step.step || step.detail}</span>
            {step.progress > 0 && (
              <div className="ml-auto w-16 h-1 rounded-full bg-slate-700 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${step.progress}%` }}
                  className="h-full rounded-full bg-gradient-to-r from-violet-500 to-cyan-500"
                />
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}
