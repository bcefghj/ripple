import { useRef, useCallback, useEffect, useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Maximize2, Minimize2, X, Network, RotateCcw, ZoomIn, Search, Expand, Sparkles } from 'lucide-react'
import ForceGraph3D from 'react-force-graph-3d'
import * as THREE from 'three'
// @ts-ignore
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
// @ts-ignore
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
// @ts-ignore
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
// @ts-ignore
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js'
import type { GraphData, GraphNode } from '../lib/api'

/* ================================================================
   Types & Props
   ================================================================ */

interface Props {
  data: GraphData
  onClose?: () => void
  onNodeClick?: (node: GraphNode) => void
  isExpanding?: boolean
}

/* ================================================================
   Constants – Neon Sci-Fi Palette
   ================================================================ */

const TYPE_LABELS: Record<string, string> = {
  person: '博主/达人', topic: '话题', platform: '平台', format: '内容形式',
  audience: '受众', trend: '趋势', strategy: '策略', brand: '品牌',
  event: '事件', metric: '指标',
}

const TYPE_COLORS: Record<string, string> = {
  person:   '#00f5ff',
  topic:    '#ff2d78',
  platform: '#00ff9d',
  format:   '#ffab40',
  audience: '#7c4dff',
  trend:    '#ff5252',
  strategy: '#40c4ff',
  brand:    '#e040fb',
  event:    '#ffea00',
  metric:   '#69f0ae',
}

const TYPE_GEOMETRIES: Record<string, string> = {
  person: 'sphere', topic: 'icosahedron', platform: 'box',
  format: 'octahedron', audience: 'torus', trend: 'cone',
  strategy: 'dodecahedron', brand: 'sphere', event: 'icosahedron',
  metric: 'octahedron',
}

/* ================================================================
   GLSL Shaders
   ================================================================ */

const NEBULA_VERT = /* glsl */ `
varying vec3 vPos;
void main() {
  vPos = position;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`

const NEBULA_FRAG = /* glsl */ `
uniform float uTime;
varying vec3 vPos;

float hash(vec3 p) {
  p = fract(p * vec3(443.897, 441.423, 437.195));
  p += dot(p, p.yzx + 19.19);
  return fract((p.x + p.y) * p.z);
}

float noise(vec3 p) {
  vec3 i = floor(p), f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(
    mix(mix(hash(i), hash(i+vec3(1,0,0)), f.x),
        mix(hash(i+vec3(0,1,0)), hash(i+vec3(1,1,0)), f.x), f.y),
    mix(mix(hash(i+vec3(0,0,1)), hash(i+vec3(1,0,1)), f.x),
        mix(hash(i+vec3(0,1,1)), hash(i+vec3(1,1,1)), f.x), f.y),
    f.z);
}

float fbm(vec3 p) {
  float v = 0.0, a = 0.5;
  for (int i = 0; i < 5; i++) { v += a * noise(p); p *= 2.0; a *= 0.5; }
  return v;
}

void main() {
  vec3 d = normalize(vPos);
  float t = uTime * 0.018;

  float n1 = fbm(d * 2.0 + t);
  float n2 = fbm(d * 3.0 - t * 0.7 + 100.0);
  float n3 = fbm(d * 1.5 + t * 0.5 + 200.0);

  vec3 c = mix(vec3(0.08, 0.0, 0.25), vec3(0.0, 0.12, 0.35), n1);
  c = mix(c, vec3(0.18, 0.0, 0.08), n2 * 0.5);
  c += vec3(0.0, 0.08, 0.18) * n3 * 0.3;
  c += vec3(0.25, 0.08, 0.45) * pow(fbm(d * 4.0 + t * 0.3), 3.0);

  gl_FragColor = vec4(c * 0.35, 1.0);
}
`

const STAR_VERT = /* glsl */ `
attribute float aSize;
attribute float aSpeed;
attribute float aPhase;
attribute vec3 aColor;
uniform float uTime;
varying vec3 vColor;

void main() {
  vColor = aColor;
  float twinkle = 0.5 + 0.5 * sin(uTime * aSpeed + aPhase);
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  gl_PointSize = aSize * twinkle * clamp(200.0 / -mv.z, 0.5, 6.0);
  gl_Position = projectionMatrix * mv;
}
`

