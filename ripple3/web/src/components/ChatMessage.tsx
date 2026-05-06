import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, ChevronDown, ChevronUp, ExternalLink, AlertTriangle, X } from 'lucide-react'
import { useState, useCallback, lazy, Suspense } from 'react'
import type { ChatMessage as ChatMsg, GraphNode, GraphData } from '../lib/api'
import MarkdownRenderer from './MarkdownRenderer'
import GraphDetailPanel from './GraphDetailPanel'
import SearchRadar from './SearchRadar'
import TokenUsagePanel from './TokenUsagePanel'
import CopyButton from './CopyButton'
import { expandGraphNode } from '../lib/api'

const KnowledgeGraph3D = lazy(() => import('./KnowledgeGraph3D'))
const WeChatEcosystemPanel = lazy(() => import('./WeChatEcosystemPanel'))
const KOCGrowthDashboard = lazy(() => import('./KOCGrowthDashboard'))
const ResultDashboard = lazy(() => import('./ResultDashboard'))
const AgentRoundtable = lazy(() => import('./AgentRoundtable'))
const ViralScoreDashboard = lazy(() => import('./ViralScoreDashboard'))

interface Props {
  message: ChatMsg
  onSendMessage?: (text: string) => void
}

export default function ChatMessage({ message, onSendMessage }: Props) {
  const [sourcesExpanded, setSourcesExpanded] = useState(false)
  const [selectedGraphNode, setSelectedGraphNode] = useState<GraphNode | null>(null)
  const [graphData, setGraphData] = useState<GraphData | undefined>(message.graph)
  const [isExpandingGraph, setIsExpandingGraph] = useState(false)
  const isUser = message.role === 'user'

  const handleGraphNodeClick = useCallback((node: GraphNode) => {
    setSelectedGraphNode(node)
  }, [])

  const handleGraphExpand = useCallback(async (node: GraphNode) => {
    setIsExpandingGraph(true)
    try {
      const domain = ''
      for await (const event of expandGraphNode(node.id, node.name, node.type, domain)) {
        if (event.type === 'graph') {
          const expandedData = event.data as GraphData
          setGraphData(prev => {
            if (!prev) return expandedData
            const existingIds = new Set(prev.nodes.map(n => n.id))
            const newNodes = expandedData.nodes.filter(n => !existingIds.has(n.id))
            const newLinks = expandedData.links.filter(l => {
              const src = typeof l.source === 'string' ? l.source : (l.source as any).id
              const tgt = typeof l.target === 'string' ? l.target : (l.target as any).id
              return !prev.links.some(existing => {
                const eSrc = typeof existing.source === 'string' ? existing.source : (existing.source as any).id
                const eTgt = typeof existing.target === 'string' ? existing.target : (existing.target as any).id
                return eSrc === src && eTgt === tgt
              })
            })
            return {
              nodes: [...prev.nodes, ...newNodes],
              links: [...prev.links, ...newLinks],
            }
          })
        }
      }
    } catch (err) {
      console.warn('Graph expand failed:', err)
    } finally {
      setIsExpandingGraph(false)
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
          <div className="px-4 py-3 rounded-2xl rounded-br-sm bg-gradient-to-r from-blue-500 to-violet-500 text-white text-sm leading-relaxed shadow-md shadow-blue-900/30">
            {message.content}
          </div>
        </div>
      </motion.div>
    )
  }

  const hasThinking = message.thinking && message.thinking.length > 0
  const hasSources = message.sources && message.sources.length > 0
  const hasGraph = (graphData || message.graph) && (graphData || message.graph)!.nodes && (graphData || message.graph)!.nodes.length > 0
  const hasDataWarning = !!message.dataWarning
  const hasTokenUsage = !!message.tokenUsage
  const currentGraph = graphData || message.graph

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-3 mb-4 relative"
    >
      <div className="flex items-start">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-white shrink-0 shadow-sm">
          <Sparkles className="w-4 h-4" />
        </div>
      </div>

      <div className="flex-1 min-w-0">
        {/* SearchRadar first — progress indication */}
        {hasThinking && (
          <SearchRadar
            stats={message.searchStats}
            steps={message.thinking!}
            isActive={!!message.isStreaming}
          />
        )}

        {hasDataWarning && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-2 mb-3 px-3 py-2 rounded-lg bg-amber-900/20 border border-amber-800 text-xs text-amber-400"
          >
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>{message.dataWarning}</span>
          </motion.div>
        )}

        {/* Knowledge Graph */}
        {hasGraph && (
          <Suspense fallback={<div className="h-[400px] animate-pulse bg-slate-800/30 rounded-2xl mb-3" />}>
            <KnowledgeGraph3D
              data={currentGraph!}
              onNodeClick={handleGraphNodeClick}
              isExpanding={isExpandingGraph}
            />
          </Suspense>
        )}

        {/* AI 评审团圆桌（在图谱之后，最显眼位置） */}
        {(message.agentMessages && message.agentMessages.length > 0) && (
          <Suspense fallback={<div className="h-[300px] animate-pulse bg-slate-800/30 rounded-2xl mb-3" />}>
            <AgentRoundtable
              agentMessages={message.agentMessages}
              scoreData={message.scoreData}
              arbiterThinking={message.arbiterThinking}
            />
          </Suspense>
        )}

        {/* 爆款指数仪表盘 */}
        {message.viralScore && (
          <Suspense fallback={<div className="h-[260px] animate-pulse bg-slate-800/30 rounded-2xl mb-3" />}>
            <ViralScoreDashboard data={message.viralScore} />
          </Suspense>
        )}

        {/* Sources shown before report content (trust-first) */}
        {hasSources && !message.isStreaming && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-3 flex flex-wrap gap-2"
          >
            {message.sources!.slice(0, 6).map((src, i) => {
              let hostname = ''
              try { hostname = new URL(src.url).hostname } catch { hostname = src.url }
              return (
                <a
                  key={i}
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-xs px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700/40 hover:border-blue-600/50 hover:bg-slate-700/50 transition-all group"
                >
                  <img
                    src={`https://www.google.com/s2/favicons?domain=${hostname}&sz=16`}
                    alt=""
                    className="w-4 h-4 rounded-sm shrink-0"
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                  />
                  <span className="text-slate-300 group-hover:text-blue-300 line-clamp-1 max-w-[200px]">{src.title || hostname}</span>
                </a>
              )
            })}
          </motion.div>
        )}

        {/* WeChat & KOC panels */}
        {message.wechatStrategy && (
          <Suspense fallback={<div className="h-40 animate-pulse bg-slate-800/50 rounded-2xl mb-3" />}>
            <WeChatEcosystemPanel strategy={message.wechatStrategy} domain="" />
          </Suspense>
        )}

        {message.kocGrowth && (
          <Suspense fallback={<div className="h-40 animate-pulse bg-slate-800/50 rounded-2xl mb-3" />}>
            <KOCGrowthDashboard data={message.kocGrowth} />
          </Suspense>
        )}

        {(message.titleAbTest || message.hooks) && (
          <Suspense fallback={<div className="h-40 animate-pulse bg-slate-800/50 rounded-2xl mb-3" />}>
            <ResultDashboard
              summary=""
              titleVariants={message.titleAbTest?.titles}
              hooks={message.hooks?.hooks}
            />
          </Suspense>
        )}

        {/* Markdown content — the actual report */}
        {message.content ? (
          <div className="rounded-2xl rounded-tl-sm bg-slate-800/80 border border-slate-700/50 px-4 py-3 shadow-sm backdrop-blur-sm relative group">
            {!message.isStreaming && (
              <div className="absolute top-2.5 right-2.5 opacity-70 group-hover:opacity-100 transition-opacity z-10">
                <CopyButton content={message.content} />
              </div>
            )}
            <MarkdownRenderer content={message.content} isStreaming={message.isStreaming} sources={message.sources} />
          </div>
        ) : message.isStreaming ? (
          <div className="rounded-2xl rounded-tl-sm bg-slate-800/80 border border-slate-700/50 px-4 py-3 shadow-sm backdrop-blur-sm">
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

        {/* Sources at bottom */}
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
                    className="flex items-start gap-2 text-xs p-2 rounded-lg bg-slate-800/50 hover:bg-blue-900/20 transition-colors group"
                  >
                    <span className="text-slate-400 shrink-0">{i + 1}.</span>
                    <span className="text-blue-400 group-hover:underline line-clamp-1">{src.title}</span>
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
                className="text-xs px-3 py-1.5 rounded-full border border-blue-800 bg-blue-900/20 text-blue-400 hover:bg-blue-900/40 transition-colors"
              >
                {step.label}
              </button>
            ))}
          </motion.div>
        )}
      </div>

      {/* Graph detail overlay panel */}
      <AnimatePresence>
        {selectedGraphNode && hasGraph && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-end p-4 bg-black/40 backdrop-blur-sm"
            onClick={() => setSelectedGraphNode(null)}
          >
            <motion.div
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 40 }}
              onClick={e => e.stopPropagation()}
              className="relative w-80 max-h-[80vh] overflow-y-auto"
            >
              <button
                onClick={() => setSelectedGraphNode(null)}
                className="absolute top-2 right-2 z-10 p-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
              <GraphDetailPanel
                node={selectedGraphNode}
                graphData={currentGraph!}
                onClose={() => setSelectedGraphNode(null)}
                onExpand={handleGraphExpand}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
