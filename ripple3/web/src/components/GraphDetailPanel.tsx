import { motion } from 'framer-motion'
import type { GraphNode, GraphData } from '../lib/api'

interface Props {
  node: GraphNode | null
  graphData?: GraphData
  onClose?: () => void
  onExpand?: (node: GraphNode) => void
  isExpanding?: boolean
}

export default function GraphDetailPanel({ node, graphData, onClose, onExpand, isExpanding }: Props) {
  if (!node) return null

  const connectedNodes = graphData?.links
    .filter(l => {
      const src = typeof l.source === 'string' ? l.source : (l.source as any).id
      const tgt = typeof l.target === 'string' ? l.target : (l.target as any).id
      return src === node.id || tgt === node.id
    })
    .map(l => {
      const src = typeof l.source === 'string' ? l.source : (l.source as any).id
      const otherId = src === node.id
        ? (typeof l.target === 'string' ? l.target : (l.target as any).id)
        : src
      const otherNode = graphData?.nodes.find(n => n.id === otherId)
      return { label: l.label, node: otherNode }
    })
    .filter(x => x.node) || []

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="w-64 shrink-0 rounded-xl border border-slate-700/50 bg-slate-900/95 backdrop-blur-xl p-4 shadow-xl self-start sticky top-4"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: node.color }} />
          <span className="text-sm font-medium text-slate-200 truncate">{node.name}</span>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-xs text-slate-500 hover:text-slate-300 transition-colors p-1">
            ✕
          </button>
        )}
      </div>

      <div className="flex items-center gap-2 mb-3">
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-500 border border-slate-700/30">
          {node.type}
        </span>
        <span className="text-[10px] text-slate-600">权重: {node.val}</span>
      </div>

      {node.desc && (
        <p className="text-xs text-slate-400 mb-3 leading-relaxed">{node.desc}</p>
      )}

      {connectedNodes.length > 0 && (
        <div className="mb-3">
          <p className="text-[10px] text-slate-500 font-medium mb-1.5">关联节点 ({connectedNodes.length})</p>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {connectedNodes.slice(0, 8).map((conn, i) => (
              <div key={i} className="flex items-center gap-1.5 text-[10px]">
                <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: conn.node!.color }} />
                <span className="text-slate-400 truncate">{conn.node!.name}</span>
                <span className="text-slate-600 ml-auto shrink-0">{conn.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {onExpand && (
        <button
          onClick={() => onExpand(node)}
          disabled={isExpanding}
          className="w-full text-xs px-3 py-2 rounded-lg bg-violet-600/20 border border-violet-500/30 text-violet-300 hover:bg-violet-600/30 disabled:opacity-50 transition-colors flex items-center justify-center gap-1.5"
        >
          {isExpanding ? (
            <>
              <motion.span animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>⟳</motion.span>
              扩展中...
            </>
          ) : (
            <>🔍 深入探索此节点</>
          )}
        </button>
      )}
    </motion.div>
  )
}
