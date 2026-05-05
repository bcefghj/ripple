import { useEffect } from 'react'
import { injectShimmerStyles } from '../lib/animations'

interface Props {
  type: 'text' | 'card' | 'graph' | 'chart' | 'avatar'
  lines?: number
  className?: string
}

function ShimmerBlock({ className = '' }: { className?: string }) {
  return <div className={`shimmer-bg rounded ${className}`} />
}

function TextSkeleton({ lines = 3 }: { lines: number }) {
  const widths = ['w-full', 'w-5/6', 'w-4/6', 'w-3/4', 'w-2/3']
  return (
    <div className="space-y-2.5">
      {Array.from({ length: lines }).map((_, i) => (
        <ShimmerBlock
          key={i}
          className={`h-3.5 ${widths[i % widths.length]}`}
        />
      ))}
    </div>
  )
}

function CardSkeleton() {
  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-700/40 bg-slate-50 dark:bg-slate-900 p-4 space-y-3">
      <ShimmerBlock className="h-32 w-full rounded-xl" />
      <ShimmerBlock className="h-4 w-3/4" />
      <ShimmerBlock className="h-3.5 w-full" />
      <ShimmerBlock className="h-3.5 w-5/6" />
      <div className="flex gap-2 pt-1">
        <ShimmerBlock className="h-7 w-16 rounded-full" />
        <ShimmerBlock className="h-7 w-20 rounded-full" />
      </div>
    </div>
  )
}

function GraphSkeleton() {
  return (
    <div className="relative flex items-center justify-center h-52">
      <div className="absolute inset-0 flex items-center justify-center">
        {/* Orbiting dots */}
        <style>{`
          @keyframes orbit1 { 0% { transform: rotate(0deg) translateX(60px) rotate(0deg); } 100% { transform: rotate(360deg) translateX(60px) rotate(-360deg); } }
          @keyframes orbit2 { 0% { transform: rotate(120deg) translateX(80px) rotate(-120deg); } 100% { transform: rotate(480deg) translateX(80px) rotate(-480deg); } }
          @keyframes orbit3 { 0% { transform: rotate(240deg) translateX(45px) rotate(-240deg); } 100% { transform: rotate(600deg) translateX(45px) rotate(-600deg); } }
        `}</style>
        <div className="w-16 h-16 rounded-full shimmer-bg" />
        <div
          className="absolute w-3 h-3 rounded-full bg-indigo-400/40"
          style={{ animation: 'orbit1 3s linear infinite' }}
        />
        <div
          className="absolute w-2.5 h-2.5 rounded-full bg-emerald-400/40"
          style={{ animation: 'orbit2 4.5s linear infinite' }}
        />
        <div
          className="absolute w-2 h-2 rounded-full bg-violet-400/40"
          style={{ animation: 'orbit3 2.5s linear infinite' }}
        />
      </div>
      {/* Connection lines */}
      <div className="absolute inset-0">
        {[0, 1, 2, 3, 4].map((i) => (
          <ShimmerBlock
            key={i}
            className="absolute h-[1px]"
            style={{
              width: `${30 + Math.random() * 40}%`,
              top: `${20 + i * 14}%`,
              left: `${10 + (i % 3) * 15}%`,
              transform: `rotate(${-15 + i * 8}deg)`,
            } as React.CSSProperties}
          />
        ))}
      </div>
    </div>
  )
}

function ChartSkeleton() {
  const bars = [40, 65, 50, 80, 55, 70, 45]
  return (
    <div className="flex items-end gap-2 h-36 px-2 pt-4">
      {bars.map((h, i) => (
        <ShimmerBlock
          key={i}
          className="flex-1 rounded-t-md"
          style={{
            height: `${h}%`,
            animationDelay: `${i * 0.12}s`,
          } as React.CSSProperties}
        />
      ))}
    </div>
  )
}

function AvatarSkeleton() {
  return (
    <div className="flex items-center gap-3">
      <ShimmerBlock className="w-11 h-11 rounded-full flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <ShimmerBlock className="h-3.5 w-28" />
        <ShimmerBlock className="h-3 w-40" />
      </div>
    </div>
  )
}

export default function ShimmerSkeleton({ type, lines = 3, className = '' }: Props) {
  useEffect(() => {
    injectShimmerStyles()
  }, [])

  const content = (() => {
    switch (type) {
      case 'text':
        return <TextSkeleton lines={lines} />
      case 'card':
        return <CardSkeleton />
      case 'graph':
        return <GraphSkeleton />
      case 'chart':
        return <ChartSkeleton />
      case 'avatar':
        return <AvatarSkeleton />
    }
  })()

  return <div className={className}>{content}</div>
}
