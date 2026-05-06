import { motion } from 'framer-motion'

interface Props {
  data?: any
}

export default function KOCGrowthDashboard({ data }: Props) {
  if (!data) return null
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-slate-700/50 bg-slate-900/80 p-4 mb-4"
    >
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm">📈</span>
        <span className="text-xs font-medium text-slate-300">KOC 增长路径</span>
      </div>
      {data.phases && (
        <div className="space-y-2">
          {data.phases.map((phase: any, i: number) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.15 }}
              className="flex items-start gap-2 p-2 rounded-lg bg-slate-800/50"
            >
              <div className="w-5 h-5 rounded-full bg-gradient-to-r from-violet-500 to-cyan-500 flex items-center justify-center text-[9px] text-white font-bold shrink-0 mt-0.5">
                {i + 1}
              </div>
              <div>
                <div className="text-xs text-slate-300 font-medium">{phase.title || `阶段 ${i+1}`}</div>
                <div className="text-[10px] text-slate-500 mt-0.5">{phase.description || ''}</div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  )
}
