import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Users, ChevronDown, ChevronUp, Award, Sparkles } from 'lucide-react'
import type { AgentMessage, ScoreData } from '../lib/api'

interface Props {
  agentMessages?: AgentMessage[]
  scoreData?: ScoreData
  arbiterThinking?: string
  topic?: string
}

// 通过简单的关键词匹配来推断每个 agent 的态度（看好/中立/谨慎）
function detectStance(content: string): 'positive' | 'neutral' | 'cautious' {
  if (!content) return 'neutral'
  const positive = ['看好', '推荐', '可行', '优势', '机会', '有潜力', '建议做', '值得', '强烈', '高概率', '爆款']
  const cautious = ['谨慎', '风险', '不建议', '挑战', '困难', '弱', '难度', '警惕', '注意', '存在问题', '需要警惕', '不适合']
  let pos = 0
  let cau = 0
  for (const w of positive) if (content.includes(w)) pos++
  for (const w of cautious) if (content.includes(w)) cau++
  if (pos >= cau + 2) return 'positive'
  if (cau >= pos + 2) return 'cautious'
  return 'neutral'
}

const STANCE_STYLES = {
  positive: { label: '看好', color: 'text-emerald-400', bg: 'bg-emerald-500/15', border: 'border-emerald-500/40', dot: 'bg-emerald-400' },
  neutral:  { label: '中立', color: 'text-amber-400', bg: 'bg-amber-500/15', border: 'border-amber-500/40', dot: 'bg-amber-400' },
  cautious: { label: '谨慎', color: 'text-orange-400', bg: 'bg-orange-500/15', border: 'border-orange-500/40', dot: 'bg-orange-400' },
} as const

