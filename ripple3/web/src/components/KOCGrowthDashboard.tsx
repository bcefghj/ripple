import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts'
import { Rocket, TrendingUp, Target } from 'lucide-react'

interface GrowthData {
  currentFollowers: number
  targetFollowers: number
  daysToTarget: number
  growthCurve: { day: number; followers: number }[]
  weeklyPlan: { week: number; focus: string; posts: number; target: string }[]
  platformBreakdown: { platform: string; percentage: number; color: string }[]
  contentCalendar: { day: number; type: string; topic: string }[]
}

interface Props {
  data?: GrowthData
  isLoading?: boolean
}

function Skeleton({ className }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded-md bg-slate-700/40 ${className ?? ''}`} />
  )
}

function useAnimatedNumber(target: number, duration = 1500) {
  const [value, setValue] = useState(0)

  useEffect(() => {
    if (target === 0) return
    const start = performance.now()
    const animate = (now: number) => {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(Math.round(target * eased))
      if (progress < 1) requestAnimationFrame(animate)
    }
    requestAnimationFrame(animate)
  }, [target, duration])

  return value
}

function formatNumber(n: number): string {
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return n.toString()
}

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.4, ease: 'easeOut' },
  }),
}

function GlassCard({ children, className, index = 0 }: { children: React.ReactNode; className?: string; index?: number }) {
  return (
    <motion.div
      custom={index}
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      className={`rounded-xl border border-slate-700/50 bg-slate-900/70 backdrop-blur-xl p-4 ${className ?? ''}`}
    >
      {children}
    </motion.div>
  )
}

function FollowerCounter({ current, target }: { current: number; target: number }) {
  const animatedCurrent = useAnimatedNumber(current)
  const animatedTarget = useAnimatedNumber(target, 2000)
  const progress = Math.min((current / target) * 100, 100)

  return (
    <div className="text-center space-y-3">
      <div className="flex items-center justify-center gap-3">
        <div>
          <p className="text-3xl font-bold text-white tabular-nums">{formatNumber(animatedCurrent)}</p>
          <p className="text-[10px] text-slate-500 mt-0.5">当前粉丝</p>
        </div>
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.3, type: 'spring' }}
        >
          <TrendingUp className="w-5 h-5 text-emerald-400" />
        </motion.div>
        <div>
          <p className="text-3xl font-bold text-emerald-400 tabular-nums">{formatNumber(animatedTarget)}</p>
          <p className="text-[10px] text-slate-500 mt-0.5">目标粉丝</p>
        </div>
      </div>
      <div className="relative w-full h-2 rounded-full bg-slate-800 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 1.2, ease: 'easeOut', delay: 0.4 }}
          className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-emerald-500 to-green-400"
          style={{ boxShadow: '0 0 12px rgba(16, 185, 129, 0.4)' }}
        />
      </div>
      <p className="text-[11px] text-slate-500">
        完成度 <span className="text-emerald-400 font-semibold">{progress.toFixed(1)}%</span>
      </p>
    </div>
  )
}

function GrowthChart({ data }: { data: GrowthData['growthCurve'] }) {
  return (
    <ResponsiveContainer width="100%" height={160}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="growthGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10b981" stopOpacity={0.4} />
            <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="day"
          tick={{ fontSize: 10, fill: '#64748b' }}
          axisLine={false}
          tickLine={false}
          tickFormatter={v => `D${v}`}
        />
        <YAxis
          tick={{ fontSize: 10, fill: '#64748b' }}
          axisLine={false}
          tickLine={false}
          tickFormatter={v => formatNumber(v as number)}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '8px',
            fontSize: '11px',
          }}
          labelFormatter={v => `第 ${v} 天`}
          formatter={(v: number) => [formatNumber(v), '粉丝']}
        />
        <Area
          type="monotone"
          dataKey="followers"
          stroke="#10b981"
          strokeWidth={2}
          fill="url(#growthGradient)"
          animationDuration={1500}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

function PlatformDonut({ data }: { data: GrowthData['platformBreakdown'] }) {
  return (
    <div className="flex items-center gap-3">
      <ResponsiveContainer width={120} height={120}>
        <PieChart>
          <Pie
            data={data}
            dataKey="percentage"
            nameKey="platform"
            cx="50%"
            cy="50%"
            innerRadius={35}
            outerRadius={55}
            paddingAngle={3}
            animationDuration={1200}
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
              fontSize: '11px',
            }}
            formatter={(v: number) => [`${v}%`, '占比']}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="space-y-1.5 flex-1">
        {data.map((item, i) => (
          <motion.div
            key={item.platform}
            initial={{ opacity: 0, x: 8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 + i * 0.08 }}
            className="flex items-center gap-2 text-xs"
          >
            <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
            <span className="text-slate-400 flex-1">{item.platform}</span>
            <span className="text-slate-200 font-medium tabular-nums">{item.percentage}%</span>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

function WeeklyTimeline({ plan }: { plan: GrowthData['weeklyPlan'] }) {
  return (
    <div className="space-y-3">
      {plan.map((week, i) => (
        <motion.div
          key={week.week}
          initial={{ opacity: 0, x: -16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 + i * 0.12 }}
          className="flex gap-3"
        >
          <div className="flex flex-col items-center">
            <div className="w-7 h-7 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-[10px] font-bold text-emerald-400">
              W{week.week}
            </div>
            {i < plan.length - 1 && (
              <div className="w-px flex-1 bg-gradient-to-b from-emerald-500/30 to-transparent mt-1" />
            )}
          </div>
          <div className="flex-1 pb-3">
            <p className="text-xs font-semibold text-slate-200">{week.focus}</p>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-[10px] text-slate-500">
                📝 {week.posts} 篇内容
              </span>
              <span className="text-[10px] text-emerald-400/80">
                🎯 {week.target}
              </span>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  )
}

export default function KOCGrowthDashboard({ data, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-700/50 bg-slate-900/80 backdrop-blur-xl p-4 space-y-4">
        <div className="flex items-center gap-2">
          <Skeleton className="w-5 h-5 rounded" />
          <Skeleton className="w-32 h-5" />
        </div>
        <Skeleton className="h-16 rounded-xl" />
        <div className="grid grid-cols-2 gap-3">
          <Skeleton className="h-44 rounded-xl" />
          <Skeleton className="h-44 rounded-xl" />
        </div>
        <Skeleton className="h-32 rounded-xl" />
      </div>
    )
  }

  if (!data) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-slate-700/50 bg-slate-900/80 backdrop-blur-xl overflow-hidden shadow-xl"
    >
      {/* Header */}
      <div className="px-4 pt-4 pb-2 flex items-center gap-2">
        <div className="w-6 h-6 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center">
          <Rocket className="w-3.5 h-3.5 text-emerald-400" />
        </div>
        <h3 className="text-sm font-bold text-slate-200">30天成长计划</h3>
        <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-emerald-500/15 text-emerald-400 font-medium">
          {data.daysToTarget}天目标
        </span>
      </div>

      <div className="px-4 pb-4 space-y-3">
        {/* Follower Counter */}
        <GlassCard index={0}>
          <FollowerCounter current={data.currentFollowers} target={data.targetFollowers} />
        </GlassCard>

        {/* Charts Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <GlassCard index={1}>
            <div className="flex items-center gap-1.5 mb-2">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
              <h4 className="text-xs font-semibold text-slate-300">增长曲线</h4>
            </div>
            <GrowthChart data={data.growthCurve} />
          </GlassCard>

          <GlassCard index={2}>
            <div className="flex items-center gap-1.5 mb-2">
              <Target className="w-3.5 h-3.5 text-emerald-400" />
              <h4 className="text-xs font-semibold text-slate-300">平台分布</h4>
            </div>
            <PlatformDonut data={data.platformBreakdown} />
          </GlassCard>
        </div>

        {/* Weekly Plan */}
        <GlassCard index={3}>
          <h4 className="text-xs font-semibold text-slate-300 mb-3">每周里程碑</h4>
          <WeeklyTimeline plan={data.weeklyPlan} />
        </GlassCard>
      </div>
    </motion.div>
  )
}
