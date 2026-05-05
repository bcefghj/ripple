import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Send, Square } from 'lucide-react'

interface Props {
  onSend: (text: string) => void
  isLoading: boolean
  placeholder?: string
}

export default function ChatInput({ onSend, isLoading, placeholder }: Props) {
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
      <motion.div
        className="relative flex items-end gap-2 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-lg shadow-slate-200/50 dark:shadow-black/20 focus-within:border-blue-400 dark:focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100 dark:focus-within:ring-blue-900/30 transition-all"
        layout
      >
        <textarea
          ref={textareaRef}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || '告诉 Ripple 你想做什么内容...'}
          rows={1}
          className="flex-1 resize-none border-0 bg-transparent py-3.5 pl-4 pr-2 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-0"
          disabled={isLoading}
        />
        <button
          onClick={handleSubmit}
          disabled={!text.trim() || isLoading}
          className="mr-2 mb-2 flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-r from-blue-500 to-violet-500 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-blue-500/25 transition-all active:scale-95"
        >
          {isLoading ? (
            <Square className="w-4 h-4" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </motion.div>
      <p className="text-center text-[10px] text-slate-400 mt-2">
        Ripple 可能会出错，请验证重要信息
      </p>
    </div>
  )
}
