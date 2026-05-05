import { useRef, useCallback, useEffect, useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Maximize2, Minimize2, X, Network, RotateCcw, ZoomIn, Search } from 'lucide-react'
import ForceGraph3D from 'react-force-graph-3d'
import * as THREE from 'three'
import type { GraphData, GraphNode } from '../lib/api'

interface Props {
  data: GraphData
  onClose?: () => void
  onNodeClick?: (node: GraphNode) => void
}

const TYPE_LABELS: Record<string, string> = {
  person: '博主/达人',
  topic: '话题',
  platform: '平台',
  format: '内容形式',
  audience: '受众',
}

const TYPE_COLORS: Record<string, string> = {
  person: '#6366f1',
  topic: '#f59e0b',
  platform: '#10b981',
  format: '#ec4899',
  audience: '#06b6d4',
}

export default function KnowledgeGraph3D({ data, onClose, onNodeClick }: Props) {
  const graphRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [expanded, setExpanded] = useState(false)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
  const [dimensions, setDimensions] = useState({ width: 600, height: 400 })

  const height = expanded ? 600 : 400

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

  const graphData = useMemo(() => {
    if (!data.nodes.length) return { nodes: [], links: [] }
    return {
      nodes: data.nodes.map(n => ({
        ...n,
        __size: Math.max(3, Math.sqrt(n.val) * 2),
      })),
      links: data.links.map(l => ({
        ...l,
        __particleWidth: 0.5 + (l.strength || 0.5) * 1.5,
      })),
    }
  }, [data])

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node)
    onNodeClick?.(node)

    if (graphRef.current) {
      const distance = 120
      const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z)
      graphRef.current.cameraPosition(
        { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
        node,
        1500,
      )
    }
  }, [onNodeClick])

  const handleNodeHover = useCallback((node: any) => {
    setHoveredNode(node || null)
    if (containerRef.current) {
      containerRef.current.style.cursor = node ? 'pointer' : 'default'
    }
  }, [])

  const resetCamera = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.cameraPosition({ x: 0, y: 0, z: 400 }, { x: 0, y: 0, z: 0 }, 1000)
    }
    setSelectedNode(null)
  }, [])

  const nodeThreeObject = useCallback((node: any) => {
    const isSelected = selectedNode?.id === node.id
    const isHovered = hoveredNode?.id === node.id
    const size = node.__size || 5
    const color = node.color || TYPE_COLORS[node.type] || '#94a3b8'

    const group = new THREE.Group()

    const sphereGeo = new THREE.SphereGeometry(size, 24, 24)
    const sphereMat = new THREE.MeshPhongMaterial({
      color: new THREE.Color(color),
      transparent: true,
      opacity: 0.9,
      shininess: 80,
    })
    const sphere = new THREE.Mesh(sphereGeo, sphereMat)
    group.add(sphere)

    if (isSelected || isHovered) {
      const glowGeo = new THREE.SphereGeometry(size * 1.6, 24, 24)
      const glowMat = new THREE.MeshBasicMaterial({
        color: new THREE.Color(color),
        transparent: true,
        opacity: isSelected ? 0.25 : 0.15,
      })
      const glow = new THREE.Mesh(glowGeo, glowMat)
      group.add(glow)
    }

    const ringGeo = new THREE.RingGeometry(size * 1.2, size * 1.4, 32)
    const ringMat = new THREE.MeshBasicMaterial({
      color: new THREE.Color(color),
      transparent: true,
      opacity: 0.15,
      side: THREE.DoubleSide,
    })
    const ring = new THREE.Mesh(ringGeo, ringMat)
    ring.lookAt(0, 0, 1)
    group.add(ring)

    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')!
    canvas.width = 256
    canvas.height = 64
    ctx.font = 'bold 28px "Inter", system-ui, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillStyle = '#ffffff'
    ctx.strokeStyle = 'rgba(0,0,0,0.6)'
    ctx.lineWidth = 3
    const label = node.name.length > 8 ? node.name.slice(0, 8) + '…' : node.name
    ctx.strokeText(label, 128, 40)
    ctx.fillText(label, 128, 40)

    const texture = new THREE.CanvasTexture(canvas)
    const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false })
    const sprite = new THREE.Sprite(spriteMat)
    sprite.scale.set(24, 6, 1)
    sprite.position.set(0, -(size + 6), 0)
    group.add(sprite)

    return group
  }, [selectedNode, hoveredNode])

  const linkColor = useCallback((link: any) => {
    const strength = link.strength || 0.5
    const alpha = Math.floor((0.15 + strength * 0.3) * 255).toString(16).padStart(2, '0')
    return `#94a3b8${alpha}`
  }, [])

  if (!data.nodes.length) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, height: 0 }}
      animate={{ opacity: 1, y: 0, height: 'auto' }}
      transition={{ duration: 0.5 }}
      className="mb-4 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-900 overflow-hidden shadow-xl"
    >
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-700 bg-slate-800/50">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
          <Network className="w-4 h-4 text-indigo-400" />
          <span>3D 知识图谱</span>
          <span className="text-xs text-slate-400">
            {data.nodes.length} 个实体 · {data.links.length} 条关系
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={resetCamera}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700 transition-colors"
            title="重置视角"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700 transition-colors"
          >
            {expanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
          {onClose && (
            <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700 transition-colors">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      <div ref={containerRef} className="relative" style={{ height }}>
        <ForceGraph3D
          ref={graphRef}
          graphData={graphData}
          width={dimensions.width}
          height={height}
          backgroundColor="rgba(15,23,42,0)"
          nodeThreeObject={nodeThreeObject}
          nodeThreeObjectExtend={false}
          onNodeClick={handleNodeClick}
          onNodeHover={handleNodeHover}
          linkColor={linkColor}
          linkWidth={(link: any) => 0.3 + (link.strength || 0.5) * 1.5}
          linkOpacity={0.4}
          linkDirectionalParticles={3}
          linkDirectionalParticleWidth={(link: any) => link.__particleWidth || 1}
          linkDirectionalParticleSpeed={0.006}
          linkDirectionalParticleColor={(link: any) => {
            const source = typeof link.source === 'object' ? link.source : graphData.nodes.find((n: any) => n.id === link.source)
            return source?.color || '#6366f1'
          }}
          enableNodeDrag={true}
          enableNavigationControls={true}
          showNavInfo={false}
          warmupTicks={50}
          cooldownTicks={100}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
        />

        {/* Node type legend */}
        <div className="absolute top-2 right-2 flex flex-wrap gap-1">
          {Object.entries(TYPE_LABELS).map(([type, label]) => {
            const count = data.nodes.filter(n => n.type === type).length
            if (!count) return null
            return (
              <span
                key={type}
                className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full bg-slate-800/80 backdrop-blur-sm text-slate-300 border border-slate-700/50"
              >
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: TYPE_COLORS[type] }} />
                {label} {count}
              </span>
            )
          })}
        </div>

        {/* Interaction hint */}
        <div className="absolute bottom-2 left-2 text-[10px] text-slate-500 flex items-center gap-1">
          <ZoomIn className="w-3 h-3" />
          拖拽旋转 · 滚轮缩放 · 点击节点查看详情
        </div>

        {/* Node detail tooltip */}
        <AnimatePresence>
          {(selectedNode || hoveredNode) && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 5 }}
              className="absolute bottom-10 left-3 right-3 px-4 py-3 rounded-xl bg-slate-800/95 backdrop-blur-sm border border-slate-600/50 shadow-2xl"
            >
              <div className="flex items-center gap-2 mb-1">
                <div className="w-3 h-3 rounded-full shadow-lg" style={{ backgroundColor: (selectedNode || hoveredNode)!.color }} />
                <span className="font-semibold text-sm text-white">{(selectedNode || hoveredNode)!.name}</span>
                <span className="text-xs px-1.5 py-0.5 rounded-full bg-slate-700 text-slate-300">
                  {TYPE_LABELS[(selectedNode || hoveredNode)!.type] || (selectedNode || hoveredNode)!.type}
                </span>
                {selectedNode && (
                  <button
                    onClick={() => onNodeClick?.(selectedNode)}
                    className="ml-auto text-xs px-2 py-0.5 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white transition-colors flex items-center gap-1"
                  >
                    <Search className="w-3 h-3" />
                    展开
                  </button>
                )}
              </div>
              {(selectedNode || hoveredNode)!.desc && (
                <p className="text-xs text-slate-400 leading-relaxed">{(selectedNode || hoveredNode)!.desc}</p>
              )}
              {selectedNode && (
                <div className="mt-2 pt-2 border-t border-slate-700/50">
                  <p className="text-[10px] text-slate-500">
                    关联关系：{data.links.filter(l =>
                      (typeof l.source === 'string' ? l.source : (l.source as any).id) === selectedNode.id ||
                      (typeof l.target === 'string' ? l.target : (l.target as any).id) === selectedNode.id
                    ).length} 条
                  </p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
