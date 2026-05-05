import { motion } from 'framer-motion'
import { Sparkles, ChevronDown, ChevronUp, ExternalLink, AlertTriangle, Database } from 'lucide-react'
import { useState, useCallback } from 'react'
import type { ChatMessage as ChatMsg, GraphNode } from '../lib/api'
import MarkdownRenderer from './MarkdownRenderer'
import ThinkingPanel from './ThinkingPanel'
import KnowledgeGraph3D from './KnowledgeGraph3D'
import GraphDetailPanel from './GraphDetailPanel'
import MultiAgentPanel from './MultiAgentPanel'
import ScoreAnimation from './ScoreAnimation'
import TokenUsagePanel from './TokenUsagePanel'
import ViralScorePanel from './ViralScorePanel'
import { expandGraphNode } from '../lib/api'

interface Props {
  message: ChatMsg
  onSendMessage?: (text: string) => void
}

export default function ChatMessage({ message, onSendMessage }: Props) {
  const [sourcesExpanded, setSourcesExpanded] = useState(false)
  const [selectedGraphNode, setSelectedGraphNode] = useState<GraphNode | null>(null)
  const isUser = message.role === 'user'

  const handleGraphNodeClick = useCallback((node: GraphNode) => {
    setSelectedGraphNode(node)
  }, [])

  const handleGraphExpand = useCallback(async (node: GraphNode) => {
    try {
      const domain = ''
      for await (const event of expandGraphNode(node.id, node.name, node.type, domain)) {
        if (event.type === 'graph') {
          // Graph expansion results would be handled by parent state
          console.log('Graph expanded:', event.data)
        }
      }
    } catch (err) {
      console.warn('Graph expand failed:', err)
    }
  }, [])

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
  const hasGraph = message.graph && message.graph.nodes && message.graph.nodes.length > 0
  const hasAgentMessages = message.agentMessages && message.agentMessages.length > 0
  const hasScore = message.scoreData && message.scoreData.total_score > 0
  const hasSearchStats = message.searchStats && message.searchStats.total_deduped > 0
  const hasDataWarning = !!message.dataWarning
  const hasTokenUsage = !!message.tokenUsage
  const hasViralScore = message.viralScore && message.viralScore.total_score > 0

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

        {hasDataWarning && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-2 mb-3 px-3 py-2 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-xs text-amber-700 dark:text-amber-400"
          >
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>{message.dataWarning}</span>
          </motion.div>
        )}

        {hasSearchStats && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-3 px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800"
          >
            <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1.5">
              <Database className="w-3 h-3" />
              <span className="font-medium">数据来源透明度</span>
              <span className="ml-auto text-[10px]">
                共 {message.searchStats!.total_deduped} 条去重数据
              </span>
            </div>
            <div className="flex flex-wrap gap-1">
              {Object.entries(message.searchStats!.engines).map(([engine, count]) => (
                <span
                  key={engine}
                  className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300"
                >
                  {engine}: {count}
                </span>
              ))}
            </div>
          </motion.div>
        )}

        {hasGraph && (
          <KnowledgeGraph3D
            data={message.graph!}
            onNodeClick={handleGraphNodeClick}
          />
        )}

        {hasAgentMessages && (
          <MultiAgentPanel
            messages={message.agentMessages!}
            arbiterThinking={message.arbiterThinking}
          />
        )}

        {hasScore && (
          <div className="mb-3 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3 shadow-sm">
            <ScoreAnimation
              totalScore={message.scoreData!.total_score}
              dimensions={message.scoreData!.dimensions}
              hkrrDimensions={message.scoreData!.hkrr}
              verdict={message.scoreData!.verdict}
            />
            {message.scoreData!.key_risks && message.scoreData!.key_risks.length > 0 && (
              <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-700">
                <p className="text-xs font-semibold text-red-500 mb-1">风险提示</p>
                <ul className="text-xs text-slate-500 space-y-0.5">
                  {message.scoreData!.key_risks!.map((r, i) => (
                    <li key={i} className="flex items-start gap-1">
                      <span className="text-red-400 shrink-0">•</span> {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {message.scoreData!.action_items && message.scoreData!.action_items.length > 0 && (
              <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-700">
                <p className="text-xs font-semibold text-emerald-500 mb-1">行动建议</p>
                <ul className="text-xs text-slate-500 space-y-0.5">
                  {message.scoreData!.action_items!.map((a, i) => (
                    <li key={i} className="flex items-start gap-1">
                      <span className="text-emerald-400 shrink-0">{i + 1}.</span> {a}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {hasViralScore && (
          <ViralScorePanel score={message.viralScore!} />
        )}

        {message.content ? (
          <div className="rounded-2xl rounded-tl-sm bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 px-4 py-3 shadow-sm">
            <MarkdownRenderer content={message.content} isStreaming={message.isStreaming} />
          </div>
        ) : message.isStreaming && !hasAgentMessages && !hasScore ? (
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

        {hasTokenUsage && (
          <TokenUsagePanel usage={message.tokenUsage!} />
        )}

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
          {message.nextSteps && message.nextSteps.length > 0 && !message.isStreaming && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-3 flex flex-wrap gap-2"
          >
            {message.nextSteps.map((step, i) => (
              <button
                key={i}
                onClick={() => onSendMessage?.(step.prompt)}
                className="text-xs px-3 py-1.5 rounded-full border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors"
              >
                {step.label}
              </button>
            ))}
          </motion.div>
        )}
    </div>

      {/* Graph detail side panel */}
      {selectedGraphNode && hasGraph && (
        <GraphDetailPanel
          node={selectedGraphNode}
          graphData={message.graph!}
          onClose={() => setSelectedGraphNode(null)}
          onExpand={handleGraphExpand}
        />
      )}
    </motion.div>
  )
}
