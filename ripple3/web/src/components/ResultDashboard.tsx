import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BarChart3, Target, Clock, Layers, TrendingUp,
  ChevronRight, Zap, BookOpen, Video, FileText
} from 'lucide-react'

interface TimelineItem {
  day: number
  action: string
  detail: string
  type: 'content' | 'strategy' | 'milestone'
}

interface PlatformCard {
  platform: string
  icon: typeof Video
  color: string
  strategy: string
  priority: 'high' | 'medium' | 'low'
  keyMetrics: string[]
}

interface Props {
  summary: string
  timeline?: TimelineItem[]
  platforms?: PlatformCard[]
  titleVariants?: { text: string; predicted_ctr: number; strategy: string }[]
  hooks?: { text: string; type: string; estimated_retention_boost: string }[]
  consensusScore?: number
}

export default function ResultDashboard({ summary, timeline, platforms, titleVariants, hooks, consensusScore }: Props) {
  const [activeTab, setActiveTab] = useState<'summary' | 'timeline' | 'titles' | 'hooks'>('summary')

  const tabs = [
    { key: 'summary' as const, label: '核心策略', icon: Target },
    ...(timeline?.length ? [{ key: 'timeline' as const, label: '30天路径', icon: Clock }] : []),
    ...(titleVariants?.length ? [{ key: 'titles' as const, label: '标题测试', icon: BarChart3 }] : []),
    ...(hooks?.length ? [{ key: 'hooks' as const, label: 'Hook库', icon: Zap }] : []),
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-slate-700/50 bg-slate-900/80 backdrop-blur-xl overflow-hidden mb-4"
    >
      {/* Tab Navigation */}
      <div className="flex items-center gap-1 px-4 py-2 border-b border-slate-700/40 overflow-x-auto">
        {tabs.map(tab => {
          const Icon = tab.icon
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
                activeTab === tab.key
                  ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              <Icon size={12} />
              {tab.label}
            </button>
          )
        })}
        {consensusScore !== undefined && (
          <div className="ml-auto flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
            <div className="w-2 h-2 rounded-full bg-emerald-400" />
            <span className="text-[10px] text-emerald-300">专家共识度 {Math.round(consensusScore * 100)}%</span>
          </div>
        )}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'summary' && (
          <motion.div
            key="summary"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="p-4"
          >
            {/* Platform Cards */}
            {platforms && platforms.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                {platforms.map((p, i) => {
                  const Icon = p.icon
                  return (
                    <motion.div
                      key={p.platform}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="p-3 rounded-xl border border-slate-700/50 bg-slate-800/50"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: `${p.color}20` }}>
                          <Icon size={14} style={{ color: p.color }} />
                        </div>
                        <div>
                          <div className="text-xs font-medium text-slate-200">{p.platform}</div>
                          <div className={`text-[9px] px-1.5 py-0.5 rounded-full ${
                            p.priority === 'high' ? 'bg-red-500/20 text-red-300' :
                            p.priority === 'medium' ? 'bg-amber-500/20 text-amber-300' :
                            'bg-slate-700 text-slate-400'
                          }`}>
                            {p.priority === 'high' ? '主攻' : p.priority === 'medium' ? '辅助' : '观望'}
                          </div>
                        </div>
                      </div>
                      <p className="text-[11px] text-slate-400 mb-2 line-clamp-2">{p.strategy}</p>
                      <div className="flex flex-wrap gap-1">
                        {p.keyMetrics.map((m, j) => (
                          <span key={j} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-500">{m}</span>
                        ))}
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            )}
            <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">{summary}</div>
          </motion.div>
        )}

        {activeTab === 'timeline' && timeline && (
          <motion.div
            key="timeline"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="p-4"
          >
            <div className="relative pl-6 space-y-3">
              <div className="absolute left-2 top-2 bottom-2 w-0.5 bg-gradient-to-b from-violet-500 via-cyan-500 to-emerald-500 rounded-full" />
              {timeline.map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="relative"
                >
                  <div className={`absolute -left-[18px] top-1.5 w-3 h-3 rounded-full border-2 ${
                    item.type === 'milestone' ? 'bg-emerald-400 border-emerald-400' :
                    item.type === 'strategy' ? 'bg-cyan-400 border-cyan-400' :
                    'bg-violet-400 border-violet-400'
                  }`} />
                  <div className="flex items-start gap-2">
                    <span className="text-[10px] text-slate-500 font-mono min-w-[36px]">D{item.day}</span>
                    <div>
                      <div className="text-xs text-slate-200 font-medium">{item.action}</div>
                      <div className="text-[11px] text-slate-500">{item.detail}</div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {activeTab === 'titles' && titleVariants && (
          <motion.div
            key="titles"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="p-4 space-y-2"
          >
            <div className="text-[10px] text-slate-500 mb-3 flex items-center gap-1">
              <BarChart3 size={10} />
              AI 预测点击率排名（基于平台算法模型）
            </div>
            {titleVariants.sort((a, b) => b.predicted_ctr - a.predicted_ctr).map((t, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -5 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-center gap-3 p-2.5 rounded-xl bg-slate-800/50 border border-slate-700/30"
              >
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${
                  i === 0 ? 'bg-amber-500/20 text-amber-300' :
                  i === 1 ? 'bg-slate-600/30 text-slate-300' :
                  'bg-slate-700/30 text-slate-500'
                }`}>
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-slate-200 truncate">{t.text}</div>
                  <div className="text-[9px] text-slate-500 mt-0.5">策略: {t.strategy}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-mono text-emerald-400">{(t.predicted_ctr * 100).toFixed(1)}%</div>
                  <div className="text-[9px] text-slate-600">CTR</div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}

        {activeTab === 'hooks' && hooks && (
          <motion.div
            key="hooks"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="p-4 space-y-2"
          >
            <div className="text-[10px] text-slate-500 mb-3 flex items-center gap-1">
              <Zap size={10} />
              开场 Hook 推荐（按预估留存提升排序）
            </div>
            {hooks.map((h, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/30"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300">{h.type}</span>
                  <span className="text-[10px] text-emerald-400 font-mono">{h.estimated_retention_boost}</span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed">"{h.text}"</p>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
