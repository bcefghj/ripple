import { useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Brain, Search, BarChart3, Users, Sparkles, FileText, Check,
} from 'lucide-react'

interface ThinkingNode {
  id: string
  label: string
  type: 'intent' | 'search' | 'analyze' | 'agent' | 'synthesize' | 'output'
  status: 'pending' | 'active' | 'done'
  children?: string[]
}

interface Props {
  nodes: ThinkingNode[]
  currentStep: string
}

const TYPE_META: Record<ThinkingNode['type'], {
  icon: typeof Brain
  gradient: string
  glow: string
  accent: string
}> = {
  intent:     { icon: Brain,     gradient: 'from-violet-500/20 to-purple-600/20', glow: 'shadow-violet-500/30', accent: 'text-violet-400' },
  search:     { icon: Search,    gradient: 'from-blue-500/20 to-cyan-500/20',     glow: 'shadow-blue-500/30',   accent: 'text-blue-400' },
  analyze:    { icon: BarChart3, gradient: 'from-emerald-500/20 to-teal-500/20',  glow: 'shadow-emerald-500/30', accent: 'text-emerald-400' },
  agent:      { icon: Users,     gradient: 'from-amber-500/20 to-orange-500/20',  glow: 'shadow-amber-500/30', accent: 'text-amber-400' },
  synthesize: { icon: Sparkles,  gradient: 'from-pink-500/20 to-rose-500/20',     glow: 'shadow-pink-500/30',  accent: 'text-pink-400' },
  output:     { icon: FileText,  gradient: 'from-indigo-500/20 to-violet-500/20', glow: 'shadow-indigo-500/30', accent: 'text-indigo-400' },
}

function ConnectionLine({ isActive }: { isActive: boolean }) {
  return (
    <div className="flex items-center self-center w-10 shrink-0 -mx-1">
      <svg width="40" height="24" viewBox="0 0 40 24" className="overflow-visible">
        <line x1="0" y1="12" x2="40" y2="12" stroke={isActive ? '#6366f1' : '#334155'} strokeWidth="2" strokeDasharray="4 3" />
        {isActive && (
          <motion.circle
            cx="0"
            cy="12"
            r="3"
            fill="#818cf8"
            animate={{ cx: [0, 40] }}
            transition={{ duration: 1.2, repeat: Infinity, ease: 'linear' }}
          />
        )}
        <polygon
          points="34,8 40,12 34,16"
          fill={isActive ? '#6366f1' : '#334155'}
        />
      </svg>
    </div>
  )
}

function NodeCard({ node }: { node: ThinkingNode }) {
  const meta = TYPE_META[node.type]
  const Icon = meta.icon
  const isDone = node.status === 'done'
  const isActive = node.status === 'active'

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.8, y: 12 }}
      animate={{
        opacity: node.status === 'pending' ? 0.45 : 1,
        scale: 1,
        y: 0,
      }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      className={`
        relative shrink-0 w-[140px] rounded-xl p-3
        border backdrop-blur-md
        bg-gradient-to-br ${meta.gradient}
        ${isActive
          ? `border-indigo-500/50 shadow-lg ${meta.glow}`
          : isDone
            ? 'border-slate-700/40 shadow-md'
            : 'border-slate-800/40 shadow-sm'}
      `}
    >
      {isActive && (
        <motion.div
          className="absolute inset-0 rounded-xl border-2 border-indigo-400/40"
          animate={{ opacity: [0.3, 0.8, 0.3] }}
          transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
        />
      )}

      <div className="flex items-center gap-2 mb-2">
        <div className={`
          w-7 h-7 rounded-lg flex items-center justify-center
          ${isActive ? 'bg-indigo-500/20' : isDone ? 'bg-emerald-500/15' : 'bg-slate-700/30'}
        `}>
          {isDone ? (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 500 }}
            >
              <Check className="w-4 h-4 text-emerald-400" />
            </motion.div>
          ) : isActive ? (
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ repeat: Infinity, duration: 2.5, ease: 'easeInOut' }}
            >
              <Icon className={`w-4 h-4 ${meta.accent}`} />
            </motion.div>
          ) : (
            <Icon className="w-4 h-4 text-slate-500" />
          )}
        </div>

        <span className={`text-[10px] font-semibold uppercase tracking-wider ${
          isActive ? meta.accent : isDone ? 'text-slate-400' : 'text-slate-600'
        }`}>
          {node.type}
        </span>
      </div>

      <p className={`text-xs leading-relaxed ${
        isActive ? 'text-slate-200 font-medium' : isDone ? 'text-slate-400' : 'text-slate-600'
      }`}>
        {node.label}
      </p>

      {isActive && (
        <motion.div
          className="mt-2 flex gap-0.5 justify-center"
        >
          {[0, 1, 2, 3].map(i => (
            <motion.span
              key={i}
              className="w-1 h-1 rounded-full bg-indigo-400"
              animate={{ opacity: [0.2, 1, 0.2], scale: [0.8, 1.2, 0.8] }}
              transition={{ repeat: Infinity, duration: 1.4, delay: i * 0.15 }}
            />
          ))}
        </motion.div>
      )}
    </motion.div>
  )
}

export default function AIThinkingFlow({ nodes, currentStep }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!scrollRef.current) return
    const activeEl = scrollRef.current.querySelector('[data-active="true"]')
    if (activeEl) {
      activeEl.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
    }
  }, [currentStep])

  if (!nodes.length) return null

  const nodeMap = new Map(nodes.map(n => [n.id, n]))

  const roots = nodes.filter(n => {
    return !nodes.some(other => other.children?.includes(n.id))
  })

  function buildChain(nodeId: string): ThinkingNode[] {
    const chain: ThinkingNode[] = []
    let current = nodeMap.get(nodeId)
    while (current) {
      chain.push(current)
      const childId = current.children?.[0]
      current = childId ? nodeMap.get(childId) : undefined
    }
    return chain
  }

  const primaryChain = roots.length > 0 ? buildChain(roots[0].id) : nodes

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.4 }}
      className="mb-3 rounded-2xl border border-slate-800/60 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 overflow-hidden shadow-xl"
    >
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-slate-800/40">
        <motion.div
          animate={{ rotate: [0, 360] }}
          transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
        >
          <Brain className="w-4 h-4 text-indigo-400" />
        </motion.div>
        <span className="text-xs font-semibold bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
          AI 推理链路
        </span>
        <span className="text-[10px] text-slate-600 ml-auto tabular-nums">
          {nodes.filter(n => n.status === 'done').length}/{nodes.length} 完成
        </span>
      </div>

      <div
        ref={scrollRef}
        className="flex items-stretch gap-0 px-4 py-4 overflow-x-auto scrollbar-thin scrollbar-track-slate-900 scrollbar-thumb-slate-700"
      >
        {primaryChain.map((node, i) => {
          const isActive = node.id === currentStep || node.status === 'active'
          const prevDone = i > 0 && primaryChain[i - 1].status === 'done'
          const connectionActive = prevDone || isActive

          return (
            <div key={node.id} className="flex items-center" data-active={isActive || undefined}>
              {i > 0 && <ConnectionLine isActive={connectionActive} />}
              <NodeCard node={{ ...node, status: isActive && node.status !== 'done' ? 'active' : node.status }} />
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}
