import { useState, useRef, useEffect, useMemo } from 'react'
import { Moon, Sun } from 'lucide-react'
import { useChat } from './hooks/useChat'
import { useDarkMode } from './hooks/useDarkMode'
import Sidebar from './components/Sidebar'
import WelcomeCards from './components/WelcomeCards'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import RippleBackground from './components/RippleBackground'
import AgentStatusPanel from './components/AgentStatus'

export default function App() {
  const { messages, isLoading, thinkingSteps, sendMessage, clearChat } = useChat()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [dark, setDark] = useDarkMode()
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
    <div className="h-screen flex bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 relative overflow-hidden">
      <RippleBackground />

      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onNewChat={clearChat}
        onQuickAction={handleSend}
      />

      <main className="flex-1 flex flex-col min-w-0 relative z-10">
        {/* Top bar with dark mode toggle */}
        <div className="flex justify-end items-center px-4 pt-3 pb-1">
          <button
            onClick={() => setDark(!dark)}
            className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="切换深色模式"
          >
            {dark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>

        {/* Agent status bar */}
        {currentAgents.length > 0 && (
          <div className="border-b border-slate-100 dark:border-slate-800">
            <div className="max-w-3xl mx-auto">
              <AgentStatusPanel agents={currentAgents} />
            </div>
          </div>
        )}

        {/* Scrollable chat area */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto"
        >
          {!hasMessages ? (
            <div className="flex flex-col items-center justify-center min-h-full py-12">
              <WelcomeCards onSelect={handleSend} />
            </div>
          ) : (
            <div className="max-w-3xl mx-auto px-4 py-6">
              {messages.map((msg, i) => (
                <ChatMessage key={i} message={msg} />
              ))}
            </div>
          )}
        </div>

        {/* Quick action chips (when chatting) */}
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
                className="text-xs px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:border-blue-300 hover:text-blue-600 dark:hover:border-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                {chip.label}
              </button>
            ))}
          </div>
        )}

        {/* Input area */}
        <ChatInput
          onSend={handleSend}
          isLoading={isLoading}
        />
      </main>
    </div>
  )
}
