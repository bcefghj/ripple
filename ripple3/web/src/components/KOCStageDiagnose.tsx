import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Stethoscope, ArrowRight, Sparkles, Target, AlertTriangle, X } from 'lucide-react'

interface Props {
  onClose?: () => void
  onAction?: (prompt: string) => void
}

const STAGES = [
  {
    id: 'lost',
    name: '0 粉迷茫期',
    range: '0-50 粉',
    color: '#94a3b8',
    bg: 'bg-slate-500/15',
    border: 'border-slate-500/40',
    indicators: ['粉丝 < 50', '笔记 < 5 篇', '无明确人设', '不知道发什么'],
    pain: '不知道做什么内容、什么平台',
    breakthrough: '15 天',
    actions: [
      { label: '🎯 第一步: 选定 1 个垂直赛道', why: '不要既想做美食又想做学习——精准定位是涨粉前提' },
      { label: '🎬 第二步: 发布首批 7 条内容', why: '7 条最少样本数，用来测算法和读者反馈' },
      { label: '👥 第三步: 加入 3 个垂类社群学习', why: '观察头部账号怎么做，少走弯路' },
    ],
  },
  {
    id: 'launching',
    name: '起号验证期',
    range: '50-500 粉',
    color: '#60a5fa',
    bg: 'bg-blue-500/15',
    border: 'border-blue-500/40',
    indicators: ['粉丝 50-500', '笔记 5-20 篇', '初步定位明确', '互动率不稳定'],
    pain: '内容时好时坏，不知道哪条会爆',
    breakthrough: '30 天',
    actions: [
      { label: '📊 第一步: 复盘 Top 3 互动笔记', why: '找出"为什么这 3 条互动高"的共性，复刻' },
      { label: '🔄 第二步: 同主题做 3 个变体测试', why: '同样的话题用不同标题/角度，找出最优解' },
      { label: '🌐 第三步: 跨平台同步分发', why: '小红书出爆款 → 同步发视频号利用社交链' },
    ],
  },
  {
    id: 'scaling',
    name: '起量爬坡期',
    range: '500-5000 粉',
    color: '#a78bfa',
    bg: 'bg-violet-500/15',
    border: 'border-violet-500/40',
    indicators: ['粉丝 500-5000', '笔记 20-50 篇', '人设稳定', '出过 1-2 次小爆款'],
    pain: '增长开始变慢，需要找到新增长点',
    breakthrough: '45 天',
    actions: [
      { label: '🚀 第一步: 制造 1 次"破圈"内容', why: '蹭热点 + 跨界，让非垂类用户也愿意点开' },
      { label: '🤝 第二步: 与 3 个同量级账号互推', why: '互导粉丝，比单打独斗增长快 3 倍' },
      { label: '💎 第三步: 建立差异化"专属栏目"', why: '形成账号记忆点，让用户为某个栏目而关注' },
    ],
  },
  {
    id: 'breakthrough',
    name: '瓶颈突破期',
    range: '5000-1万+ 粉',
    color: '#f59e0b',
    bg: 'bg-amber-500/15',
    border: 'border-amber-500/40',
    indicators: ['粉丝 5000+', '笔记 50+ 篇', '稳定输出', '增长曲线进入平台期'],
    pain: '内容同质化，需要升维突破',
    breakthrough: '60 天',
    actions: [
      { label: '🎯 第一步: 定位"专家级"人设升级', why: '从"分享者"到"专家"，付费意愿天花板拉高' },
      { label: '💼 第二步: 启动商业化测试', why: '广告/带货/课程，验证商业模式' },
      { label: '🌳 第三步: 搭建私域承接转化', why: '公域是流量，私域是留量，构建长期生意' },
    ],
  },
]

