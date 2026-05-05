import { useState, useEffect, useRef } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { formatCompactNumber } from '../lib/animations'

interface Props {
  value: number
  prefix?: string
  suffix?: string
  duration?: number
  className?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  compact?: boolean
}

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3)
}

const SIZE_CLASSES: Record<NonNullable<Props['size']>, string> = {
  sm: 'text-sm',
  md: 'text-lg',
  lg: 'text-2xl',
  xl: 'text-4xl',
}

export default function AnimatedCounter({
  value,
  prefix = '',
  suffix = '',
  duration = 1.2,
  className = '',
  size = 'md',
  compact = false,
}: Props) {
  const [display, setDisplay] = useState('0')
  const [counting, setCounting] = useState(false)
  const rafRef = useRef<number>(0)
  const startRef = useRef<number | null>(null)
  const fromRef = useRef(0)
  const prefersReduced = useReducedMotion()

  useEffect(() => {
    if (prefersReduced) {
      setDisplay(compact ? formatCompactNumber(value) : value.toLocaleString())
      return
    }

    const from = fromRef.current
    const to = value
    startRef.current = null
    setCounting(true)

    const tick = (ts: number) => {
      if (startRef.current === null) startRef.current = ts
      const elapsed = (ts - startRef.current) / 1000
      const progress = Math.min(elapsed / duration, 1)
      const eased = easeOutCubic(progress)
      const current = from + (to - from) * eased
      const rounded = Number.isInteger(to) ? Math.round(current) : parseFloat(current.toFixed(1))

      setDisplay(compact ? formatCompactNumber(rounded) : rounded.toLocaleString())

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick)
      } else {
        fromRef.current = to
        setCounting(false)
      }
    }

    rafRef.current = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(rafRef.current)
      setCounting(false)
    }
  }, [value, duration, compact, prefersReduced])

  return (
    <motion.span
      className={`inline-flex items-baseline font-bold tabular-nums ${SIZE_CLASSES[size]} ${className}`}
      animate={
        counting
          ? { textShadow: '0 0 12px rgba(99,102,241,0.5)' }
          : { textShadow: '0 0 0px rgba(99,102,241,0)' }
      }
      transition={{ duration: 0.3 }}
    >
      {prefix && <span className="mr-0.5 opacity-70 font-medium">{prefix}</span>}
      <span>{display}</span>
      {suffix && <span className="ml-0.5 opacity-70 font-medium">{suffix}</span>}
    </motion.span>
  )
}
