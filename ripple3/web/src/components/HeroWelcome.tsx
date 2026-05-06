import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Search, Network, MessageCircle } from 'lucide-react'
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
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-4">
      {/* Logo & Title */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center mb-8"
      >
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-violet-400 to-cyan-400 bg-clip-text text-transparent mb-3">
          KOC 智能增长引擎
        </h1>
        <p className="text-slate-400 text-sm">
          AI 深度分析 × 实时数据 × 微信生态
        </p>
      </motion.div>

      {/* Search Input */}
      <motion.form
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        onSubmit={handleSubmit}
        className="w-full max-w-2xl mb-8"
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

      {/* Value Propositions */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="flex items-center gap-6 mb-10 text-xs text-slate-400"
      >
        <div className="flex items-center gap-1.5">
          <Search className="w-3.5 h-3.5 text-blue-400" />
          <span>实时搜索5引擎</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Network className="w-3.5 h-3.5 text-violet-400" />
          <span>知识图谱可视化</span>
        </div>
        <div className="flex items-center gap-1.5">
          <MessageCircle className="w-3.5 h-3.5 text-emerald-400" />
          <span>微信生态策略</span>
        </div>
      </motion.div>

      {/* Demo Cases Grid */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
        className="w-full max-w-2xl"
      >
        <p className="text-xs text-slate-500 mb-3 text-center">试试这些案例 ↓</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {DEMO_CASES.map((c, i) => (
            <motion.button
              key={c.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + i * 0.05 }}
              onClick={() => onSelect(c.prompt)}
              className="flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-800/60 border border-slate-700/40 hover:border-violet-500/40 hover:bg-slate-800 text-left transition-all group"
            >
              <span className="text-lg shrink-0">{c.emoji}</span>
              <div className="min-w-0">
                <p className="text-xs font-medium text-slate-200 group-hover:text-violet-300 transition-colors truncate">
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
