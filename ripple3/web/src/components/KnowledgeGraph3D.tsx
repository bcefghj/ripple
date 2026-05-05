import { useRef, useCallback, useEffect, useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Maximize2, Minimize2, X, Network, RotateCcw, ZoomIn, Search, Expand, Sparkles } from 'lucide-react'
import ForceGraph3D from 'react-force-graph-3d'
import * as THREE from 'three'
import type { GraphData, GraphNode } from '../lib/api'

interface Props {
  data: GraphData
  onClose?: () => void
  onNodeClick?: (node: GraphNode) => void
  isExpanding?: boolean
}

const TYPE_LABELS: Record<string, string> = {
  person: '博主/达人',
  topic: '话题',
  platform: '平台',
  format: '内容形式',
  audience: '受众',
  trend: '趋势',
  strategy: '策略',
}

const TYPE_COLORS: Record<string, string> = {
  person: '#818cf8',
  topic: '#fbbf24',
  platform: '#34d399',
  format: '#f472b6',
  audience: '#22d3ee',
  trend: '#a78bfa',
  strategy: '#fb923c',
}

const TYPE_GEOMETRIES: Record<string, string> = {
  person: 'sphere',
  topic: 'icosahedron',
  platform: 'box',
  format: 'octahedron',
  audience: 'torus',
  trend: 'cone',
  strategy: 'dodecahedron',
}

const BLOOM_INTENSITY = 1.5
const STAR_COUNT = 2000

function createStarField(): THREE.Points {
  const geometry = new THREE.BufferGeometry()
  const positions = new Float32Array(STAR_COUNT * 3)
  const colors = new Float32Array(STAR_COUNT * 3)
  const sizes = new Float32Array(STAR_COUNT)

  for (let i = 0; i < STAR_COUNT; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 2000
    positions[i * 3 + 1] = (Math.random() - 0.5) * 2000
    positions[i * 3 + 2] = (Math.random() - 0.5) * 2000

    const brightness = 0.3 + Math.random() * 0.7
    colors[i * 3] = brightness * (0.8 + Math.random() * 0.2)
    colors[i * 3 + 1] = brightness * (0.8 + Math.random() * 0.2)
    colors[i * 3 + 2] = brightness

    sizes[i] = 0.5 + Math.random() * 2
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
  geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))

  const material = new THREE.PointsMaterial({
    size: 1.5,
    vertexColors: true,
    transparent: true,
    opacity: 0.6,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  })

  return new THREE.Points(geometry, material)
}

function createNebulaParticles(): THREE.Points {
  const count = 500
  const geometry = new THREE.BufferGeometry()
  const positions = new Float32Array(count * 3)
  const colors = new Float32Array(count * 3)

  const nebulaColors = [
    new THREE.Color('#4f46e5'),
    new THREE.Color('#7c3aed'),
    new THREE.Color('#2563eb'),
    new THREE.Color('#0891b2'),
  ]

  for (let i = 0; i < count; i++) {
    const theta = Math.random() * Math.PI * 2
    const phi = Math.random() * Math.PI
    const r = 200 + Math.random() * 400
    positions[i * 3] = r * Math.sin(phi) * Math.cos(theta)
    positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta)
    positions[i * 3 + 2] = r * Math.cos(phi)

    const color = nebulaColors[Math.floor(Math.random() * nebulaColors.length)]
    colors[i * 3] = color.r
    colors[i * 3 + 1] = color.g
    colors[i * 3 + 2] = color.b
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))

  const material = new THREE.PointsMaterial({
    size: 4,
    vertexColors: true,
    transparent: true,
    opacity: 0.15,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  })

  return new THREE.Points(geometry, material)
}

function createNodeGeometry(type: string, size: number): THREE.BufferGeometry {
  const geoType = TYPE_GEOMETRIES[type] || 'sphere'
  switch (geoType) {
    case 'icosahedron': return new THREE.IcosahedronGeometry(size, 1)
    case 'box': return new THREE.BoxGeometry(size * 1.5, size * 1.5, size * 1.5)
    case 'octahedron': return new THREE.OctahedronGeometry(size, 0)
    case 'torus': return new THREE.TorusGeometry(size * 0.8, size * 0.3, 12, 24)
    case 'cone': return new THREE.ConeGeometry(size, size * 2, 8)
    case 'dodecahedron': return new THREE.DodecahedronGeometry(size, 0)
    default: return new THREE.SphereGeometry(size, 32, 32)
  }
}

