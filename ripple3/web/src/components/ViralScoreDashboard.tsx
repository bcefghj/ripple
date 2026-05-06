import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip,
} from 'recharts'
import { Flame, TrendingUp, AlertTriangle, Zap, Target, Sparkles } from 'lucide-react'
import type { ViralScoreData } from '../lib/api'

interface Props {
  data: ViralScoreData
}

const POOL_COLORS = [
  { name: '冷启动池', threshold: 0, color: '#94a3b8' },
  { name: '初级流量池', threshold: 50, color: '#60a5fa' },
  { name: '热门流量池', threshold: 70, color: '#a78bfa' },
  { name: '全站推荐池', threshold: 85, color: '#f59e0b' },
]

function getPool(score: number) {
  for (let i = POOL_COLORS.length - 1; i >= 0; i--) {
    if (score >= POOL_COLORS[i].threshold) return POOL_COLORS[i]
  }
  return POOL_COLORS[0]
}

// 30 天增长曲线投影（base/optimistic/pessimistic 三条线）
function projectGrowth(score: number) {
  const baseGrowthFactor = score / 100  // 0-1
  const days = [0, 3, 7, 14, 21, 30]
  return days.map(day => {
    const t = day / 30
    // S 型曲线：sigmoid-like
    const sigmoid = 1 / (1 + Math.exp(-5 * (t - 0.4)))
    const base = Math.round(sigmoid * 1000 * (0.5 + baseGrowthFactor))
    const optimistic = Math.round(base * 1.6)
    const pessimistic = Math.round(base * 0.4)
    return { day, base, optimistic, pessimistic }
  })
}

