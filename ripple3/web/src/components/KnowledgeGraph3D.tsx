import { useRef, useCallback, useEffect, useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Maximize2, Minimize2, X, Network, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react'
import ForceGraph2D from 'react-force-graph-2d'
import type { GraphData, GraphNode } from '../lib/api'

interface Props {
  data: GraphData
  onClose?: () => void
  onNodeClick?: (node: GraphNode) => void
  isExpanding?: boolean
}

const TYPE_LABELS: Record<string, string> = {
  person: '博主/达人', topic: '话题', platform: '平台', format: '内容形式',
  audience: '受众', trend: '趋势', strategy: '策略', brand: '品牌',
  event: '事件', metric: '指标', keyword: '关键词', content: '内容',
}

const TYPE_COLORS: Record<string, string> = {
  person:   '#f472b6',
  topic:    '#60a5fa',
  platform: '#34d399',
  format:   '#fbbf24',
  audience: '#a78bfa',
  trend:    '#f87171',
  strategy: '#22d3ee',
  brand:    '#e879f9',
  event:    '#fb923c',
  metric:   '#4ade80',
  keyword:  '#38bdf8',
  content:  '#c084fc',
}

export default function KnowledgeGraph3D({ data, onClose, onNodeClick, isExpanding }: Props) {
  const graphRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [expanded, setExpanded] = useState(false)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [dimensions, setDimensions] = useState({ width: 600, height: 400 })
  const [hoveredNode, setHoveredNode] = useState<any>(null)

  const height = expanded ? 600 : 400

  useEffect(() => {
    if (!containerRef.current) return
    const obs = new ResizeObserver(entries => {
      for (const e of entries) {
        setDimensions({ width: e.contentRect.width, height })
      }
    })
    obs.observe(containerRef.current)
    return () => obs.disconnect()
  }, [height])

  const graphData = useMemo(() => {
    return {
      nodes: data.nodes.map(n => ({
        ...n,
        __size: Math.max(6, Math.sqrt(n.val || 10) * 2.5),
      })),
      links: data.links.map(l => ({
        ...l,
        __color: 'rgba(148, 163, 184, 0.3)',
      })),
    }
  }, [data])

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node)
    onNodeClick?.(node)
    if (graphRef.current) {
      graphRef.current.centerAt(node.x, node.y, 800)
      graphRef.current.zoom(2.5, 800)
    }
  }, [onNodeClick])

  const resetView = useCallback(() => {
    setSelectedNode(null)
    if (graphRef.current) {
      graphRef.current.zoomToFit(400, 40)
    }
  }, [])

  const zoomIn = useCallback(() => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom()
      graphRef.current.zoom(currentZoom * 1.5, 300)
    }
  }, [])

  const zoomOut = useCallback(() => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom()
      graphRef.current.zoom(currentZoom / 1.5, 300)
    }
  }, [])

  const nodeCanvasObject = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const size = node.__size || 8
    const isSelected = selectedNode?.id === node.id
    const isHovered = hoveredNode?.id === node.id
    const color = node.color || TYPE_COLORS[node.type] || '#60a5fa'
    const x = node.x || 0
    const y = node.y || 0

    // Node circle
    ctx.beginPath()
    ctx.arc(x, y, size, 0, 2 * Math.PI)
    ctx.fillStyle = color
    ctx.globalAlpha = isSelected || isHovered ? 1 : 0.85
    ctx.fill()

    // Border
    if (isSelected || isHovered) {
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 2 / globalScale
      ctx.stroke()

      // Glow effect
      ctx.beginPath()
      ctx.arc(x, y, size + 4 / globalScale, 0, 2 * Math.PI)
      ctx.strokeStyle = color
      ctx.globalAlpha = 0.3
      ctx.lineWidth = 3 / globalScale
      ctx.stroke()
    }

    ctx.globalAlpha = 1

    // Label
    const label = node.name || ''
    const fontSize = Math.max(10 / globalScale, 3)
    ctx.font = `600 ${fontSize}px "Inter", system-ui, sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'

    // Label background
    const textWidth = ctx.measureText(label).width
    const padding = 2 / globalScale
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)'
    ctx.fillRect(
      x - textWidth / 2 - padding,
      y + size + 2 / globalScale,
      textWidth + padding * 2,
      fontSize + padding * 2
    )

    // Label text
    ctx.fillStyle = '#e2e8f0'
    ctx.fillText(label, x, y + size + 2 / globalScale + padding)

    // Type badge (small)
    if (globalScale > 1.2) {
      const typeLabel = TYPE_LABELS[node.type] || node.type
      const typeFontSize = Math.max(8 / globalScale, 2.5)
      ctx.font = `400 ${typeFontSize}px "Inter", system-ui, sans-serif`
      ctx.fillStyle = color
      ctx.globalAlpha = 0.7
      ctx.fillText(typeLabel, x, y + size + fontSize + 6 / globalScale)
      ctx.globalAlpha = 1
    }
  }, [selectedNode, hoveredNode])

  const linkCanvasObject = useCallback((link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const start = link.source
    const end = link.target
    if (!start || !end || typeof start.x !== 'number') return

    // Draw line
    ctx.beginPath()
    ctx.moveTo(start.x, start.y)
    ctx.lineTo(end.x, end.y)
    ctx.strokeStyle = 'rgba(100, 116, 139, 0.25)'
    ctx.lineWidth = Math.max(0.5, (link.strength || 0.5) * 1.5 / globalScale)
    ctx.stroke()

    // Draw label if zoomed in enough
    if (globalScale > 1.0 && link.label) {
      const midX = (start.x + end.x) / 2
      const midY = (start.y + end.y) / 2
      const fontSize = Math.max(7 / globalScale, 2.5)
      ctx.font = `400 ${fontSize}px "Inter", system-ui, sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'

      const textWidth = ctx.measureText(link.label).width
      const padding = 1.5 / globalScale
      ctx.fillStyle = 'rgba(15, 23, 42, 0.75)'
      ctx.fillRect(midX - textWidth / 2 - padding, midY - fontSize / 2 - padding, textWidth + padding * 2, fontSize + padding * 2)

      ctx.fillStyle = 'rgba(148, 163, 184, 0.8)'
      ctx.fillText(link.label, midX, midY)
    }
  }, [])

  if (!data.nodes.length) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-4 rounded-xl border border-slate-700/50 bg-slate-900/90 overflow-hidden shadow-lg"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-700/40 bg-slate-800/50">
        <div className="flex items-center gap-2 text-sm">
          <Network className="w-4 h-4 text-violet-400" />
          <span className="font-medium text-slate-200">知识图谱</span>
          <span className="text-xs text-slate-500">
            {data.nodes.length} 实体 · {data.links.length} 关系
          </span>
          {isExpanding && (
            <motion.span
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
              className="text-xs text-amber-400"
            >
              扩展中...
            </motion.span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button onClick={zoomIn} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-all" title="放大">
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button onClick={zoomOut} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-all" title="缩小">
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button onClick={resetView} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-all" title="重置">
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <button onClick={() => setExpanded(!expanded)} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-all">
            {expanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
          {onClose && (
            <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-all">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Graph */}
      <div ref={containerRef} className="relative" style={{ height }}>
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          width={dimensions.width}
          height={height}
          backgroundColor="rgba(2,6,23,1)"
          nodeCanvasObject={nodeCanvasObject}
          nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
            const size = node.__size || 8
            ctx.beginPath()
            ctx.arc(node.x, node.y, size + 4, 0, 2 * Math.PI)
            ctx.fillStyle = color
            ctx.fill()
          }}
          linkCanvasObject={linkCanvasObject}
          onNodeClick={handleNodeClick}
          onNodeHover={(node: any) => setHoveredNode(node || null)}
          cooldownTicks={100}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
          warmupTicks={50}
          enableNodeDrag
          enableZoomInteraction
          enablePanInteraction
        />

        {/* Legend */}
        <div className="absolute top-2 right-2 flex flex-wrap gap-1 max-w-[180px]">
          {Object.entries(TYPE_COLORS).map(([type, color]) => {
            const count = data.nodes.filter(n => n.type === type).length
            if (!count) return null
            return (
              <span key={type} className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-slate-900/80 text-slate-400">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                {TYPE_LABELS[type] || type}
              </span>
            )
          })}
        </div>

        {/* Hint */}
        <div className="absolute bottom-2 left-2 text-[10px] text-slate-500 px-2 py-1 rounded bg-slate-900/70">
          拖拽移动 · 滚轮缩放 · 点击节点查看详情
        </div>
      </div>

      {/* Selected node detail */}
      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-slate-700/40 px-4 py-3 bg-slate-800/50"
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: selectedNode.color || TYPE_COLORS[selectedNode.type] }} />
              <span className="text-sm font-medium text-slate-200">{selectedNode.name}</span>
              <span className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-400">
                {TYPE_LABELS[selectedNode.type] || selectedNode.type}
              </span>
              <button onClick={() => setSelectedNode(null)} className="ml-auto text-slate-500 hover:text-slate-300">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            {selectedNode.desc && (
              <p className="text-xs text-slate-400 mb-2">{selectedNode.desc}</p>
            )}
            <div className="flex flex-wrap gap-1.5">
              {data.links
                .filter(l => {
                  const s = typeof l.source === 'string' ? l.source : (l.source as any).id
                  const t = typeof l.target === 'string' ? l.target : (l.target as any).id
                  return s === selectedNode.id || t === selectedNode.id
                })
                .slice(0, 8)
                .map((link, i) => {
                  const s = typeof link.source === 'string' ? link.source : (link.source as any).id
                  const t = typeof link.target === 'string' ? link.target : (link.target as any).id
                  const otherId = s === selectedNode.id ? t : s
                  const otherNode = data.nodes.find(n => n.id === otherId)
                  return (
                    <span key={i} className="text-[11px] px-2 py-1 rounded-lg bg-slate-700/50 text-slate-300 border border-slate-600/30">
                      <span className="text-slate-500">{link.label}</span> → {otherNode?.name || otherId}
                    </span>
                  )
                })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