const STAR_FRAG = /* glsl */ `
varying vec3 vColor;
void main() {
  float d = length(gl_PointCoord - vec2(0.5));
  if (d > 0.5) discard;
  float a = 1.0 - smoothstep(0.0, 0.5, d);
  gl_FragColor = vec4(vColor, a * 0.85);
}
`

const PULSE_VERT = /* glsl */ `
varying vec3 vNorm;
varying vec3 vViewDir;
varying vec3 vWorldPos;
void main() {
  vec4 wp = modelMatrix * vec4(position, 1.0);
  vWorldPos = wp.xyz;
  vNorm = normalize(normalMatrix * normal);
  vViewDir = normalize(cameraPosition - wp.xyz);
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`

const PULSE_FRAG = /* glsl */ `
uniform vec3 uColor;
uniform float uTime;
varying vec3 vNorm;
varying vec3 vViewDir;
varying vec3 vWorldPos;
void main() {
  float fresnel = pow(1.0 - abs(dot(normalize(vNorm), normalize(vViewDir))), 2.5);
  float phase = dot(vWorldPos, vec3(0.1, 0.17, 0.23));
  float pulse = 0.5 + 0.5 * sin(uTime * 2.0 + phase);
  float a = fresnel * 0.18 * (0.4 + 0.6 * pulse);
  gl_FragColor = vec4(uColor, a);
}
`

const ORBIT_VERT = /* glsl */ `
attribute float aAngle;
attribute float aSpeed;
attribute float aRadius;
uniform float uTime;
uniform vec3 uColor;
varying vec3 vColor;

void main() {
  vColor = uColor;
  float ang = aAngle + uTime * aSpeed;
  vec3 p = vec3(
    aRadius * cos(ang),
    aRadius * sin(ang) * 0.25,
    aRadius * sin(ang) * cos(ang * 0.5) * 0.4
  );
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  gl_PointSize = 2.5 * clamp(180.0 / -mv.z, 0.4, 4.0);
  gl_Position = projectionMatrix * mv;
}
`

const ORBIT_FRAG = /* glsl */ `
varying vec3 vColor;
void main() {
  float d = length(gl_PointCoord - vec2(0.5)) * 2.0;
  if (d > 1.0) discard;
  float a = 1.0 - d * d;
  gl_FragColor = vec4(vColor, a * 0.7);
}
`

const VignetteShader = {
  uniforms: {
    tDiffuse: { value: null as THREE.Texture | null },
    offset:   { value: 1.0 },
    darkness: { value: 1.4 },
  },
  vertexShader: /* glsl */ `
    varying vec2 vUv;
    void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }
  `,
  fragmentShader: /* glsl */ `
    uniform sampler2D tDiffuse;
    uniform float offset;
    uniform float darkness;
    varying vec2 vUv;
    void main() {
      vec4 t = texture2D(tDiffuse, vUv);
      vec2 u = (vUv - 0.5) * vec2(offset);
      gl_FragColor = vec4(mix(t.rgb, vec3(0.0), dot(u,u) * darkness), t.a);
    }
  `,
}

/* ================================================================
   Scene Helpers
   ================================================================ */

function createStarField(timeUniform: { value: number }): THREE.Points {
  const N = 3000
  const geo = new THREE.BufferGeometry()
  const pos = new Float32Array(N * 3)
  const col = new Float32Array(N * 3)
  const sizes = new Float32Array(N)
  const speeds = new Float32Array(N)
  const phases = new Float32Array(N)

  for (let i = 0; i < N; i++) {
    pos[i * 3]     = (Math.random() - 0.5) * 2200
    pos[i * 3 + 1] = (Math.random() - 0.5) * 2200
    pos[i * 3 + 2] = (Math.random() - 0.5) * 2200

    const b = 0.5 + Math.random() * 0.5
    const h = Math.random()
    if (h < 0.3)      { col[i*3]=b*0.7;  col[i*3+1]=b*0.85; col[i*3+2]=b; }
    else if (h < 0.6)  { col[i*3]=b;      col[i*3+1]=b;      col[i*3+2]=b; }
    else               { col[i*3]=b;      col[i*3+1]=b*0.8;  col[i*3+2]=b*0.55; }

    sizes[i]  = 1.0 + Math.random() * 3.0
    speeds[i] = 0.5 + Math.random() * 2.5
    phases[i] = Math.random() * Math.PI * 2
  }

  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
  geo.setAttribute('aColor',   new THREE.BufferAttribute(col, 3))
  geo.setAttribute('aSize',    new THREE.BufferAttribute(sizes, 1))
  geo.setAttribute('aSpeed',   new THREE.BufferAttribute(speeds, 1))
  geo.setAttribute('aPhase',   new THREE.BufferAttribute(phases, 1))

  return new THREE.Points(geo, new THREE.ShaderMaterial({
    uniforms: { uTime: timeUniform },
    vertexShader: STAR_VERT,
    fragmentShader: STAR_FRAG,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  }))
}

