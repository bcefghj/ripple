import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Search, Network, MessageCircle, Users, Flame, Zap } from 'lucide-react'
import { DEMO_CASES } from '../data/demoCases'

interface Props {
  onSelect: (text: string) => void
}

const TYPING_PROMPTS = DEMO_CASES.map(c => c.prompt)

export default function HeroWelcome({ onSelect }: Props) {
  const [typingIndex, setTypingIndex] = useState(0)
  const [displayText, setDisplayText] = useState('')
  const [inputValue, setInputValue] = useState('')

  useEffect(() => {
    const prompt = TYPING_PROMPTS[typingIndex % TYPING_PROMPTS.length]
    let charIndex = 0
    setDisplayText('')

    const typeInterval = setInterval(() => {
      if (charIndex <= prompt.length) {
        setDisplayText(prompt.slice(0, charIndex))
        charIndex++
      } else {
        clearInterval(typeInterval)
        setTimeout(() => {
          setTypingIndex(prev => (prev + 1) % TYPING_PROMPTS.length)
        }, 2000)
      }
    }, 60)

    return () => clearInterval(typeInterval)
  }, [typingIndex])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (inputValue.trim()) {
      onSelect(inputValue.trim())
      setInputValue('')
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-4 relative">
      {/* 顶部混元徽章 */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="absolute top-4 right-4 hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-slate-700/40 bg-slate-900/60 backdrop-blur"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-[10px] text-slate-400">Powered by 腾讯混元 + 5 引擎搜索</span>
      </motion.div>

      {/* Ripple 波纹背景动画 */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center overflow-hidden">
        {[0, 1, 2].map(i => (
          <motion.div
            key={i}
            className="absolute rounded-full border border-violet-400/20"
            style={{ width: 400, height: 400 }}
            animate={{
              scale: [0.4, 1.6],
              opacity: [0.4, 0],
            }}
            transition={{
              duration: 4,
              delay: i * 1.3,
              repeat: Infinity,
              ease: 'easeOut',
            }}
          />
        ))}
      </div>

      {/* Logo & Title */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center mb-6 relative z-10"
      >
        <h1 className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-blue-400 via-violet-400 to-cyan-400 bg-clip-text text-transparent mb-3 leading-tight">
          把 60 秒的内容直觉<br className="sm:hidden" />变成 5 分钟的可执行方案
        </h1>
        <p className="text-slate-400 text-sm max-w-xl mx-auto">
          AI 帮大学生 KOC 在小红书 + 微信视频号 + 搜一搜 + 公众号生态长出第一个 1000 粉丝
        </p>
      </motion.div>

      {/* Search Input */}
      <motion.form
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        onSubmit={handleSubmit}
        className="w-full max-w-2xl mb-8 relative z-10"
      >
        <div className="relative group">
          <input
            type="text"
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            placeholder={displayText || '描述你的内容方向...'}
            className="w-full px-5 py-4 rounded-2xl bg-slate-800/80 border border-slate-700/50 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/10 transition-all"
          />
          <button
            type="submit"
            disabled={!inputValue.trim()}
            className="absolute right-3 top-1/2 -translate-y-1/2 w-9 h-9 flex items-center justify-center rounded-xl bg-gradient-to-r from-violet-500 to-indigo-500 text-white disabled:opacity-30 hover:shadow-lg hover:shadow-violet-500/25 transition-all active:scale-95"
          >
            <Search className="w-4 h-4" />
          </button>
        </div>
      </motion.form>

      {/* Value Propositions — 5 个核心 AI 原生卖点 */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 mb-8 max-w-3xl w-full px-2 relative z-10"
      >
        {[
          { icon: Search, label: '5 引擎实时搜索', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30' },
          { icon: Network, label: '内容生态图', color: 'text-violet-400', bg: 'bg-violet-500/10', border: 'border-violet-500/30' },
          { icon: Users, label: 'AI 评审团', color: 'text-pink-400', bg: 'bg-pink-500/10', border: 'border-pink-500/30' },
          { icon: Flame, label: 'CES 爆款指数', color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30' },
          { icon: MessageCircle, label: '微信生态策略', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' },
        ].map((item, i) => {
          const Icon = item.icon
          return (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + i * 0.05 }}
              className={`flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg ${item.bg} border ${item.border} backdrop-blur-sm`}
            >
              <Icon className={`w-3.5 h-3.5 ${item.color}`} />
              <span className={`text-[11px] font-medium ${item.color}`}>{item.label}</span>
            </motion.div>
          )
        })}
      </motion.div>

      {/* Demo Cases Grid */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
        className="w-full max-w-2xl relative z-10"
      >
        <p className="text-xs text-slate-500 mb-3 text-center flex items-center justify-center gap-1.5">
          <Zap className="w-3 h-3 text-amber-400" />
          点击任意案例 · 即时查看完整演示
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {DEMO_CASES.map((c, i) => (
            <motion.button
              key={c.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + i * 0.05 }}
              onClick={() => onSelect(c.prompt)}
              className="flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-800/60 border border-slate-700/40 hover:border-violet-500/40 hover:bg-slate-800 text-left transition-all group relative overflow-hidden"
            >
              <span className="absolute top-1.5 right-1.5 text-[9px] px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-0.5">
                <Zap className="w-2 h-2" />
                即时
              </span>
              <span className="text-lg shrink-0">{c.emoji}</span>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-slate-200 group-hover:text-violet-300 transition-colors truncate pr-12">
                  {c.title}
                </p>
                <p className="text-[11px] text-slate-500 truncate mt-0.5">
                  {c.prompt.length > 25 ? c.prompt.slice(0, 25) + '...' : c.prompt}
                </p>
              </div>
            </motion.button>
          ))}
        </div>
      </motion.div>
    </div>
  )
}
