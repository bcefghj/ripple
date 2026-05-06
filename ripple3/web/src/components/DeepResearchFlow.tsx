import { useCallback, useEffect, useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  MarkerType,
  type Node,
  type Edge,
} from 'reactflow'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, Search, BarChart3, Users, Sparkles, FileText, Loader2 } from 'lucide-react'
import 'reactflow/dist/style.css'

export interface ThinkingStep {
  id: string
  label: string
  type: 'intent' | 'search' | 'analyze' | 'agent' | 'synthesize' | 'output'
  status: 'pending' | 'active' | 'done'
  detail?: string
  children?: string[]
}

interface Props {
  steps: ThinkingStep[]
  compact?: boolean
}

const TYPE_CONFIG: Record<ThinkingStep['type'], {
  icon: typeof Brain
  color: string
  bgColor: string
  borderColor: string
}> = {
  intent:     { icon: Brain,     color: '#a78bfa', bgColor: 'rgba(167,139,250,0.1)', borderColor: 'rgba(167,139,250,0.5)' },
  search:     { icon: Search,    color: '#22d3ee', bgColor: 'rgba(34,211,238,0.1)',  borderColor: 'rgba(34,211,238,0.5)' },
  analyze:    { icon: BarChart3, color: '#34d399', bgColor: 'rgba(52,211,153,0.1)',  borderColor: 'rgba(52,211,153,0.5)' },
  agent:      { icon: Users,     color: '#fbbf24', bgColor: 'rgba(251,191,36,0.1)',  borderColor: 'rgba(251,191,36,0.5)' },
  synthesize: { icon: Sparkles,  color: '#f472b6', bgColor: 'rgba(244,114,182,0.1)', borderColor: 'rgba(244,114,182,0.5)' },
  output:     { icon: FileText,  color: '#60a5fa', bgColor: 'rgba(96,165,250,0.1)',  borderColor: 'rgba(96,165,250,0.5)' },
}

function ThinkingNode({ data }: { data: { step: ThinkingStep } }) {
  const { step } = data
  const config = TYPE_CONFIG[step.type]
  const Icon = config.icon
  const isActive = step.status === 'active'
  const isDone = step.status === 'done'

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className="relative"
    >
      <div
        className="px-3 py-2 rounded-xl border backdrop-blur-sm flex items-center gap-2 min-w-[140px]"
        style={{
          background: config.bgColor,
          borderColor: isActive ? config.color : config.borderColor,
          boxShadow: isActive ? `0 0 20px ${config.color}40` : 'none',
        }}
      >
        <div className="relative">
          <Icon size={16} style={{ color: config.color }} />
          {isActive && (
            <motion.div
              className="absolute -inset-1 rounded-full"
              style={{ border: `2px solid ${config.color}` }}
              animate={{ scale: [1, 1.5, 1], opacity: [1, 0, 1] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
            />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-medium text-slate-200 truncate">{step.label}</div>
          {step.detail && (
            <div className="text-[10px] text-slate-400 truncate mt-0.5">{step.detail}</div>
          )}
        </div>
        {isActive && <Loader2 size={12} className="animate-spin text-slate-400" />}
        {isDone && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="w-4 h-4 rounded-full bg-emerald-500/20 flex items-center justify-center"
          >
            <div className="w-2 h-2 rounded-full bg-emerald-400" />
          </motion.div>
        )}
      </div>
    </motion.div>
  )
}

const nodeTypes = { thinking: ThinkingNode }

export default function DeepResearchFlow({ steps, compact }: Props) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  const buildGraph = useCallback(() => {
    const newNodes: Node[] = []
    const newEdges: Edge[] = []
    const cols = compact ? 2 : 3
    const xGap = compact ? 200 : 240
    const yGap = compact ? 80 : 100

    steps.forEach((step, i) => {
      const col = i % cols
      const row = Math.floor(i / cols)
      newNodes.push({
        id: step.id,
        type: 'thinking',
        position: { x: col * xGap, y: row * yGap },
        data: { step },
      })

      if (i > 0) {
        const parentId = step.children
          ? steps.find(s => s.children?.includes(step.id))?.id || steps[i - 1].id
          : steps[i - 1].id
        newEdges.push({
          id: `e-${parentId}-${step.id}`,
          source: parentId,
          target: step.id,
          animated: step.status === 'active',
          style: {
            stroke: step.status === 'done' ? '#34d399' : step.status === 'active' ? '#6366f1' : '#334155',
            strokeWidth: 1.5,
          },
          markerEnd: { type: MarkerType.ArrowClosed, width: 12, height: 12 },
        })
      }
    })

    setNodes(newNodes)
    setEdges(newEdges)
  }, [steps, compact, setNodes, setEdges])

  useEffect(() => {
    buildGraph()
  }, [buildGraph])

  const activeCount = steps.filter(s => s.status === 'done').length
  const totalCount = steps.length

  if (!steps.length) return null

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: compact ? 200 : 320 }}
      exit={{ opacity: 0, height: 0 }}
      className="w-full rounded-2xl border border-slate-700/50 bg-slate-900/80 backdrop-blur-xl overflow-hidden mb-4"
    >
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-700/50">
        <div className="flex items-center gap-2">
          <Brain size={14} className="text-violet-400" />
          <span className="text-xs font-medium text-slate-300">AI 深度研究进程</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-20 bg-slate-700 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-violet-500 to-cyan-500 rounded-full"
              animate={{ width: `${(activeCount / Math.max(totalCount, 1)) * 100}%` }}
            />
          </div>
          <span className="text-[10px] text-slate-500">{activeCount}/{totalCount}</span>
        </div>
      </div>
      <div style={{ height: compact ? 168 : 288 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          proOptions={{ hideAttribution: true }}
          minZoom={0.5}
          maxZoom={1.5}
          panOnDrag={false}
          zoomOnScroll={false}
          nodesDraggable={false}
        >
          <Background color="#1e293b" gap={20} size={1} />
        </ReactFlow>
      </div>
    </motion.div>
  )
}
