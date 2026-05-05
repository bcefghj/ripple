import { motion } from 'framer-motion'
import { Zap, Clock, Search, MessageSquare } from 'lucide-react'
import type { TokenUsage } from '../lib/api'

interface Props {
  usage: TokenUsage
}

export default function TokenUsagePanel({ usage }: Props) {
  const elapsed = usage.elapsed_ms > 0 ? (usage.elapsed_ms / 1000).toFixed(1) : '—'

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-3 p-3 rounded-lg bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/20 dark:to-orange-950/20 border border-amber-200/50 dark:border-amber-800/30"
    >
      <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-700 dark:text-amber-300 mb-2">
        <Zap className="w-3.5 h-3.5" />
        <span>本次分析消耗</span>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div className="flex items-center gap-1.5">
          <Search className="w-3 h-3 text-blue-500" />
          <div>
            <div className="text-xs text-slate-500 dark:text-slate-400">搜索调用</div>
            <div className="text-sm font-bold text-slate-700 dark:text-slate-200 tabular-nums">
              {usage.search_calls}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <MessageSquare className="w-3 h-3 text-violet-500" />
          <div>
            <div className="text-xs text-slate-500 dark:text-slate-400">Agent轮次</div>
            <div className="text-sm font-bold text-slate-700 dark:text-slate-200 tabular-nums">
              {usage.agent_rounds}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <Clock className="w-3 h-3 text-emerald-500" />
          <div>
            <div className="text-xs text-slate-500 dark:text-slate-400">耗时</div>
            <div className="text-sm font-bold text-slate-700 dark:text-slate-200 tabular-nums">
              {elapsed}s
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