export default function KnowledgeGraph3D({ data, onClose, onNodeClick, isExpanding }: Props) {
  const graphRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const starsRef = useRef<THREE.Points | null>(null)
  const nebulaRef = useRef<THREE.Points | null>(null)
  const animFrameRef = useRef<number>(0)
  const [expanded, setExpanded] = useState(false)
  const [fullscreen, setFullscreen] = useState(false)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
  const [dimensions, setDimensions] = useState({ width: 600, height: 400 })
  const [pulsePhase, setPulsePhase] = useState(0)

  const height = fullscreen ? window.innerHeight : expanded ? 650 : 450

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
    if (!graphRef.current) return
    const scene = graphRef.current.scene()
    if (!scene) return

    if (!starsRef.current) {
      starsRef.current = createStarField()
      scene.add(starsRef.current)
    }
    if (!nebulaRef.current) {
      nebulaRef.current = createNebulaParticles()
      scene.add(nebulaRef.current)
    }

    const ambientLight = new THREE.AmbientLight(0x404060, 0.5)
    scene.add(ambientLight)
    const pointLight = new THREE.PointLight(0x6366f1, 1, 800)
    pointLight.position.set(100, 100, 200)
    scene.add(pointLight)
    const pointLight2 = new THREE.PointLight(0x22d3ee, 0.5, 600)
    pointLight2.position.set(-100, -100, -200)
    scene.add(pointLight2)

    let t = 0
    const animate = () => {
      t += 0.001
      if (starsRef.current) {
        starsRef.current.rotation.y = t * 0.1
        starsRef.current.rotation.x = t * 0.05
      }
      if (nebulaRef.current) {
        nebulaRef.current.rotation.y = -t * 0.05
        nebulaRef.current.rotation.z = t * 0.02
      }
      setPulsePhase(prev => (prev + 0.02) % (Math.PI * 2))
      animFrameRef.current = requestAnimationFrame(animate)
    }
    animate()

    return () => {
      cancelAnimationFrame(animFrameRef.current)
    }
  }, [graphRef.current])

  const graphData = useMemo(() => {
    if (!data.nodes.length) return { nodes: [], links: [] }
    return {
      nodes: data.nodes.map(n => ({
        ...n,
        __size: Math.max(4, Math.sqrt(n.val) * 2.5),
      })),
      links: data.links.map(l => ({
        ...l,
        __particleWidth: 0.8 + (l.strength || 0.5) * 2,
      })),
    }
  }, [data])

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node)
    onNodeClick?.(node)

    if (graphRef.current) {
      const distance = 100
      const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z)
      graphRef.current.cameraPosition(
        { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
        node,
        1200,
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
      graphRef.current.cameraPosition({ x: 0, y: 0, z: 350 }, { x: 0, y: 0, z: 0 }, 1000)
    }
    setSelectedNode(null)
  }, [])

  const nodeThreeObject = useCallback((node: any) => {
    const isSelected = selectedNode?.id === node.id
    const isHovered = hoveredNode?.id === node.id
    const size = node.__size || 5
    const color = node.color || TYPE_COLORS[node.type] || '#94a3b8'
    const threeColor = new THREE.Color(color)

    const group = new THREE.Group()

    const geo = createNodeGeometry(node.type, size)
    const mat = new THREE.MeshPhongMaterial({
      color: threeColor,
      emissive: threeColor,
      emissiveIntensity: isSelected ? 0.8 : isHovered ? 0.5 : 0.2,
      transparent: true,
      opacity: 0.92,
      shininess: 100,
      specular: new THREE.Color(0xffffff),
    })
    const mesh = new THREE.Mesh(geo, mat)
    group.add(mesh)

    if (isSelected || isHovered) {
      const glowSize = size * (isSelected ? 2.2 : 1.8)
      const glowGeo = new THREE.SphereGeometry(glowSize, 24, 24)
      const glowMat = new THREE.MeshBasicMaterial({
        color: threeColor,
        transparent: true,
        opacity: isSelected ? 0.2 : 0.12,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      })
      group.add(new THREE.Mesh(glowGeo, glowMat))

      const pulseGeo = new THREE.RingGeometry(size * 1.8, size * 2.0, 32)
      const pulseMat = new THREE.MeshBasicMaterial({
        color: threeColor,
        transparent: true,
        opacity: 0.3 * (0.5 + 0.5 * Math.sin(pulsePhase)),
        side: THREE.DoubleSide,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      })
      const pulseRing = new THREE.Mesh(pulseGeo, pulseMat)
      pulseRing.lookAt(0, 0, 1)
      group.add(pulseRing)
    }

    const orbitalGeo = new THREE.RingGeometry(size * 1.3, size * 1.35, 48)
    const orbitalMat = new THREE.MeshBasicMaterial({
      color: threeColor,
      transparent: true,
      opacity: 0.1 + (isHovered || isSelected ? 0.15 : 0),
      side: THREE.DoubleSide,
      depthWrite: false,
    })
    const orbital = new THREE.Mesh(orbitalGeo, orbitalMat)
    orbital.rotation.x = Math.PI * 0.3
    orbital.rotation.z = Math.random() * Math.PI
    group.add(orbital)

    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')!
    canvas.width = 512
    canvas.height = 96
    ctx.font = 'bold 32px "Inter", system-ui, -apple-system, sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'

    const label = node.name.length > 10 ? node.name.slice(0, 10) + '…' : node.name

    ctx.shadowColor = 'rgba(0,0,0,0.8)'
    ctx.shadowBlur = 8
    ctx.fillStyle = '#ffffff'
    ctx.fillText(label, 256, 48)

    ctx.shadowBlur = 0
    ctx.fillStyle = color
    ctx.globalAlpha = 0.8
    ctx.font = '22px "Inter", system-ui, sans-serif'
    ctx.fillText(TYPE_LABELS[node.type] || node.type, 256, 80)

    const texture = new THREE.CanvasTexture(canvas)
    texture.needsUpdate = true
    const spriteMat = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthWrite: false,
      blending: THREE.NormalBlending,
    })
    const sprite = new THREE.Sprite(spriteMat)
    sprite.scale.set(28, 5.5, 1)
    sprite.position.set(0, -(size + 8), 0)
    group.add(sprite)

    return group
  }, [selectedNode, hoveredNode, pulsePhase])

  const linkColor = useCallback((link: any) => {
    const strength = link.strength || 0.5
    const alpha = Math.floor((0.2 + strength * 0.4) * 255).toString(16).padStart(2, '0')
    return `#a5b4fc${alpha}`
  }, [])

  const linkParticleColor = useCallback((link: any) => {
    const source = typeof link.source === 'object' ? link.source : graphData.nodes.find((n: any) => n.id === link.source)
    return source?.color || '#818cf8'
  }, [graphData.nodes])

  if (!data.nodes.length) return null

  const containerClass = fullscreen
    ? 'fixed inset-0 z-50 bg-slate-950'
    : 'mb-4 rounded-2xl border border-slate-700/50 bg-slate-950 overflow-hidden shadow-2xl'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className={containerClass}
      style={fullscreen ? {} : { boxShadow: '0 0 40px rgba(99, 102, 241, 0.15), 0 0 80px rgba(99, 102, 241, 0.05)' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-700/50 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900">
        <div className="flex items-center gap-2.5 text-sm font-medium text-slate-200">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
          >
            <Network className="w-4.5 h-4.5 text-indigo-400" />
          </motion.div>
          <span className="bg-gradient-to-r from-indigo-300 to-cyan-300 bg-clip-text text-transparent font-semibold">
            AI 知识图谱
          </span>
          <span className="text-xs text-slate-400 font-normal">
            {data.nodes.length} 实体 · {data.links.length} 关系
          </span>
          {isExpanding && (
            <motion.span
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
              className="text-xs text-amber-400 flex items-center gap-1"
            >
              <Sparkles className="w-3 h-3" />
              扩展中...
            </motion.span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={resetCamera}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-all"
            title="重置视角"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-all"
            title={expanded ? '收起' : '展开'}
          >
            {expanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={() => setFullscreen(!fullscreen)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-all"
            title="全屏沉浸"
          >
            <Expand className="w-3.5 h-3.5" />
          </button>
          {onClose && (
            <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-all">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Graph container */}
      <div ref={containerRef} className="relative" style={{ height }}>
        <ForceGraph3D
          ref={graphRef}
          graphData={graphData}
          width={dimensions.width}
          height={height}
          backgroundColor="rgba(2,6,23,0)"
          nodeThreeObject={nodeThreeObject}
          nodeThreeObjectExtend={false}
          onNodeClick={handleNodeClick}
          onNodeHover={handleNodeHover}
          linkColor={linkColor}
          linkWidth={(link: any) => 0.4 + (link.strength || 0.5) * 1.8}
          linkOpacity={0.5}
          linkDirectionalParticles={4}
          linkDirectionalParticleWidth={(link: any) => link.__particleWidth || 1.2}
          linkDirectionalParticleSpeed={0.005}
          linkDirectionalParticleColor={linkParticleColor}
          linkCurvature={0.1}
          enableNodeDrag={true}
          enableNavigationControls={true}
          showNavInfo={false}
          warmupTicks={80}
          cooldownTicks={200}
          d3AlphaDecay={0.015}
          d3VelocityDecay={0.25}
          d3AlphaMin={0.001}
        />

        {/* Ambient glow overlay */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-0 bg-gradient-radial from-indigo-500/5 via-transparent to-transparent" />
          <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-slate-950/60 to-transparent" />
          <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-slate-950/60 to-transparent" />
        </div>

        {/* Node type legend */}
        <div className="absolute top-3 right-3 flex flex-col gap-1">
          {Object.entries(TYPE_LABELS).map(([type, label]) => {
            const count = data.nodes.filter(n => n.type === type).length
            if (!count) return null
            return (
              <motion.span
                key={type}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-1.5 text-[10px] px-2 py-1 rounded-lg bg-slate-900/80 backdrop-blur-md text-slate-300 border border-slate-700/30"
              >
                <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: TYPE_COLORS[type], boxShadow: `0 0 6px ${TYPE_COLORS[type]}` }} />
                {label} <span className="text-slate-500">{count}</span>
              </motion.span>
            )
          })}
        </div>

        {/* Stats badge */}
        <div className="absolute top-3 left-3">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="px-3 py-1.5 rounded-lg bg-slate-900/80 backdrop-blur-md border border-slate-700/30 text-[10px] text-slate-400"
          >
            <div className="flex items-center gap-3">
              <span>节点密度: <span className="text-indigo-300 font-semibold">{(data.links.length / Math.max(data.nodes.length, 1)).toFixed(1)}</span></span>
              <span>连通率: <span className="text-emerald-300 font-semibold">{Math.min(100, Math.round(data.links.length / Math.max(data.nodes.length - 1, 1) * 100))}%</span></span>
            </div>
          </motion.div>
        </div>

        {/* Interaction hint */}
        <div className="absolute bottom-3 left-3 text-[10px] text-slate-500 flex items-center gap-1.5 px-2 py-1 rounded-lg bg-slate-900/60 backdrop-blur-sm">
          <ZoomIn className="w-3 h-3" />
          <span>拖拽旋转 · 滚轮缩放 · 点击节点展开详情</span>
        </div>

        {/* Node detail panel */}
        <AnimatePresence>
          {(selectedNode || hoveredNode) && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="absolute bottom-12 left-3 right-3 max-w-md mx-auto px-4 py-3 rounded-xl bg-slate-900/95 backdrop-blur-lg border border-slate-600/30 shadow-2xl"
              style={{ boxShadow: `0 0 30px ${(selectedNode || hoveredNode)!.color}20` }}
            >
              <div className="flex items-center gap-2.5 mb-1.5">
                <div
                  className="w-4 h-4 rounded-md shadow-lg"
                  style={{
                    backgroundColor: (selectedNode || hoveredNode)!.color,
                    boxShadow: `0 0 12px ${(selectedNode || hoveredNode)!.color}`,
                  }}
                />
                <span className="font-semibold text-sm text-white">{(selectedNode || hoveredNode)!.name}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/50">
                  {TYPE_LABELS[(selectedNode || hoveredNode)!.type] || (selectedNode || hoveredNode)!.type}
                </span>
                {selectedNode && (
                  <button
                    onClick={() => onNodeClick?.(selectedNode)}
                    className="ml-auto text-xs px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-all flex items-center gap-1 shadow-lg shadow-indigo-500/20"
                  >
                    <Search className="w-3 h-3" />
                    深度探索
                  </button>
                )}
              </div>
              {(selectedNode || hoveredNode)!.desc && (
                <p className="text-xs text-slate-400 leading-relaxed">{(selectedNode || hoveredNode)!.desc}</p>
              )}
              {selectedNode && (
                <div className="mt-2 pt-2 border-t border-slate-700/50 flex items-center justify-between">
                  <p className="text-[10px] text-slate-500">
                    关联关系：{data.links.filter(l =>
                      (typeof l.source === 'string' ? l.source : (l.source as any).id) === selectedNode.id ||
                      (typeof l.target === 'string' ? l.target : (l.target as any).id) === selectedNode.id
                    ).length} 条
                  </p>
                  <p className="text-[10px] text-slate-500">
                    重要度：{selectedNode.val}/30
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
