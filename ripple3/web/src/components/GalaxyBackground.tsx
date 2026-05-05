import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'

function GalaxyParticles() {
  const points = useRef<THREE.Points>(null!)
  const count = 3000

  const [positions, colors, sizes] = useMemo(() => {
    const pos = new Float32Array(count * 3)
    const col = new Float32Array(count * 3)
    const sz = new Float32Array(count)
    const palette = [
      new THREE.Color('#6366f1'),
      new THREE.Color('#8b5cf6'),
      new THREE.Color('#3b82f6'),
      new THREE.Color('#06b6d4'),
      new THREE.Color('#ec4899'),
    ]

    for (let i = 0; i < count; i++) {
      const radius = Math.random() * 8 + 0.5
      const spinAngle = radius * 2.5
      const branchAngle = ((i % 5) / 5) * Math.PI * 2
      const randomness = Math.pow(Math.random(), 3) * (Math.random() < 0.5 ? 1 : -1) * 0.5

      pos[i * 3] = Math.cos(branchAngle + spinAngle) * radius + randomness
      pos[i * 3 + 1] = (Math.random() - 0.5) * 0.4 * (1 - radius / 8.5)
      pos[i * 3 + 2] = Math.sin(branchAngle + spinAngle) * radius + randomness

      const color = palette[i % 5].clone()
      const mixFactor = radius / 8.5
      color.lerp(new THREE.Color('#1e1b4b'), mixFactor * 0.6)
      col[i * 3] = color.r
      col[i * 3 + 1] = color.g
      col[i * 3 + 2] = color.b

      sz[i] = Math.random() * 3 + 0.5
    }
    return [pos, col, sz]
  }, [])

  useFrame((_, delta) => {
    if (points.current) {
      points.current.rotation.y += delta * 0.03
    }
  })

  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
        <bufferAttribute attach="attributes-color" count={count} array={colors} itemSize={3} />
        <bufferAttribute attach="attributes-size" count={count} array={sizes} itemSize={1} />
      </bufferGeometry>
      <pointsMaterial
        size={0.04}
        vertexColors
        transparent
        opacity={0.8}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  )
}

function FloatingNodes() {
  const group = useRef<THREE.Group>(null!)
  const count = 20

  const nodes = useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      position: [
        (Math.random() - 0.5) * 12,
        (Math.random() - 0.5) * 6,
        (Math.random() - 0.5) * 8,
      ] as [number, number, number],
      scale: 0.02 + Math.random() * 0.04,
      speed: 0.3 + Math.random() * 0.5,
      offset: i * 0.5,
    }))
  }, [])

  useFrame(({ clock }) => {
    if (!group.current) return
    const t = clock.getElapsedTime()
    group.current.children.forEach((child, i) => {
      const node = nodes[i]
      child.position.y = node.position[1] + Math.sin(t * node.speed + node.offset) * 0.3
      const mat = (child as THREE.Mesh).material as THREE.MeshBasicMaterial
      mat.opacity = 0.3 + Math.sin(t * 0.8 + node.offset) * 0.2
    })
  })

  return (
    <group ref={group}>
      {nodes.map((node, i) => (
        <mesh key={i} position={node.position} scale={node.scale}>
          <sphereGeometry args={[1, 8, 8]} />
          <meshBasicMaterial
            color={i % 2 === 0 ? '#6366f1' : '#06b6d4'}
            transparent
            opacity={0.4}
          />
        </mesh>
      ))}
    </group>
  )
}

export default function GalaxyBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none" style={{ zIndex: 0 }}>
      <Canvas
        camera={{ position: [0, 2, 8], fov: 60 }}
        gl={{ antialias: false, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <ambientLight intensity={0.1} />
        <GalaxyParticles />
        <FloatingNodes />
      </Canvas>
    </div>
  )
}
