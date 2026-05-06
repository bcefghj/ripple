import { motion } from 'framer-motion'
import type { AgentStatus as AgentStatusType } from '../lib/api'

interface Props {
  agents: AgentStatusType[]
}

export default function AgentStatusPanel({ agents }: Props) {
  if (!agents || agents.length === 0) return null
  
  return (
    <div className="flex items-center gap-2 px-4 py-2 overflow-x-auto">
      {agents.map((agent, i) => (
        <motion.div
          key={agent.name}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: i * 0.05 }}
          className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-slate-800/50 border border-slate-700/30 shrink-0"
        >
          <span className={`w-1.5 h-1.5 rounded-full ${
            agent.status === 'done' ? 'bg-emerald-400' :
            agent.status === 'running' ? 'bg-amber-400 animate-pulse' :
            'bg-slate-600'
          }`} />
          <span className="text-[10px] text-slate-400 whitespace-nowrap">{agent.name}</span>
          {agent.count && <span className="text-[10px] text-emerald-400">{agent.count}</span>}
        </motion.div>
      ))}
    </div>
  )
}
