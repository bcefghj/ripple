import { AnimatePresence, motion } from 'framer-motion'
import { Plus, Search, Lightbulb, TrendingUp, PenTool, Palette, X, Menu, Waves } from 'lucide-react'

interface Props {
  isOpen: boolean
  onToggle: () => void
  onNewChat: () => void
  onQuickAction: (prompt: string) => void
}

const actions = [
  { icon: Search, label: '探索领域', prompt: '帮我分析一下这个领域的博主和内容生态' },
  { icon: Lightbulb, label: '发现选题', prompt: '帮我想一些有创意的选题点子' },
  { icon: TrendingUp, label: '评估选题', prompt: '帮我评估这个选题能不能火' },
  { icon: PenTool, label: '创作内容', prompt: '帮我写一篇完整的内容' },
  { icon: Palette, label: '分析风格', prompt: '帮我分析一下这位博主的创作风格' },
]

export default function Sidebar({ isOpen, onToggle, onNewChat, onQuickAction }: Props) {
  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onToggle}
            className="fixed inset-0 bg-black/30 z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Toggle button */}
      <button
        onClick={onToggle}
        className="fixed top-4 left-4 z-50 p-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors lg:hidden"
      >
        {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Sidebar panel */}
      <aside
        className={`fixed top-0 left-0 h-full w-[260px] z-50 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col shadow-xl transition-transform duration-300 ease-in-out lg:shadow-none lg:relative lg:!translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        {/* Brand */}
        <div className="p-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center">
              <Waves className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="font-bold text-sm bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">Ripple</div>
              <div className="text-[10px] text-slate-400">KOC 内容灵感助手</div>
            </div>
          </div>
          <button
            onClick={onNewChat}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>新对话</span>
          </button>
        </div>

        {/* Quick actions */}
        <div className="flex-1 overflow-y-auto p-3">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-2 px-1">
            快捷入口
          </div>
          <div className="space-y-0.5">
            {actions.map(a => (
              <button
                key={a.label}
                onClick={() => { onQuickAction(a.prompt); onToggle(); }}
                className="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg text-sm text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
              >
                <a.icon className="w-4 h-4" />
                <span>{a.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-slate-100 dark:border-slate-800">
          <p className="text-[10px] text-slate-400 leading-relaxed">
            直接用自然语言告诉我你想做什么，Ripple 会自动理解你的需求。
          </p>
        </div>
      </aside>
    </>
  )
}
