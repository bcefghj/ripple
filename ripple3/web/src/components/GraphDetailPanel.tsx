import { motion, AnimatePresence } from 'framer-motion'
import { X, ExternalLink, Loader2, Network, ChevronRight } from 'lucide-react'
import { useState, useEffect } from 'react'
import type { GraphNode, GraphData } from '../lib/api'

interface Props {
  node: GraphNode | null
  graphData: GraphData
  onClose: () => void
  onExpand?: (node: GraphNode) => void
}

const TYPE_INFO: Record<string, { label: string; icon: string; description: string }> = {
  person: { label: '博主/达人', icon: '👤', description: '内容创作者' },
  topic: { label: '话题', icon: '💡', description: '内容主题' },
  platform: { label: '平台', icon: '📱', description: '社媒平台' },
  format: { label: '内容形式', icon: '📝', description: '内容类型' },
  audience: { label: '受众', icon: '👥', description: '目标用户' },
}

export default function GraphDetailPanel({ node, graphData, onClose, onExpand }: Props) {
  const [isExpanding, setIsExpanding] = useState(false)

  if (!node) return null

  const typeInfo = TYPE_INFO[node.type] || { label: node.type, icon: '📌', description: '' }

  const connections = graphData.links.filter(l => {
    const srcId = typeof l.source === 'string' ? l.source : (l.source as any).id
    const tgtId = typeof l.target === 'string' ? l.target : (l.target as any).id
    return srcId === node.id || tgtId === node.id
  })

  const connectedNodes = connections.map(l => {
    const srcId = typeof l.source === 'string' ? l.source : (l.source as any).id
    const tgtId = typeof l.target === 'string' ? l.target : (l.target as any).id
    const otherId = srcId === node.id ? tgtId : srcId
    const otherNode = graphData.nodes.find(n => n.id === otherId)
    return {
      node: otherNode,
      label: l.label,
      strength: l.strength,
      isSource: srcId === node.id,
    }
  }).filter(c => c.node)

  const handleExpand = async () => {
    if (isExpanding) return
    setIsExpanding(true)
    onExpand?.(node)
    setTimeout(() => setIsExpanding(false), 3000)
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, x: 300 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 300 }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="fixed right-0 top-0 bottom-0 w-80 bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-700 shadow-2xl z-50 overflow-y-auto"
      >
        {/* Header */}
        <div className="sticky top-0 bg-white/95 dark:bg-slate-900/95 backdrop-blur-sm border-b border-slate-100 dark:border-slate-800 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">{typeInfo.icon}</span>
            <div>
              <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">{node.name}</h3>
              <p className="text-[10px] text-slate-400">{typeInfo.label}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          {/* Node importance */}
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <div className="text-[10px] uppercase tracking-wider text-slate-400 mb-1">重要度</div>
              <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: node.color }}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(100, (node.val / 30) * 100)}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                />
              </div>
            </div>
            <span className="text-sm font-bold" style={{ color: node.color }}>{node.val}/30</span>
          </div>

          {/* Description */}
          {node.desc && (
            <div>
              <div className="text-[10px] uppercase tracking-wider text-slate-400 mb-1">描述</div>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{node.desc}</p>
            </div>
          )}

          {/* Color badge */}
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full shadow-inner" style={{ backgroundColor: node.color }} />
            <span className="text-xs text-slate-500">{node.color}</span>
          </div>

          {/* Expand button */}
          {onExpand && (
            <button
              onClick={handleExpand}
              disabled={isExpanding}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white text-sm font-medium shadow-lg shadow-indigo-200/50 dark:shadow-indigo-900/30 transition-all disabled:opacity-50"
            >
              {isExpanding ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  正在搜索关联内容...
                </>
              ) : (
                <>
                  <Network className="w-4 h-4" />
                  展开关联图谱
                </>
              )}
            </button>
          )}

          {/* Connections */}
          {connectedNodes.length > 0 && (
            <div>
              <div className="text-[10px] uppercase tracking-wider text-slate-400 mb-2">
                关联关系 ({connectedNodes.length})
              </div>
              <div className="space-y-1.5">
                {connectedNodes.map((conn, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-center gap-2 p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors group"
                  >
                    <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: conn.node!.color }} />
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium text-slate-700 dark:text-slate-300 truncate">
                        {conn.node!.name}
                      </div>
                      <div className="text-[10px] text-slate-400 flex items-center gap-1">
                        {conn.isSource ? (
                          <>{node.name} <ChevronRight className="w-2.5 h-2.5" /> {conn.label} <ChevronRight className="w-2.5 h-2.5" /> {conn.node!.name}</>
                        ) : (
                          <>{conn.node!.name} <ChevronRight className="w-2.5 h-2.5" /> {conn.label} <ChevronRight className="w-2.5 h-2.5" /> {node.name}</>
                        )}
                      </div>
                    </div>
                    <div className="text-[10px] text-slate-400 shrink-0">
                      {Math.round((conn.strength || 0.5) * 100)}%
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