export default function KOCStageDiagnose({ onClose, onAction }: Props) {
  const [followers, setFollowers] = useState(80)
  const [posts, setPosts] = useState(8)
  const [avgEngagement, setAvgEngagement] = useState(15)
  const [domain, setDomain] = useState('')
  const [diagnosed, setDiagnosed] = useState(false)

  // 阶段判定
  const currentStageIdx = useMemo(() => {
    if (followers < 50) return 0
    if (followers < 500) return 1
    if (followers < 5000) return 2
    return 3
  }, [followers])

  const currentStage = STAGES[currentStageIdx]
  const nextStage = STAGES[Math.min(currentStageIdx + 1, STAGES.length - 1)]

  // 健康度评分（基于互动率 + 笔记数）
  const healthScore = useMemo(() => {
    const engagementRate = followers > 0 ? (avgEngagement / followers) * 100 : 0
    const engagementScore = Math.min(100, engagementRate * 15)
    const postsScore = Math.min(100, posts * 5)
    return Math.round((engagementScore * 0.6 + postsScore * 0.4))
  }, [followers, posts, avgEngagement])

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="rounded-2xl border border-violet-700/30 bg-gradient-to-br from-slate-900 to-violet-950/30 overflow-hidden shadow-2xl"
    >
      <div className="px-5 py-4 border-b border-slate-700/40 bg-slate-900/60 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
            <Stethoscope className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-100">KOC 阶段诊断</div>
            <div className="text-[11px] text-slate-500">输入账号现状 → AI 诊断当前阶段 + 专属下一步</div>
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="p-5">
        {/* 输入区 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-[11px] text-slate-400 mb-1.5 flex items-center justify-between">
              <span>当前粉丝数</span>
              <span className="text-violet-300 tabular-nums">{followers.toLocaleString()}</span>
            </label>
            <input
              type="range"
              min="0"
              max="20000"
              step="10"
              value={followers}
              onChange={e => setFollowers(Number(e.target.value))}
              className="w-full accent-violet-500"
            />
          </div>
          <div>
            <label className="text-[11px] text-slate-400 mb-1.5 flex items-center justify-between">
              <span>已发笔记数</span>
              <span className="text-violet-300 tabular-nums">{posts}</span>
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={posts}
              onChange={e => setPosts(Number(e.target.value))}
              className="w-full accent-violet-500"
            />
          </div>
          <div>
            <label className="text-[11px] text-slate-400 mb-1.5 flex items-center justify-between">
              <span>单条平均互动数</span>
              <span className="text-violet-300 tabular-nums">{avgEngagement}</span>
            </label>
            <input
              type="range"
              min="0"
              max="500"
              value={avgEngagement}
              onChange={e => setAvgEngagement(Number(e.target.value))}
              className="w-full accent-violet-500"
            />
          </div>
          <div>
            <label className="text-[11px] text-slate-400 mb-1.5">主营领域 (选填)</label>
            <input
              type="text"
              value={domain}
              onChange={e => setDomain(e.target.value)}
              placeholder="如：美食探店 / AI工具评测"
              className="w-full px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-200 focus:border-violet-500 focus:outline-none"
            />
          </div>
        </div>

        {!diagnosed ? (
          <button
            onClick={() => setDiagnosed(true)}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-white text-sm font-medium hover:shadow-lg hover:shadow-emerald-500/25 transition-all"
          >
            🩺 诊断我的账号阶段
          </button>
        ) : (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            {/* 阶段进度条 */}
            <div className="mb-5">
              <div className="text-[11px] text-slate-400 mb-2 flex items-center gap-1">
                <Target className="w-3 h-3" />
                你处于第 {currentStageIdx + 1}/4 阶段
              </div>
              <div className="flex items-center gap-1">
                {STAGES.map((stage, i) => {
                  const isActive = i === currentStageIdx
                  const isPassed = i < currentStageIdx
                  return (
                    <div key={stage.id} className="flex items-center flex-1">
                      <div
                        className={`flex-1 h-12 rounded-lg flex flex-col items-center justify-center px-1 transition-all ${
                          isActive ? `${stage.bg} border-2 ${stage.border} ring-2 ring-offset-1 ring-offset-slate-900` :
                          isPassed ? 'bg-emerald-500/10 border border-emerald-500/30' :
                          'bg-slate-800/40 border border-slate-700/40'
                        }`}
                        style={isActive ? { boxShadow: `0 0 0 1px ${stage.color}` } : {}}
                      >
                        <div className={`text-[10px] font-medium ${isActive ? 'text-slate-100' : isPassed ? 'text-emerald-300' : 'text-slate-500'}`}>
                          {stage.name}
                        </div>
                        <div className={`text-[9px] ${isActive ? 'text-slate-300' : 'text-slate-600'}`}>{stage.range}</div>
                      </div>
                      {i < STAGES.length - 1 && (
                        <ArrowRight className={`w-3 h-3 mx-0.5 ${i < currentStageIdx ? 'text-emerald-400' : 'text-slate-700'}`} />
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* 现状诊断 */}
            <div className={`rounded-xl ${currentStage.bg} border ${currentStage.border} p-4 mb-4`}>
              <div className="flex items-center gap-2 mb-2">
                <div className="text-base font-bold" style={{ color: currentStage.color }}>{currentStage.name}</div>
                <span className="text-[10px] text-slate-400">健康度 {healthScore}/100</span>
                <div className="ml-auto flex items-center gap-1 text-[10px] text-slate-400">
                  <span>预期 {currentStage.breakthrough} 突破</span>
                  <ArrowRight className="w-3 h-3" />
                  <span style={{ color: nextStage.color }}>{nextStage.name}</span>
                </div>
              </div>
              <div className="flex items-start gap-2 text-xs text-slate-300 mb-2">
                <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0 mt-0.5" />
                <span><strong className="text-amber-300">核心痛点：</strong>{currentStage.pain}</span>
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                {currentStage.indicators.map((ind, i) => (
                  <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900/40 text-slate-400">{ind}</span>
                ))}
              </div>
            </div>

            {/* 专属下一步 */}
            <div className="rounded-xl bg-gradient-to-br from-emerald-950/40 to-cyan-950/30 border border-emerald-700/30 p-4">
              <div className="text-[11px] font-semibold text-emerald-300 mb-3 flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                AI 为你定制的 3 步突破方案
              </div>
              <div className="space-y-2">
                {currentStage.actions.map((action, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="rounded-lg bg-slate-900/40 border border-slate-700/40 p-3"
                  >
                    <div className="text-xs font-medium text-emerald-200 mb-1">{action.label}</div>
                    <div className="text-[11px] text-slate-400 leading-relaxed">为什么：{action.why}</div>
                  </motion.div>
                ))}
              </div>
              {onAction && domain && (
                <button
                  onClick={() => onAction(`帮我分析 ${domain} 领域，针对${currentStage.name}（${currentStage.range}），给出具体下一步`)}
                  className="mt-3 w-full py-2 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-xs text-emerald-200 hover:bg-emerald-500/30 transition-all"
                >
                  🚀 进入完整分析（让 AI 评审团圆桌讨论你的方案）
                </button>
              )}
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  )
}
