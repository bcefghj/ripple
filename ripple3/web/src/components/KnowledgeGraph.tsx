import { useRef, useCallback, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Maximize2, Minimize2, X, Network } from 'lucide-react'
import type { GraphData, GraphNode } from '../lib/api'

interface Props {
  data: GraphData
  onClose?: () => void
}

const TYPE_LABELS: Record<string, string> = {
  person: '博主/达人',
  topic: '话题',
  platform: '平台',
  format: '内容形式',
  audience: '受众',
}

export default function KnowledgeGraph({ data, onClose }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [expanded, setExpanded] = useState(false)
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })
  const nodesRef = useRef<(GraphNode & { x: number; y: number; vx: number; vy: number })[]>([])
  const animRef = useRef<number>(0)
  const mouseRef = useRef({ x: -1000, y: -1000 })

  const height = expanded ? 500 : 300

  useEffect(() => {
    if (!containerRef.current) return
    const obs = new ResizeObserver(entries => {
      for (const entry of entries) {
        setDimensions({ width: entry.contentRect.width, height })
      }
    })
    obs.observe(containerRef.current)
    return () => obs.disconnect()
  }, [height])

  useEffect(() => {
    if (!data.nodes.length || !canvasRef.current || !dimensions.width) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')!
    const W = dimensions.width
    const H = height
    canvas.width = W * window.devicePixelRatio
    canvas.height = H * window.devicePixelRatio
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio)

    const nodes = data.nodes.map((n) => ({
      ...n,
      x: W / 2 + (Math.random() - 0.5) * W * 0.6,
      y: H / 2 + (Math.random() - 0.5) * H * 0.6,
      vx: 0,
      vy: 0,
    }))
    nodesRef.current = nodes

    const nodeMap = new Map(nodes.map(n => [n.id, n]))
    const links = data.links
      .filter(l => nodeMap.has(l.source as string) && nodeMap.has(l.target as string))
      .map(l => ({
        ...l,
        sourceNode: nodeMap.get(l.source as string)!,
        targetNode: nodeMap.get(l.target as string)!,
      }))

    let tick = 0

    function simulate() {
      const alpha = Math.max(0.01, 0.3 * Math.exp(-tick * 0.02))

      for (const n of nodes) {
        n.vx *= 0.85
        n.vy *= 0.85
      }

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x
          const dy = nodes[j].y - nodes[i].y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          const force = (150 * alpha) / dist
          const fx = (dx / dist) * force
          const fy = (dy / dist) * force
          nodes[i].vx -= fx
          nodes[i].vy -= fy
          nodes[j].vx += fx
          nodes[j].vy += fy
        }
      }

      for (const l of links) {
        const dx = l.targetNode.x - l.sourceNode.x
        const dy = l.targetNode.y - l.sourceNode.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const target_dist = 80 + (1 - l.strength) * 60
        const force = (dist - target_dist) * 0.02 * alpha
        const fx = (dx / dist) * force
        const fy = (dy / dist) * force
        l.sourceNode.vx += fx
        l.sourceNode.vy += fy
        l.targetNode.vx -= fx
        l.targetNode.vy -= fy
      }

      for (const n of nodes) {
        const cx = (n.x - W / 2) * 0.005 * alpha
        const cy = (n.y - H / 2) * 0.005 * alpha
        n.vx -= cx
        n.vy -= cy
      }

      for (const n of nodes) {
        n.x += n.vx
        n.y += n.vy
        n.x = Math.max(20, Math.min(W - 20, n.x))
        n.y = Math.max(20, Math.min(H - 20, n.y))
      }

      tick++
    }

    function draw() {
      ctx.clearRect(0, 0, W, H)

      for (const l of links) {
        ctx.beginPath()
        ctx.moveTo(l.sourceNode.x, l.sourceNode.y)
        ctx.lineTo(l.targetNode.x, l.targetNode.y)
        ctx.strokeStyle = `rgba(148, 163, 184, ${0.15 + l.strength * 0.2})`
        ctx.lineWidth = 0.5 + l.strength
        ctx.stroke()

        const progress = (tick * 0.005 * l.strength) % 1
        const px = l.sourceNode.x + (l.targetNode.x - l.sourceNode.x) * progress
        const py = l.sourceNode.y + (l.targetNode.y - l.sourceNode.y) * progress
        ctx.beginPath()
        ctx.arc(px, py, 1.5, 0, Math.PI * 2)
        ctx.fillStyle = l.sourceNode.color || '#6366f1'
        ctx.globalAlpha = 0.6
        ctx.fill()
        ctx.globalAlpha = 1
      }

      const mx = mouseRef.current.x
      const my = mouseRef.current.y
      let closest: typeof nodes[0] | null = null
      let closestDist = 30

      for (const n of nodes) {
        const dx = n.x - mx
        const dy = n.y - my
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < closestDist) {
          closest = n
          closestDist = dist
        }
      }

      for (const n of nodes) {
        const r = Math.max(4, Math.sqrt(n.val) * 2.5)
        const isHovered = n === closest

        if (isHovered) {
          ctx.beginPath()
          ctx.arc(n.x, n.y, r + 8, 0, Math.PI * 2)
          ctx.fillStyle = n.color + '20'
          ctx.fill()
        }

        ctx.beginPath()
        ctx.arc(n.x, n.y, r + 2, 0, Math.PI * 2)
        ctx.fillStyle = n.color + '30'
        ctx.fill()

        ctx.beginPath()
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2)
        const grad = ctx.createRadialGradient(n.x - r * 0.3, n.y - r * 0.3, 0, n.x, n.y, r)
        grad.addColorStop(0, n.color + 'ff')
        grad.addColorStop(1, n.color + 'cc')
        ctx.fillStyle = grad
        ctx.fill()

        ctx.font = `${isHovered ? 'bold ' : ''}${isHovered ? 11 : 9}px "Inter", system-ui, sans-serif`
        ctx.textAlign = 'center'
        ctx.fillStyle = isHovered ? (n.color || '#334155') : '#64748b'
        ctx.fillText(n.name, n.x, n.y + r + 12)
      }

      if (closest) {
        setHoveredNode(closest)
      } else {
        setHoveredNode(null)
      }
    }

    function loop() {
      simulate()
      draw()
      animRef.current = requestAnimationFrame(loop)
    }

    loop()

    return () => {
      cancelAnimationFrame(animRef.current)
    }
  }, [data, dimensions.width, height])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    const rect = canvasRef.current?.getBoundingClientRect()
    if (rect) {
      mouseRef.current = { x: e.clientX - rect.left, y: e.clientY - rect.top }
    }
  }, [])

  const handleMouseLeave = useCallback(() => {
    mouseRef.current = { x: -1000, y: -1000 }
    setHoveredNode(null)
  }, [])

  if (!data.nodes.length) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, height: 0 }}
      animate={{ opacity: 1, y: 0, height: 'auto' }}
      transition={{ duration: 0.5 }}
      className="mb-4 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 overflow-hidden shadow-lg"
    >
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-100 dark:border-slate-700">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300">
          <Network className="w-4 h-4 text-indigo-500" />
          <span>知识图谱</span>
          <span className="text-xs text-slate-400">
            {data.nodes.length} 个实体 · {data.links.length} 条关系
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          >
            {expanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      <div ref={containerRef} className="relative" style={{ height }}>
        <canvas
          ref={canvasRef}
          className="w-full h-full cursor-crosshair"
          style={{ width: '100%', height }}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        />

        <AnimatePresence>
          {hoveredNode && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 5 }}
              className="absolute bottom-3 left-3 right-3 px-3 py-2 rounded-lg bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm border border-slate-200 dark:border-slate-700 shadow-lg"
            >
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: hoveredNode.color }} />
                <span className="font-medium text-sm">{hoveredNode.name}</span>
                <span className="text-xs px-1.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500">
                  {TYPE_LABELS[hoveredNode.type] || hoveredNode.type}
                </span>
              </div>
              {hoveredNode.desc && (
                <p className="text-xs text-slate-500 mt-1 line-clamp-1">{hoveredNode.desc}</p>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        <div className="absolute top-2 right-2 flex flex-wrap gap-1">
          {Object.entries(TYPE_LABELS).map(([type, label]) => {
            const count = data.nodes.filter(n => n.type === type).length
            if (!count) return null
            const colors: Record<string, string> = {
              person: '#6366f1', topic: '#f59e0b', platform: '#10b981', format: '#ec4899', audience: '#06b6d4',
            }
            return (
              <span
                key={type}
                className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm text-slate-600 dark:text-slate-400"
              >
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: colors[type] }} />
                {label} {count}
              </span>
            )
          })}
        </div>
      </div>
    </motion.div>
  )
}
