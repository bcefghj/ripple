import { motion, AnimatePresence } from 'framer-motion'
import { Search, BarChart3, PenTool, Eye, Loader2, CheckCircle2, Clock } from 'lucide-react'
import type { AgentStatus as AgentStatusType } from '../lib/api'

const agentMeta: Record<string, { icon: typeof Search; color: string }> = {
  '同行内容': { icon: Search, color: 'text-blue-500' },
  '博主达人': { icon: Search, color: 'text-cyan-500' },
  '最新动态': { icon: Search, color: 'text-indigo-500' },
  '热搜趋势': { icon: Search, color: 'text-violet-500' },
  '竞品分析': { icon: BarChart3, color: 'text-amber-500' },
  '内容样本': { icon: Search, color: 'text-teal-500' },
  '博主资料': { icon: Search, color: 'text-pink-500' },
  '搜索 Agent': { icon: Search, color: 'text-blue-500' },
  '分析 Agent': { icon: BarChart3, color: 'text-amber-500' },
  '创作 Agent': { icon: PenTool, color: 'text-emerald-500' },
  '评审 Agent': { icon: Eye, color: 'text-violet-500' },
}

const defaultMeta = { icon: Search, color: 'text-slate-500' }

interface Props {
  agents: AgentStatusType[]
}

export default function AgentStatusPanel({ agents }: Props) {
  if (!agents.length) return null

  return (
    <div className="flex flex-wrap gap-2 px-2 py-2">
      <AnimatePresence>
        {agents.map((agent, i) => {
          const meta = agentMeta[agent.name] || defaultMeta
          const Icon = meta.icon

          return (
            <motion.div
              key={agent.name}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm text-xs"
            >
              <Icon className={`w-3.5 h-3.5 ${meta.color}`} />
              <span className="text-slate-700 dark:text-slate-300 font-medium">{agent.name}</span>
              {agent.status === 'running' && (
                <Loader2 className="w-3 h-3 text-blue-500 animate-spin" />
              )}
              {agent.status === 'done' && (
                <CheckCircle2 className="w-3 h-3 text-emerald-500" />
              )}
              {agent.status === 'pending' && (
                <Clock className="w-3 h-3 text-slate-400" />
              )}
              {agent.count !== undefined && (
                <span className="text-slate-400">{agent.count}</span>
              )}
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}
