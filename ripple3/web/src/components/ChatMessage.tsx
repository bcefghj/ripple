import { motion } from 'framer-motion'
import { useState } from 'react'
import type { ChatMessage as ChatMsg, GraphNode } from '../lib/api'
import MarkdownRenderer from './MarkdownRenderer'
import KnowledgeGraph3D from './KnowledgeGraph3D'

interface Props {
  message: ChatMsg
}

export default function ChatMessage({ message }: Props) {
  const [selectedGraphNode, setSelectedGraphNode] = useState<GraphNode | null>(null)
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[80%] px-4 py-2.5 rounded-2xl rounded-tr-sm bg-violet-600/20 border border-violet-500/30 text-sm text-slate-200">
          {message.content}
        </div>
      </div>
    )
  }

  const hasGraph = message.graph && message.graph.nodes?.length > 0
  const hasThinking = message.thinking && message.thinking.length > 0
  const lastStep = hasThinking ? message.thinking![message.thinking!.length - 1] : null

  return (
    <div className="mb-6">
      {/* Progress indicator */}
      {message.isStreaming && lastStep && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700/30"
        >
          <div className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
          <span className="text-xs text-slate-400">{lastStep.label || lastStep.text}</span>
          {lastStep.detail && (
            <span className="text-xs text-slate-600">— {lastStep.detail}</span>
          )}
        </motion.div>
      )}

      {/* Knowledge Graph */}
      {hasGraph && (
        <div className="mb-4 rounded-2xl border border-slate-700/50 overflow-hidden">
          <KnowledgeGraph3D
            data={message.graph!}
            onNodeClick={setSelectedGraphNode}
          />
        </div>
      )}

      {/* Report content */}
      {message.content && (
        <div className="rounded-2xl bg-slate-900/60 border border-slate-700/40 px-5 py-4">
          <MarkdownRenderer content={message.content} isStreaming={message.isStreaming} />
        </div>
      )}

      {/* Streaming placeholder */}
      {message.isStreaming && !message.content && !hasGraph && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-2xl bg-slate-900/60 border border-slate-700/40">
          <div className="flex gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
          <span className="text-xs text-slate-500">Ripple 正在分析...</span>
        </div>
      )}

      {/* Sources */}
      {message.sources && message.sources.length > 0 && (
        <details className="mt-3">
          <summary className="text-xs text-slate-600 cursor-pointer hover:text-slate-400 transition-colors">
            参考来源 ({message.sources.length})
          </summary>
          <div className="mt-2 space-y-1 pl-3">
            {message.sources.slice(0, 10).map((s, i) => (
              <a key={i} href={s.url} target="_blank" rel="noopener"
                className="block text-xs text-slate-500 hover:text-violet-400 truncate transition-colors">
                {s.title}
              </a>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}
