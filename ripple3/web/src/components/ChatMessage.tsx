import { motion } from 'framer-motion'
import { Sparkles, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import { useState } from 'react'
import type { ChatMessage as ChatMsg } from '../lib/api'
import MarkdownRenderer from './MarkdownRenderer'
import ThinkingPanel from './ThinkingPanel'

interface Props {
  message: ChatMsg
}

export default function ChatMessage({ message }: Props) {
  const [sourcesExpanded, setSourcesExpanded] = useState(false)
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-end mb-4"
      >
        <div className="max-w-[80%] sm:max-w-[70%]">
          <div className="px-4 py-3 rounded-2xl rounded-br-sm bg-gradient-to-r from-blue-500 to-violet-500 text-white text-sm leading-relaxed shadow-md shadow-blue-200/50 dark:shadow-blue-900/30">
            {message.content}
          </div>
        </div>
      </motion.div>
    )
  }

  const hasThinking = message.thinking && message.thinking.length > 0
  const hasSources = message.sources && message.sources.length > 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-3 mb-4"
    >
      <div className="flex items-start">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-white shrink-0 shadow-sm">
          <Sparkles className="w-4 h-4" />
        </div>
      </div>

      <div className="flex-1 min-w-0">
        {hasThinking && <ThinkingPanel steps={message.thinking!} />}

        {message.content ? (
          <div className="rounded-2xl rounded-tl-sm bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 px-4 py-3 shadow-sm">
            <MarkdownRenderer content={message.content} isStreaming={message.isStreaming} />
          </div>
        ) : message.isStreaming ? (
          <div className="rounded-2xl rounded-tl-sm bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 px-4 py-3 shadow-sm">
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <span>Ripple 正在思考</span>
              <span className="flex gap-1">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </span>
            </div>
          </div>
        ) : null}

        {hasSources && (
          <div className="mt-2">
            <button
              onClick={() => setSourcesExpanded(!sourcesExpanded)}
              className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-blue-500 transition-colors"
            >
              <ExternalLink className="w-3 h-3" />
              <span>{message.sources!.length} 个参考来源</span>
              {sourcesExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
            {sourcesExpanded && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-2 space-y-1"
              >
                {message.sources!.map((src, i) => (
                  <a
                    key={i}
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-start gap-2 text-xs p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors group"
                  >
                    <span className="text-slate-400 shrink-0">{i + 1}.</span>
                    <span className="text-blue-600 dark:text-blue-400 group-hover:underline line-clamp-1">{src.title}</span>
                  </a>
                ))}
              </motion.div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  )
}