function createNebula(timeUniform: { value: number }): THREE.Mesh {
  return new THREE.Mesh(
    new THREE.IcosahedronGeometry(950, 4),
    new THREE.ShaderMaterial({
      uniforms: { uTime: timeUniform },
      vertexShader: NEBULA_VERT,
      fragmentShader: NEBULA_FRAG,
      side: THREE.BackSide,
      depthWrite: false,
      transparent: false,
    }),
  )
}

function makeNodeGeo(type: string, s: number): THREE.BufferGeometry {
  switch (TYPE_GEOMETRIES[type] || 'sphere') {
    case 'icosahedron':   return new THREE.IcosahedronGeometry(s, 1)
    case 'box':           return new THREE.BoxGeometry(s * 1.5, s * 1.5, s * 1.5)
    case 'octahedron':    return new THREE.OctahedronGeometry(s, 0)
    case 'torus':         return new THREE.TorusGeometry(s * 0.8, s * 0.3, 12, 24)
    case 'cone':          return new THREE.ConeGeometry(s, s * 2, 8)
    case 'dodecahedron':  return new THREE.DodecahedronGeometry(s, 0)
    default:              return new THREE.SphereGeometry(s, 32, 32)
  }
}

/* ================================================================
   Component
   ================================================================ */

export default function KnowledgeGraph3D({ data, onClose, onNodeClick, isExpanding }: Props) {
  const graphRef      = useRef<any>(null)
  const containerRef  = useRef<HTMLDivElement>(null)
  const composerRef   = useRef<any>(null)
  const bloomRef      = useRef<any>(null)
  const sceneObjsRef  = useRef<THREE.Object3D[]>([])
  const disposeRef    = useRef(false)

  const globalTime = useRef({ value: 0 })

  const [expanded, setExpanded]       = useState(false)
  const [fullscreen, setFullscreen]   = useState(false)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
  const [dimensions, setDimensions]   = useState({ width: 600, height: 400 })
  const [growthCount, setGrowthCount] = useState(0)

  const height = fullscreen ? window.innerHeight : expanded ? 650 : 450

  /* ---------- Resize observer ---------- */
  useEffect(() => {
    if (!containerRef.current) return
    const obs = new ResizeObserver(entries => {
      for (const e of entries) setDimensions({ width: e.contentRect.width, height })
    })
    obs.observe(containerRef.current)
    return () => obs.disconnect()
  }, [height])

  /* ---------- Post-processing & Scene Setup ---------- */
  useEffect(() => {
    disposeRef.current = false
    let animId = 0
    let idleTimer = 0
    let origRender: any = null
    let renderer: any = null

    const init = () => {
      if (disposeRef.current || !graphRef.current) {
        if (!disposeRef.current) setTimeout(init, 60)
        return
      }
      renderer = graphRef.current.renderer()
      const scene: THREE.Scene = graphRef.current.scene()
      const camera: THREE.Camera = graphRef.current.camera()
      const controls = graphRef.current.controls()
      if (!renderer || !scene || !camera) { if (!disposeRef.current) setTimeout(init, 60); return }

      renderer.toneMapping = THREE.ACESFilmicToneMapping
      renderer.toneMappingExposure = 1.2

      const composer = new EffectComposer(renderer)
      composer.addPass(new RenderPass(scene, camera))

      const bloom = new UnrealBloomPass(
        new THREE.Vector2(dimensions.width, height),
        1.8,   // strength
        0.5,   // radius
        0.28,  // threshold
      )
      composer.addPass(bloom)

      const vignette = new ShaderPass(VignetteShader)
      vignette.renderToScreen = true
      composer.addPass(vignette)

      composerRef.current = composer
      bloomRef.current = bloom

      let inComposer = false
      origRender = renderer.render.bind(renderer)
      renderer.render = function (...args: any[]) {
        if (inComposer) return origRender(...args)
        inComposer = true
        composer.render()
        inComposer = false
      }

      /* --- Background objects --- */
      const objs = sceneObjsRef.current
      const nebula = createNebula(globalTime.current)
      scene.add(nebula); objs.push(nebula)
      const stars = createStarField(globalTime.current)
      scene.add(stars); objs.push(stars)

      const ambient = new THREE.AmbientLight(0x303050, 0.6)
      scene.add(ambient); objs.push(ambient)

      const pL1 = new THREE.PointLight(0x6366f1, 1.2, 900)
      pL1.position.set(120, 120, 220)
      scene.add(pL1); objs.push(pL1)

      const pL2 = new THREE.PointLight(0x00f5ff, 0.6, 700)
      pL2.position.set(-120, -80, -200)
      scene.add(pL2); objs.push(pL2)

      const pL3 = new THREE.PointLight(0xff2d78, 0.4, 600)
      pL3.position.set(0, 150, -100)
      scene.add(pL3); objs.push(pL3)

      /* --- Camera auto-rotate --- */
      if (controls) {
        controls.autoRotate = true
        controls.autoRotateSpeed = 0.35
      }
      const pauseAutoRotate = () => {
        if (controls) controls.autoRotate = false
        clearTimeout(idleTimer)
        idleTimer = window.setTimeout(() => { if (controls) controls.autoRotate = true }, 8000)
      }
      const el = containerRef.current
      el?.addEventListener('mousedown', pauseAutoRotate)
      el?.addEventListener('wheel', pauseAutoRotate)
      el?.addEventListener('touchstart', pauseAutoRotate)

      /* --- Animation loop --- */
      const clock = new THREE.Clock()
      const tick = () => {
        if (disposeRef.current) return
        const t = clock.getElapsedTime()
        globalTime.current.value = t
        stars.rotation.y = t * 0.008
        stars.rotation.x = t * 0.004
        animId = requestAnimationFrame(tick)
      }
      tick()

      /* --- Cleanup closure --- */
      const cleanup = () => {
        el?.removeEventListener('mousedown', pauseAutoRotate)
        el?.removeEventListener('wheel', pauseAutoRotate)
        el?.removeEventListener('touchstart', pauseAutoRotate)
        clearTimeout(idleTimer)
      }
      ;(init as any).__cleanup = cleanup
    }

    setTimeout(init, 80)

    return () => {
      disposeRef.current = true
      cancelAnimationFrame(animId)
      if (origRender && renderer) renderer.render = origRender
      ;(init as any).__cleanup?.()
      const scene = graphRef.current?.scene?.()
      for (const o of sceneObjsRef.current) scene?.remove(o)
      sceneObjsRef.current = []
      composerRef.current = null
      bloomRef.current = null
    }
  }, [])

  /* ---------- Resize composer ---------- */
  useEffect(() => {
    composerRef.current?.setSize(dimensions.width, height)
    bloomRef.current?.setSize?.(dimensions.width, height)
  }, [dimensions.width, height])

  /* ---------- Growth animation ---------- */
  useEffect(() => {
    const total = data.nodes.length
    if (total === 0) { setGrowthCount(0); return }

    setGrowthCount(1)
    let step = 1
    const batch = Math.max(1, Math.ceil(total / 22))

    const id = setInterval(() => {
      step += batch
      const next = Math.min(step, total)
      setGrowthCount(next)
      if (next >= total) clearInterval(id)
    }, 75)

    return () => clearInterval(id)
  }, [data.nodes.length])

  /* ---------- Graph data with growth ---------- */
  const sortedNodes = useMemo(
    () => [...data.nodes].sort((a, b) => (b.val || 0) - (a.val || 0)),
    [data.nodes],
  )

  const graphData = useMemo(() => {
    const count = Math.min(growthCount, sortedNodes.length) || sortedNodes.length
    const visible = sortedNodes.slice(0, count)
    const ids = new Set(visible.map(n => n.id))
    return {
      nodes: visible.map(n => ({
        ...n,
        __size: Math.max(5, Math.sqrt(n.val) * 3),
      })),
      links: data.links
        .filter(l => {
          const s = typeof l.source === 'string' ? l.source : (l.source as any).id
          const t = typeof l.target === 'string' ? l.target : (l.target as any).id
          return ids.has(s) && ids.has(t)
        })
        .map(l => ({ ...l, __pw: 0.8 + (l.strength || 0.5) * 2 })),
    }
  }, [sortedNodes, growthCount, data.links])

  /* ---------- Event handlers ---------- */
  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node)
    onNodeClick?.(node)
    if (graphRef.current) {
      const d = 100
      const r = 1 + d / Math.hypot(node.x, node.y, node.z)
      graphRef.current.cameraPosition(
        { x: node.x * r, y: node.y * r, z: node.z * r }, node, 1200,
      )
    }
  }, [onNodeClick])

  const handleNodeHover = useCallback((node: any, prevNode: any) => {
    if (prevNode?.__threeObj) prevNode.__threeObj.scale.setScalar(1)
    if (node?.__threeObj) node.__threeObj.scale.setScalar(1.3)
    setHoveredNode(node || null)
    if (containerRef.current) containerRef.current.style.cursor = node ? 'pointer' : 'default'
  }, [])

  const resetCamera = useCallback(() => {
    graphRef.current?.cameraPosition({ x: 0, y: 0, z: 350 }, { x: 0, y: 0, z: 0 }, 1000)
    setSelectedNode(null)
  }, [])

  /* ---------- Node three object ---------- */
  const nodeThreeObject = useCallback((node: any) => {
    const isSelected = selectedNode?.id === node.id
    const size = node.__size || 5
    const hex = node.color || TYPE_COLORS[node.type] || '#00f5ff'
    const col = new THREE.Color(hex)
    const group = new THREE.Group()

    // 1 · Core mesh
    const core = new THREE.Mesh(
      makeNodeGeo(node.type, size),
      new THREE.MeshStandardMaterial({
        color: col, emissive: col,
        emissiveIntensity: isSelected ? 1.0 : 0.6,
        metalness: 0.4, roughness: 0.15,
        transparent: true, opacity: 0.95,
      }),
    )
    group.add(core)

    // 2 · Inner glow sphere
    group.add(new THREE.Mesh(
      new THREE.SphereGeometry(size * 1.55, 24, 24),
      new THREE.MeshBasicMaterial({
        color: col, transparent: true,
        opacity: isSelected ? 0.18 : 0.1,
        blending: THREE.AdditiveBlending, depthWrite: false,
      }),
    ))

    // 3 · Outer pulse sphere (fresnel + animated)
    group.add(new THREE.Mesh(
      new THREE.SphereGeometry(size * (isSelected ? 2.6 : 2.1), 24, 24),
      new THREE.ShaderMaterial({
        uniforms: { uColor: { value: col }, uTime: globalTime.current },
        vertexShader: PULSE_VERT,
        fragmentShader: PULSE_FRAG,
        transparent: true, blending: THREE.AdditiveBlending,
        depthWrite: false, side: THREE.FrontSide,
      }),
    ))

    // 4 · Energy ring 1
    group.add(Object.assign(
      new THREE.Mesh(
        new THREE.TorusGeometry(size * 1.45, 0.12, 8, 64),
        new THREE.MeshBasicMaterial({
          color: col, transparent: true, opacity: 0.25,
          blending: THREE.AdditiveBlending, depthWrite: false,
        }),
      ),
      { rotation: new THREE.Euler(Math.PI * 0.35, 0, Math.random() * Math.PI) },
    ))

    // 5 · Energy ring 2
    group.add(Object.assign(
      new THREE.Mesh(
        new THREE.TorusGeometry(size * 1.2, 0.1, 8, 64),
        new THREE.MeshBasicMaterial({
          color: col, transparent: true, opacity: 0.18,
          blending: THREE.AdditiveBlending, depthWrite: false,
        }),
      ),
      { rotation: new THREE.Euler(Math.PI * 0.6, Math.PI * 0.4, 0) },
    ))

    // 6 · Orbiting particles
    const PC = 8
    const pGeo = new THREE.BufferGeometry()
    const angles  = new Float32Array(PC)
    const speeds  = new Float32Array(PC)
    const radii   = new Float32Array(PC)
    const dummyPos = new Float32Array(PC * 3)
    for (let i = 0; i < PC; i++) {
      angles[i] = (i / PC) * Math.PI * 2
      speeds[i] = 0.6 + Math.random() * 1.2
      radii[i]  = size * (1.5 + Math.random() * 0.5)
    }
    pGeo.setAttribute('position', new THREE.BufferAttribute(dummyPos, 3))
    pGeo.setAttribute('aAngle',   new THREE.BufferAttribute(angles, 1))
    pGeo.setAttribute('aSpeed',   new THREE.BufferAttribute(speeds, 1))
    pGeo.setAttribute('aRadius',  new THREE.BufferAttribute(radii, 1))
    group.add(new THREE.Points(pGeo, new THREE.ShaderMaterial({
      uniforms: { uTime: globalTime.current, uColor: { value: col } },
      vertexShader: ORBIT_VERT, fragmentShader: ORBIT_FRAG,
      transparent: true, blending: THREE.AdditiveBlending, depthWrite: false,
    })))

    // 7 · Selection extra glow
    if (isSelected) {
      group.add(new THREE.Mesh(
        new THREE.SphereGeometry(size * 3.2, 24, 24),
        new THREE.MeshBasicMaterial({
          color: col, transparent: true, opacity: 0.08,
          blending: THREE.AdditiveBlending, depthWrite: false,
        }),
      ))
    }

    // 8 · Label sprite
    const cvs = document.createElement('canvas')
    const ctx = cvs.getContext('2d')!
    cvs.width = 512; cvs.height = 128

    const label = node.name.length > 10 ? node.name.slice(0, 10) + '…' : node.name

    ctx.font = 'bold 30px "Inter", system-ui, -apple-system, sans-serif'
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'

    // glow
    ctx.shadowColor = hex
    ctx.shadowBlur = 14
    ctx.fillStyle = '#e8e8e8'
    ctx.fillText(label, 256, 46)
    ctx.fillText(label, 256, 46)

    ctx.shadowBlur = 0
    ctx.fillStyle = hex
    ctx.globalAlpha = 0.85
    ctx.font = '20px "Inter", system-ui, sans-serif'
    ctx.fillText(TYPE_LABELS[node.type] || node.type, 256, 82)

    const tex = new THREE.CanvasTexture(cvs)
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
      map: tex, transparent: true, depthWrite: false,
    }))
    sprite.scale.set(28, 7, 1)
    sprite.position.set(0, -(size + 9), 0)
    group.add(sprite)

    return group
  }, [selectedNode])

  /* ---------- Link helpers ---------- */
  const linkColor = useCallback((link: any) => {
    const s = link.strength || 0.5
    const a = Math.floor((0.25 + s * 0.45) * 255).toString(16).padStart(2, '0')
    return `#818cf8${a}`
  }, [])

  const linkParticleColor = useCallback((link: any) => {
    const src = typeof link.source === 'object' ? link.source : null
    return src?.color || TYPE_COLORS[src?.type] || '#818cf8'
  }, [])

  if (!data.nodes.length) return null

  /* ---------- Render ---------- */
  const containerClass = fullscreen
    ? 'fixed inset-0 z-50 bg-slate-950'
    : 'mb-4 rounded-2xl border border-slate-700/50 bg-slate-950 overflow-hidden shadow-2xl'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className={containerClass}
      style={fullscreen ? {} : { boxShadow: '0 0 60px rgba(99,102,241,.18), 0 0 120px rgba(0,245,255,.06)' }}
    >
      {/* -------- Header -------- */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-700/50 bg-gradient-to-r from-slate-900/95 via-slate-800/80 to-slate-900/95 backdrop-blur-md">
        <div className="flex items-center gap-2.5 text-sm font-medium text-slate-200">
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}>
            <Network className="w-4.5 h-4.5 text-indigo-400" />
          </motion.div>
          <span className="bg-gradient-to-r from-indigo-300 via-cyan-300 to-purple-300 bg-clip-text text-transparent font-semibold">
            AI 知识图谱
          </span>
          <span className="text-xs text-slate-400 font-normal">
            {data.nodes.length} 实体 · {data.links.length} 关系
          </span>
          {isExpanding && (
            <motion.span animate={{ opacity: [0.5, 1, 0.5] }} transition={{ repeat: Infinity, duration: 1.5 }} className="text-xs text-amber-400 flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> 扩展中...
            </motion.span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button onClick={resetCamera} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-all" title="重置视角">
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <button onClick={() => setExpanded(!expanded)} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-all" title={expanded ? '收起' : '展开'}>
            {expanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
          <button onClick={() => setFullscreen(!fullscreen)} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-all" title="全屏沉浸">
            <Expand className="w-3.5 h-3.5" />
          </button>
          {onClose && (
            <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-all">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* -------- Graph -------- */}
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
          linkWidth={(l: any) => 0.5 + (l.strength || 0.5) * 2}
          linkOpacity={0.55}
          linkDirectionalParticles={5}
          linkDirectionalParticleWidth={(l: any) => l.__pw || 1.2}
          linkDirectionalParticleSpeed={0.006}
          linkDirectionalParticleColor={linkParticleColor}
          linkCurvature={0.15}
          enableNodeDrag
          enableNavigationControls
          showNavInfo={false}
          warmupTicks={80}
          cooldownTicks={200}
          d3AlphaDecay={0.015}
          d3VelocityDecay={0.25}
          d3AlphaMin={0.001}
        />

        {/* Vignette-style CSS overlay for edge polish */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-0 bg-gradient-radial from-indigo-500/5 via-transparent to-transparent" />
          <div className="absolute top-0 left-0 w-full h-28 bg-gradient-to-b from-slate-950/50 to-transparent" />
          <div className="absolute bottom-0 left-0 w-full h-28 bg-gradient-to-t from-slate-950/50 to-transparent" />
        </div>

        {/* Legend */}
        <div className="absolute top-3 right-3 flex flex-col gap-1">
          {Object.entries(TYPE_LABELS).map(([type, label]) => {
            const c = data.nodes.filter(n => n.type === type).length
            if (!c) return null
            return (
              <motion.span key={type} initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-1.5 text-[10px] px-2 py-1 rounded-lg bg-slate-900/80 backdrop-blur-md text-slate-300 border border-slate-700/30"
              >
                <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: TYPE_COLORS[type], boxShadow: `0 0 8px ${TYPE_COLORS[type]}` }} />
                {label} <span className="text-slate-500">{c}</span>
              </motion.span>
            )
          })}
        </div>

        {/* Stats */}
        <div className="absolute top-3 left-3">
          <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}
            className="px-3 py-1.5 rounded-lg bg-slate-900/80 backdrop-blur-md border border-slate-700/30 text-[10px] text-slate-400"
          >
            <div className="flex items-center gap-3">
              <span>节点密度: <span className="text-indigo-300 font-semibold">{(data.links.length / Math.max(data.nodes.length, 1)).toFixed(1)}</span></span>
              <span>连通率: <span className="text-emerald-300 font-semibold">{Math.min(100, Math.round(data.links.length / Math.max(data.nodes.length - 1, 1) * 100))}%</span></span>
            </div>
          </motion.div>
        </div>

        {/* Hint */}
        <div className="absolute bottom-3 left-3 text-[10px] text-slate-500 flex items-center gap-1.5 px-2 py-1 rounded-lg bg-slate-900/60 backdrop-blur-sm">
          <ZoomIn className="w-3 h-3" />
          <span>拖拽旋转 · 滚轮缩放 · 点击节点展开详情</span>
        </div>

        {/* Detail panel */}
        <AnimatePresence>
          {(selectedNode || hoveredNode) && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="absolute bottom-12 left-3 right-3 max-w-md mx-auto px-4 py-3 rounded-xl bg-slate-900/90 backdrop-blur-xl border border-slate-600/30 shadow-2xl"
              style={{ boxShadow: `0 0 40px ${(selectedNode || hoveredNode)!.color}25` }}
            >
              <div className="flex items-center gap-2.5 mb-1.5">
                <div className="w-4 h-4 rounded-md shadow-lg" style={{
                  backgroundColor: (selectedNode || hoveredNode)!.color,
                  boxShadow: `0 0 14px ${(selectedNode || hoveredNode)!.color}`,
                }} />
                <span className="font-semibold text-sm text-white">{(selectedNode || hoveredNode)!.name}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/50">
                  {TYPE_LABELS[(selectedNode || hoveredNode)!.type] || (selectedNode || hoveredNode)!.type}
                </span>
                {selectedNode && (
                  <button onClick={() => onNodeClick?.(selectedNode)}
                    className="ml-auto text-xs px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-all flex items-center gap-1 shadow-lg shadow-indigo-500/20"
                  >
                    <Search className="w-3 h-3" /> 深度探索
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
                  <p className="text-[10px] text-slate-500">重要度：{selectedNode.val}/30</p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