export default function ViralScoreDashboard({ data }: Props) {
  const [showSimulator, setShowSimulator] = useState(false)
  const [simLikes, setSimLikes] = useState(100)
  const [simCollects, setSimCollects] = useState(50)
  const [simShares, setSimShares] = useState(20)
  const [simComments, setSimComments] = useState(15)
  const [simFollows, setSimFollows] = useState(8)

  const pool = getPool(data.total_score)

  // 雷达图数据
  const radarData = useMemo(
    () => (data.dimensions || []).map(d => ({
      name: d.name,
      value: Math.round((d.score / d.max) * 100),
      raw: d.score,
      max: d.max,
    })),
    [data.dimensions]
  )

  // 增长曲线
  const growthData = useMemo(() => projectGrowth(data.total_score), [data.total_score])

  // CES 模拟器实时计算
  const simCES = useMemo(
    () => simLikes * 1 + simCollects * 1 + simShares * 4 + simComments * 4 + simFollows * 8,
    [simLikes, simCollects, simShares, simComments, simFollows]
  )
  const simPoolName =
    simCES >= 1500 ? '全站推荐池' :
    simCES >= 600 ? '热门流量池' :
    simCES >= 200 ? '初级流量池' : '冷启动池'

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-4 rounded-2xl border border-orange-700/30 bg-gradient-to-br from-slate-900/95 to-orange-950/20 overflow-hidden shadow-xl"
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-700/40 bg-slate-900/60 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-orange-500 to-rose-500 flex items-center justify-center">
            <Flame className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-100">爆款指数</div>
            <div className="text-[10px] text-slate-500">{data.engagement_formula || 'CES 算法 · 9 维度评分'}</div>
          </div>
        </div>
        <button
          onClick={() => setShowSimulator(!showSimulator)}
          className="text-[10px] px-2.5 py-1 rounded-full border border-orange-500/40 bg-orange-500/15 text-orange-300 hover:bg-orange-500/25 transition-colors flex items-center gap-1"
        >
          <Zap className="w-3 h-3" />
          {showSimulator ? '收起模拟器' : 'CES 模拟器'}
        </button>
      </div>

      {/* 主体网格 */}
      <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* 左：分数 + 流量池 + 增长曲线 */}
        <div className="space-y-4">
          {/* 大分数 */}
          <div className="text-center md:text-left">
            <div className="flex items-end gap-2 justify-center md:justify-start">
              <div
                className="text-6xl font-bold tabular-nums leading-none bg-clip-text text-transparent bg-gradient-to-br"
                style={{
                  backgroundImage: `linear-gradient(135deg, ${pool.color}, #fbbf24)`,
                }}
              >
                {data.total_score}
              </div>
              <div className="text-slate-500 text-base mb-1">/100</div>
            </div>
            <div className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium" style={{ backgroundColor: `${pool.color}20`, color: pool.color, border: `1px solid ${pool.color}50` }}>
              <Sparkles className="w-3 h-3" />
              预测：{data.predicted_pool || pool.name}
            </div>
            {data.pool_probability && (
              <div className="text-[11px] text-slate-400 mt-1.5">{data.pool_probability}</div>
            )}
          </div>

          {/* 流量池阶梯 */}
          <div>
            <div className="text-[11px] text-slate-500 mb-2 flex items-center gap-1">
              <Target className="w-3 h-3" />
              流量池阶梯（曝光范围）
            </div>
            <div className="space-y-1.5">
              {POOL_COLORS.map((p, i) => {
                const isActive = data.total_score >= p.threshold && (i === POOL_COLORS.length - 1 || data.total_score < POOL_COLORS[i + 1].threshold)
                const isPassed = data.total_score >= p.threshold
                return (
                  <div key={p.name} className={`relative flex items-center gap-2 px-2.5 py-1.5 rounded-lg transition-all ${isActive ? 'ring-2 ring-offset-1 ring-offset-slate-900' : ''}`} style={{ background: isPassed ? `${p.color}18` : 'rgba(30,41,59,0.4)', borderColor: p.color, ...(isActive ? { boxShadow: `0 0 0 1px ${p.color}` } : {}) }}>
                    <div className={`w-2 h-2 rounded-full ${isActive ? 'animate-pulse' : ''}`} style={{ background: isPassed ? p.color : '#475569' }} />
                    <span className={`text-xs font-medium ${isPassed ? 'text-slate-200' : 'text-slate-500'}`}>{p.name}</span>
                    {data.traffic_pools?.[i]?.exposure && (
                      <span className="text-[10px] text-slate-500 ml-auto">{data.traffic_pools[i].exposure}</span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* 30 天粉丝增长投影 */}
          <div>
            <div className="text-[11px] text-slate-500 mb-2 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              30 天粉丝增长预测（含乐观 / 悲观区间）
            </div>
            <div className="h-[120px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={growthData} margin={{ top: 5, right: 5, bottom: 0, left: -25 }}>
                  <defs>
                    <linearGradient id="growth-grad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="day" tick={{ fontSize: 10, fill: '#94a3b8' }} tickFormatter={d => `D${d}`} />
                  <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: 'rgba(15,23,42,0.95)', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }}
                    labelFormatter={(d) => `第 ${d} 天`}
                    formatter={(v: number, n: string) => {
                      const labels: Record<string, string> = { base: '预期', optimistic: '乐观', pessimistic: '悲观' }
                      return [`${v} 粉丝`, labels[n] || n]
                    }}
                  />
                  <Area type="monotone" dataKey="optimistic" stroke="#22d3ee" strokeWidth={1} fill="none" strokeDasharray="3 3" />
                  <Area type="monotone" dataKey="base" stroke="#f59e0b" strokeWidth={2} fill="url(#growth-grad)" />
                  <Area type="monotone" dataKey="pessimistic" stroke="#94a3b8" strokeWidth={1} fill="none" strokeDasharray="3 3" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* 右：维度雷达图 + 优势/不足 */}
        <div className="space-y-4">
          {radarData.length > 0 && (
            <div>
              <div className="text-[11px] text-slate-500 mb-2 flex items-center gap-1">
                <Flame className="w-3 h-3" />
                {radarData.length} 维度评分
              </div>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
                    <PolarGrid stroke="#334155" />
                    <PolarAngleAxis dataKey="name" tick={{ fontSize: 10, fill: '#cbd5e1' }} />
                    <PolarRadiusAxis tick={{ fontSize: 9, fill: '#64748b' }} angle={90} domain={[0, 100]} />
                    <Radar name="得分" dataKey="value" stroke="#fb923c" fill="#fb923c" fillOpacity={0.3} />
                    <Tooltip
                      contentStyle={{ backgroundColor: 'rgba(15,23,42,0.95)', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }}
                      formatter={(v: number, _n, p) => [`${p.payload.raw}/${p.payload.max}`, p.payload.name]}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* 优势 / 不足 */}
          <div className="grid grid-cols-1 gap-2">
            {data.strengths && data.strengths.length > 0 && (
              <div className="rounded-lg p-2.5 bg-emerald-950/30 border border-emerald-700/30">
                <div className="text-[10px] font-semibold text-emerald-300 mb-1">优势</div>
                <ul className="text-[11px] text-emerald-200/90 space-y-0.5">
                  {data.strengths.slice(0, 3).map((s, i) => <li key={i} className="leading-snug">· {s}</li>)}
                </ul>
              </div>
            )}
            {data.weaknesses && data.weaknesses.length > 0 && (
              <div className="rounded-lg p-2.5 bg-rose-950/30 border border-rose-700/30">
                <div className="text-[10px] font-semibold text-rose-300 mb-1 flex items-center gap-1">
                  <AlertTriangle className="w-2.5 h-2.5" />
                  待优化
                </div>
                <ul className="text-[11px] text-rose-200/90 space-y-0.5">
                  {data.weaknesses.slice(0, 3).map((s, i) => <li key={i} className="leading-snug">· {s}</li>)}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* CES 模拟器（展开式） */}
      {showSimulator && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="border-t border-orange-700/30 bg-slate-950/40 px-5 py-4"
        >
          <div className="text-[11px] text-orange-300 mb-3 flex items-center gap-1">
            <Zap className="w-3 h-3" />
            小红书 CES 模拟器 · 拖动滑块预测流量池
          </div>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mb-4">
            {[
              { label: '点赞 ×1', value: simLikes, set: setSimLikes, max: 5000, color: '#f87171' },
              { label: '收藏 ×1', value: simCollects, set: setSimCollects, max: 2000, color: '#fbbf24' },
              { label: '转发 ×4', value: simShares, set: setSimShares, max: 500, color: '#34d399' },
              { label: '评论 ×4', value: simComments, set: setSimComments, max: 500, color: '#60a5fa' },
              { label: '关注 ×8', value: simFollows, set: setSimFollows, max: 200, color: '#a78bfa' },
            ].map(slider => (
              <div key={slider.label}>
                <div className="flex justify-between text-[10px] text-slate-400 mb-1">
                  <span>{slider.label}</span>
                  <span className="tabular-nums" style={{ color: slider.color }}>{slider.value}</span>
                </div>
                <input
                  type="range" min="0" max={slider.max} value={slider.value}
                  onChange={e => slider.set(Number(e.target.value))}
                  className="w-full accent-orange-400"
                  style={{ ['--tw-ring-color' as any]: slider.color }}
                />
              </div>
            ))}
          </div>
          <div className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-orange-950/40 to-rose-950/40 border border-orange-700/40">
            <div className="text-[11px] text-slate-400">CES 总分：</div>
            <motion.div
              key={simCES}
              initial={{ scale: 1.2 }}
              animate={{ scale: 1 }}
              className="text-3xl font-bold tabular-nums text-orange-300"
            >
              {simCES.toLocaleString()}
            </motion.div>
            <div className="text-[10px] text-slate-500 ml-auto">预测流量池：</div>
            <div className="text-sm font-semibold" style={{ color: getPool(simCES / 30).color }}>{simPoolName}</div>
          </div>
          {data.optimization_tips && data.optimization_tips.length > 0 && (
            <div className="mt-3">
              <div className="text-[10px] font-semibold text-amber-300 mb-1.5">AI 优化建议</div>
              <ul className="text-[11px] text-amber-200/90 space-y-0.5">
                {data.optimization_tips.slice(0, 4).map((tip, i) => (
                  <li key={i} className="leading-snug">· {tip}</li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}

      {/* CES 分析底栏 */}
      {data.ces_analysis && (
        <div className="px-5 py-2.5 border-t border-slate-700/40 bg-slate-900/40 text-[11px] text-slate-400 leading-relaxed">
          <span className="text-slate-500 font-medium">分析：</span>
          {data.ces_analysis}
        </div>
      )}
    </motion.div>
  )
}
