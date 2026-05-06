import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { motion } from 'framer-motion'
import type { ComponentPropsWithoutRef } from 'react'

interface Props {
  content: string
  isStreaming?: boolean
}

export default function MarkdownRenderer({ content, isStreaming }: Props) {
  return (
    <div className={`prose prose-sm max-w-none prose-invert prose-slate 
      prose-headings:text-slate-100 prose-headings:font-semibold
      prose-p:text-slate-300 prose-p:leading-relaxed
      prose-strong:text-slate-100
      prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
      prose-code:text-cyan-300 prose-code:bg-slate-800 prose-code:px-1 prose-code:py-0.5 prose-code:rounded
      prose-pre:bg-slate-800/80 prose-pre:border prose-pre:border-slate-700/50
      prose-li:text-slate-300
      prose-table:text-slate-300
      prose-th:text-slate-200 prose-th:border-slate-700
      prose-td:border-slate-700/50
      ${isStreaming ? 'cursor-blink' : ''}`}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h3: ({ children, ...props }: ComponentPropsWithoutRef<'h3'>) => (
            <motion.h3
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
              {...(props as any)}
            >
              {children}
            </motion.h3>
          ),
          table: ({ children, ...props }: ComponentPropsWithoutRef<'table'>) => (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="overflow-x-auto rounded-lg border border-slate-700/50 my-3"
            >
              <table {...(props as any)} className="text-xs">
                {children}
              </table>
            </motion.div>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
