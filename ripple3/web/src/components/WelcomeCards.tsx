import { motion } from 'framer-motion'
import { Search, Lightbulb, TrendingUp, PenTool } from 'lucide-react'

const cards = [
  {
    icon: Search,
    title: '探索领域',
    desc: '了解内容生态、热门博主和入场机会',
    prompt: '我对美食探店感兴趣，帮我分析一下这个领域的内容生态',
    color: 'from-blue-500 to-cyan-400',
  },
  {
    icon: Lightbulb,
    title: '发现选题',
    desc: 'AI 帮你想出有创意的选题点子',
    prompt: '帮我想10个职场效率类的选题灵感',
    color: 'from-amber-500 to-orange-400',
  },
  {
    icon: TrendingUp,
    title: '评估选题',
    desc: '12维度深度评分，预测爆款潜力',
    prompt: '帮我评估「月薪3000吃遍北京」这个选题的爆款潜力',
    color: 'from-emerald-500 to-teal-400',
  },
  {
    icon: PenTool,
    title: '创作内容',
    desc: '从选题到多平台文案，一站式完成',
    prompt: '帮我写一篇关于「5个提升工作效率的AI工具推荐」的小红书笔记',
    color: 'from-violet-500 to-purple-400',
  },
]

interface Props {
  onSelect: (prompt: string) => void
}

export default function WelcomeCards({ onSelect }: Props) {
  return (
    <div className="w-full max-w-3xl mx-auto px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center mb-8"
      >
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent mb-2">
          Ripple
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm">
          你的 KOC 内容灵感助手 — 从选题到创作，对话即完成
        </p>
      </motion.div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {cards.map((card, i) => (
          <motion.button
            key={card.title}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.08 }}
            whileHover={{ y: -2, scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onSelect(card.prompt)}
            className="group relative flex items-start gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 text-left hover:border-blue-300 dark:hover:border-blue-700 hover:shadow-lg hover:shadow-blue-100/50 dark:hover:shadow-blue-900/20 transition-all"
          >
            <div className={`flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br ${card.color} text-white shrink-0 shadow-sm`}>
              <card.icon className="w-5 h-5" />
            </div>
            <div>
              <div className="font-semibold text-sm text-slate-900 dark:text-slate-100 mb-0.5">
                {card.title}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                {card.desc}
              </div>
            </div>
          </motion.button>
        ))}
      </div>
    </div>
  )
}
