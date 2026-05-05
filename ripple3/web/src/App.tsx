import { useState, useRef, useEffect, useMemo } from 'react'
import { BarChart3 } from 'lucide-react'
import { AnimatePresence } from 'framer-motion'
import { useChat } from './hooks/useChat'
import Sidebar from './components/Sidebar'
import HeroWelcome from './components/HeroWelcome'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import GalaxyBackground from './components/GalaxyBackground'
import AgentStatusPanel from './components/AgentStatus'
import TrendDashboard from './components/TrendDashboard'

export default function App() {
  const {
    messages, isLoading, thinkingSteps, sendMessage, clearChat,
    conversationId, conversations, loadHistory, deleteHistory,
  } = useChat()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [showDashboard, setShowDashboard] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const hasMessages = messages.length > 0

  const currentAgents = useMemo(() => {
    if (!thinkingSteps.length) return []
    for (let i = thinkingSteps.length - 1; i >= 0; i--) {
      if (thinkingSteps[i].agents?.length) return thinkingSteps[i].agents!
    }
    return []
  }, [thinkingSteps])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
    }
  }, [messages])

  const handleSend = (text: string) => {
    sendMessage(text)
    setSidebarOpen(false)
  }

  return (
    <div className="h-screen flex bg-slate-950 text-slate-100 relative overflow-hidden">
      <GalaxyBackground />

      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onNewChat={clearChat}
        onQuickAction={handleSend}
        conversations={conversations}
        currentConversationId={conversationId}
        onLoadConversation={loadHistory}
        onDeleteConversation={deleteHistory}
      />

      <main className="flex-1 flex flex-col min-w-0 relative z-10">
        <div className="flex justify-end items-center gap-1 px-4 pt-3 pb-1">
          <button
            onClick={() => setShowDashboard(true)}
            className="p-2 rounded-lg text-slate-500 hover:bg-slate-800 transition-colors"
            aria-label="热搜仪表盘"
            title="热搜趋势仪表盘"
          >
            <BarChart3 className="w-4 h-4" />
          </button>
        </div>

        {currentAgents.length > 0 && (
          <div className="border-b border-slate-800">
            <div className="max-w-3xl mx-auto">
              <AgentStatusPanel agents={currentAgents} />
            </div>
          </div>
        )}

        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto"
        >
          {!hasMessages ? (
            <HeroWelcome onSelect={handleSend} />
          ) : (
            <div className="max-w-3xl mx-auto px-4 py-6">
              {messages.map((msg, i) => (
                <ChatMessage key={`${conversationId}-${i}`} message={msg} onSendMessage={handleSend} />
              ))}
            </div>
          )}
        </div>

        {hasMessages && !isLoading && (
          <div className="flex justify-center gap-2 px-4 py-1 flex-wrap">
            {[
              { label: '💡 帮我想选题', prompt: '帮我想10个选题灵感' },
              { label: '🔍 分析领域', prompt: '帮我分析一下这个领域的内容生态' },
              { label: '✍️ 写笔记', prompt: '帮我写一篇小红书笔记' },
              { label: '📊 评估爆款', prompt: '帮我评估这个选题的爆款潜力' },
            ].map(chip => (
              <button
                key={chip.label}
                onClick={() => handleSend(chip.prompt)}
                className="text-xs px-3 py-1.5 rounded-full border border-slate-700 bg-slate-800 text-slate-400 hover:border-violet-500/50 hover:text-violet-300 transition-colors"
              >
                {chip.label}
              </button>
            ))}
          </div>
        )}

        <ChatInput
          onSend={handleSend}
          isLoading={isLoading}
        />
      </main>

      <AnimatePresence>
        {showDashboard && (
          <TrendDashboard
            onClose={() => setShowDashboard(false)}
            onTopicSelect={(prompt) => {
              setShowDashboard(false)
              handleSend(prompt)
            }}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
