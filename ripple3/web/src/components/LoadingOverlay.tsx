import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

interface Props {
  isVisible: boolean
}

const PARTICLES = Array.from({ length: 20 }, (_, i) => ({
  id: i,
  x: Math.random() * 100,
  y: Math.random() * 100,
  size: 2 + Math.random() * 4,
  duration: 2 + Math.random() * 3,
  delay: Math.random() * 2,
}))

export default function LoadingOverlay({ isVisible }: Props) {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (!isVisible) {
      setProgress(0)
      return
    }
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 95) return prev
        return prev + (95 - prev) * 0.05
      })
    }, 100)
    return () => clearInterval(interval)
  }, [isVisible])

  if (!isVisible) return null

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/90 backdrop-blur-md"
    >
      {/* Background particles */}
      {PARTICLES.map(p => (
        <motion.div
          key={p.id}
          className="absolute rounded-full bg-indigo-500/20"
          style={{ width: p.size, height: p.size, left: `${p.x}%`, top: `${p.y}%` }}
          animate={{
            y: [0, -30, 0],
            opacity: [0.2, 0.8, 0.2],
            scale: [1, 1.5, 1],
          }}
          transition={{
            duration: p.duration,
            delay: p.delay,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      ))}

      <div className="flex flex-col items-center gap-6">
        {/* Neural network animation */}
        <div className="relative w-32 h-32">
          {/* Outer ring */}
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-indigo-500/30"
            animate={{ rotate: 360 }}
            transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
          />

          {/* Middle ring */}
          <motion.div
            className="absolute inset-3 rounded-full border-2 border-violet-500/40"
            animate={{ rotate: -360 }}
            transition={{ duration: 6, repeat: Infinity, ease: 'linear' }}
          />

          {/* Inner ring */}
          <motion.div
            className="absolute inset-6 rounded-full border-2 border-cyan-500/50"
            animate={{ rotate: 360 }}
            transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
          />

          {/* Center pulse */}
          <motion.div
            className="absolute inset-0 m-auto w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600"
            animate={{ scale: [1, 1.2, 1], opacity: [0.8, 1, 0.8] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
            style={{ boxShadow: '0 0 40px rgba(99, 102, 241, 0.5)' }}
          />

          {/* Orbiting dots */}
          {[0, 1, 2, 3, 4, 5].map(i => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 rounded-full bg-indigo-400"
              style={{ left: '50%', top: '50%', marginLeft: -4, marginTop: -4 }}
              animate={{
                x: Math.cos((i / 6) * Math.PI * 2) * 50,
                y: Math.sin((i / 6) * Math.PI * 2) * 50,
                scale: [1, 1.5, 1],
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 3,
                delay: i * 0.3,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            />
          ))}
        </div>

        {/* Text */}
        <div className="text-center">
          <motion.h3
            className="text-lg font-semibold text-white mb-1"
            animate={{ opacity: [0.7, 1, 0.7] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            Ripple AI 正在分析
          </motion.h3>
          <p className="text-sm text-slate-400">
            9层搜索矩阵 · 多Agent辩论中...
          </p>
        </div>

        {/* Progress bar */}
        <div className="w-48 h-1 rounded-full bg-slate-800 overflow-hidden">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-violet-500 to-cyan-500"
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>
    </motion.div>
  )
}
