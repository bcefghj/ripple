import { useState, useEffect, useRef, useCallback } from 'react'
import type { Variants } from 'framer-motion'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

// ---------------------------------------------------------------------------
// 1. CountUp Hook
// ---------------------------------------------------------------------------

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3)
}

export function useCountUp(target: number, duration = 1.5): number {
  const [value, setValue] = useState(0)
  const rafRef = useRef<number>(0)
  const startRef = useRef<number | null>(null)
  const prevTargetRef = useRef(0)

  useEffect(() => {
    const from = prevTargetRef.current
    const to = target
    startRef.current = null

    const tick = (ts: number) => {
      if (startRef.current === null) startRef.current = ts
      const elapsed = (ts - startRef.current) / 1000
      const progress = Math.min(elapsed / duration, 1)
      const eased = easeOutCubic(progress)
      const current = from + (to - from) * eased

      setValue(Number.isInteger(to) ? Math.round(current) : parseFloat(current.toFixed(1)))

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick)
      } else {
        prevTargetRef.current = to
      }
    }

    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [target, duration])

  return value
}

// ---------------------------------------------------------------------------
// 2. StaggeredList – Framer Motion variants
// ---------------------------------------------------------------------------

export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.06,
      delayChildren: 0.05,
    },
  },
}

export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 16, filter: 'blur(4px)' },
  visible: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: { type: 'spring', stiffness: 300, damping: 24 },
  },
}

// ---------------------------------------------------------------------------
// 3. GSAP Utilities
// ---------------------------------------------------------------------------

export function initScrollAnimations(
  root: HTMLElement | Document = document,
): gsap.core.Timeline[] {
  const elements = root.querySelectorAll<HTMLElement>('.animate-on-scroll')
  const timelines: gsap.core.Timeline[] = []

  elements.forEach((el) => {
    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: el,
        start: 'top 85%',
        end: 'bottom 20%',
        toggleActions: 'play none none reverse',
      },
    })

    tl.fromTo(
      el,
      { opacity: 0, y: 40, scale: 0.96 },
      { opacity: 1, y: 0, scale: 1, duration: 0.7, ease: 'power3.out' },
    )

    timelines.push(tl)
  })

  return timelines
}

export function createPulseTimeline(element: HTMLElement): gsap.core.Timeline {
  return gsap.timeline({ repeat: -1, yoyo: true }).to(element, {
    boxShadow: '0 0 20px 6px rgba(99,102,241,0.35)',
    scale: 1.05,
    duration: 1.2,
    ease: 'sine.inOut',
  })
}

export function createDataFlowTimeline(
  path: SVGPathElement,
  dotEl: HTMLElement | SVGElement,
): gsap.core.Timeline {
  const length = path.getTotalLength()

  return gsap.timeline({ repeat: -1 }).to(dotEl, {
    motionPath: {
      path,
      align: path,
      alignOrigin: [0.5, 0.5],
      autoRotate: true,
    },
    duration: 3,
    ease: 'none',
    onUpdate() {
      const progress = this.progress()
      const pt = path.getPointAtLength(progress * length)
      gsap.set(dotEl, { x: pt.x, y: pt.y })
    },
  })
}

// ---------------------------------------------------------------------------
// 4. Shimmer CSS keyframes (injected once)
// ---------------------------------------------------------------------------

let shimmerInjected = false

export function injectShimmerStyles(): void {
  if (shimmerInjected || typeof document === 'undefined') return
  shimmerInjected = true

  const style = document.createElement('style')
  style.textContent = `
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}
.shimmer-bg {
  background: linear-gradient(
    90deg,
    rgba(148,163,184,0.06) 25%,
    rgba(148,163,184,0.15) 50%,
    rgba(148,163,184,0.06) 75%
  );
  background-size: 800px 100%;
  animation: shimmer 1.8s ease-in-out infinite;
}
`
  document.head.appendChild(style)
}

// ---------------------------------------------------------------------------
// 5. TypewriterEffect hook
// ---------------------------------------------------------------------------

export function useTypewriter(
  text: string,
  speed = 30,
  enabled = true,
): { displayed: string; done: boolean } {
  const [displayed, setDisplayed] = useState('')
  const [done, setDone] = useState(false)
  const idxRef = useRef(0)
  const prevTextRef = useRef('')

  useEffect(() => {
    if (!enabled) {
      setDisplayed(text)
      setDone(true)
      return
    }

    if (text.startsWith(prevTextRef.current)) {
      idxRef.current = prevTextRef.current.length
      setDisplayed(prevTextRef.current)
    } else {
      idxRef.current = 0
      setDisplayed('')
    }
    setDone(false)

    const interval = setInterval(() => {
      idxRef.current += 1
      if (idxRef.current >= text.length) {
        setDisplayed(text)
        setDone(true)
        prevTextRef.current = text
        clearInterval(interval)
      } else {
        setDisplayed(text.slice(0, idxRef.current))
      }
    }, speed)

    return () => clearInterval(interval)
  }, [text, speed, enabled])

  return { displayed, done }
}

// ---------------------------------------------------------------------------
// 6. GlowPulse – Framer Motion variants for node pulsing
// ---------------------------------------------------------------------------

export const glowPulse: Variants = {
  idle: {
    boxShadow: '0 0 0px 0px rgba(99,102,241,0)',
    scale: 1,
  },
  pulse: {
    boxShadow: [
      '0 0 0px 0px rgba(99,102,241,0)',
      '0 0 16px 4px rgba(99,102,241,0.4)',
      '0 0 0px 0px rgba(99,102,241,0)',
    ],
    scale: [1, 1.08, 1],
    transition: {
      duration: 1.6,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
}

export const glowPulseCustom = (color: string): Variants => ({
  idle: {
    boxShadow: `0 0 0px 0px ${color}00`,
    scale: 1,
  },
  pulse: {
    boxShadow: [
      `0 0 0px 0px ${color}00`,
      `0 0 16px 4px ${color}66`,
      `0 0 0px 0px ${color}00`,
    ],
    scale: [1, 1.08, 1],
    transition: {
      duration: 1.6,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
})

// ---------------------------------------------------------------------------
// 7. Shared number formatting
// ---------------------------------------------------------------------------

export function formatCompactNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1).replace(/\.0$/, '') + 'K'
  return String(n)
}
