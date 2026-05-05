import { motion, AnimatePresence } from 'framer-motion'
import { useState, useEffect } from 'react'
import { Sparkles, TrendingUp, ArrowRight, Zap, MessageCircle, Flame } from 'lucide-react'
import { fetchTrends } from '../lib/api'

interface TrendItem {
  title: string
  hot_value: string
  platform: string
  rank: number
}

const scenarios = [
  {
    emoji: '🔍',
    title: '我想做自媒体，但不知道选什么领域',
    prompt: '帮我分析一下美食探店、数码科技、职场效率这几个领域，哪个更适合新手入场？',
    gradient: 'from-blue-500/10 to-cyan-500/10',
    border: 'border-blue-200 dark:border-blue-800',
    hover: 'hover:border-blue-400 dark:hover:border-blue-600',
  },
  {
    emoji: '💡',
    title: '最近没灵感了，帮我想几个爆款选题',
    prompt: '帮我想10个美食探店相关的选题灵感，最好能蹭上最近的热点',
    gradient: 'from-amber-500/10 to-orange-500/10',
    border: 'border-amber-200 dark:border-amber-800',
    hover: 'hover:border-amber-400 dark:hover:border-amber-600',
  },
  {
    emoji: '📊',
    title: '这个选题能火吗？帮我评估一下',
    prompt: '帮我评估一下"打工人的一周极简早餐"这个选题的爆款潜力',
    gradient: 'from-emerald-500/10 to-teal-500/10',
    border: 'border-emerald-200 dark:border-emerald-800',
    hover: 'hover:border-emerald-400 dark:hover:border-emerald-600',
  },
  {
    emoji: '✍️',
    title: '帮我写一篇能火的笔记',
    prompt: '帮我写一篇关于"大学生必备的10个效率工具"的小红书笔记',
    gradient: 'from-violet-500/10 to-purple-500/10',
    border: 'border-violet-200 dark:border-violet-800',
    hover: 'hover:border-violet-400 dark:hover:border-violet-600',
  },
  {
    emoji: '🎯',
    title: '学习某个博主的创作方法',
    prompt: '帮我蒸馏分析一下"影视飓风"的创作方法论，我想学习他的内容风格',
    gradient: 'from-rose-500/10 to-pink-500/10',
    border: 'border-rose-200 dark:border-rose-800',
    hover: 'hover:border-rose-400 dark:hover:border-rose-600',
  },
]

interface Props {
  onSelect: (prompt: string) => void
}

export default function WelcomeCards({ onSelect }: Props) {
  const [trends, setTrends] = useState<Record<string, TrendItem[]>>({})
  const [activeTab, setActiveTab] = useState('weibo')

  useEffect(() => {
    fetchTrends().then(data => {
      if (data && Object.keys(data).length > 0) {
        setTrends(data)
        const firstKey = Object.keys(data).find(k => data[k]?.length > 0)
        if (firstKey) setActiveTab(firstKey)
      }
    })
  }, [])

  const platformNames: Record<string, string> = {
    weibo: '微博', douyin: '抖音', zhihu: '知乎',
    bilibili: 'B站', baidu: '百度', toutiao: '头条',
    '36kr': '36氪', sspai: '少数派', ithome: 'IT之家', juejin: '掘金',
  }

  const trendPlatforms = Object.keys(trends).filter(k => trends[k]?.length > 0)

  return (
    <div className="w-full max-w-3xl mx-auto px-4">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-10"
      >
        <div className="inline-flex items-center gap-2.5 mb-4">
          <motion.div
            animate={{ rotate: [0, 10, -10, 0], scale: [1, 1.1, 1] }}
            transition={{ repeat: Infinity, duration: 4, ease: 'easeInOut' }}
          >
            <Sparkles className="w-9 h-9 text-violet-500" />
          </motion.div>
          <h1 className="text-5xl font-black bg-gradient-to-r from-blue-600 via-violet-600 to-purple-600 bg-clip-text text-transparent tracking-tight">
            Ripple
          </h1>
          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-gradient-to-r from-violet-500 to-purple-500 text-white uppercase tracking-wider">
            6.0
          </span>
        </div>
        <p className="text-slate-500 dark:text-slate-400 text-base leading-relaxed max-w-md mx-auto">
          KOC 决策智能平台
          <br />
          <span className="text-xs text-slate-400 dark:text-slate-500">
            9层搜索矩阵 · 多Agent辩论 · CES爆款预测 · 内容DNA分析
          </span>
        </p>
      </motion.div>

      {/* Scenario Cards */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-8"
      >
        <div className="flex items-center gap-2 mb-4">
          <MessageCircle className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
            点击开始对话，或直接在下方输入你的问题
          </span>
        </div>

        <div className="space-y-2.5">
          {scenarios.map((s, i) => (
            <motion.button
              key={s.title}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + i * 0.06 }}
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.99 }}
              onClick={() => onSelect(s.prompt)}
              className={`w-full group flex items-center gap-3 px-4 py-3.5 rounded-xl border bg-white dark:bg-slate-900/50 text-left transition-all duration-200 ${s.border} ${s.hover} hover:shadow-md`}
            >
              <span className="text-xl shrink-0">{s.emoji}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                  {s.title}
                </p>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-slate-500 dark:group-hover:text-slate-300 transition-colors shrink-0" />
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* Real-time Hot Trends */}
      {trendPlatforms.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 overflow-hidden"
        >
          <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-100 dark:border-slate-800">
            <Flame className="w-4 h-4 text-orange-500" />
            <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              实时热榜
            </span>
            <span className="text-[10px] text-slate-400 ml-auto flex items-center gap-1">
              <Zap className="w-3 h-3" /> 数据来自 DailyHotApi + 平台直连
            </span>
          </div>

          {/* Platform tabs */}
          <div className="flex gap-1 px-3 py-2 border-b border-slate-100 dark:border-slate-800 overflow-x-auto scrollbar-hide">
            {trendPlatforms.map(p => (
              <button
                key={p}
                onClick={() => setActiveTab(p)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                  activeTab === p
                    ? 'bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300'
                    : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                {platformNames[p] || p}
              </button>
            ))}
          </div>

          {/* Trend items */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="max-h-64 overflow-y-auto"
            >
              {(trends[activeTab] || []).slice(0, 10).map((item, i) => (
                <button
                  key={`${item.title}-${i}`}
                  onClick={() => onSelect(`帮我分析一下"${item.title}"这个话题，适合做什么类型的内容？`)}
                  className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors text-left group"
                >
                  <span className={`w-5 h-5 flex items-center justify-center rounded text-[10px] font-bold shrink-0 ${
                    i < 3
                      ? 'bg-gradient-to-br from-orange-500 to-red-500 text-white'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                  }`}>
                    {i + 1}
                  </span>
                  <span className="flex-1 text-sm text-slate-700 dark:text-slate-300 truncate group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors">
                    {item.title}
                  </span>
                  {item.hot_value && item.hot_value !== '0' && item.hot_value !== '' && (
                    <span className="text-[10px] text-slate-400 shrink-0 flex items-center gap-0.5">
                      <TrendingUp className="w-3 h-3" />
                      {Number(item.hot_value) > 10000
                        ? `${(Number(item.hot_value) / 10000).toFixed(1)}万`
                        : item.hot_value}
                    </span>
                  )}
                </button>
              ))}
            </motion.div>
          </AnimatePresence>
        </motion.div>
      )}

      {trendPlatforms.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="text-center text-xs text-slate-400 dark:text-slate-500 py-4"
        >
          正在加载实时热榜数据...
        </motion.div>
      )}
    </div>
  )
}
