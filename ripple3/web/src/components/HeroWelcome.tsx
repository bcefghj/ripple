import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import { Sparkles, TrendingUp, Zap, ArrowRight, Search, Globe } from 'lucide-react'
import { DEMO_CASES } from '../data/demoCases'

interface Props {
  onSelect: (prompt: string) => void
}

const SHOWCASE_CASES = DEMO_CASES.slice(0, 3).map((c, i) => ({
  emoji: c.emoji,
  title: c.title,
  subtitle: c.subtitle,
  prompt: c.prompt,
  gradient: ['from-violet-600/20 to-indigo-600/20', 'from-cyan-600/20 to-blue-600/20', 'from-amber-600/20 to-orange-600/20'][i],
  border: ['border-violet-500/30', 'border-cyan-500/30', 'border-amber-500/30'][i],
  stats: c.tags.join(' · '),
}))

const TYPING_TEXTS = [
  '帮我分析美食探店赛道的机会...',
  '这个选题能火吗？帮我评估一下...',
  '如何从 0 开始做好一个小红书账号...',
  '帮我写一篇能上热门的笔记...',
]

export default function HeroWelcome({ onSelect }: Props) {
  const [inputValue, setInputValue] = useState('')
  const [typingIndex, setTypingIndex] = useState(0)
  const [displayText, setDisplayText] = useState('')
  const [isTyping, setIsTyping] = useState(true)

  useEffect(() => {
    if (!isTyping) return
    const text = TYPING_TEXTS[typingIndex]
    let charIndex = 0
    const interval = setInterval(() => {
      if (charIndex <= text.length) {
        setDisplayText(text.slice(0, charIndex))
        charIndex++
      } else {
        clearInterval(interval)
        setTimeout(() => {
          setDisplayText('')
          setTypingIndex((typingIndex + 1) % TYPING_TEXTS.length)
        }, 2000)
      }
    }, 60)
    return () => clearInterval(interval)
  }, [typingIndex, isTyping])

  const handleSubmit = () => {
    if (inputValue.trim()) {
      onSelect(inputValue.trim())
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-full py-8 px-4 relative">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="text-center mb-8 max-w-2xl"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring' }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-violet-500/10 to-cyan-500/10 border border-violet-500/20 mb-6"
        >
          <Sparkles size={14} className="text-violet-400" />
          <span className="text-xs text-violet-300 font-medium">Powered by 9 层搜索矩阵 · 7 位 AI 专家 · 腾讯混元</span>
        </motion.div>

        <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-white via-violet-200 to-cyan-200 bg-clip-text text-transparent mb-4">
          告诉我你想做什么内容
        </h1>
        <p className="text-base text-slate-400 mb-2">
          AI 深度分析全网数据，为你找到增长路径
        </p>
        <div className="flex items-center justify-center gap-4 text-xs text-slate-500">
          <span className="flex items-center gap-1"><Search size={10} /> 15+ 搜索引擎</span>
          <span className="flex items-center gap-1"><Globe size={10} /> 实时热点追踪</span>
          <span className="flex items-center gap-1"><TrendingUp size={10} /> 爆款预测</span>
        </div>
      </motion.div>

      {/* Input Box */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="w-full max-w-xl mb-10"
      >
        <div className="relative group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-violet-600 to-cyan-600 rounded-2xl blur opacity-20 group-hover:opacity-40 transition-opacity" />
          <div className="relative flex items-center bg-slate-900/90 border border-slate-700/50 rounded-2xl px-4 py-3 backdrop-blur-xl">
            <input
              type="text"
              value={inputValue}
              onChange={e => { setInputValue(e.target.value); setIsTyping(false) }}
              onFocus={() => setIsTyping(false)}
              onKeyDown={e => e.key === 'Enter' && handleSubmit()}
              placeholder={isTyping ? displayText + '|' : '描述你的内容方向、想做的账号或具体选题...'}
              className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSubmit}
              className="ml-2 px-4 py-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 text-white text-xs font-medium flex items-center gap-1 hover:shadow-lg hover:shadow-violet-500/25 transition-shadow"
            >
              <Zap size={12} />
              深度分析
            </motion.button>
          </div>
        </div>
      </motion.div>

      {/* Showcase Cases */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="w-full max-w-3xl"
      >
        <div className="flex items-center gap-2 mb-4 px-1">
          <TrendingUp size={14} className="text-slate-500" />
          <span className="text-xs text-slate-500 font-medium">精选案例 · 点击即可体验完整分析</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {SHOWCASE_CASES.map((item, i) => (
            <motion.button
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 + i * 0.1 }}
              whileHover={{ y: -4, scale: 1.02 }}
              onClick={() => onSelect(item.prompt)}
              className={`group relative text-left p-4 rounded-xl border ${item.border} bg-gradient-to-br ${item.gradient} backdrop-blur-sm hover:shadow-lg transition-all`}
            >
              <div className="text-2xl mb-2">{item.emoji}</div>
              <div className="text-sm font-semibold text-white mb-1">{item.title}</div>
              <div className="text-xs text-slate-400 mb-3">{item.subtitle}</div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-slate-500">{item.stats}</span>
                <ArrowRight size={12} className="text-slate-600 group-hover:text-violet-400 transition-colors" />
              </div>
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="flex flex-wrap justify-center gap-2 mt-8"
      >
        {[
          { label: '🔥 今日热点选题', prompt: '帮我从今日全网热搜中找出 5 个适合新手 KOC 的选题' },
          { label: '📊 竞品拆解', prompt: '帮我拆解分析小红书"影视飓风"的内容方法论' },
          { label: '🎯 账号诊断', prompt: '我的小红书账号做美食探店，目前 500 粉，帮我诊断问题并给出增长建议' },
          { label: '✍️ 爆款笔记', prompt: '帮我写一篇关于"大学生省钱神器"的小红书爆款笔记' },
        ].map((chip, i) => (
          <motion.button
            key={i}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onSelect(chip.prompt)}
            className="px-3 py-1.5 rounded-full text-xs bg-slate-800/60 border border-slate-700/50 text-slate-400 hover:text-violet-300 hover:border-violet-500/30 transition-colors"
          >
            {chip.label}
          </motion.button>
        ))}
      </motion.div>
    </div>
  )
}
