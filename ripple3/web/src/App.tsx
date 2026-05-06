import { useState, useRef, useEffect, useMemo } from 'react'
import { useChat } from './hooks/useChat'
import Sidebar from './components/Sidebar'
import HeroWelcome from './components/HeroWelcome'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import AIProgressBar from './components/AIProgressBar'

export default function App() {
  const {
    messages, isLoading, thinkingSteps, sendMessage, clearChat,
    conversationId, conversations, loadHistory, deleteHistory,
  } = useChat()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const hasMessages = messages.length > 0

  const aiPhase = useMemo(() => {
    if (!isLoading) return 'idle' as const
    const lastStep = thinkingSteps[thinkingSteps.length - 1]
    if (!lastStep) return 'searching' as const
    if (lastStep.step?.includes('搜索')) return 'searching' as const
    if (lastStep.step?.includes('图谱') || lastStep.step?.includes('关联')) return 'graphing' as const
    if (lastStep.step?.includes('报告') || lastStep.step?.includes('综合')) return 'reporting' as const
    return 'searching' as const
  }, [isLoading, thinkingSteps])

  const aiProgress = useMemo(() => {
    const lastStep = thinkingSteps[thinkingSteps.length - 1]
    return lastStep?.progress || 0
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
        <AIProgressBar phase={aiPhase} progress={aiProgress} />
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
                className="text-xs px-3 py-1.5 rounded-full border border-slate-700/50 bg-slate-800/60 text-slate-400 hover:border-violet-500/50 hover:text-violet-300 transition-colors"
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
    </div>
  )
}
