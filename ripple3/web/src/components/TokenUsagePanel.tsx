import { motion } from 'framer-motion'
import type { TokenUsage } from '../lib/api'

interface Props {
  usage: TokenUsage
}

export default function TokenUsagePanel({ usage }: Props) {
  if (!usage) return null
  
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex items-center gap-3 px-3 py-2 mt-3 rounded-lg bg-slate-800/30 border border-slate-700/30"
    >
      <span className="text-[10px] text-slate-500">⚡ {(usage.elapsed_ms / 1000).toFixed(1)}s</span>
      <span className="text-[10px] text-slate-500">🔍 {usage.search_calls} 条数据</span>
      {usage.agent_rounds > 0 && <span className="text-[10px] text-slate-500">🤖 {usage.agent_rounds} 轮分析</span>}
    </motion.div>
  )
}
