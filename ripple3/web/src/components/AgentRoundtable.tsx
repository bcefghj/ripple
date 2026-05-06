import { motion, AnimatePresence } from 'framer-motion'
import { useState, useEffect, useRef } from 'react'
import { MessageCircle, Zap, Crown } from 'lucide-react'
import type { AgentMessage } from '../lib/api'

interface Props {
  messages: AgentMessage[]
  arbiterThinking?: string
}

const AGENT_POSITIONS = [
  { angle: 0, x: 0, y: -1 },
  { angle: 51, x: 0.78, y: -0.62 },
  { angle: 103, x: 0.97, y: 0.22 },
  { angle: 154, x: 0.43, y: 0.9 },
  { angle: 206, x: -0.43, y: 0.9 },
  { angle: 257, x: -0.97, y: 0.22 },
  { angle: 309, x: -0.78, y: -0.62 },
]

export default function AgentRoundtable({ messages, arbiterThinking }: Props) {
  const [activeAgent, setActiveAgent] = useState<string | null>(null)
  const [showMessages, setShowMessages] = useState(true)
  const containerRef = useRef<HTMLDivElement>(null)

  const agents = new Map<string, typeof messages[0]['agent']>()
  for (const m of messages) {
    if (!agents.has(m.agent.id)) agents.set(m.agent.id, m.agent)
  }
  const agentList = Array.from(agents.values())

  useEffect(() => {
    if (messages.length > 0) {
      const lastMsg = messages[messages.length - 1]
      setActiveAgent(lastMsg.agent.id)
      const timer = setTimeout(() => setActiveAgent(null), 3000)
      return () => clearTimeout(timer)
    }
  }, [messages.length])

  if (!messages.length) return null

  const radius = 90

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-4 rounded-2xl border border-slate-700/50 bg-slate-900/80 backdrop-blur-xl overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-700/50">
        <div className="flex items-center gap-2">
          <div className="relative">
            <MessageCircle size={14} className="text-violet-400" />
            <motion.div
              className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-green-400"
              animate={{ scale: [1, 1.4, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
            />
          </div>
          <span className="text-xs font-medium text-slate-300">AI 专家圆桌会议</span>
          <span className="text-[10px] text-slate-500">{agentList.length} 位专家 · {messages.length} 条发言</span>
        </div>
        <button
          onClick={() => setShowMessages(!showMessages)}
          className="text-[10px] text-slate-500 hover:text-slate-300 transition-colors"
        >
          {showMessages ? '收起' : '展开'}
        </button>
      </div>

      {/* Roundtable Visualization */}
      <div className="relative flex justify-center py-6">
        <div className="relative" style={{ width: radius * 2 + 80, height: radius * 2 + 80 }}>
          {/* Center glow */}
          <motion.div
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-16 h-16 rounded-full"
            style={{ background: 'radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%)' }}
            animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0.8, 0.5] }}
            transition={{ repeat: Infinity, duration: 3 }}
          />
          
          {/* Connection lines */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none">
            {agentList.map((agent, i) => {
              const pos = AGENT_POSITIONS[i % AGENT_POSITIONS.length]
              const cx = radius + 40
              const cy = radius + 40
              const x = cx + pos.x * radius
              const y = cy + pos.y * radius
              return (
                <motion.line
                  key={`line-${agent.id}`}
                  x1={cx} y1={cy} x2={x} y2={y}
                  stroke={activeAgent === agent.id ? '#6366f1' : '#334155'}
                  strokeWidth={activeAgent === agent.id ? 1.5 : 0.5}
                  strokeDasharray="4 4"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 0.5, delay: i * 0.1 }}
                />
              )
            })}
          </svg>

          {/* Agent avatars */}
          {agentList.map((agent, i) => {
            const pos = AGENT_POSITIONS[i % AGENT_POSITIONS.length]
            const x = (radius + 40) + pos.x * radius - 20
            const y = (radius + 40) + pos.y * radius - 20
            const isActive = activeAgent === agent.id
            const agentMsgs = messages.filter(m => m.agent.id === agent.id)

            return (
              <motion.div
                key={agent.id}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: i * 0.1, type: 'spring' }}
                className="absolute flex flex-col items-center"
                style={{ left: x, top: y, width: 40 }}
              >
                <div className="relative">
                  <motion.div
                    className="w-9 h-9 rounded-full flex items-center justify-center text-sm border-2"
                    style={{
                      borderColor: isActive ? (agent.color || '#6366f1') : '#334155',
                      background: isActive ? `${agent.color || '#6366f1'}20` : '#1e293b',
                      boxShadow: isActive ? `0 0 16px ${agent.color || '#6366f1'}40` : 'none',
                    }}
                    animate={isActive ? { scale: [1, 1.1, 1] } : {}}
                    transition={{ repeat: isActive ? Infinity : 0, duration: 1 }}
                  >
                    {agent.emoji || '🤖'}
                  </motion.div>
                  {isActive && (
                    <motion.div
                      className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-green-400 border border-slate-900"
                      animate={{ scale: [1, 1.3, 1] }}
                      transition={{ repeat: Infinity, duration: 0.8 }}
                    />
                  )}
                </div>
                <div className="text-[9px] text-slate-500 mt-1 truncate w-full text-center">
                  {agent.name}
                </div>
              </motion.div>
            )
          })}

          {/* Center label */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
            <Crown size={12} className="mx-auto text-amber-400 mb-0.5" />
            <div className="text-[9px] text-slate-500">仲裁中</div>
          </div>
        </div>
      </div>

      {/* Messages Feed */}
      <AnimatePresence>
        {showMessages && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-3 space-y-2 max-h-[300px] overflow-y-auto">
              {messages.slice(-6).map((msg, i) => (
                <motion.div
                  key={`${msg.agent.id}-${i}`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex gap-2 items-start"
                >
                  <div
                    className="w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0 border"
                    style={{ borderColor: msg.agent.color || '#6366f1', background: `${msg.agent.color || '#6366f1'}10` }}
                  >
                    {msg.agent.emoji || '🤖'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <span className="text-[10px] font-medium" style={{ color: msg.agent.color || '#6366f1' }}>
                        {msg.agent.name}
                      </span>
                      <span className="text-[9px] text-slate-600">{msg.agent.role}</span>
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-2">{msg.content}</p>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Arbiter thinking */}
            {arbiterThinking && (
              <div className="mx-4 mb-3 px-3 py-2 rounded-xl bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/20">
                <div className="flex items-center gap-1.5 mb-1">
                  <Zap size={10} className="text-amber-400" />
                  <span className="text-[10px] font-medium text-amber-300">仲裁官综合分析</span>
                </div>
                <p className="text-xs text-slate-400 line-clamp-3">{arbiterThinking}</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
