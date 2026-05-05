import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Video, FileText, Search, Users } from 'lucide-react'

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

function VideoTab({ data }: { data: WeChatStrategy['videoAccount'] }) {
  return (
    <div className="space-y-4">
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

function SearchTab({ data }: { data: WeChatStrategy['search'] }) {
  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-xs font-semibold text-slate-300 mb-2">目标关键词</h4>
        <div className="flex flex-wrap gap-1.5">
          {data.keywords.map((kw, i) => (
            <motion.span
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
              className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700"
            >
              🔍 {kw}
            </motion.span>
          ))}
        </div>
      </div>
      <div>
        <h4 className="text-xs font-semibold text-slate-300 mb-2">优化策略</h4>
        <AnimatedList items={data.optimization} />
      </div>
    </div>
  )
}

function PrivateTab({ data }: { data: WeChatStrategy['privateDomain'] }) {
  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-xs font-semibold text-slate-300 mb-2">转化漏斗</h4>
        <div className="space-y-1">
          {data.funnelSteps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="flex items-center gap-2"
            >
              <div className="w-6 h-6 rounded-full bg-[#07C160]/20 border border-[#07C160]/30 flex items-center justify-center text-[10px] font-bold text-emerald-400">
                {i + 1}
              </div>
              <div className="flex-1 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/50 text-xs text-slate-300">
                {step}
              </div>
              {i < data.funnelSteps.length - 1 && (
                <div className="absolute left-3 top-full w-px h-1 bg-[#07C160]/30" />
              )}
            </motion.div>
          ))}
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
