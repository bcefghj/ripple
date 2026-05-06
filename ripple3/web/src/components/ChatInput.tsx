import { useState, useRef, useEffect } from 'react'
import { Send, Square } from 'lucide-react'

interface Props {
  onSend: (text: string) => void
  isLoading: boolean
}

export default function ChatInput({ onSend, isLoading }: Props) {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + 'px'
    }
  }, [text])

  const handleSubmit = () => {
    if (!text.trim() || isLoading) return
    onSend(text)
    setText('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-4 pt-2">
      <div className="relative flex items-end gap-2 rounded-2xl border border-slate-700/50 bg-slate-900/80 shadow-lg shadow-black/20 backdrop-blur-xl focus-within:border-violet-500/50 focus-within:ring-2 focus-within:ring-violet-500/10 transition-all">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="描述你的内容方向..."
          rows={1}
          className="flex-1 resize-none border-0 bg-transparent py-3.5 pl-4 pr-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-0"
          disabled={isLoading}
        />
        <button
          onClick={handleSubmit}
          disabled={!text.trim() || isLoading}
          className="mr-2 mb-2 flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-r from-violet-500 to-indigo-500 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-violet-500/25 transition-all active:scale-95"
        >
          {isLoading ? (
            <Square className="w-4 h-4" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </div>
    </div>
  )
}
