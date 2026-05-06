import { useState, useRef, useEffect } from 'react'
import { Plus, Clock } from 'lucide-react'
import { useChat } from './hooks/useChat'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'

export default function App() {
  const {
    messages, isLoading, sendMessage, clearChat,
    conversationId, conversations, loadHistory, deleteHistory,
  } = useChat()
  const [showHistory, setShowHistory] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const hasMessages = messages.length > 0

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
    }
  }, [messages])

  const handleSend = (text: string) => {
    sendMessage(text)
  }

  return (
    <div className="h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Top bar */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-800/50">
        <h1 className="text-base font-semibold bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
          Ripple
        </h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <Clock size={16} />
          </button>
          <button
            onClick={clearChat}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <Plus size={16} />
          </button>
        </div>
      </div>

      {/* History dropdown */}
      {showHistory && (
        <div className="absolute top-14 right-4 z-50 w-72 max-h-80 overflow-y-auto rounded-xl border border-slate-700 bg-slate-900 shadow-xl p-2">
          <div className="text-xs text-slate-500 px-2 py-1 mb-1">历史对话</div>
          {conversations.length === 0 ? (
            <div className="text-xs text-slate-600 px-2 py-3 text-center">暂无历史</div>
          ) : (
            conversations.map(c => (
              <button
                key={c.id}
                onClick={() => { loadHistory(c.id); setShowHistory(false) }}
                className="w-full text-left px-3 py-2 rounded-lg text-xs text-slate-300 hover:bg-slate-800 truncate transition-colors"
              >
                {c.title || c.domain || '未命名对话'}
              </button>
            ))
          )}
        </div>
      )}

      {/* Main content */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        {!hasMessages ? (
          <div className="flex flex-col items-center justify-center min-h-full px-4">
            <h2 className="text-2xl font-bold text-slate-200 mb-2">告诉我你想做什么内容</h2>
            <p className="text-sm text-slate-500 mb-8">AI 深度分析全网数据，30秒内给出完整方案</p>
            <div className="flex flex-wrap justify-center gap-2">
              {[
                { label: '🚀 AI工具测评冷启动', prompt: '我想做一个 AI 工具测评的小红书账号，帮我分析从 0 开始如何冷启动到 1000 粉丝' },
                { label: '🎓 考研Vlog爆款分析', prompt: '帮我分析"考研人的一天"这个选题在小红书和视频号的爆款潜力，给出完整内容方案' },
                { label: '💼 打工人效率神器', prompt: '帮我策划"打工人必备的 10 个效率神器"系列内容，分析竞品和差异化策略' },
              ].map(chip => (
                <button
                  key={chip.label}
                  onClick={() => handleSend(chip.prompt)}
                  className="px-4 py-2 rounded-xl text-xs bg-slate-800/80 border border-slate-700/50 text-slate-300 hover:border-violet-500/40 hover:text-violet-300 transition-colors"
                >
                  {chip.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-6">
            {messages.map((msg, i) => (
              <ChatMessage key={`${conversationId}-${i}`} message={msg} />
            ))}
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} isLoading={isLoading} />
    </div>
  )
}
