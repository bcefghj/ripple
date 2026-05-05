import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { TrendingUp, X, RefreshCw } from 'lucide-react'
import { fetchTrends } from '../lib/api'

interface TrendItem {
  title: string
  hot_value: string
  platform: string
  rank: number
}

const COLORS = [
  '#6366f1', '#ec4899', '#f59e0b', '#10b981', '#ef4444',
  '#8b5cf6', '#06b6d4', '#f97316', '#84cc16', '#e11d48',
]

const platformNames: Record<string, string> = {
  weibo: '微博', douyin: '抖音', zhihu: '知乎',
  bilibili: 'B站', baidu: '百度', toutiao: '头条',
  '36kr': '36氪', sspai: '少数派', ithome: 'IT之家', juejin: '掘金',
}

interface Props {
  onClose: () => void
  onTopicSelect?: (prompt: string) => void
}

export default function TrendDashboard({ onClose, onTopicSelect }: Props) {
  const [trends, setTrends] = useState<Record<string, TrendItem[]>>({})
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    setLoading(true)
    const data = await fetchTrends()
    setTrends(data)
    setLoading(false)
  }

  useEffect(() => { loadData() }, [])

  const platformStats = Object.entries(trends)
    .filter(([, items]) => items?.length > 0)
    .map(([key, items]) => ({
      name: platformNames[key] || key,
      count: items.length,
      key,
    }))

  const topItems = Object.values(trends)
    .flat()
    .filter(item => item && item.hot_value && Number(item.hot_value) > 0)
    .sort((a, b) => Number(b.hot_value) - Number(a.hot_value))
    .slice(0, 15)
    .map(item => ({
      ...item,
      displayValue: Number(item.hot_value) > 10000
        ? `${(Number(item.hot_value) / 10000).toFixed(1)}万`
        : item.hot_value,
      numValue: Number(item.hot_value),
    }))

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-800 sticky top-0 bg-white dark:bg-slate-900 z-10">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-violet-500" />
            <h2 className="text-lg font-bold text-slate-800 dark:text-slate-200">
              热搜趋势仪表盘
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadData}
              disabled={loading}
              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-500"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-500"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20 text-slate-400">
            <RefreshCw className="w-6 h-6 animate-spin mr-2" />
            加载热搜数据中...
          </div>
        ) : (
          <div className="p-6 space-y-8">
            {/* Platform distribution */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                  各平台热搜数量
                </h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={platformStats}>
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {platformStats.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                  平台占比
                </h3>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={platformStats}
                      dataKey="count"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {platformStats.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Top trending topics */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                全网热度 TOP 15
              </h3>
              <div className="space-y-1.5">
                {topItems.map((item, i) => (
                  <button
                    key={`${item.title}-${i}`}
                    onClick={() => onTopicSelect?.(`帮我分析"${item.title}"这个话题的内容创作机会`)}
                    className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-violet-50 dark:hover:bg-violet-900/20 transition-colors text-left group"
                  >
                    <span className={`w-6 h-6 flex items-center justify-center rounded-md text-xs font-bold shrink-0 ${
                      i < 3
                        ? 'bg-gradient-to-br from-orange-500 to-red-500 text-white'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                    }`}>
                      {i + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-700 dark:text-slate-300 truncate group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors">
                        {item.title}
                      </p>
                      <p className="text-[10px] text-slate-400">{item.platform}</p>
                    </div>
                    <div className="shrink-0">
                      <div
                        className="h-2 rounded-full bg-gradient-to-r from-violet-500 to-purple-500"
                        style={{
                          width: `${Math.max(20, (item.numValue / (topItems[0]?.numValue || 1)) * 100)}px`,
                        }}
                      />
                      <p className="text-[10px] text-slate-400 text-right mt-0.5">
                        {item.displayValue}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  )
}