export default function AgentRoundtable({ agentMessages = [], scoreData, arbiterThinking, topic }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [activeRound, setActiveRound] = useState(1)
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null)

  const rounds = useMemo(() => {
    const set = new Set(agentMessages.map(m => m.round || 1))
    return Array.from(set).sort()
  }, [agentMessages])

  // 按 agent 分组
  const agentGroups = useMemo(() => {
    const map = new Map<string, { agent: AgentMessage['agent']; messages: AgentMessage[] }>()
    for (const msg of agentMessages) {
      const id = msg.agent.id
      if (!map.has(id)) map.set(id, { agent: msg.agent, messages: [] })
      map.get(id)!.messages.push(msg)
    }
    return Array.from(map.values())
  }, [agentMessages])

  // 当前轮次的发言
  const currentRoundMessages = useMemo(
    () => agentMessages.filter(m => (m.round || 1) === activeRound),
    [agentMessages, activeRound]
  )

  // 共识度（从 scoreData 推断）
  const consensus = useMemo(() => {
    if (!agentGroups.length) return 0
    const stances = agentGroups.map(g => detectStance(g.messages.map(m => m.content).join(' ')))
    const positive = stances.filter(s => s === 'positive').length
    const neutral = stances.filter(s => s === 'neutral').length
    return Math.round(((positive + neutral * 0.5) / agentGroups.length) * 100)
  }, [agentGroups])

  if (!agentMessages.length && !scoreData) return null

  // 计算每个头像在圆环上的位置
  const agentCount = agentGroups.length
  const radius = 130

  const selectedAgent = selectedAgentId ? agentGroups.find(g => g.agent.id === selectedAgentId) : null

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-4 rounded-2xl border border-violet-700/30 bg-gradient-to-br from-slate-900/95 to-violet-950/30 overflow-hidden shadow-xl"
    >
      {/* 顶部 Header */}
      <div className="px-4 py-3 border-b border-slate-700/40 bg-slate-900/60 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center">
            <Users className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-100">AI 评审团</div>
            <div className="text-[10px] text-slate-500">7 位 AI 专家圆桌辩论 · 已汇总 {agentMessages.length} 条发言</div>
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors"
        >
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          {expanded ? '收起' : '查看完整辩论'}
        </button>
      </div>

      {/* 圆桌主体（始终显示） */}
      <div className="p-5">
        <div className="flex flex-col lg:flex-row gap-5">
          {/* 左：圆桌 */}
          <div className="flex-shrink-0 mx-auto lg:mx-0">
            <div className="relative" style={{ width: 320, height: 320 }}>
              {/* 中心议题 + 共识度环 */}
              <div className="absolute inset-0 flex items-center justify-center">
                <svg width={140} height={140} viewBox="0 0 140 140" className="absolute">
                  <circle cx={70} cy={70} r={62} fill="none" stroke="rgba(148,163,184,0.15)" strokeWidth={4} />
                  <circle
                    cx={70} cy={70} r={62}
                    fill="none"
                    stroke="url(#consensus-grad)"
                    strokeWidth={4}
                    strokeLinecap="round"
                    strokeDasharray={`${(consensus / 100) * 389.6} 389.6`}
                    transform="rotate(-90 70 70)"
                  />
                  <defs>
                    <linearGradient id="consensus-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#a78bfa" />
                      <stop offset="100%" stopColor="#22d3ee" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="z-10 text-center w-32 px-2">
                  <div className="text-[10px] text-slate-500 mb-1">辩论议题</div>
                  <div className="text-xs font-medium text-slate-100 line-clamp-3 leading-snug">{topic || '选题爆款潜力评估'}</div>
                  <div className="mt-2 text-[10px] text-violet-300">共识度 <span className="font-bold text-base text-violet-200">{consensus}%</span></div>
                </div>
              </div>

              {/* 7 位 Agent 头像围一圈 */}
              {agentGroups.map((group, i) => {
                const angle = (i / Math.max(agentCount, 1)) * 2 * Math.PI - Math.PI / 2
                const x = Math.cos(angle) * radius + 160
                const y = Math.sin(angle) * radius + 160
                const stance = detectStance(group.messages.map(m => m.content).join(' '))
                const style = STANCE_STYLES[stance]
                const isSelected = selectedAgentId === group.agent.id

                return (
                  <motion.button
                    key={group.agent.id}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: isSelected ? 1.15 : 1 }}
                    transition={{ delay: 0.1 + i * 0.08, type: 'spring', stiffness: 200 }}
                    onClick={() => setSelectedAgentId(isSelected ? null : group.agent.id)}
                    className={`absolute w-14 h-14 -ml-7 -mt-7 rounded-full border-2 ${style.border} ${style.bg} flex items-center justify-center text-2xl shadow-lg backdrop-blur-sm transition-all hover:scale-110 group`}
                    style={{ left: x, top: y, color: group.agent.color }}
                    title={`${group.agent.name} · ${style.label}`}
                  >
                    <span>{group.agent.emoji || '🤖'}</span>
                    {/* 态度小圆点 */}
                    <span className={`absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-slate-900 ${style.dot}`} />
                    {/* hover 显示名字 */}
                    <span className="absolute top-full mt-1 left-1/2 -translate-x-1/2 text-[10px] font-medium whitespace-nowrap text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity">
                      {group.agent.name}
                    </span>
                  </motion.button>
                )
              })}
            </div>

            {/* 轮次切换 */}
            {rounds.length > 1 && (
              <div className="flex justify-center gap-1.5 mt-2">
                {rounds.map(r => (
                  <button
                    key={r}
                    onClick={() => setActiveRound(r)}
                    className={`text-xs px-2.5 py-1 rounded-full transition-all ${
                      activeRound === r
                        ? 'bg-violet-500/30 text-violet-200 border border-violet-500/50'
                        : 'bg-slate-800 text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    第 {r} 轮
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 右：发言流 */}
          <div className="flex-1 min-w-0 max-h-[340px] overflow-y-auto pr-1 space-y-2">
            <div className="text-[11px] text-slate-500 sticky top-0 bg-slate-900/95 backdrop-blur py-1 z-10">
              {selectedAgent ? `${selectedAgent.agent.name}的全部发言` : `第 ${activeRound} 轮发言（点击头像查看单人发言）`}
            </div>
            {(selectedAgent ? selectedAgent.messages : currentRoundMessages).map((msg, i) => {
              const stance = detectStance(msg.content)
              const style = STANCE_STYLES[stance]
              return (
                <motion.div
                  key={`${msg.agent.id}-${msg.round}-${i}`}
                  initial={{ opacity: 0, x: 8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className={`p-3 rounded-xl bg-slate-800/60 border ${style.border}`}
                >
                  <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                    <span className="text-base">{msg.agent.emoji || '🤖'}</span>
                    <span className="text-xs font-medium text-slate-200">{msg.agent.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full border ${style.border} ${style.bg} ${style.color}`}>
                      {style.label}
                    </span>
                    {!selectedAgent && msg.round && (
                      <span className="text-[10px] text-slate-500 ml-auto">第 {msg.round} 轮</span>
                    )}
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                </motion.div>
              )
            })}
            {(selectedAgent ? selectedAgent.messages : currentRoundMessages).length === 0 && (
              <div className="text-xs text-slate-500 italic px-3 py-4 text-center">该轮次暂无发言</div>
            )}
          </div>
        </div>
      </div>

      {/* 仲裁卡片 */}
      {(scoreData || arbiterThinking) && (
        <div className="border-t border-amber-500/30 bg-gradient-to-r from-amber-950/40 to-orange-950/30 px-5 py-4">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center flex-shrink-0 shadow-lg shadow-amber-500/30">
              <Award className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                <span className="text-sm font-semibold text-amber-200">首席仲裁官</span>
                {scoreData?.total_score !== undefined && (
                  <>
                    <span className="text-[11px] text-amber-400/70">最终评分</span>
                    <span className="text-2xl font-bold text-amber-300 tabular-nums leading-none">
                      {scoreData.total_score}
                    </span>
                    <span className="text-[10px] text-amber-400/70 self-end mb-0.5">/ 100</span>
                  </>
                )}
                {scoreData?.verdict && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-200 ml-auto">
                    {scoreData.verdict}
                  </span>
                )}
              </div>
              {scoreData?.summary && (
                <p className="text-xs text-amber-100/90 leading-relaxed mb-2">{scoreData.summary}</p>
              )}
              {arbiterThinking && !scoreData?.summary && (
                <p className="text-xs text-amber-100/90 leading-relaxed mb-2 line-clamp-3">{arbiterThinking}</p>
              )}

              {/* 三栏：风险 / 行动 / 维度 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-3">
                {scoreData?.key_risks && scoreData.key_risks.length > 0 && (
                  <div className="rounded-lg bg-rose-950/30 border border-rose-700/30 p-2.5">
                    <div className="text-[10px] font-semibold text-rose-300 mb-1 flex items-center gap-1">
                      <span className="w-1 h-1 rounded-full bg-rose-400" />
                      关键风险
                    </div>
                    <ul className="space-y-0.5">
                      {scoreData.key_risks.slice(0, 3).map((r, i) => (
                        <li key={i} className="text-[11px] text-rose-200/90 leading-snug">· {r}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {scoreData?.action_items && scoreData.action_items.length > 0 && (
                  <div className="rounded-lg bg-emerald-950/30 border border-emerald-700/30 p-2.5">
                    <div className="text-[10px] font-semibold text-emerald-300 mb-1 flex items-center gap-1">
                      <Sparkles className="w-2.5 h-2.5" />
                      行动建议
                    </div>
                    <ul className="space-y-0.5">
                      {scoreData.action_items.slice(0, 3).map((a, i) => (
                        <li key={i} className="text-[11px] text-emerald-200/90 leading-snug">· {a}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 完整辩论展开 */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-slate-700/40 bg-slate-950/40"
          >
            <div className="p-4 max-h-[400px] overflow-y-auto space-y-2">
              <div className="text-[11px] text-slate-500 mb-2">完整辩论记录（共 {agentMessages.length} 条）</div>
              {agentMessages.map((msg, i) => {
                const stance = detectStance(msg.content)
                const style = STANCE_STYLES[stance]
                return (
                  <div key={i} className={`p-2.5 rounded-lg bg-slate-800/40 border ${style.border}`}>
                    <div className="flex items-center gap-2 mb-1 text-xs">
                      <span>{msg.agent.emoji || '🤖'}</span>
                      <span className="font-medium text-slate-200">{msg.agent.name}</span>
                      <span className={`text-[9px] px-1.5 rounded ${style.bg} ${style.color}`}>{style.label}</span>
                      <span className="text-[10px] text-slate-500 ml-auto">第 {msg.round || 1} 轮</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  </div>
                )
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
