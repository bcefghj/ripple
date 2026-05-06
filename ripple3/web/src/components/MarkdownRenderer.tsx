import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { motion } from 'framer-motion'
import { useState } from 'react'
import type { ComponentPropsWithoutRef } from 'react'
import type { Citation } from '../lib/api'

interface Props {
  content: string
  isStreaming?: boolean
  sources?: Citation[]
}

function CitationBadge({ index, source }: { index: number; source?: Citation }) {
  const [showTooltip, setShowTooltip] = useState(false)

  let hostname = ''
  try { hostname = source?.url ? new URL(source.url).hostname : '' } catch { hostname = '' }

  return (
    <span className="relative inline-block">
      <button
        className="inline-flex items-center justify-center w-4 h-4 text-[10px] font-semibold bg-blue-500/20 text-blue-400 rounded-full hover:bg-blue-500/40 transition-colors align-super ml-0.5 cursor-pointer"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onClick={() => source?.url && window.open(source.url, '_blank')}
      >
        {index}
      </button>
      {showTooltip && source && (
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-2.5 rounded-lg bg-slate-800 border border-slate-700/50 shadow-xl z-50"
        >
          <div className="flex items-start gap-2">
            {hostname && (
              <img
                src={`https://www.google.com/s2/favicons?domain=${hostname}&sz=16`}
                alt=""
                className="w-4 h-4 rounded-sm mt-0.5 shrink-0"
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
              />
            )}
            <div className="min-w-0">
              <p className="text-xs font-medium text-slate-200 line-clamp-2 leading-snug">{source.title}</p>
              {hostname && <p className="text-[10px] text-slate-500 mt-0.5 truncate">{hostname}</p>}
              {source.snippet && (
                <p className="text-[10px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">{source.snippet}</p>
              )}
            </div>
          </div>
          <div className="absolute top-full left-1/2 -translate-x-1/2 w-2 h-2 bg-slate-800 border-r border-b border-slate-700/50 transform rotate-45 -mt-1" />
        </motion.div>
      )}
    </span>
  )
}

function processInlineCitations(text: string, sources?: Citation[]): (string | JSX.Element)[] {
  const parts: (string | JSX.Element)[] = []
  const regex = /\[(\d+)\]/g
  let lastIndex = 0
  let match

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index))
    }
    const num = parseInt(match[1], 10)
    const source = sources?.[num - 1]
    parts.push(<CitationBadge key={`cite-${match.index}`} index={num} source={source} />)
    lastIndex = regex.lastIndex
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }

  return parts.length > 0 ? parts : [text]
}

export default function MarkdownRenderer({ content, isStreaming, sources }: Props) {
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
          p: ({ children, ...props }: ComponentPropsWithoutRef<'p'>) => {
            if (!sources || sources.length === 0) {
              return <p {...(props as any)}>{children}</p>
            }
            const processed = Array.isArray(children)
              ? children.map((child, i) =>
                  typeof child === 'string'
                    ? processInlineCitations(child, sources)
                    : child
                )
              : typeof children === 'string'
              ? processInlineCitations(children, sources)
              : children
            return <p {...(props as any)}>{processed}</p>
          },
          li: ({ children, ...props }: ComponentPropsWithoutRef<'li'>) => {
            if (!sources || sources.length === 0) {
              return <li {...(props as any)}>{children}</li>
            }
            const processed = Array.isArray(children)
              ? children.map((child) =>
                  typeof child === 'string'
                    ? processInlineCitations(child, sources)
                    : child
                )
              : typeof children === 'string'
              ? processInlineCitations(children, sources)
              : children
            return <li {...(props as any)}>{processed}</li>
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
