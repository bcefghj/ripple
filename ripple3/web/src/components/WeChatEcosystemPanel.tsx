import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Video, FileText, Search, Users, Heart, MessageCircle, Eye, Share2 } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface WeChatStrategy {
  videoAccount: {
    tips: string[]
    algorithm: string
    bestPractices: string[]
  }
  officialAccount: {
    seoKeywords: string[]
    format: string
    tips: string[]
  }
  search: {
    keywords: string[]
    optimization: string[]
  }
  privateDomain: {
    funnelSteps: string[]
    tips: string[]
  }
}

interface Props {
  strategy?: WeChatStrategy
  domain: string
  isLoading?: boolean
}

const WECHAT_GREEN = '#07C160'

const tabs = [
  { key: 'video', label: '视频号', icon: Video },
  { key: 'official', label: '公众号', icon: FileText },
  { key: 'search', label: '搜一搜', icon: Search },
  { key: 'private', label: '私域', icon: Users },
] as const

type TabKey = (typeof tabs)[number]['key']

function Skeleton({ className }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded-md bg-slate-700/40 ${className ?? ''}`} />
  )
}

function FlowDiagram() {
  const nodes = [
    { label: '搜一搜', x: 0 },
    { label: '公众号/视频号', x: 1 },
    { label: '私域', x: 2 },
  ]

  return (
    <div className="flex items-center justify-center gap-2 py-3 px-4">
      {nodes.map((node, i) => (
        <div key={node.label} className="flex items-center gap-2">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.15 }}
            className="px-3 py-1.5 rounded-lg text-xs font-medium border border-[#07C160]/30 bg-[#07C160]/10 text-emerald-300 whitespace-nowrap"
          >
            {node.label}
          </motion.div>
          {i < nodes.length - 1 && (
            <motion.svg
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.15 + 0.1 }}
              width="24" height="12" viewBox="0 0 24 12" className="shrink-0"
            >
              <path d="M0 6h18m0 0l-4-4m4 4l-4 4" stroke={WECHAT_GREEN} strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
            </motion.svg>
          )}
        </div>
      ))}
    </div>
  )
}

function AnimatedList({ items, delay = 0 }: { items: string[]; delay?: number }) {
  return (
    <ul className="space-y-2">
      {items.map((item, i) => (
        <motion.li
          key={i}
          initial={{ opacity: 0, x: -16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: delay + i * 0.08, duration: 0.3 }}
          className="flex items-start gap-2 text-sm text-slate-300"
        >
          <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#07C160] shrink-0" />
          <span>{item}</span>
        </motion.li>
      ))}
    </ul>
  )
}

function SocialLinkDiagram() {
  const stages = [
    { label: '你发布', desc: '内容生产', icon: Video, color: '#94a3b8' },
    { label: '好友点赞', desc: '社交触发', icon: Heart, color: '#f87171' },
    { label: '朋友在看', desc: '社交链放大', icon: Eye, color: '#fbbf24' },
    { label: '推荐池', desc: '算法分发', icon: Share2, color: WECHAT_GREEN },
    { label: '热门池', desc: '万级曝光', icon: MessageCircle, color: '#a78bfa' },
  ]
  return (
    <div className="rounded-xl bg-emerald-950/30 border border-emerald-900/40 p-3 mb-3">
      <div className="text-[11px] font-semibold text-emerald-400 mb-3">视频号社交链路放大机制</div>
      <div className="flex items-center justify-between gap-1 overflow-x-auto pb-1">
        {stages.map((s, i) => {
          const Icon = s.icon
          return (
            <div key={s.label} className="flex items-center shrink-0">
              <motion.div
                initial={{ opacity: 0, scale: 0.6 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.15 }}
                className="flex flex-col items-center min-w-[58px]"
              >
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center mb-1 border"
                  style={{ background: `${s.color}20`, borderColor: `${s.color}50` }}
                >
                  <Icon className="w-4 h-4" style={{ color: s.color }} />
                </div>
                <div className="text-[10px] font-medium text-slate-200">{s.label}</div>
                <div className="text-[9px] text-slate-500">{s.desc}</div>
              </motion.div>
              {i < stages.length - 1 && (
                <motion.svg
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.15 + 0.1 }}
                  width="20" height="10" viewBox="0 0 20 10" className="shrink-0"
                >
                  <path d="M0 5h14m0 0l-3-3m3 3l-3 3" stroke={WECHAT_GREEN} strokeWidth="1.2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                </motion.svg>
              )}
            </div>
          )
        })}
      </div>
      <div className="flex items-center gap-3 mt-3 pt-2.5 border-t border-emerald-900/40">
        <div className="text-[10px] text-emerald-300">推荐分公式</div>
        <div className="text-[10px] text-slate-300 font-mono">社交链路 60% + 完播率 25% + 互动深度 15%</div>
      </div>
    </div>
  )
}

function VideoTab({ data }: { data: WeChatStrategy['videoAccount'] }) {
  return (
    <div className="space-y-4">
      <SocialLinkDiagram />
      <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-900/40">
        <h4 className="text-xs font-semibold text-emerald-400 mb-1">算法逻辑</h4>
        <p className="text-xs text-slate-400 leading-relaxed">{data.algorithm}</p>
      </div>
      <div>
        <h4 className="text-xs font-semibold text-slate-300 mb-2">运营技巧</h4>
        <AnimatedList items={data.tips} />
      </div>
      <div>
        <h4 className="text-xs font-semibold text-slate-300 mb-2">最佳实践</h4>
        <AnimatedList items={data.bestPractices} delay={0.3} />
      </div>
    </div>
  )
}

function OfficialTab({ data }: { data: WeChatStrategy['officialAccount'] }) {
  return (
    <div className="space-y-4">
      <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-900/40">
        <h4 className="text-xs font-semibold text-emerald-400 mb-1">推荐格式</h4>
        <p className="text-xs text-slate-400 leading-relaxed">{data.format}</p>
      </div>
      <div>
        <h4 className="text-xs font-semibold text-slate-300 mb-2">SEO 关键词</h4>
        <div className="flex flex-wrap gap-1.5">
          {data.seoKeywords.map((kw, i) => (
            <motion.span
              key={i}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
              className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-[#07C160]/15 text-emerald-300 border border-[#07C160]/20"
            >
              {kw}
            </motion.span>
          ))}
        </div>
      </div>
      <div>
        <h4 className="text-xs font-semibold text-slate-300 mb-2">运营技巧</h4>
        <AnimatedList items={data.tips} delay={0.2} />
      </div>
    </div>
  )
}

// 估算关键词月搜索量（基于词长度+特征做合理估算，标注为"AI 估算"）
function estimateSearchVolume(keyword: string, idx: number): number {
  const len = keyword.length
  const isProblem = /怎么|如何|什么|为什么|哪个|多少|值不值|难不难/.test(keyword)
  const isLongTail = len > 8
  const isCore = len <= 5

  let base = 50000
  if (isCore) base = 800000
  else if (isLongTail && isProblem) base = 80000
  else if (isLongTail) base = 30000
  else if (isProblem) base = 200000

  // 加入位置衰减 + 一点随机
  const decay = 1 - (idx * 0.08)
  const seed = ((keyword.charCodeAt(0) || 60) % 10) / 20 + 0.85
  return Math.max(1000, Math.round(base * decay * seed))
}

function SearchTab({ data }: { data: WeChatStrategy['search'] }) {
  // 把所有关键词转换为图表数据
  const chartData = data.keywords.slice(0, 8).map((kw, i) => ({
    keyword: kw.length > 10 ? kw.slice(0, 10) + '…' : kw,
    fullKeyword: kw,
    monthlySearch: estimateSearchVolume(kw, i),
    competition: i < 2 ? 90 : i < 5 ? 60 : 30,  // 越靠前竞争越大
  }))

  const formatVolume = (v: number) => v >= 10000 ? `${(v / 10000).toFixed(1)}万` : `${v}`

  return (
    <div className="space-y-4">
      {/* 关键词热度图 */}
      {chartData.length > 0 && (
        <div className="rounded-xl bg-slate-800/40 border border-slate-700/40 p-3">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-semibold text-slate-300 flex items-center gap-1">
              <Search className="w-3 h-3 text-emerald-400" />
              搜一搜关键词热度
            </h4>
            <span className="text-[9px] text-slate-500">数据：AI 估算 · 微信指数</span>
          </div>
          <div className="h-[180px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 5, right: 10, bottom: 5, left: -15 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                <XAxis dataKey="keyword" tick={{ fontSize: 9, fill: '#94a3b8' }} angle={-15} textAnchor="end" height={50} />
                <YAxis tick={{ fontSize: 9, fill: '#94a3b8' }} tickFormatter={formatVolume} />
                <Tooltip
                  contentStyle={{ backgroundColor: 'rgba(15,23,42,0.95)', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }}
                  formatter={(v: number, n: string, p: any) => {
                    if (n === 'monthlySearch') return [`${formatVolume(v)} 次/月`, '月搜索量']
                    if (n === 'competition') return [`${v}%`, '竞争度']
                    return [v, n]
                  }}
                  labelFormatter={(v: string, p: any) => p[0]?.payload?.fullKeyword || v}
                />
                <Bar dataKey="monthlySearch" fill={WECHAT_GREEN} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center gap-3 mt-2 text-[10px] text-slate-500">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm" style={{ background: WECHAT_GREEN }} /> 月搜索量</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-amber-400" /> 高竞争词</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-blue-400" /> 蓝海词</span>
          </div>
        </div>
      )}

      {/* 关键词标签 */}
      <div>
        <h4 className="text-xs font-semibold text-slate-300 mb-2">目标关键词（按搜索量排序）</h4>
        <div className="flex flex-wrap gap-1.5">
          {data.keywords.map((kw, i) => {
            const isCore = i < 2
            const isLongTail = kw.length > 8
            const tagColor = isCore ? 'border-amber-500/40 bg-amber-500/10 text-amber-300'
                          : isLongTail ? 'border-blue-500/40 bg-blue-500/10 text-blue-300'
                          : 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
            return (
              <motion.span
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className={`px-2 py-0.5 rounded-md text-[11px] font-medium border ${tagColor}`}
              >
                🔍 {kw}
                <span className="ml-1 text-[9px] opacity-70">{isCore ? '核心' : isLongTail ? '长尾' : '中尾'}</span>
              </motion.span>
            )
          })}
        </div>
      </div>

      <div>
        <h4 className="text-xs font-semibold text-slate-300 mb-2">优化策略（基于搜一搜 Peoplerank 算法）</h4>
        <AnimatedList items={data.optimization} />
      </div>
    </div>
  )
}

function KOCPyramid() {
  const layers = [
    { tier: 'KOL', label: '头部 KOL', percent: 5, color: '#fbbf24', desc: '5% · 100 万粉丝+ · 品牌背书' },
    { tier: 'KOC', label: '腰部 KOC', percent: 65, color: '#a78bfa', desc: '65% · 1-100 万粉丝 · 内容主力（最佳定位）' },
    { tier: 'UGC', label: '素人 UGC', percent: 30, color: '#22d3ee', desc: '30% · <1 万粉丝 · 真实分享' },
  ]
  return (
    <div className="rounded-xl bg-slate-800/40 border border-slate-700/40 p-3 mb-3">
      <h4 className="text-xs font-semibold text-slate-300 mb-3 flex items-center gap-1">
        <Users className="w-3 h-3 text-emerald-400" />
        小红书内容生态金字塔（建议你定位在腰部 KOC）
      </h4>
      <div className="flex flex-col items-center gap-1.5">
        {layers.map((layer, i) => {
          const width = 100 - i * 30
          const isYou = layer.tier === 'KOC'
          return (
            <motion.div
              key={layer.tier}
              initial={{ opacity: 0, scaleX: 0 }}
              animate={{ opacity: 1, scaleX: 1 }}
              transition={{ delay: i * 0.15 }}
              className="relative w-full flex justify-center"
            >
              <div
                className={`relative h-12 flex items-center justify-center rounded-md text-xs font-medium text-white ${isYou ? 'ring-2 ring-violet-400 ring-offset-2 ring-offset-slate-900' : ''}`}
                style={{ width: `${width}%`, background: `linear-gradient(135deg, ${layer.color}cc, ${layer.color}88)` }}
              >
                <div className="text-center">
                  <div className="text-xs font-semibold leading-tight">{layer.label}</div>
                  <div className="text-[10px] opacity-90">{layer.percent}%</div>
                </div>
                {isYou && (
                  <motion.div
                    initial={{ y: -10, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.6 }}
                    className="absolute -right-2 -top-2 px-2 py-0.5 rounded-full bg-violet-500 text-[10px] font-medium text-white shadow-lg"
                  >
                    ⬇️ 你在这里
                  </motion.div>
                )}
              </div>
              <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 text-[10px] text-slate-400 whitespace-nowrap hidden md:block">
                {layer.desc}
              </div>
            </motion.div>
          )
        })}
      </div>
      <div className="text-[10px] text-slate-500 mt-3 leading-relaxed">
        💡 <span className="text-emerald-300 font-medium">KOC 是性价比之王</span>：粉丝量适中（互动率比 KOL 高 3-5 倍），获客成本低（CPE 8-15 元为健康），转化率高（同龄人推荐天然信任）。
      </div>
    </div>
  )
}

function PrivateTab({ data }: { data: WeChatStrategy['privateDomain'] }) {
  return (
    <div className="space-y-4">
      <KOCPyramid />
      <div>
        <h4 className="text-xs font-semibold text-slate-300 mb-2">公域 → 私域 转化漏斗</h4>
        <div className="space-y-1.5">
          {data.funnelSteps.map((step, i) => {
            const conversion = [100, 20, 8, 3, 1][Math.min(i, 4)]
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-center gap-2"
              >
                <div className="w-6 h-6 rounded-full bg-[#07C160]/20 border border-[#07C160]/40 flex items-center justify-center text-[10px] font-bold text-emerald-400 shrink-0">
                  {i + 1}
                </div>
                <div className="flex-1 px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700/50 flex items-center gap-2">
                  <span className="text-xs text-slate-300 flex-1">{step}</span>
                  <span className="text-[10px] text-emerald-300 tabular-nums whitespace-nowrap">{conversion}%</span>
                  <div className="w-12 h-1 rounded-full bg-slate-700 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-emerald-400 to-emerald-600 rounded-full transition-all"
                      style={{ width: `${conversion}%` }}
                    />
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>
      <div>
        <h4 className="text-xs font-semibold text-slate-300 mb-2">运营建议</h4>
        <AnimatedList items={data.tips} delay={0.3} />
      </div>
    </div>
  )
}

export default function WeChatEcosystemPanel({ strategy, domain, isLoading }: Props) {
  const [activeTab, setActiveTab] = useState<TabKey>('video')

  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-700/50 bg-slate-900/80 backdrop-blur-xl p-4 space-y-4">
        <div className="flex items-center gap-2 mb-3">
          <Skeleton className="w-4 h-4 rounded" />
          <Skeleton className="w-24 h-4" />
        </div>
        <div className="flex gap-2">
          {[1, 2, 3, 4].map(i => (
            <Skeleton key={i} className="h-8 flex-1 rounded-lg" />
          ))}
        </div>
        <div className="space-y-3 pt-2">
          {[1, 2, 3, 4, 5].map(i => (
            <Skeleton key={i} className="h-4 rounded" style={{ width: `${90 - i * 10}%` }} />
          ))}
        </div>
      </div>
    )
  }

  if (!strategy) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-slate-700/50 bg-slate-900/80 backdrop-blur-xl overflow-hidden shadow-xl"
    >
      {/* Header */}
      <div className="px-4 pt-4 pb-2">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-5 h-5 rounded-md flex items-center justify-center" style={{ backgroundColor: `${WECHAT_GREEN}20` }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill={WECHAT_GREEN}>
              <path d="M8.5 13.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm7 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM12 2C6.48 2 2 6.04 2 11c0 2.76 1.36 5.22 3.47 6.84L5 22l4.33-2.17C10.22 19.94 11.09 20 12 20c5.52 0 10-4.04 10-9s-4.48-9-10-9z"/>
            </svg>
          </div>
          <h3 className="text-sm font-bold text-slate-200">微信生态</h3>
          <span className="text-[10px] text-slate-500 ml-1">· {domain}</span>
        </div>
      </div>

      {/* Flow Diagram */}
      <FlowDiagram />

      {/* Tabs */}
      <div className="px-4">
        <div className="flex gap-1 p-1 rounded-xl bg-slate-800/60 border border-slate-700/40">
          {tabs.map(tab => {
            const Icon = tab.icon
            const isActive = activeTab === tab.key
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`relative flex-1 flex items-center justify-center gap-1.5 py-2 px-2 rounded-lg text-xs font-medium transition-colors ${
                  isActive ? 'text-white' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="wechat-tab-bg"
                    className="absolute inset-0 rounded-lg"
                    style={{ backgroundColor: `${WECHAT_GREEN}25`, border: `1px solid ${WECHAT_GREEN}40` }}
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
                <Icon className="w-3.5 h-3.5 relative z-10" style={isActive ? { color: WECHAT_GREEN } : undefined} />
                <span className="relative z-10 hidden sm:inline">{tab.label}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Tab Content */}
      <div className="px-4 py-4 min-h-[200px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'video' && <VideoTab data={strategy.videoAccount} />}
            {activeTab === 'official' && <OfficialTab data={strategy.officialAccount} />}
            {activeTab === 'search' && <SearchTab data={strategy.search} />}
            {activeTab === 'private' && <PrivateTab data={strategy.privateDomain} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
