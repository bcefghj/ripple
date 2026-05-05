import { motion, AnimatePresence } from 'framer-motion'
import { useState, useEffect, useRef } from 'react'
import { ChevronDown, ChevronUp, MessageCircle, Zap } from 'lucide-react'
import type { AgentMessage } from '../lib/api'

interface Props {
  messages: AgentMessage[]
  arbiterThinking?: string
}

export default function MultiAgentPanel({ messages, arbiterThinking }: Props) {
  const [expanded, setExpanded] = useState(true)
  const [activeRound, setActiveRound] = useState<1 | 2>(1)

  if (!messages.length) return null

  const round1 = messages.filter(m => m.round === 1)
  const round2 = messages.filter(m => m.round === 2)
  const agents = new Map<string, typeof messages[0]['agent']>()
  for (const m of messages) {
    if (!agents.has(m.agent.id)) agents.set(m.agent.id, m.agent)
  }
  const agentList = Array.from(agents.values())
  const hasRound2 = round2.length > 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-3 rounded-2xl border border-slate-200 dark:border-slate-700 bg-gradient-to-br from-white to-slate-50 dark:from-slate-800 dark:to-slate-900 overflow-hidden shadow-lg"
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <div className="relative">
            <MessageCircle className="w-4 h-4 text-violet-500" />
            <motion.div
              className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-green-400"
              animate={{ scale: [1, 1.3, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
            />
          </div>
          <span>AI 专家圆桌会议</span>
          <span className="text-xs text-slate-400">{agentList.length} 位专家 · {messages.length} 条发言</span>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            {/* Roundtable avatar circle */}
            <div className="px-4 py-3">
              <RoundTableView agents={agentList} messages={messages} />
            </div>

            {/* Round tabs */}
            <div className="flex gap-1 px-4 mb-2">
              <button
                onClick={() => setActiveRound(1)}
                className={`flex-1 py-1.5 text-xs rounded-lg font-medium transition-colors ${
                  activeRound === 1
                    ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                }`}
              >
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-400 mr-1" />
                第一轮：独立分析
              </button>
              {hasRound2 && (
                <button
                  onClick={() => setActiveRound(2)}
                  className={`flex-1 py-1.5 text-xs rounded-lg font-medium transition-colors ${
                    activeRound === 2
                      ? 'bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                  }`}
                >
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-violet-400 mr-1" />
                  第二轮：交叉讨论
                </button>
              )}
            </div>

            {/* Messages */}
            <div className="px-4 pb-3 space-y-2 max-h-[500px] overflow-y-auto">
              {(activeRound === 1 ? round1 : round2).map((msg, i) => (
                <AgentBubble key={`r${activeRound}-${msg.agent.id}`} message={msg} delay={i * 0.05} />
              ))}
            </div>

            {/* Arbiter thinking */}
            {arbiterThinking && (
              <div className="px-4 pb-3">
                <ArbiterThinking content={arbiterThinking} />
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}


function RoundTableView({ agents, messages }: { agents: any[]; messages: AgentMessage[] }) {
  const n = agents.length
  const cx = 120
  const cy = 75
  const rx = 95
  const ry = 55

  const latestRound = messages.length > 0 ? Math.max(...messages.map(m => m.round)) : 0
  const lastSpeaker = messages.length > 0 ? messages[messages.length - 1].agent.id : ''

  const getAttitude = (agentId: string): string => {
    const agentMsgs = messages.filter(m => m.agent.id === agentId)
    if (!agentMsgs.length) return '思考中'
    const lastMsg = agentMsgs[agentMsgs.length - 1].content
    if (lastMsg.includes('看好')) return '看好'
    if (lastMsg.includes('谨慎')) return '谨慎'
    return '中立'
  }

  const attitudeColor: Record<string, string> = {
    '看好': '#10b981',
    '中立': '#f59e0b',
    '谨慎': '#ef4444',
    '思考中': '#94a3b8',
  }

  return (
    <div className="relative" style={{ height: cy * 2 + 10 }}>
      {/* Center topic */}
      <motion.div
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-16 h-16 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-300/30 dark:shadow-violet-900/30"
        animate={{ scale: [1, 1.05, 1] }}
        transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
      >
        <Zap className="w-6 h-6 text-white" />
      </motion.div>

      {/* Connecting lines to center */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox={`0 0 ${cx * 2} ${cy * 2 + 10}`}>
        {agents.map((agent, i) => {
          const angle = (2 * Math.PI * i) / n - Math.PI / 2
          const x = cx + rx * Math.cos(angle)
          const y = cy + 5 + ry * Math.sin(angle)
          const isSpeaking = agent.id === lastSpeaker
          return (
            <line
              key={agent.id}
              x1={cx} y1={cy + 5} x2={x} y2={y}
              stroke={isSpeaking ? agent.color : '#94a3b8'}
              strokeWidth={isSpeaking ? 2 : 0.5}
              strokeDasharray={isSpeaking ? '' : '3 3'}
              opacity={isSpeaking ? 0.6 : 0.2}
            />
          )
        })}
      </svg>

      {/* Agent avatars around circle */}
      {agents.map((agent, i) => {
        const angle = (2 * Math.PI * i) / n - Math.PI / 2
        const x = cx + rx * Math.cos(angle)
        const y = cy + 5 + ry * Math.sin(angle)
        const isSpeaking = agent.id === lastSpeaker
        const attitude = getAttitude(agent.id)

        return (
          <motion.div
            key={agent.id}
            className="absolute flex flex-col items-center"
            style={{ left: `${(x / (cx * 2)) * 100}%`, top: `${(y / (cy * 2 + 10)) * 100}%`, transform: 'translate(-50%, -50%)' }}
            animate={isSpeaking ? { scale: [1, 1.15, 1] } : {}}
            transition={isSpeaking ? { repeat: Infinity, duration: 1.5 } : {}}
          >
            <div className="relative">
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center text-sm shadow-md"
                style={{
                  backgroundColor: agent.color + '20',
                  border: `2px solid ${isSpeaking ? agent.color : agent.color + '40'}`,
                  boxShadow: isSpeaking ? `0 0 12px ${agent.color}40` : 'none',
                }}
              >
                {agent.emoji}
              </div>
              {/* Attitude indicator */}
              <div
                className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white dark:border-slate-800"
                style={{ backgroundColor: attitudeColor[attitude] }}
                title={attitude}
              />
            </div>
            <span className="text-[9px] mt-0.5 text-slate-500 dark:text-slate-400 whitespace-nowrap">{agent.name.slice(0, 4)}</span>
          </motion.div>
        )
      })}
    </div>
  )
}


function AgentBubble({ message, delay }: { message: AgentMessage; delay: number }) {
  const { agent, content } = message
  const [displayed, setDisplayed] = useState('')
  const [isTyping, setIsTyping] = useState(true)

  useEffect(() => {
    setDisplayed(content)
    setIsTyping(false)
  }, [content])

  const attitude = content.includes('看好') ? '看好' : content.includes('谨慎') ? '谨慎' : '中立'
  const attitudeStyle: Record<string, string> = {
    '看好': 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
    '中立': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    '谨慎': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay, duration: 0.3 }}
      className="flex gap-2"
    >
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center text-sm shrink-0 shadow-sm"
        style={{ backgroundColor: agent.color + '20', border: `2px solid ${agent.color}40` }}
      >
        {agent.emoji}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-0.5">
          <span className="text-xs font-semibold" style={{ color: agent.color }}>{agent.name}</span>
          {!isTyping && (
            <motion.span
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className={`text-[9px] px-1.5 py-0.5 rounded-full font-medium ${attitudeStyle[attitude]}`}
            >
              {attitude}
            </motion.span>
          )}
        </div>
        <div className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed bg-white dark:bg-slate-800 rounded-lg rounded-tl-sm px-3 py-2 border border-slate-100 dark:border-slate-700 shadow-sm">
          {displayed}
          {isTyping && (
            <span className="inline-flex gap-0.5 ml-1">
              <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
            </span>
          )}
        </div>
      </div>
    </motion.div>
  )
}


function ArbiterThinking({ content }: { content: string }) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [content])

  return (
    <motion.div
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-amber-200 dark:border-amber-800/50 bg-amber-50/50 dark:bg-amber-950/20 overflow-hidden"
    >
      <div className="flex items-center gap-2 px-3 py-2 border-b border-amber-100 dark:border-amber-900/30">
        <motion.div
          animate={{ rotate: [0, 360] }}
          transition={{ repeat: Infinity, duration: 3, ease: 'linear' }}
        >
          <Zap className="w-3.5 h-3.5 text-amber-500" />
        </motion.div>
        <span className="text-xs font-semibold text-amber-700 dark:text-amber-400">首席仲裁者正在思考...</span>
      </div>
      <div ref={scrollRef} className="px-3 py-2 max-h-40 overflow-y-auto">
        <p className="text-xs text-amber-800/70 dark:text-amber-300/60 leading-relaxed whitespace-pre-wrap">
          {content}
        </p>
      </div>
    </motion.div>
  )
}
