import { AnimatePresence, motion } from 'framer-motion'
import { Plus, Search, Lightbulb, TrendingUp, PenTool, Palette, X, Menu, Waves, Clock, Trash2, MessageSquare } from 'lucide-react'
import type { Conversation } from '../lib/api'

interface Props {
  isOpen: boolean
  onToggle: () => void
  onNewChat: () => void
  onQuickAction: (prompt: string) => void
  conversations: Conversation[]
  currentConversationId: string
  onLoadConversation: (id: string) => void
  onDeleteConversation: (id: string) => void
}

const actions = [
  { icon: Search, label: '探索领域', prompt: '帮我分析一下这个领域的博主和内容生态' },
  { icon: Lightbulb, label: '发现选题', prompt: '帮我想一些有创意的选题点子' },
  { icon: TrendingUp, label: '评估选题', prompt: '帮我评估这个选题能不能火' },
  { icon: PenTool, label: '创作内容', prompt: '帮我写一篇完整的内容' },
  { icon: Palette, label: '分析风格', prompt: '帮我分析一下这位博主的创作风格' },
]

function timeAgo(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return '刚刚'
    if (mins < 60) return `${mins}分钟前`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours}小时前`
    const days = Math.floor(hours / 24)
    if (days < 7) return `${days}天前`
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  } catch {
    return ''
  }
}

export default function Sidebar({
  isOpen, onToggle, onNewChat, onQuickAction,
  conversations, currentConversationId, onLoadConversation, onDeleteConversation,
}: Props) {
  return (
    <>
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

      <button
        onClick={onToggle}
        aria-label="切换侧边栏"
        className="fixed top-4 left-4 z-50 p-2 rounded-lg bg-slate-900 border border-slate-700 shadow-sm hover:bg-slate-800 transition-colors lg:hidden"
      >
        {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      <aside
        className={`fixed top-0 left-0 h-full w-[260px] z-50 bg-slate-900 border-r border-slate-800/50 flex flex-col shadow-xl transition-transform duration-300 ease-in-out lg:shadow-none lg:relative lg:!translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        {/* Brand */}
        <div className="p-4 border-b border-slate-800/50">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center">
              <Waves className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="font-bold text-sm bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">Ripple</div>
              <div className="text-xs text-slate-400">KOC 内容增长引擎</div>
            </div>
          </div>
          <button
            onClick={onNewChat}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>新对话</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {/* Quick actions */}
          <div className="p-3">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 px-1">
              快捷入口
            </div>
            <div className="space-y-0.5">
              {actions.map(a => (
                <button
                  key={a.label}
                  onClick={() => { onQuickAction(a.prompt); onToggle(); }}
                  className="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg text-sm text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
                >
                  <a.icon className="w-4 h-4" />
                  <span>{a.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* History */}
          {conversations.length > 0 && (
            <div className="p-3 border-t border-slate-800/50">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 px-1 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                历史对话
              </div>
              <div className="space-y-0.5">
                {conversations.map(conv => (
                  <div
                    key={conv.id}
                    className={`group flex items-center gap-2 w-full px-2.5 py-2 rounded-lg text-sm transition-colors cursor-pointer ${
                      conv.id === currentConversationId
                        ? 'bg-blue-900/20 text-blue-400'
                        : 'text-slate-400 hover:bg-slate-800'
                    }`}
                  >
                    <button
                      className="flex items-center gap-2 flex-1 min-w-0 text-left"
                      onClick={() => { onLoadConversation(conv.id); onToggle(); }}
                    >
                      <MessageSquare className="w-3.5 h-3.5 shrink-0 opacity-50" />
                      <div className="flex-1 min-w-0">
                        <div className="truncate text-xs">{conv.title}</div>
                        <div className="text-xs text-slate-500">{timeAgo(conv.updated_at)}</div>
                      </div>
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); onDeleteConversation(conv.id); }}
                      className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-900/30 text-slate-400 hover:text-red-500 transition-all"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  )
}
