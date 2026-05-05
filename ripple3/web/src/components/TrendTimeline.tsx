import { motion } from 'framer-motion'
import { Flame } from 'lucide-react'

interface TrendItem {
  title: string
  hot_value: string
  platform: string
  rank: number
}

interface Props {
  trends: Record<string, TrendItem[]>
}

const PLATFORM_CONFIG: Record<string, { color: string; label: string }> = {
  weibo: { color: '#e6162d', label: '微博' },
  douyin: { color: '#161823', label: '抖音' },
  zhihu: { color: '#0066ff', label: '知乎' },
  bilibili: { color: '#fb7299', label: 'B站' },
  baidu: { color: '#306cff', label: '百度' },
}

export default function TrendTimeline({ trends }: Props) {
  const platforms = Object.entries(trends).filter(([, items]) => items.length > 0)

  if (!platforms.length) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-4 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 overflow-hidden"
    >
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-slate-100 dark:border-slate-700">
        <Flame className="w-4 h-4 text-orange-500" />
        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">实时热搜</span>
        <span className="text-xs text-slate-400">{platforms.length} 个平台</span>
      </div>

      <div className="flex overflow-x-auto gap-0 divide-x divide-slate-100 dark:divide-slate-700">
        {platforms.map(([platform, items], pIdx) => {
          const config = PLATFORM_CONFIG[platform] || { color: '#6b7280', label: platform }
          return (
            <div key={platform} className="min-w-[160px] flex-1">
              <div className="px-3 py-1.5 bg-slate-50 dark:bg-slate-800/50">
                <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: config.color }}>
                  {config.label}
                </span>
              </div>
              <div className="px-2 py-1.5 space-y-0.5">
                {items.slice(0, 5).map((item, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -5 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: pIdx * 0.1 + i * 0.05 }}
                    className="flex items-start gap-1.5 px-1.5 py-1 rounded-md hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors cursor-default"
                  >
                    <span className={`text-[10px] font-bold w-4 text-center shrink-0 ${
                      item.rank <= 3 ? 'text-orange-500' : 'text-slate-400'
                    }`}>
                      {item.rank}
                    </span>
                    <span className="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-1 leading-tight">
                      {item.title}
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}
