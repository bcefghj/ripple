import type { ChatMessage, AgentMessage, ScoreData, ViralScoreData, WeChatStrategy } from '../lib/api'

export interface DemoCase {
  id: string
  title: string
  prompt: string
  emoji: string
  result: ChatMessage
}

// ── 7 位 AI 评审团（与后端 multi_agent.py 中定义保持一致） ────────────────
const AGENTS = {
  data:     { id: 'agent-data',     name: '数据分析师',  emoji: '📊', color: '#60a5fa' },
  content:  { id: 'agent-content',  name: '内容策划师',  emoji: '🎨', color: '#f472b6' },
  psych:    { id: 'agent-psych',    name: '用户心理专家', emoji: '🧠', color: '#a78bfa' },
  platform: { id: 'agent-platform', name: '平台运营专家', emoji: '⚙️', color: '#34d399' },
  risk:     { id: 'agent-risk',     name: '风险评估师',  emoji: '🛡️', color: '#fb923c' },
  research: { id: 'agent-research', name: '行业研究员',  emoji: '🔬', color: '#22d3ee' },
  advocate: { id: 'agent-advocate', name: '用户代言人',  emoji: '👤', color: '#fbbf24' },
} as const

type AgentKey = keyof typeof AGENTS

function buildAgentMessages(rounds: { agent: AgentKey; round: number; content: string }[]): AgentMessage[] {
  return rounds.map(({ agent, round, content }) => ({
    agent: AGENTS[agent],
    round,
    content,
  }))
}

// ── 通用维度模板（按需替换 score 与 reason） ──────────────────────────────
function buildDimensions(scores: { id: string; name: string; score: number; max: number; reason: string }[]) {
  return scores
}

const DEFAULT_TRAFFIC_POOLS = [
  { name: '冷启动池', exposure: '100-500曝光', threshold: 'CTR>=3%' },
  { name: '初级流量池', exposure: '1k-5k曝光', threshold: '完播率>20%' },
  { name: '热门流量池', exposure: '1万+曝光', threshold: '搜索匹配+持续高互动' },
  { name: '全站推荐池', exposure: '10万+曝光', threshold: '跨圈层+高CES' },
]

const CES_WEIGHTS = { '关注': 8, '评论': 4, '转发': 4, '收藏': 1, '点赞': 1 }

function viralScore(opts: {
  total: number
  pool: string
  poolProb: string
  analysis: string
  dimensions: { id: string; name: string; score: number; max: number; reason: string }[]
  strengths: string[]
  weaknesses: string[]
  tips: string[]
  formula?: string
}): ViralScoreData {
  return {
    total_score: opts.total,
    dimensions: opts.dimensions,
    predicted_pool: opts.pool,
    pool_probability: opts.poolProb,
    ces_analysis: opts.analysis,
    ces_weights: CES_WEIGHTS,
    traffic_pools: DEFAULT_TRAFFIC_POOLS,
    strengths: opts.strengths,
    weaknesses: opts.weaknesses,
    optimization_tips: opts.tips,
    engagement_formula: opts.formula || 'CES = 关注×8 + 评论×4 + 转发×4 + 收藏×1 + 点赞×1',
  }
}

function arbiterScore(opts: {
  total: number
  verdict: string
  summary: string
  risks: string[]
  actions: string[]
  dimensions?: { name: string; score: number }[]
  hkrr?: { name: string; score: number }[]
}): ScoreData {
  return {
    total_score: opts.total,
    verdict: opts.verdict,
    summary: opts.summary,
    dimensions: opts.dimensions || [],
    hkrr: opts.hkrr || [],
    key_risks: opts.risks,
    action_items: opts.actions,
  }
}

function wechatStrategy(s: {
  videoTips: string[]
  videoAlgorithm: string
  videoBest: string[]
  officialKws: string[]
  officialFmt: string
  officialTips: string[]
  searchKws: string[]
  searchOpt: string[]
  privateFunnel: string[]
  privateTips: string[]
}): WeChatStrategy {
  return {
    videoAccount: { tips: s.videoTips, algorithm: s.videoAlgorithm, bestPractices: s.videoBest },
    officialAccount: { seoKeywords: s.officialKws, format: s.officialFmt, tips: s.officialTips },
    search: { keywords: s.searchKws, optimization: s.searchOpt },
    privateDomain: { funnelSteps: s.privateFunnel, tips: s.privateTips },
  }
}

export const DEMO_CASES: DemoCase[] = [
  {
    id: 'campus-ai-notes',
    title: '大学生AI学习笔记双平台定位',
    prompt: '大学生做AI学习笔记账号，视频号+小红书双平台怎么定位？',
    emoji: '🎓',
    result: {
      role: 'assistant',
      content: `### 赛道机会评分：8.5/10

AI学习笔记是2025年校园赛道增长最快的细分品类之一，视频号"AI学习"相关搜索量季度环比增长280%，小红书"AI笔记"话题浏览量突破2.3亿。竞争格局：头部账号不足20个，腰部空白明显，大学生身份自带信任感。

### 内容策略

**双平台差异化定位：**

| 维度 | 视频号 | 小红书 |
|------|--------|--------|
| 人设 | "AI学长/学姐" 知识分享者 | "AI工具收藏家" 效率达人 |
| 内容形式 | 1-3分钟讲解视频 | 图文卡片+教程截图 |
| 调性 | 专业可信、有深度 | 实用好看、易收藏 |
| 更新频率 | 每周3条 | 日更1条 |

**标题建议：**
1. 我用AI一天读完《经济学原理》，附完整笔记模板 (预估CTR: 13%)
2. 大二学生用Kimi做课堂笔记，期末成绩提升40分 (预估CTR: 12%)
3. 这5个AI学习方法，让我从年级200名逆袭到前30 (预估CTR: 11%)
4. ChatGPT读论文太强了！我的导师都震惊了 (预估CTR: 10%)
5. 别再死记硬背了！AI费曼学习法实操指南 (预估CTR: 10%)

**开场Hook：**
1. "上学期我还是学渣，这学期室友问我怎么突然开窍了——其实是我偷偷用了一套AI学习系统..." (+40%留存)
2. "一本300页的教材，AI帮我20分钟提炼出核心框架，今天把方法全部公开" (+35%留存)
3. "如果你还在用传统方法做笔记，看完这条你会恨自己为什么不早点知道" (+32%留存)

### 微信生态策略

**视频号：** 发布时间：周一/三/五 12:00-13:00（午休学习时段）+ 周末20:00 | 内容方向：AI工具深度教程、学习方法论、期末复习技巧 | 完播率优化：前3秒展示学习成果对比，中间穿插实操录屏 | 互动设计：结尾"你们专业用AI学什么？评论区告诉我"

**搜一搜：** 核心词：AI学习方法、AI做笔记、大学生AI工具 | 长尾词：AI读论文方法、Kimi学习技巧、ChatGPT期末复习、AI思维导图 | 布局策略：每条视频标题+描述嵌入2-3个搜一搜关键词

**公众号：** 开设"AI学习周报"栏目，每周汇总最新AI学习工具+实操案例 | 输出"XX专业AI学习指南"系列长文（计算机/经济/法学等），布局搜索SEO | 引导视频号粉丝关注公众号获取"AI学习资料包"

### 30天行动路径

**D1-D7（账号搭建期）：** 确定视觉风格和人设；视频号发布5条"AI学习工具测评"短视频；小红书发布7条图文笔记，覆盖不同学科场景。目标：视频号100粉 + 小红书200粉。

**D8-D14（内容验证期）：** 分析第一周数据，确定2个高互动方向；尝试"AI帮我做XX"系列内容；视频号做1条3分钟深度教程。目标：单条播放破1000 + 总粉丝500。

**D15-D21（起量期）：** 蹭期末季热点"AI复习攻略"；发布对比类内容（传统方法 vs AI方法）；开始在评论区互动引导关注。目标：1条爆款破万播放 + 总粉丝1500。

**D22-D30（矩阵期）：** 视频号引流公众号，建立内容矩阵闭环；发布"期末AI学习工具大全"长内容；尝试直播"AI陪学"。目标：双平台总粉丝3000+，公众号粉丝500。

### 数据来源

本次分析基于 MiniMax联网搜索、Serper(Google)、Tavily、DuckDuckGo、DailyHot热搜聚合 共5个引擎的实时数据，覆盖视频号指数、小红书话题热度、搜一搜关键词趋势等维度。`,
      thinking: [
        { step: '搜索中', detail: '正在从多个引擎搜索AI学习笔记赛道数据...', progress: 10, agents: [{ name: 'MiniMax搜索', status: 'running' }, { name: 'Serper搜索', status: 'running' }, { name: 'Tavily搜索', status: 'pending' }] },
        { step: '搜索完成', detail: '找到 82 条数据，来自 5 个引擎，涵盖视频号指数和小红书话题数据', progress: 35, agents: [{ name: 'MiniMax搜索', status: 'done', count: 20 }, { name: 'Serper搜索', status: 'done', count: 22 }, { name: 'Tavily搜索', status: 'done', count: 18 }] },
        { step: '构建知识图谱', detail: '正在分析双平台定位策略、校园场景关联关系...', progress: 50 },
        { step: '生成报告', detail: 'AI 正在综合分析并生成双平台定位方案...', progress: 65 },
      ],
      searchStats: { total_raw: 82, total_deduped: 82, engines: { minimax: 20, serper: 22, tavily: 18, ddgs: 12, dailyhot: 10 } },
      graph: {
        nodes: [
          { id: 'center', name: 'AI学习笔记', type: 'topic', val: 40, color: '#6366f1' },
          { id: 'shipinhao', name: '视频号', type: 'platform', val: 30, color: '#07c160' },
          { id: 'xiaohongshu', name: '小红书', type: 'platform', val: 28, color: '#ff2442' },
          { id: 'souyisou', name: '搜一搜', type: 'platform', val: 22, color: '#07c160' },
          { id: 'kimi', name: 'Kimi', type: 'tool', val: 20, color: '#4f46e5' },
          { id: 'chatgpt', name: 'ChatGPT', type: 'tool', val: 20, color: '#10a37f' },
          { id: 'student', name: '大学生', type: 'audience', val: 25, color: '#f59e0b' },
          { id: 'exam', name: '期末复习', type: 'scenario', val: 18, color: '#ef4444' },
          { id: 'paper', name: '论文阅读', type: 'scenario', val: 16, color: '#ef4444' },
          { id: 'mindmap', name: 'AI思维导图', type: 'content', val: 15, color: '#8b5cf6' },
          { id: 'tutorial', name: '工具教程', type: 'content', val: 18, color: '#8b5cf6' },
          { id: 'gongzhonghao', name: '公众号', type: 'platform', val: 20, color: '#07c160' },
          { id: 'feynman', name: '费曼学习法', type: 'method', val: 14, color: '#06b6d4' },
          { id: 'notes-template', name: '笔记模板', type: 'content', val: 16, color: '#8b5cf6' },
        ],
        links: [
          { source: 'center', target: 'shipinhao', label: '视频讲解', strength: 1 },
          { source: 'center', target: 'xiaohongshu', label: '图文种草', strength: 0.9 },
          { source: 'center', target: 'souyisou', label: 'SEO获客', strength: 0.8 },
          { source: 'center', target: 'student', label: '核心受众', strength: 1 },
          { source: 'center', target: 'kimi', label: '推荐工具', strength: 0.8 },
          { source: 'center', target: 'chatgpt', label: '推荐工具', strength: 0.7 },
          { source: 'student', target: 'exam', label: '刚需场景', strength: 0.9 },
          { source: 'student', target: 'paper', label: '高频场景', strength: 0.8 },
          { source: 'center', target: 'mindmap', label: '爆款形式', strength: 0.7 },
          { source: 'center', target: 'tutorial', label: '主力内容', strength: 0.8 },
          { source: 'shipinhao', target: 'gongzhonghao', label: '引流沉淀', strength: 0.7 },
          { source: 'center', target: 'feynman', label: '方法论', strength: 0.6 },
          { source: 'center', target: 'notes-template', label: '引流钩子', strength: 0.7 },
        ],
      },
      sources: [
        { title: '2025年微信视频号教育赛道增长报告', url: 'https://mp.weixin.qq.com/s/video-edu-2025' },
        { title: '小红书AI学习话题数据分析', url: 'https://www.xiaohongshu.com/explore/ai-study' },
        { title: '大学生AI工具使用调研（N=2000）', url: 'https://research.tencent.com/student-ai-2025' },
      ],
      tokenUsage: { search_tokens: 0, llm_tokens: 0, total_tokens: 0, search_calls: 82, agent_rounds: 2, elapsed_ms: 32400 },
      agentMessages: buildAgentMessages([
        { agent: 'data', round: 1, content: 'AI学习笔记赛道在视频号近一年增长 280%，小红书话题浏览破 2.3 亿，但头部账号不足 20 个，腰部断层明显。**机会**：跨平台双开是空白。' },
        { agent: 'content', round: 1, content: '双平台差异化定位很关键：视频号做"AI学长讲深度"，小红书做"AI工具收藏家"。一份内容做两套外壳，效率最大化。' },
        { agent: 'psych', round: 1, content: '大学生用户的核心心理诉求是"快速被同龄人认可+期末焦虑缓解"。建议主打"逆袭叙事"+"工具捷径"，而不是"系统讲方法"。' },
        { agent: 'platform', round: 1, content: '视频号必须利用社交关系链——发布后立刻分享到班级群，让 5-10 个同学点赞，能撬动"朋友在看"机制，48h 流量翻 3-5 倍。' },
        { agent: 'risk', round: 1, content: '风险点在于内容同质化严重。建议绑定一个具体身份标签，如"双非冲 985 用 AI"，避免被埋没在通用 AI 内容池里。' },
        { agent: 'research', round: 1, content: '参考头部案例 @AI学习室Tina（视频号 12 万粉丝），其爆款主要是"对比型"——传统方法 vs AI 方法，CTR 平均高出 40%。' },
        { agent: 'advocate', round: 1, content: '作为大学生，我会被"具体学科+AI"的内容吸引（如经济学、法学），通用的"AI 学习方法"我会划走。建议做学科细分。' },
        { agent: 'data', round: 2, content: '综合数据：双平台同期开号，30 天内可达 3000+ 粉丝。视频号占 60%，小红书占 40%。' },
        { agent: 'content', round: 2, content: '内容形式建议：视频号每周 3 条 1-3 分钟讲解视频；小红书日更图文卡片+教程截图，效率比视频高 5 倍。' },
        { agent: 'platform', round: 2, content: '搜一搜 SEO 重点：把"AI做笔记""AI读论文""费曼学习法"嵌入标题前 18 字，可截 30% 长尾流量。' },
      ]),
      scoreData: arbiterScore({
        total: 85,
        verdict: '强烈推荐',
        summary: 'AI 学习笔记是当前校园 KOC 最具机会的赛道之一：流量增长快、竞争稀薄、刚需性强、变现路径清晰（工具佣金+课程）。专家共识度 85%。',
        dimensions: [
          { name: '赛道热度', score: 92 },
          { name: '竞争蓝海', score: 88 },
          { name: '刚需匹配', score: 95 },
          { name: '变现潜力', score: 78 },
          { name: '内容门槛', score: 70 },
        ],
        hkrr: [
          { name: '钩子(Hook)', score: 85 },
          { name: '认知(Knowledge)', score: 80 },
          { name: '关系(Relation)', score: 88 },
          { name: '行动(Reaction)', score: 78 },
        ],
        risks: [
          'AI 工具更新快，需保持每周新工具评测',
          '同质化风险高，必须绑定个人身份标签',
          '版权敏感，避免直接搬运教材内容',
        ],
        actions: [
          'D1-7：定位"双非冲 985 + AI 学习"，发首批 7 条内容',
          'D8-21：每周 1 条对比型爆款，蹭期末季热点',
          'D22+：建立"AI 学习资料包"引流公众号沉淀粉丝',
        ],
      }),
      arbiterThinking: '综合 7 位专家观点，本选题在"赛道适配度""增长速度""KOC 个人优势"三个核心维度均为强项；唯一短板在"长期内容差异化"，需通过身份标签绑定来解决。',
      viralScore: viralScore({
        total: 82,
        pool: '热门流量池',
        poolProb: '78% 概率突破初级、进入热门池',
        analysis: '小红书 CES 公式下，"AI做笔记"标题钩子强、收藏率预期高（学习类内容平均收藏:点赞 = 1.5:1），评分进入热门池可能性大。视频号需依靠社交链路加速，单条目标 5000+ 完播。',
        dimensions: [
          { id: 'title_appeal', name: '标题吸引力', score: 13, max: 15, reason: '"我用AI一天读完《经济学原理》"具备数字+对比+身份钩子，CTR 预估 13%。' },
          { id: 'emotion', name: '情绪共鸣', score: 12, max: 15, reason: '直击大学生期末焦虑+逆袭幻想，二次元自带社交货币价值。' },
          { id: 'platform_fit', name: '平台适配', score: 13, max: 15, reason: '小红书收藏属性匹配学习类内容，视频号社交链激活强。' },
          { id: 'blue_ocean', name: '竞争蓝海', score: 9, max: 10, reason: 'AI+学科细分仍是空白，腰部账号 < 20 个。' },
          { id: 'timeliness', name: '时效窗口', score: 8, max: 10, reason: '期末季+开学季双高峰，全年都有需求。' },
          { id: 'hook_strength', name: 'Hook 强度', score: 8, max: 10, reason: '"上学期我还是学渣"开头制造身份反差。' },
          { id: 'info_density', name: '信息密度', score: 8, max: 10, reason: 'AI 工具+方法论双线，信息可收藏度高。' },
          { id: 'originality', name: '原创空间', score: 7, max: 10, reason: '需要深度个人案例支撑，否则陷入工具罗列陷阱。' },
          { id: 'completion_predict', name: '完播预测', score: 4, max: 5, reason: '1-3 分钟视频长度合理，开头悬念+中段实操+结尾价值。' },
        ],
        strengths: ['赛道高速增长 (+280% YoY)', '大学生身份自带信任感', '双平台分发提升曝光天花板'],
        weaknesses: ['同质化风险高', '需要个人化身份标签', '直接变现路径偏长'],
        tips: ['标题前置"双非"或"普通大学生"等身份标签', '前 3 秒展示"成绩单对比"', '在评论区主动收集"你想用 AI 学什么"形成下期选题', '每月做一次"AI 工具红黑榜"长视频'],
      }),
      wechatStrategy: wechatStrategy({
        videoTips: [
          '发布后 30 分钟内分享到 3 个班级群激活社交链',
          '前 3 秒展示成绩对比图，留存提升 40%',
          '标题前 18 字必须包含"AI做笔记"或核心搜索词',
          '每周三 12:00 + 周日 20:00 双发，校园用户活跃高峰',
          '回复前 20 条评论，触发"互动加权"提升曝光池',
        ],
        videoAlgorithm: '微信视频号推荐分 = 社交关系链×60% + 完播率×25% + 互动深度×15%。"朋友在看"是核心放大器，单个好友点赞可带来 8-15 个二级曝光。',
        videoBest: [
          '建立 30+ 校园种子群作为冷启动池',
          '每条视频前 3 秒必须有"成绩对比/界面对比"画面',
          '结尾 CTA："关注我，下期讲 [具体学科]"',
          '每月做一次直播"AI 陪我复习"，绑定铁粉',
        ],
        officialKws: ['AI学习方法', 'AI做笔记', '大学生AI工具', 'Kimi学习技巧', 'ChatGPT复习', 'AI思维导图', '费曼学习法'],
        officialFmt: '深度 SEO 长文格式（2500-3500 字），结构：痛点引入 → 工具对比 → 实操步骤 → 资料包引导。每月 4 篇，专攻搜一搜长尾词。',
        officialTips: [
          '每篇文章标题包含"专业名+AI"（如"经济学AI学习指南"）',
          '提供可下载资料包（PDF）引导粉丝关注',
          '与校园社团、表白墙互推，30 天内积累首批 500 粉',
          '设立"AI学习周报"固定栏目培养读者习惯',
        ],
        searchKws: ['AI做笔记 怎么用', '大学生AI学习', 'AI写论文 工具', 'AI思维导图 模板', '费曼学习法 AI'],
        searchOpt: [
          '前 18 字命中核心词（小红书"前 18 字"是搜索匹配窗口）',
          '一篇文章布局 1 个核心词 + 3 个长尾词',
          '每月监测搜一搜词频，及时蹭新工具关键词',
          '建立"工具+学科"矩阵：覆盖至少 8 个学科 × 5 个工具',
        ],
        privateFunnel: [
          '视频号关注 → 公众号引流（资料包钩子）',
          '公众号关注 → 微信群（"AI学习互助群"）',
          '微信群活跃 → 付费小课程 / 1 对 1 咨询',
          '高活跃粉丝 → 转化为内容共创者',
        ],
        privateTips: [
          '提供"AI学习资料包"作为关注钩子（PDF + Notion 模板）',
          '微信群每周三 20:00 主题分享，培养仪式感',
          '私域用户每月推送 1 次工具优惠券，复购率提升',
          '建立"学姐学长内推圈"加深用户粘性',
        ],
      }),
    },
  },
  {
    id: 'campus-food-blog',
    title: '校园美食公众号AI日更',
    prompt: '校园美食探店公众号如何用AI提效做到日更？',
    emoji: '🍜',
    result: {
      role: 'assistant',
      content: `### 赛道机会评分：8.2/10

校园美食探店是公众号经典长青赛道，但痛点明显：传统方式1篇探店文需2-3小时（拍摄+修图+写文），日更几乎不可能。AI介入后，效率可提升3-5倍，使"一人日更"成为现实。全国2800+高校，每所学校的美食公众号最多2-3个活跃号，蓝海空间极大。

### 内容策略

**AI提效工作流：**

| 环节 | 传统方式 | AI提效方式 | 时间节省 |
|------|---------|-----------|---------|
| 选题 | 手动找店 | AI热点监控+大众点评数据 | 80% |
| 拍摄 | 多角度精修 | AI构图建议+一键修图 | 50% |
| 写文 | 手写1500字 | AI生成初稿+人工润色 | 70% |
| 排版 | 手动排版 | 模板化+AI配图 | 60% |
| 推广 | 手动发布 | 定时发布+AI生成朋友圈文案 | 90% |

**日更内容矩阵（每日1篇，轮换主题）：**
- 周一：新店首发（探店实拍）
- 周二：食堂隐藏菜单/神仙搭配
- 周三：校门口小吃排行榜
- 周四：外卖红黑榜
- 周五：周末聚餐推荐
- 周六：学生党省钱美食攻略
- 周日：下周新店预告+粉丝点单

**标题建议：**
1. 我在XX大学吃了100天，这10家绝对不能错过 (预估CTR: 14%)
2. 食堂阿姨都不知道的隐藏吃法，今天全公开 (预估CTR: 13%)
3. 全校最便宜的饱腹套餐Top5，最低只要8块！ (预估CTR: 12%)
4. 校门口开了3年的老店要关了，最后再吃一次 (预估CTR: 12%)
5. 外卖点了200单，帮你们排出了雷区名单 (预估CTR: 11%)

**开场Hook：**
1. "在这所学校待了三年，吃过的店比上过的课还多——今天这份终极攻略，建议收藏" (+38%留存)
2. "食堂二楼最里面那个窗口，99%的人都不知道，但它是我大学四年最大的秘密" (+42%留存)

### 微信生态策略

**公众号（主阵地）：** 每日推送美食推文，标题嵌入学校名+地标关键词 | 开发"美食地图"小程序嵌入文章 | 每月做一次"粉丝投票最爱餐厅"互动 | 接入AI自动生成"今日推荐"栏目

**视频号：** 每周2条30秒探店短视频，展示菜品+环境 | 内容风格：第一人称视角，真实不做作 | 关键词：校名+美食+探店+食堂

**搜一搜：** 核心词：XX大学美食、XX大学食堂推荐、XX大学周边吃什么 | 长尾词：XX大学外卖推荐、XX大学约会餐厅、XX大学深夜食堂 | 策略：每篇文章标题包含学校名称，确保搜一搜精准匹配

### 30天行动路径

**D1-D7（系统搭建期）：** 搭建AI写作工作流（Kimi/ChatGPT写初稿+秘塔修改）；建立探店模板（结构化prompt）；拍摄10家店的素材储备。目标：公众号日更7天，粉丝200+。

**D8-D14（内容验证期）：** 测试不同类型文章的打开率；优化AI prompt，让生成文案更有"学生感"；在校内社群推广。目标：单篇阅读500+，粉丝800+。

**D15-D21（破圈期）：** 发布"XX大学美食地图"长文（3000字+），做成收藏型内容；联动学校社团/表白墙转发；开始视频号同步分发。目标：1篇阅读破2000，粉丝2000+。

**D22-D30（商业化启动期）：** 开始接校园周边商家推广；推出"粉丝专属优惠"栏目；公众号+视频号+社群三位一体运营。目标：首笔商业收入，粉丝3500+。

### 数据来源

本次分析基于 MiniMax联网搜索、Serper(Google)、Tavily、DuckDuckGo、DailyHot热搜聚合 共5个引擎的实时数据，覆盖公众号美食赛道数据、校园KOC案例及AI写作效率研究。`,
      thinking: [
        { step: '搜索中', detail: '正在搜索校园美食公众号运营方案...', progress: 10, agents: [{ name: 'MiniMax搜索', status: 'running' }, { name: 'Serper搜索', status: 'running' }, { name: 'DailyHot热搜', status: 'running' }] },
        { step: '搜索完成', detail: '找到 76 条数据，来自 5 个引擎，包含公众号运营案例和AI写作工具评测', progress: 35, agents: [{ name: 'MiniMax搜索', status: 'done', count: 18 }, { name: 'Serper搜索', status: 'done', count: 20 }, { name: 'Tavily搜索', status: 'done', count: 16 }] },
        { step: '构建知识图谱', detail: '正在分析AI提效工作流与校园美食内容生态...', progress: 48 },
        { step: '生成报告', detail: 'AI 正在综合生成日更运营方案...', progress: 62 },
      ],
      searchStats: { total_raw: 76, total_deduped: 76, engines: { minimax: 18, serper: 20, tavily: 16, ddgs: 12, dailyhot: 10 } },
      graph: {
        nodes: [
          { id: 'center', name: '校园美食探店', type: 'topic', val: 40, color: '#f97316' },
          { id: 'gongzhonghao', name: '公众号', type: 'platform', val: 32, color: '#07c160' },
          { id: 'shipinhao', name: '视频号', type: 'platform', val: 22, color: '#07c160' },
          { id: 'souyisou', name: '搜一搜', type: 'platform', val: 20, color: '#07c160' },
          { id: 'ai-writing', name: 'AI写作', type: 'tool', val: 25, color: '#6366f1' },
          { id: 'ai-image', name: 'AI修图', type: 'tool', val: 18, color: '#6366f1' },
          { id: 'student', name: '在校大学生', type: 'audience', val: 28, color: '#f59e0b' },
          { id: 'canteen', name: '食堂美食', type: 'content', val: 18, color: '#ef4444' },
          { id: 'takeaway', name: '外卖测评', type: 'content', val: 16, color: '#ef4444' },
          { id: 'nearby', name: '校门口探店', type: 'content', val: 20, color: '#ef4444' },
          { id: 'daily-update', name: '日更模式', type: 'strategy', val: 22, color: '#8b5cf6' },
          { id: 'template', name: '模板化生产', type: 'strategy', val: 18, color: '#8b5cf6' },
          { id: 'local-seo', name: '本地SEO', type: 'strategy', val: 16, color: '#8b5cf6' },
          { id: 'merchant', name: '校园商家', type: 'monetize', val: 15, color: '#10b981' },
        ],
        links: [
          { source: 'center', target: 'gongzhonghao', label: '主阵地', strength: 1 },
          { source: 'center', target: 'shipinhao', label: '视频分发', strength: 0.7 },
          { source: 'center', target: 'souyisou', label: '搜索获客', strength: 0.8 },
          { source: 'center', target: 'student', label: '目标用户', strength: 1 },
          { source: 'center', target: 'ai-writing', label: '效率提升', strength: 0.9 },
          { source: 'center', target: 'ai-image', label: '图片处理', strength: 0.7 },
          { source: 'center', target: 'canteen', label: '内容方向', strength: 0.8 },
          { source: 'center', target: 'nearby', label: '内容方向', strength: 0.8 },
          { source: 'ai-writing', target: 'daily-update', label: '实现基础', strength: 0.9 },
          { source: 'daily-update', target: 'template', label: '核心方法', strength: 0.8 },
          { source: 'souyisou', target: 'local-seo', label: '获客路径', strength: 0.8 },
          { source: 'center', target: 'merchant', label: '商业化', strength: 0.6 },
          { source: 'gongzhonghao', target: 'shipinhao', label: '内容复用', strength: 0.7 },
        ],
      },
      sources: [
        { title: '高校公众号美食赛道运营白皮书2025', url: 'https://mp.weixin.qq.com/s/campus-food-report' },
        { title: 'AI辅助内容创作效率研究', url: 'https://research.tencent.com/ai-content-efficiency' },
        { title: '校园KOC商业化案例集', url: 'https://example.com/campus-koc-monetize' },
      ],
      tokenUsage: { search_tokens: 0, llm_tokens: 0, total_tokens: 0, search_calls: 76, agent_rounds: 2, elapsed_ms: 29800 },
      agentMessages: buildAgentMessages([
        { agent: 'data', round: 1, content: '校园美食公众号赛道：每所高校最多 2-3 个活跃号，全国 2800+ 高校 = 巨大蓝海。AI 提效后单人日更可行性极高。' },
        { agent: 'content', round: 1, content: '日更内容矩阵设计精妙：周一新店 / 周二食堂 / 周三排行 / 周四黑榜 / 周五聚餐 / 周六省钱 / 周日预告。固定栏目降低用户认知负担。' },
        { agent: 'psych', round: 1, content: '美食内容核心心理 = 即刻满足感+省钱焦虑+社交炫耀。"食堂阿姨都不知道的隐藏吃法"完美命中"信息差优越感"。' },
        { agent: 'platform', round: 1, content: '微信公众号在本地化美食赛道有天然优势：搜一搜本地权重高+朋友圈分享自然。建议公众号为主阵地。' },
        { agent: 'risk', round: 1, content: '风险：AI 写作味道太重会失去信任。建议 AI 写初稿+真实探店照片+人工口语化润色，保持"学生感"。' },
        { agent: 'research', round: 1, content: '参考案例 @XX大学美食地图（公众号 5 万粉），其商业模式：粉丝增长→校园商家广告→活动策划，月营收 1-3 万。' },
        { agent: 'advocate', round: 1, content: '我会因为"全校最便宜套餐"或"老店要关了"这种情绪点关注，而不是日常推荐。情绪锚点很重要。' },
        { agent: 'data', round: 2, content: 'AI 提效全链路：选品调研 80% 节省 + 写文 70% + 排版 60% + 推广 90%。一人日更稳定可达成。' },
        { agent: 'content', round: 2, content: '建议建立 PromptKit：每个栏目 1 个固定 prompt 模板，新手 5 分钟出初稿。' },
        { agent: 'platform', round: 2, content: '搜一搜核心词：[学校名]+美食/食堂/外卖/聚餐。每篇文章标题必含校名，确保精准匹配。' },
      ]),
      scoreData: arbiterScore({
        total: 80,
        verdict: '强烈推荐',
        summary: '本地美食赛道是"AI 提效"最显著的场景之一，可让一个大学生通过 AI 工作流稳定日更。商业化路径清晰（校园商家+CPS）。建议立即启动。',
        risks: ['AI 写作痕迹明显需人工润色', '美食季节性波动需多元化', '商家对接需建立标准 SOP'],
        actions: ['D1-7：搭建 AI 选品+写作工作流，发首批 7 篇', 'D8-14：测试 7 个固定栏目数据，找出爆款方向', 'D15-30：开始接校园周边商家广告，验证商业闭环'],
        dimensions: [{ name: '本地化优势', score: 95 }, { name: '可日更性', score: 90 }, { name: '变现速度', score: 85 }, { name: '内容门槛', score: 60 }],
        hkrr: [{ name: '钩子', score: 82 }, { name: '认知', score: 75 }, { name: '关系', score: 90 }, { name: '行动', score: 80 }],
      }),
      arbiterThinking: '7 位专家高度共识：本赛道在"本地化壁垒+AI提效适配度+商业化清晰度"三维度均为强项，唯一挑战是"AI 写作痕迹"，可通过模板+真实素材组合解决。',
      viralScore: viralScore({
        total: 76,
        pool: '初级流量池',
        poolProb: '突破初级池概率 70%，进入热门池需依赖爆款单篇',
        analysis: '微信公众号本地美食内容 CES 算法下，"打开率"是核心。标题钩子明确（"100天""绝对不能错过"）+ 本地化关键词 + 朋友圈分享天然，预期单篇打开率 8-12%。',
        dimensions: [
          { id: 'title_appeal', name: '标题吸引力', score: 12, max: 15, reason: '"我在XX大学吃了100天"具备身份+时间+悬念，CTR 14%。' },
          { id: 'emotion', name: '情绪共鸣', score: 11, max: 15, reason: '校友身份共鸣+"老店要关了"情怀诉求双重命中。' },
          { id: 'platform_fit', name: '平台适配', score: 14, max: 15, reason: '公众号本地化属性极强，搜一搜匹配度高。' },
          { id: 'blue_ocean', name: '竞争蓝海', score: 9, max: 10, reason: '每所高校仅 2-3 个活跃号，腰部空白。' },
          { id: 'timeliness', name: '时效窗口', score: 7, max: 10, reason: '美食季节性强，需结合开学季+期末季' },
          { id: 'hook_strength', name: 'Hook 强度', score: 7, max: 10, reason: '"食堂二楼最里面那个窗口"具体细节制造好奇。' },
          { id: 'info_density', name: '信息密度', score: 8, max: 10, reason: '价格+地址+评分+图片信息完整。' },
          { id: 'originality', name: '原创空间', score: 6, max: 10, reason: 'AI 提效内容需注意原创性，避免被认定搬运。' },
          { id: 'completion_predict', name: '完播预测', score: 2, max: 5, reason: '公众号长文需用图片密度防跳读。' },
        ],
        strengths: ['本地垄断壁垒高', 'AI 提效效果最显著', '商业化路径短'],
        weaknesses: ['内容季节性波动', '需要真实探店照', '商家关系需建立'],
        tips: ['每篇文章配 8+ 真实照片', '建立"美食地图"小程序作为内容载体', '每月做一次粉丝投票选下期推荐', '加入"学生证打折"等独家信息'],
        formula: '微信公众号 CES = 打开率×50% + 在看率×30% + 转发率×20%',
      }),
      wechatStrategy: wechatStrategy({
        videoTips: [
          '每周 2 条 30 秒探店视频（菜品+环境）',
          '第一人称视角，真实不修图',
          '发布后立即在班级群+表白墙转发',
          '标签：#校名 #美食 #探店',
          '结尾 CTA："你最爱学校哪家店？评论区告诉我"',
        ],
        videoAlgorithm: '本地化探店内容主要靠"朋友在看"传播。学生群体社交链密集，1 条视频可触达 50-200 个同学。',
        videoBest: ['周二/四/六 20:00 发布最佳', '建立"30 秒快测"固定模板', '每月一次"美食季"主题策划'],
        officialKws: ['XX大学美食', 'XX大学食堂推荐', 'XX大学外卖', 'XX大学约会餐厅', 'XX大学深夜食堂'],
        officialFmt: '深度推文（1500-2500 字），结构：标题钩子 → 推荐理由 → 4-6 家店详细介绍（含照片+价格+评分）→ 学生证优惠提示 → 引导关注。',
        officialTips: ['每篇标题必含学校名称', '每月做一次"粉丝投票最爱餐厅"', '与学校官方号联动推送', '提供"美食地图"PDF 引流'],
        searchKws: ['XX大学美食推荐', '大学生省钱攻略', '校园探店攻略', 'XX大学外卖红黑榜'],
        searchOpt: ['标题精准包含校名（搜一搜本地权重高）', '每篇文章覆盖 3-5 个长尾词', '每月更新"当季美食"长文持续收割搜索流量', '与抖音/小红书同步分发提升综合权重'],
        privateFunnel: [
          '公众号关注 → 校园美食群（每校一群）',
          '群内每日 18:00 推送"今日推荐"',
          '群活跃 → 商家优惠券分发（CPS 抽佣）',
          '高粘性粉丝 → 每月线下"探店局"',
        ],
        privateTips: ['群名"XX大学美食指南"+群规明确', '商家合作明码标价（防割韭菜）', '每月做一次"学生节"粉丝福利', '高质量粉丝聘为"美食探店官"'],
      }),
    },
  },
  {
    id: 'campus-kaoyan',
    title: '考研经验搜一搜关键词布局',
    prompt: '大学生做考研经验分享，搜一搜关键词怎么布局？',
    emoji: '📚',
    result: {
      role: 'assistant',
      content: `### 赛道机会评分：9.1/10

考研是大学生最大的刚需赛道之一，2025年考研报名人数438万，搜一搜"考研"相关日均搜索量超1200万次。关键优势：搜索意图明确、用户付费意愿强、内容长尾效应极佳（一篇经验帖可持续获取流量2-3年）。KOC身份优势：刚上岸的学长/学姐是最具信任感的信息源。

### 内容策略

**关键词布局体系（搜一搜Peoplerank适配）：**

**第一层：核心大词（竞争高，用视频号+公众号联合霸屏）**
| 关键词 | 月搜索量 | 竞争度 | 布局策略 |
|--------|---------|--------|---------|
| 考研经验 | 800万+ | 极高 | 公众号长文+视频号合集 |
| 考研规划 | 500万+ | 高 | 系列化内容矩阵 |
| 考研时间线 | 300万+ | 高 | 时间节点型内容 |

**第二层：院校+专业词（精准流量，转化率高）**
| 关键词 | 月搜索量 | 竞争度 | 布局策略 |
|--------|---------|--------|---------|
| XX大学考研经验 | 10-50万 | 中 | 针对性经验帖 |
| XX专业考研 | 5-30万 | 中低 | 专业备考指南 |
| XX大学XX专业真题 | 3-20万 | 低 | 资料引流型内容 |

**第三层：长尾问题词（蓝海流量，完美匹配搜一搜）**
| 关键词 | 月搜索量 | 竞争度 | 布局策略 |
|--------|---------|--------|---------|
| 考研二战值不值 | 80万 | 低 | 深度分析文 |
| 跨专业考研难不难 | 60万 | 低 | 案例故事型 |
| 考研和考公怎么选 | 100万 | 中 | 对比分析型 |
| 大三开始准备考研晚不晚 | 40万 | 极低 | 规划建议型 |

**标题建议：**
1. 双非三跨上岸985，我的考研400分全程规划（附时间表） (预估CTR: 15%)
2. 考研最后100天，我从320分逆袭到410分的真实记录 (预估CTR: 14%)
3. 2026考研人必看：这份备考时间线帮你少走3个月弯路 (预估CTR: 13%)
4. 用AI做考研笔记，我每天多出2小时背单词 (预估CTR: 12%)
5. 劝退帖：这5类人真的不适合考研 (预估CTR: 12%)

**开场Hook：**
1. "初试410分，复试第一——但一年前的我，连目标院校都没想好。今天把我的完整规划拆给你看" (+45%留存)
2. "你现在搜'考研经验'，说明你和一年前的我一样迷茫。但只要你看完这条，至少少走2个月弯路" (+38%留存)

### 微信生态策略

**搜一搜（核心获客引擎）：** 算法权重要点 —— 账号垂直度(30%)：只发考研相关内容，不杂 | 内容新鲜度(25%)：贴合当前备考阶段 | 互动信号(20%)：引导收藏和转发 | 标题匹配(25%)：精准包含搜索词

布局节奏：
- 3-5月：发布"择校""规划"类关键词内容
- 6-8月：发布"暑假复习""强化阶段"类内容
- 9-11月：发布"冲刺""真题""背诵"类内容
- 12月-次年2月：发布"考前心态""初试经验""复试准备"

**视频号：** 每周3条，1-2分钟经验分享短视频 | 形式：真人出镜+手写笔记展示 | 标签：#考研 #考研经验 #XX大学 | 引导：评论区置顶公众号链接

**公众号：** 深度长文阵地，输出3000-5000字经验帖 | 系列化内容："考研上岸全记录"（20篇连载） | SEO标题格式：[院校名]+[专业]+考研经验/攻略/真题 | 提供资料包（PDF笔记/思维导图）引导关注

### 30天行动路径

**D1-D7（关键词调研+种子内容）：** 用5118/微信指数调研关键词热度；产出7篇公众号文章，覆盖核心词+院校词；视频号发3条短视频。目标：搜一搜收录全部文章。

**D8-D14（长尾词铺量期）：** 每天1篇针对长尾问题词的内容（"考研二战值不值""跨考难不难"等）；用AI批量生成标题+大纲，人工填充真实经历。目标：搜一搜出词10个+。

**D15-D21（流量收割期）：** 发布3篇重磅长文（完整上岸经验帖），覆盖高搜索量关键词；视频号做1条深度分享（5分钟以上）。目标：搜一搜单词排名前3，日均流量500+。

**D22-D30（矩阵闭环期）：** 搭建公众号→视频号→社群的引流链路；发起"考研打卡"社群活动；开始接学长学姐付费咨询。目标：总粉丝5000+，社群200人。

### 数据来源

本次分析基于 MiniMax联网搜索、Serper(Google)、Tavily、DuckDuckGo、DailyHot热搜聚合 共5个引擎的实时数据，覆盖搜一搜关键词指数、微信指数、考研报名数据及公众号竞品分析。`,
      thinking: [
        { step: '搜索中', detail: '正在搜索考研经验分享赛道及搜一搜SEO数据...', progress: 10, agents: [{ name: 'MiniMax搜索', status: 'running' }, { name: 'Serper搜索', status: 'running' }, { name: '微信指数抓取', status: 'running' }] },
        { step: '搜索完成', detail: '找到 91 条数据，来自 5 个引擎，含搜一搜关键词热度及竞品分析', progress: 35, agents: [{ name: 'MiniMax搜索', status: 'done', count: 22 }, { name: 'Serper搜索', status: 'done', count: 25 }, { name: 'Tavily搜索', status: 'done', count: 20 }] },
        { step: '构建知识图谱', detail: '正在分析关键词层级、搜索意图及竞争格局...', progress: 52 },
        { step: '生成报告', detail: 'AI 正在生成搜一搜关键词布局策略...', progress: 68 },
      ],
      searchStats: { total_raw: 91, total_deduped: 91, engines: { minimax: 22, serper: 25, tavily: 20, ddgs: 14, dailyhot: 10 } },
      graph: {
        nodes: [
          { id: 'center', name: '考研经验分享', type: 'topic', val: 40, color: '#6366f1' },
          { id: 'souyisou', name: '搜一搜', type: 'platform', val: 35, color: '#07c160' },
          { id: 'gongzhonghao', name: '公众号', type: 'platform', val: 28, color: '#07c160' },
          { id: 'shipinhao', name: '视频号', type: 'platform', val: 22, color: '#07c160' },
          { id: 'core-kw', name: '核心大词', type: 'keyword', val: 25, color: '#ef4444' },
          { id: 'school-kw', name: '院校专业词', type: 'keyword', val: 22, color: '#f59e0b' },
          { id: 'longtail-kw', name: '长尾问题词', type: 'keyword', val: 20, color: '#10b981' },
          { id: 'student', name: '考研学生', type: 'audience', val: 28, color: '#22d3ee' },
          { id: 'timeline', name: '备考时间线', type: 'content', val: 18, color: '#8b5cf6' },
          { id: 'experience', name: '上岸经验帖', type: 'content', val: 22, color: '#8b5cf6' },
          { id: 'materials', name: '资料引流', type: 'strategy', val: 16, color: '#fb923c' },
          { id: 'community', name: '考研社群', type: 'strategy', val: 15, color: '#fb923c' },
          { id: 'peoplerank', name: 'Peoplerank', type: 'algorithm', val: 18, color: '#a78bfa' },
          { id: 'ai-notes', name: 'AI辅助笔记', type: 'tool', val: 14, color: '#6366f1' },
        ],
        links: [
          { source: 'center', target: 'souyisou', label: '核心流量入口', strength: 1 },
          { source: 'center', target: 'gongzhonghao', label: '深度内容', strength: 0.9 },
          { source: 'center', target: 'shipinhao', label: '短视频引流', strength: 0.7 },
          { source: 'souyisou', target: 'core-kw', label: '高竞争', strength: 0.8 },
          { source: 'souyisou', target: 'school-kw', label: '精准流量', strength: 0.9 },
          { source: 'souyisou', target: 'longtail-kw', label: '蓝海机会', strength: 0.9 },
          { source: 'center', target: 'student', label: '目标用户', strength: 1 },
          { source: 'souyisou', target: 'peoplerank', label: '排名算法', strength: 0.8 },
          { source: 'center', target: 'experience', label: '核心内容', strength: 0.9 },
          { source: 'center', target: 'timeline', label: '结构化内容', strength: 0.8 },
          { source: 'gongzhonghao', target: 'materials', label: '涨粉手段', strength: 0.7 },
          { source: 'center', target: 'community', label: '私域沉淀', strength: 0.6 },
          { source: 'center', target: 'ai-notes', label: 'AI提效', strength: 0.7 },
        ],
      },
      sources: [
        { title: '2025年考研报名及搜索趋势分析', url: 'https://education.tencent.com/kaoyan-trend-2025' },
        { title: '搜一搜Peoplerank算法权重解析', url: 'https://mp.weixin.qq.com/s/peoplerank-guide' },
        { title: '考研公众号Top50竞品分析报告', url: 'https://example.com/kaoyan-gzh-analysis' },
      ],
      tokenUsage: { search_tokens: 0, llm_tokens: 0, total_tokens: 0, search_calls: 91, agent_rounds: 2, elapsed_ms: 35600 },
      agentMessages: buildAgentMessages([
        { agent: 'data', round: 1, content: '考研经验赛道：2025 年报名 438 万，搜一搜日均搜索 1200 万次。最大特点：长尾效应极强，一篇优质经验帖可持续获取流量 2-3 年。' },
        { agent: 'content', round: 1, content: '关键词布局应该按"核心大词→院校专业词→长尾问题词"三级体系。蓝海在第三级（"考研二战值不值"等问题词），月搜索 40-100 万但竞争极低。' },
        { agent: 'psych', round: 1, content: '考研用户处于高焦虑状态，最容易被"上岸学长姐"身份吸引。"双非三跨上岸 985"这类标题转化率最高，因为给读者"我也行"的心理暗示。' },
        { agent: 'platform', round: 1, content: '搜一搜 Peoplerank 算法权重：账号垂直度 25% + 内容相关性 40% + 用户行为 35%。建议账号 100% 垂直考研，不发其他内容。' },
        { agent: 'risk', round: 1, content: '风险点：考研政策每年变化，旧内容可能误导。建议明确标注"XXXX 届适用"，并每年 6 月更新一次主推内容。' },
        { agent: 'research', round: 1, content: '头部账号 @考研张老师 的策略：90% 公众号长文 + 10% 视频号短视频引流，单月广告+课程收入 5-10 万。验证商业模式可行。' },
        { agent: 'advocate', round: 1, content: '作为考研用户，我最看重"真实性"。建议提供"成绩单截图""学校录取通知书"作为信任背书。' },
        { agent: 'data', round: 2, content: '关键词布局节奏：3-5 月择校词 / 6-8 月强化词 / 9-11 月冲刺词 / 12-2 月初试经验词。全年滚动收割。' },
        { agent: 'platform', round: 2, content: '搜一搜出词节奏：每周 1 篇深度长文（2500+ 字），每天 1 篇长尾问题文（800-1200 字）。30 天内出词 30+ 个。' },
        { agent: 'content', round: 2, content: '建议建立"考研全程时间线"系列（20 篇连载），覆盖每个备考阶段，形成完整内容矩阵。' },
      ]),
      scoreData: arbiterScore({
        total: 91,
        verdict: '强烈推荐',
        summary: '考研赛道是大学生 KOC 商业化最快的赛道之一：用户付费意愿强 + 内容长尾效应+ 信任度天然。建议立即启动，3 个月内可达 5000 粉，6 个月内开始变现。',
        risks: ['政策每年变化', '需要真实背书', '高峰期竞争激烈'],
        actions: [
          'D1-7：用 5118 调研关键词，发 7 篇覆盖核心词',
          'D8-14：每天 1 篇长尾词文章，铺量出搜索流量',
          'D15-21：发 3 篇重磅长文（完整经验帖）',
          'D22-30：建立社群+ 1 对 1 咨询商业化',
        ],
        dimensions: [{ name: '商业潜力', score: 95 }, { name: '搜索流量', score: 92 }, { name: '内容长尾', score: 95 }, { name: '信任门槛', score: 78 }],
        hkrr: [{ name: '钩子', score: 88 }, { name: '认知', score: 92 }, { name: '关系', score: 85 }, { name: '行动', score: 90 }],
      }),
      arbiterThinking: '7 位专家共识度 91%。核心优势：搜索意图明确+用户付费意愿强+长尾效应+ KOC 身份天然。唯一短板：需要真实背书，但这恰恰是 KOC 相比 MCN 的优势。',
      viralScore: viralScore({
        total: 88,
        pool: '热门流量池',
        poolProb: '85% 概率突破热门池，部分长尾词可进入全站推荐',
        analysis: '考研内容在小红书 + 公众号双平台 CES 表现极佳：高收藏率（学习类典型）+ 高分享率（同学间互推）+ 长尾搜索持续流入。预期单篇收藏 200+，转发 50+，总 CES 突破 1500，进热门池。',
        dimensions: [
          { id: 'title_appeal', name: '标题吸引力', score: 14, max: 15, reason: '"双非三跨上岸 985"具备身份+难度+结果三重钩子。' },
          { id: 'emotion', name: '情绪共鸣', score: 14, max: 15, reason: '直击考研焦虑+逆袭幻想，情绪冲击力极强。' },
          { id: 'platform_fit', name: '平台适配', score: 13, max: 15, reason: '搜一搜+公众号长文最佳组合。' },
          { id: 'blue_ocean', name: '竞争蓝海', score: 8, max: 10, reason: '长尾问题词蓝海明显，但核心词竞争激烈。' },
          { id: 'timeliness', name: '时效窗口', score: 9, max: 10, reason: '考研全年都有热度，节点性强。' },
          { id: 'hook_strength', name: 'Hook 强度', score: 9, max: 10, reason: '"410 分"具体数字+"年前的我也迷茫"共情。' },
          { id: 'info_density', name: '信息密度', score: 9, max: 10, reason: '时间线+具体方法+真实数据，价值密度极高。' },
          { id: 'originality', name: '原创空间', score: 8, max: 10, reason: '个人经验天然原创，但需注意不被搬运。' },
          { id: 'completion_predict', name: '完播预测', score: 4, max: 5, reason: '长文需用结构化标题分段防跳读。' },
        ],
        strengths: ['长尾效应 2-3 年', '用户付费意愿极强', 'KOC 身份信任溢价'],
        weaknesses: ['需提供真实背书', '高峰期竞争激烈', '政策更新风险'],
        tips: ['标题前置"双非/普通本科"等身份钩子', '提供成绩单截图作为信任背书', '建立"考研上岸全记录"20 篇连载', '每年 6 月做一次年度内容更新'],
      }),
      wechatStrategy: wechatStrategy({
        videoTips: [
          '每周 3 条 1-2 分钟经验视频',
          '真人出镜 + 手写笔记展示',
          '发布后引导研友群转发',
          '#考研 #考研经验 #XX大学',
          '评论区置顶公众号链接',
        ],
        videoAlgorithm: '考研类视频依赖搜索流量更多于推荐流量。视频号"朋友在看"在备考阶段触发率较高（同学间互推）。建议视频号作为短钩子，公众号作为转化主阵地。',
        videoBest: ['每条视频结尾"完整经验帖在公众号"', '直播：每周日 20:00 答疑', '系列化标签"考研倒计时 X 天"'],
        officialKws: ['考研经验', '考研规划', 'XX大学考研', '考研时间线', '考研真题', '考研二战值不值', '跨专业考研难不难'],
        officialFmt: '深度长文（3000-5000 字），结构：身份背书 → 时间线 → 复习方法 → 心态调整 → 资源推荐 → 引导关注。',
        officialTips: [
          '"上岸全记录"20 篇连载',
          '提供资料包（PDF 笔记+思维导图）引流',
          '每月做一次"院校调剂资讯"长文',
          '与目标院校学长姐互推',
        ],
        searchKws: ['考研经验 XX大学', '跨考 难度', 'XX 专业 真题', '考研规划 时间线'],
        searchOpt: [
          '布局节奏匹配备考时间线',
          '长尾问题词为主（蓝海+精准）',
          '每篇 SEO 长文目标搜一搜出词 3+',
          '每年更新主力文章保持新鲜度',
        ],
        privateFunnel: [
          '公众号关注 → 加入"考研互助群"',
          '群内每日 6:00 早起打卡',
          '群活跃 → 付费 1V1 咨询',
          '上岸后转化为内容共创者',
        ],
        privateTips: [
          '社群按"目标院校"分群',
          '每月公众号文章总结群内问答',
          '提供"模拟卷+答疑"付费产品',
          '建立"上岸学姐学长内推圈"',
        ],
      }),
    },
  },
  {
    id: 'ai-tool-review',
    title: '学生AI工具测评冷启动',
    prompt: '学生党做AI工具测评内容，从0到1000粉冷启动方案',
    emoji: '🤖',
    result: {
      role: 'assistant',
      content: `### 赛道机会评分：8.8/10

AI工具测评是2025年增长最快的内容赛道，视频号"AI工具"搜索量月均增长45%，公众号新增AI类账号季度环比增长230%。学生党优势：时间充裕可深度体验、天然的"小白视角"降低内容门槛、校园社交圈为冷启动提供种子流量。从0到1000粉预计需要21-30天。

### 内容策略

**冷启动定位三要素：**
1. 身份标签："大学生AI体验官" — 比专业博主更亲切，比普通用户更深入
2. 内容角度："学生党视角" — 免费替代、学习场景、省钱实用
3. 差异化：不做功能罗列，做"场景化解决方案"（如"用AI 3小时写完课程论文"）

**内容金字塔（冷启动期）：**
- 60%引流款：蹭AI热点+新工具首发测评（获取曝光）
- 30%留存款：系列化教程"AI工具实验室"（培养关注）
- 10%转化款：深度对比横评（建立专业度）

**标题建议：**
1. 大学生必装的8个免费AI工具，我后悔没早点知道 (预估CTR: 14%)
2. Kimi vs ChatGPT vs 通义：写课程论文谁最强？实测对比 (预估CTR: 13%)
3. 用AI做PPT，10分钟搞定期末答辩演示（附模板） (预估CTR: 12%)
4. 这个AI工具救了我的毕设！导师以为我肝了一个月 (预估CTR: 12%)
5. 0成本AI工具组合，大学四年够用了 (预估CTR: 11%)

**开场Hook：**
1. "先说结论：这8个AI工具全部免费，覆盖你大学四年90%的学习场景。第3个我天天都在用" (+42%留存)
2. "我把同一篇论文题目分别给ChatGPT、Kimi、通义千问写，结果差距大到我惊了" (+38%留存)
3. "你知道你每天花在重复性学习上的时间有多少吗？AI可以帮你省下来的，远比你想象的多" (+33%留存)

### 微信生态策略

**视频号（冷启动主力）：** 发布时间：每天12:00 + 21:00 双发 | 内容：45-90秒工具快测视频，前3秒展示最终效果 | 标签：#AI工具 #大学生必备 #学习效率 | 冷启动技巧：发布后立即转发到班群/年级群/学校表白墙，撬动校园社交推荐

**搜一搜（长尾流量）：** 核心词：免费AI工具推荐、大学生AI工具、AI写论文 | 长尾词：Kimi怎么用、ChatGPT平替、AI做PPT教程、AI思维导图工具 | 布局节奏：每周用公众号发1篇搜一搜SEO长文

**公众号（内容沉淀）：** 每周1篇深度评测长文（2000-3000字）| 建立"AI工具库"合集功能，方便搜一搜索引 | 引流设计：视频号结尾"完整教程在公众号，回复'AI'获取" | 输出"AI工具周报"栏目，每周推荐3个新工具

**冷启动流量矩阵：**
- 私域引爆：班群+年级群+学校社团群（首批50-100阅读）
- 搜一搜截流：抢占"AI工具推荐"等关键词（日均搜索流量）
- 视频号社交推荐：利用校园社交关系链获取推荐流量
- 公众号SEO：长文布局，收割长尾搜索

### 30天行动路径

**D1-D7（冷启动种子期）：** 视频号日更1条AI工具快测；公众号发布2篇深度文；每条内容发布后转发3-5个校园社群。目标：视频号150粉 + 公众号100粉 = 总250粉。

**D8-D14（蹭热点起量期）：** 第一时间测评最新发布的AI工具/功能更新（如GPT新版本、Kimi新功能）；发布1条对比横评视频（目标爆款）；开始布局搜一搜长尾词。目标：单条播放破5000，总粉丝600。

**D15-D21（系列化留存期）：** 推出"AI工具实验室"固定栏目（每周三发）；发布"大学生AI工具全景图"长内容；开始引导评论互动"你最想测什么工具"。目标：粉丝粘性提升，总粉丝850。

**D22-D30（破千冲刺期）：** 做一次"AI效率挑战"直播/视频（如"AI帮我1天完成一周作业"）；发起粉丝投票选下期测评工具；输出"月度AI工具红黑榜"。目标：总粉丝突破1000，建立稳定更新节奏。

### 数据来源

本次分析基于 MiniMax联网搜索、Serper(Google)、Tavily、DuckDuckGo、DailyHot热搜聚合 共5个引擎的实时数据，覆盖AI工具搜索趋势、视频号新号增长案例及校园KOC冷启动数据。`,
      thinking: [
        { step: '搜索中', detail: '正在搜索AI工具测评冷启动案例与数据...', progress: 10, agents: [{ name: 'MiniMax搜索', status: 'running' }, { name: 'Serper搜索', status: 'running' }, { name: 'Tavily搜索', status: 'pending' }] },
        { step: '搜索完成', detail: '找到 88 条数据，来自 5 个引擎，含视频号新号增长数据和AI赛道分析', progress: 35, agents: [{ name: 'MiniMax搜索', status: 'done', count: 22 }, { name: 'Serper搜索', status: 'done', count: 24 }, { name: 'Tavily搜索', status: 'done', count: 19 }] },
        { step: '构建知识图谱', detail: '正在分析冷启动路径、内容策略及微信生态玩法...', progress: 50 },
        { step: '生成报告', detail: 'AI 正在生成从0到1000粉的完整冷启动方案...', progress: 65 },
      ],
      searchStats: { total_raw: 88, total_deduped: 88, engines: { minimax: 22, serper: 24, tavily: 19, ddgs: 13, dailyhot: 10 } },
      graph: {
        nodes: [
          { id: 'center', name: 'AI工具测评', type: 'topic', val: 40, color: '#6366f1' },
          { id: 'shipinhao', name: '视频号', type: 'platform', val: 30, color: '#07c160' },
          { id: 'gongzhonghao', name: '公众号', type: 'platform', val: 25, color: '#07c160' },
          { id: 'souyisou', name: '搜一搜', type: 'platform', val: 22, color: '#07c160' },
          { id: 'chatgpt', name: 'ChatGPT', type: 'tool', val: 22, color: '#10a37f' },
          { id: 'kimi', name: 'Kimi', type: 'tool', val: 20, color: '#4f46e5' },
          { id: 'tongyi', name: '通义千问', type: 'tool', val: 18, color: '#ff6a00' },
          { id: 'student', name: '大学生', type: 'audience', val: 28, color: '#f59e0b' },
          { id: 'cold-start', name: '冷启动', type: 'strategy', val: 25, color: '#ef4444' },
          { id: 'campus-social', name: '校园社交圈', type: 'channel', val: 20, color: '#22d3ee' },
          { id: 'hot-chase', name: '蹭AI热点', type: 'strategy', val: 18, color: '#fb923c' },
          { id: 'series', name: '系列化内容', type: 'strategy', val: 16, color: '#fb923c' },
          { id: 'comparison', name: '横向对比', type: 'content', val: 20, color: '#8b5cf6' },
          { id: 'tutorial', name: '场景化教程', type: 'content', val: 18, color: '#8b5cf6' },
          { id: 'free-tools', name: '免费工具', type: 'hook', val: 16, color: '#10b981' },
        ],
        links: [
          { source: 'center', target: 'shipinhao', label: '冷启动主力', strength: 1 },
          { source: 'center', target: 'gongzhonghao', label: '深度沉淀', strength: 0.8 },
          { source: 'center', target: 'souyisou', label: '长尾获客', strength: 0.8 },
          { source: 'center', target: 'student', label: '目标用户', strength: 1 },
          { source: 'center', target: 'chatgpt', label: '测评对象', strength: 0.8 },
          { source: 'center', target: 'kimi', label: '测评对象', strength: 0.8 },
          { source: 'center', target: 'tongyi', label: '测评对象', strength: 0.7 },
          { source: 'cold-start', target: 'campus-social', label: '种子流量', strength: 0.9 },
          { source: 'cold-start', target: 'hot-chase', label: '起量手段', strength: 0.8 },
          { source: 'cold-start', target: 'series', label: '留存手段', strength: 0.7 },
          { source: 'center', target: 'comparison', label: '爆款形式', strength: 0.9 },
          { source: 'center', target: 'tutorial', label: '主力内容', strength: 0.8 },
          { source: 'center', target: 'free-tools', label: '流量钩子', strength: 0.7 },
          { source: 'shipinhao', target: 'gongzhonghao', label: '导流', strength: 0.7 },
        ],
      },
      sources: [
        { title: '2025年AI工具类账号增长趋势报告', url: 'https://mp.weixin.qq.com/s/ai-tool-growth-2025' },
        { title: '视频号新号冷启动方法论', url: 'https://channels.weixin.qq.com/cold-start-guide' },
        { title: '校园KOC从0到1案例研究', url: 'https://research.tencent.com/campus-koc-cases' },
      ],
      tokenUsage: { search_tokens: 0, llm_tokens: 0, total_tokens: 0, search_calls: 88, agent_rounds: 2, elapsed_ms: 33100 },
      agentMessages: buildAgentMessages([
        { agent: 'data', round: 1, content: 'AI 工具测评赛道增速第一：视频号月增 45%，公众号新账号季度增 230%。窗口期还有 6-12 个月，必须立即入场。' },
        { agent: 'content', round: 1, content: '冷启动金字塔：60% 引流款（蹭热点新工具）+ 30% 留存款（系列化教程）+ 10% 转化款（深度对比）。结构清晰可复制。' },
        { agent: 'psych', round: 1, content: '大学生选择 AI 工具的核心心理 = "免费替代+省时间+学习场景"。"0 成本 AI 工具"标题最容易点击。' },
        { agent: 'platform', round: 1, content: '冷启动靠校园社交链至关重要：班群+年级群+表白墙是种子流量主战场。1 条视频可起到 50-100 阅读基础。' },
        { agent: 'risk', round: 1, content: 'AI 工具变化快，3 个月前的内容就过时。必须建立"工具周报"机制保持鲜活度。' },
        { agent: 'research', round: 1, content: '参考 @AI 学长（视频号 8 万粉丝），其爆款公式：1 条对比型横评（每月 1 条）+ 工具快测短视频（每周 3 条）。' },
        { agent: 'advocate', round: 1, content: '我希望测评者真的用过这些工具，而不是搜索后罗列。"我用 100 天后总结的"才是真的可信。' },
        { agent: 'data', round: 2, content: '从 0 到 1000 粉冷启动 21-30 天可达成。视频号 + 公众号双开效率最高。' },
        { agent: 'content', round: 2, content: '建议确立 4 个固定栏目：每日工具推荐 / 每周横评 / 每月红黑榜 / 每季趋势报告。' },
        { agent: 'platform', round: 2, content: '搜一搜布局核心：抓"免费 AI 工具""ChatGPT 平替""AI 写论文"等长尾词，单篇 SEO 文可月引 2000+ 阅读。' },
      ]),
      scoreData: arbiterScore({
        total: 88,
        verdict: '强烈推荐',
        summary: 'AI 工具测评是当前增长最快的内容赛道，技术门槛低、内容迭代快、商业化路径清晰（CPS+品牌合作）。专家共识度 88%，立即启动。',
        risks: ['AI 工具更新极快需持续跟进', '同质化严重需绑定身份', '技术错误会损失信任'],
        actions: [
          'D1-7：选定"大学生 AI 体验官"定位，发首批 7 条快测',
          'D8-14：蹭最新工具热点（GPT 新版本、Kimi 新功能）',
          'D15-21：发布"AI 工具实验室"固定栏目，做对比横评',
          'D22-30：开播直播"AI 效率挑战"',
        ],
        dimensions: [{ name: '赛道增速', score: 95 }, { name: '内容迭代', score: 88 }, { name: '商业化', score: 82 }, { name: '技术门槛', score: 75 }],
        hkrr: [{ name: '钩子', score: 90 }, { name: '认知', score: 82 }, { name: '关系', score: 80 }, { name: '行动', score: 86 }],
      }),
      arbiterThinking: '7 位专家共识：本赛道短期爆发力强、KOC 身份天然适配、商业化清晰。但需持续跟进新工具，建立"工具周报"机制。',
      viralScore: viralScore({
        total: 84,
        pool: '热门流量池',
        poolProb: '80% 概率突破初级、进入热门池',
        analysis: 'AI 工具内容在小红书 CES 算法下表现优异：收藏属性强（用户先存后用），分享意愿高（推荐给同学），评论互动质量高（求工具求方法）。预期单条收藏 100+，CES 1000+。',
        dimensions: [
          { id: 'title_appeal', name: '标题吸引力', score: 13, max: 15, reason: '"必装"+"免费"+"我后悔没早知道"具备多重钩子。' },
          { id: 'emotion', name: '情绪共鸣', score: 12, max: 15, reason: '"省钱+省时间"双痛点击中大学生。' },
          { id: 'platform_fit', name: '平台适配', score: 12, max: 15, reason: '小红书+视频号+公众号三平台都适用。' },
          { id: 'blue_ocean', name: '竞争蓝海', score: 7, max: 10, reason: '通用 AI 工具竞争激烈，但"AI+学科细分"仍蓝海。' },
          { id: 'timeliness', name: '时效窗口', score: 9, max: 10, reason: 'AI 行业快速发展，每周都有新工具可蹭。' },
          { id: 'hook_strength', name: 'Hook 强度', score: 8, max: 10, reason: '前 3 秒展示工具效果对比有视觉冲击。' },
          { id: 'info_density', name: '信息密度', score: 9, max: 10, reason: '工具+用法+效果+免费/付费信息完整。' },
          { id: 'originality', name: '原创空间', score: 7, max: 10, reason: '需个人化使用场景才能突围同质化。' },
          { id: 'completion_predict', name: '完播预测', score: 4, max: 5, reason: '45-90 秒短视频长度合理。' },
        ],
        strengths: ['赛道增速最快', 'AI 自带工具属性', '商业化路径短'],
        weaknesses: ['同质化严重', '工具更新快', '需技术准确性'],
        tips: ['每条视频前 3 秒"工具界面对比"', '建立"AI工具实验室"固定栏目', '每月做"AI工具红黑榜"', '与 AI 工具厂商谈合作分成'],
      }),
      wechatStrategy: wechatStrategy({
        videoTips: [
          '每天 12:00 + 21:00 双发，校园活跃高峰',
          '45-90 秒工具快测，前 3 秒展示最终效果',
          '#AI工具 #大学生必备 #学习效率',
          '发布后立即转发班群/年级群/表白墙',
          '每周三发"工具实验室"系列固定栏目',
        ],
        videoAlgorithm: '视频号 AI 类内容靠"朋友在看"传播尤其有效（同学间分享率高）。建议绑定具体身份"大学生 AI 体验官"，建立认知。',
        videoBest: [
          '每月 1 条横评（5 分钟+）形成深度内容护城河',
          '直播"AI 效率挑战"如"1 天完成一周作业"',
          '与其他校园 AI 博主互推',
        ],
        officialKws: ['免费AI工具', '大学生AI', 'AI写论文', 'Kimi教程', 'ChatGPT平替', 'AI做PPT', 'AI思维导图'],
        officialFmt: '每周 1 篇深度评测长文（2000-3000 字），结构：工具介绍 → 试用场景 → 效果对比 → 优缺点 → 推荐人群。',
        officialTips: [
          '建立"AI 工具库"合集功能，方便搜一搜',
          '"AI 工具周报"栏目每周三推送',
          '提供"AI 工具包"作为关注钩子',
          '与 AI 工具厂商谈定向合作',
        ],
        searchKws: ['免费AI工具推荐', 'Kimi怎么用', 'AI做PPT教程', 'ChatGPT平替', 'AI思维导图工具'],
        searchOpt: [
          '前 18 字命中"免费/工具/教程"高频词',
          '布局长尾"具体工具+具体场景"',
          '每月更新"工具排行榜"长文',
          '抢占新工具发布的 24h 黄金窗口',
        ],
        privateFunnel: [
          '视频号关注 → 公众号资料包',
          '公众号关注 → AI工具学习群',
          '群活跃 → 付费 AI 课程',
          '高活跃 → 一对一咨询',
        ],
        privateTips: [
          '群内每周分享"工具+场景"组合',
          '提供工具优惠码作为粉丝福利',
          '建立"AI 工具评测员"招募机制',
          '每月直播"AI 工具研究所"',
        ],
      }),
    },
  },
  {
    id: 'graduation-content',
    title: '毕业季全平台分发策略',
    prompt: '毕业季相关内容如何做全平台分发策略？',
    emoji: '🎓',
    result: {
      role: 'assistant',
      content: `### 赛道机会评分：9.3/10

毕业季（5-7月）是年度最大的校园内容流量峰值，微信生态"毕业"相关搜索量在6月达到全年峰值（日均搜索2000万+）。特点：时效性强（黄金窗口仅6-8周）、情绪价值高（共鸣感极强）、商业价值大（毕业照/旅行/租房/求职多个变现场景）。大学生KOC具备天然优势——你就是毕业季的"当事人"。

### 内容策略

**全平台内容差异化矩阵：**

| 平台 | 内容方向 | 形式 | 调性 | 发布时机 |
|------|---------|------|------|---------|
| 视频号 | 毕业vlog/校园回忆 | 1-3分钟视频 | 温情、共鸣 | 6月初开始 |
| 公众号 | 毕业攻略/干货长文 | 3000字图文 | 实用、全面 | 5月中开始 |
| 搜一搜 | 毕业相关问题解答 | SEO文章 | 精准、有用 | 4月底布局 |
| 小红书 | 毕业穿搭/拍照攻略 | 图文笔记 | 好看、种草 | 5月开始 |
| 朋友圈 | 毕业仪式感内容 | 精美图文 | 真实、感动 | 全程记录 |

**内容选题池（覆盖毕业季全周期）：**

**情感向（高传播）：**
- "大学四年，最后悔没做的5件事"
- "给大一新生的一封信：如果重来一次..."
- "散伙饭上我们说好不哭，但没人做到"

**实用向（高搜索）：**
- "毕业答辩PPT模板+AI一键生成"
- "应届生租房避坑指南（亲身经历版）"
- "毕业论文查重从80%降到5%的全过程"

**记录向（高互动）：**
- "毕业前的100个校园瞬间"
- "我在学校的最后一顿食堂"
- "四年前vs四年后的对比照"

**标题建议：**
1. 毕业前最后30天，我用镜头记录了所有"最后一次" (预估CTR: 16%)
2. 2026届毕业生必看：这份毕业清单帮你不留遗憾 (预估CTR: 14%)
3. AI帮我做了一份大学四年回忆录，看哭了全寝室 (预估CTR: 13%)
4. 答辩PPT别自己做了！AI 10分钟搞定（附prompt） (预估CTR: 12%)
5. 毕业旅行人均800的绝美路线，大学生狠狠省 (预估CTR: 11%)

### 微信生态策略

**视频号（情感共鸣+社交裂变）：** 核心策略：拍摄"毕业倒计时"系列vlog（D-30到D-Day）| 发布时间：每天20:00-22:00 | 裂变设计：结尾"转发给你最想@的大学同学" | AI应用：用AI剪辑工具自动匹配BGM和转场，效率提升5倍 | 变现：毕业照/毕业视频定制服务

**搜一搜（提前布局长尾词）：** 提前2个月布局：
- 高流量词："毕业论文查重""毕业答辩PPT""毕业证照片要求"
- 情感词："大学毕业文案""毕业朋友圈配文""给室友的毕业寄语"
- 实用词："应届生档案怎么处理""报到证办理流程""毕业后社保怎么交"
- 策略：用AI批量生成10-20篇SEO文章，提前抢占搜一搜排名

**公众号（深度内容+资源沉淀）：** 推出"毕业季完全手册"系列（5-8篇）| 提供可下载资源（毕业PPT模板、论文格式模板、简历模板）| 引导加入"毕业互助群" | 与学校官方号联动转发

### 30天行动路径

**D1-D7（预热布局期 / 毕业前45天）：** 搜一搜发布10篇SEO文章抢占关键词；公众号发布"毕业季完全指南"首篇；视频号预告"毕业倒计时vlog"。目标：搜一搜出词5个+，粉丝积累300。

**D8-D14（内容爆发期 / 毕业前30天）：** 视频号日更"倒计时vlog"；公众号发布答辩/论文/求职干货系列；蹭毕业季热搜话题。目标：视频号单条播放破万，粉丝1500+。

**D15-D21（情感高潮期 / 毕业典礼周）：** 发布"毕业典礼"当天实况；制作"四年回顾"AI混剪视频；情感向内容冲击爆款（目标10万+播放）。目标：1-2条内容破10万播放，粉丝5000+。

**D22-D30（长尾收割期 / 毕业后）：** 发布"毕业后第一周"真实记录；输出"给学弟学妹的建议"长内容；搜一搜继续收割"应届生""档案""租房"等长尾流量。目标：总粉丝8000+，建立"校园→职场过渡"内容方向。

### 数据来源

本次分析基于 MiniMax联网搜索、Serper(Google)、Tavily、DuckDuckGo、DailyHot热搜聚合 共5个引擎的实时数据，覆盖往年毕业季搜索趋势、视频号情感类爆款案例及校园KOC毕业季运营案例。`,
      thinking: [
        { step: '搜索中', detail: '正在搜索毕业季内容营销案例及平台数据...', progress: 10, agents: [{ name: 'MiniMax搜索', status: 'running' }, { name: 'DailyHot热搜', status: 'running' }, { name: 'Tavily搜索', status: 'running' }] },
        { step: '搜索完成', detail: '找到 94 条数据，来自 5 个引擎，覆盖多平台毕业季内容趋势', progress: 35, agents: [{ name: 'MiniMax搜索', status: 'done', count: 24 }, { name: 'Serper搜索', status: 'done', count: 26 }, { name: 'Tavily搜索', status: 'done', count: 20 }] },
        { step: '构建知识图谱', detail: '正在分析全平台分发策略及毕业季内容生态...', progress: 52 },
        { step: '生成报告', detail: 'AI 正在生成毕业季全平台运营策略...', progress: 68 },
      ],
      searchStats: { total_raw: 94, total_deduped: 94, engines: { minimax: 24, serper: 26, tavily: 20, ddgs: 14, dailyhot: 10 } },
      graph: {
        nodes: [
          { id: 'center', name: '毕业季内容', type: 'topic', val: 40, color: '#6366f1' },
          { id: 'shipinhao', name: '视频号', type: 'platform', val: 30, color: '#07c160' },
          { id: 'gongzhonghao', name: '公众号', type: 'platform', val: 28, color: '#07c160' },
          { id: 'souyisou', name: '搜一搜', type: 'platform', val: 25, color: '#07c160' },
          { id: 'xiaohongshu', name: '小红书', type: 'platform', val: 22, color: '#ff2442' },
          { id: 'emotion', name: '情感共鸣', type: 'content', val: 25, color: '#f472b6' },
          { id: 'practical', name: '实用干货', type: 'content', val: 22, color: '#10b981' },
          { id: 'vlog', name: '毕业vlog', type: 'content', val: 20, color: '#8b5cf6' },
          { id: 'graduate', name: '应届毕业生', type: 'audience', val: 30, color: '#f59e0b' },
          { id: 'freshman', name: '大一新生', type: 'audience', val: 18, color: '#f59e0b' },
          { id: 'ai-edit', name: 'AI剪辑', type: 'tool', val: 16, color: '#6366f1' },
          { id: 'ai-write', name: 'AI写作', type: 'tool', val: 16, color: '#6366f1' },
          { id: 'thesis', name: '毕业论文', type: 'scenario', val: 20, color: '#ef4444' },
          { id: 'job', name: '求职', type: 'scenario', val: 18, color: '#ef4444' },
          { id: 'countdown', name: '倒计时策略', type: 'strategy', val: 18, color: '#fb923c' },
          { id: 'viral', name: '社交裂变', type: 'strategy', val: 16, color: '#fb923c' },
        ],
        links: [
          { source: 'center', target: 'shipinhao', label: '情感主阵地', strength: 1 },
          { source: 'center', target: 'gongzhonghao', label: '深度干货', strength: 0.9 },
          { source: 'center', target: 'souyisou', label: '提前SEO', strength: 0.9 },
          { source: 'center', target: 'xiaohongshu', label: '种草分发', strength: 0.7 },
          { source: 'center', target: 'graduate', label: '核心用户', strength: 1 },
          { source: 'center', target: 'emotion', label: '高传播', strength: 0.9 },
          { source: 'center', target: 'practical', label: '高搜索', strength: 0.8 },
          { source: 'center', target: 'vlog', label: '核心形式', strength: 0.8 },
          { source: 'shipinhao', target: 'countdown', label: '系列策略', strength: 0.8 },
          { source: 'shipinhao', target: 'viral', label: '裂变机制', strength: 0.7 },
          { source: 'center', target: 'ai-edit', label: '提效工具', strength: 0.7 },
          { source: 'center', target: 'thesis', label: '刚需场景', strength: 0.8 },
          { source: 'center', target: 'job', label: '延伸方向', strength: 0.6 },
          { source: 'graduate', target: 'freshman', label: '受众延伸', strength: 0.5 },
        ],
      },
      sources: [
        { title: '微信生态毕业季搜索趋势报告（2023-2025）', url: 'https://mp.weixin.qq.com/s/graduation-trend' },
        { title: '视频号情感类内容爆款案例库', url: 'https://channels.weixin.qq.com/emotion-cases' },
        { title: '校园KOC毕业季运营实操手册', url: 'https://example.com/campus-graduation-ops' },
      ],
      tokenUsage: { search_tokens: 0, llm_tokens: 0, total_tokens: 0, search_calls: 94, agent_rounds: 2, elapsed_ms: 36200 },
      agentMessages: buildAgentMessages([
        { agent: 'data', round: 1, content: '毕业季内容是年度最大流量峰值（5-7 月），微信"毕业"日均搜索 2000 万+。窗口期仅 6-8 周，必须提前 2 个月布局。' },
        { agent: 'content', round: 1, content: '内容矩阵建议：情感向（高传播）+ 实用向（高搜索）+ 记录向（高互动）三类并行。情感向单条破 10 万播放可能性最大。' },
        { agent: 'psych', round: 1, content: '毕业生心理：怀念+焦虑+仪式感。"最后 30 天最后一次"系列直击仪式感诉求，转发率最高。' },
        { agent: 'platform', round: 1, content: '视频号在毕业季有天然优势：朋友圈发达，社交链路触发率最高。建议视频号为情感主阵地。' },
        { agent: 'risk', round: 1, content: '风险：毕业季后流量暴跌，需提前准备"应届生"延伸内容（租房/求职/档案）作为长尾。' },
        { agent: 'research', round: 1, content: '参考案例 @毕业季鸭（视频号 30 万粉），核心爆款是"散伙饭""最后一节课"等情绪锚点视频，单条平均 50 万播放。' },
        { agent: 'advocate', round: 1, content: '我会主动转发"代我说出心声"的内容。建议多用"我们""你""他"的人称词制造代入感。' },
        { agent: 'data', round: 2, content: '建议视频号倒计时 vlog（D-30 到 D-Day）系列化，每天发布制造期待感。' },
        { agent: 'content', round: 2, content: '搜一搜布局应提前 2 个月开始：4 月起布局"毕业论文""答辩 PPT""毕业证照片"等长尾词。' },
        { agent: 'platform', round: 2, content: '视频号+公众号联动：视频号情感引爆+公众号深度长文沉淀，形成内容生态闭环。' },
      ]),
      scoreData: arbiterScore({
        total: 93,
        verdict: '强烈推荐',
        summary: '毕业季内容是流量峰值赛道，KOC 大学生身份天然适配（你就是当事人）。建议立即启动，错过窗口期后赛道沉寂。',
        risks: ['窗口期短（6-8 周）', '7 月后流量暴跌', '需提前布局长尾'],
        actions: [
          'D1-7（毕业前 45 天）：搜一搜 SEO 文章布局 10 篇',
          'D8-14（毕业前 30 天）：视频号倒计时 vlog 启动',
          'D15-21（毕业典礼周）：发布"四年回顾"AI 混剪冲击爆款',
          'D22-30（毕业后）：转向"应届生"延伸内容（长尾收割）',
        ],
        dimensions: [{ name: '流量天花板', score: 100 }, { name: '情感共鸣', score: 95 }, { name: 'KOC适配', score: 92 }, { name: '商业化', score: 75 }, { name: '窗口期长度', score: 60 }],
        hkrr: [{ name: '钩子', score: 92 }, { name: '认知', score: 78 }, { name: '关系', score: 95 }, { name: '行动', score: 85 }],
      }),
      arbiterThinking: '7 位专家高度一致：本赛道在"流量天花板+情感共鸣+KOC 身份适配"三维度均为最强项。唯一风险是窗口期短，需提前 2 个月布局并准备长尾延伸。',
      viralScore: viralScore({
        total: 90,
        pool: '全站推荐池',
        poolProb: '88% 概率单篇破 10 万播放',
        analysis: '毕业季情感内容在视频号的爆款公式：社交关系链×情感共鸣 = 病毒式传播。预期单条爆款 50-100 万播放、点赞 5 万+、转发 1 万+，CES 突破 5000 进全站推荐池。',
        dimensions: [
          { id: 'title_appeal', name: '标题吸引力', score: 14, max: 15, reason: '"最后 30 天""所有最后一次"具备时间紧迫+仪式感双重钩子。' },
          { id: 'emotion', name: '情绪共鸣', score: 15, max: 15, reason: '毕业是全人生最强情绪锚点之一，共鸣天花板高。' },
          { id: 'platform_fit', name: '平台适配', score: 14, max: 15, reason: '视频号社交链路+情感内容完美匹配。' },
          { id: 'blue_ocean', name: '竞争蓝海', score: 6, max: 10, reason: '毕业季内容竞争激烈，需差异化角度。' },
          { id: 'timeliness', name: '时效窗口', score: 10, max: 10, reason: '5-7 月年度最高峰，全网毕业关键词搜索爆炸。' },
          { id: 'hook_strength', name: 'Hook 强度', score: 9, max: 10, reason: '"散伙饭上我们说好不哭"瞬间共情。' },
          { id: 'info_density', name: '信息密度', score: 6, max: 10, reason: '情感内容信息密度可低，但需画面/音乐补足。' },
          { id: 'originality', name: '原创空间', score: 8, max: 10, reason: '每个人毕业故事都不同，原创空间足够。' },
          { id: 'completion_predict', name: '完播预测', score: 5, max: 5, reason: '1-3 分钟视频+情感节奏完美。' },
        ],
        strengths: ['流量天花板最高', '情感共鸣天然', 'KOC 身份适配最优'],
        weaknesses: ['窗口期短', '需高质量画面', '后期流量断崖'],
        tips: ['倒计时 vlog 系列化（D-30 到 D-Day）', '使用 AI 剪辑工具提升效率（剪映 AI、Premiere AI）', '每条视频结尾"@你最想标记的人"', '提前布局"应届生"长尾延伸内容'],
      }),
      wechatStrategy: wechatStrategy({
        videoTips: [
          '每天 20:00-22:00 发布（晚间情感时段）',
          '倒计时 vlog 系列：D-30 → D-Day',
          '前 3 秒展示场景（教室/食堂/校门口）',
          '结尾 CTA："转发给你最想@的同学"',
          '使用经典毕业 BGM 触发情绪',
        ],
        videoAlgorithm: '视频号情感内容主要靠"朋友在看"传播。毕业季同学间分享率最高（人际关系最浓密的时刻），1 条优质内容可触达 200-500 个同学。',
        videoBest: [
          '与同班同学合拍 vlog 系列',
          '使用 AI 剪辑批量生产（提效 5x）',
          '每周日做一次"本周毕业回忆"长视频',
          '直播"毕业典礼"当天实况',
        ],
        officialKws: ['毕业文案', '毕业朋友圈', '毕业季配文', '答辩 PPT', '毕业论文', '应届生租房', '档案处理'],
        officialFmt: '深度推文（2500-4000 字），结构：情感引入 → 干货部分（论文/答辩/求职）→ 资源包（PPT 模板/简历模板）→ 引导关注。',
        officialTips: [
          '"毕业季完全手册"系列 5-8 篇连载',
          '提供下载资源（PPT/论文/简历模板）',
          '与学校官方号联动转发',
          '建立"毕业互助群"沉淀长尾用户',
        ],
        searchKws: ['毕业 文案', '答辩 PPT 模板', '毕业论文 查重', '应届生 档案', '毕业季 vlog'],
        searchOpt: [
          '提前 2 个月布局长尾词（4 月开始）',
          'AI 批量生成 10-20 篇 SEO 文章',
          '每周更新"当周毕业季话题"',
          '抢占"应届生"长尾延伸（5-12 月持续）',
        ],
        privateFunnel: [
          '视频号关注 → 公众号"毕业资料包"',
          '公众号关注 → 毕业季互助群',
          '群活跃 → 求职信息分享',
          '应届生→ 长期"职场过渡"用户',
        ],
        privateTips: [
          '群名"XX 大学 2026 届毕业生"',
          '群内每周分享 1 个干货资源',
          '建立"毕业季拍摄团"互助小组',
          '后续转化为"应届生互助群"',
        ],
      }),
    },
  },
  {
    id: 'dorm-budget',
    title: '宿舍好物博主AI提效',
    prompt: '宿舍好物/校园省钱博主如何用AI提升笔记质量？',
    emoji: '💰',
    result: {
      role: 'assistant',
      content: `### 赛道机会评分：8.0/10

"宿舍好物/校园省钱"是大学生消费决策的核心内容赛道，视频号"宿舍好物"话题播放量超15亿，公众号"大学生省钱"类文章平均打开率比均值高40%。赛道优势：受众精准（全国3000万在校大学生）、复购性强（每学期都需要新好物）、商业化路径清晰（好物推荐→带货佣金）。AI可解决最大痛点：内容同质化严重，用AI做差异化是破局关键。

### 内容策略

**AI提效5大应用场景：**

| 场景 | 传统做法 | AI提效做法 | 质量提升 |
|------|---------|-----------|---------|
| 选品调研 | 手动翻平台 | AI抓取多平台热销数据 | 选品精准度↑60% |
| 文案撰写 | 通用模板 | AI生成多角度卖点描述 | 创意度↑80% |
| 价格对比 | 手动比价 | AI自动抓取价格+历史最低价 | 数据完整度↑90% |
| 封面设计 | 固定模板 | AI生成多款封面A/B测试 | 点击率↑35% |
| 评论互动 | 手动回复 | AI辅助生成个性化回复 | 互动率↑50% |

**差异化内容方向：**
1. "数据型好物推荐" — 每个推荐都附带价格走势、评分对比（AI自动收集）
2. "省钱计算器" — AI帮算一学期各类支出对比方案
3. "宿舍改造AI设计" — 用AI出宿舍布局效果图+好物清单
4. "好物红黑榜" — AI分析全网评价，做正反面对比

**标题建议：**
1. 我用AI帮室友省了2000块，这份宿舍好物清单太实在了 (预估CTR: 14%)
2. 大学生月消费1500，我的省钱神器全靠这8样 (预估CTR: 13%)
3. AI帮我比价后发现：这些宿舍"网红"产品是智商税 (预估CTR: 13%)
4. 9.9包邮 vs 99块的宿舍好物，AI显微镜测评来了 (预估CTR: 12%)
5. 开学季宿舍必买清单，AI帮你算出最优解 (预估CTR: 11%)

**开场Hook：**
1. "你花200块买的宿舍好物，我用AI找到了19.9的平替——质量几乎一样" (+40%留存)
2. "我让AI分析了5000条好物评价，帮你们筛掉了一半智商税" (+36%留存)
3. "一学期在宿舍好物上花了3000？如果你早看到这篇，至少省1500" (+34%留存)

### 微信生态策略

**视频号（种草主阵地）：** 内容形式：30-60秒好物开箱/对比视频 | 发布时间：周二/四/六 20:00（大学生刷手机高峰）| AI应用：视频脚本AI生成+AI字幕 | 互动：结尾"你宿舍还缺什么？评论区告诉我" | 带货：视频号小店挂链接

**搜一搜（搜索截流）：** 核心词：宿舍好物推荐、大学生省钱攻略、宿舍收纳 | 长尾词：女生宿舍必买清单、男生宿舍好物、大学生生活费1500怎么花 | 季节词：开学必备清单、夏天宿舍神器、冬天宿舍保暖好物 | 策略：每月更新"当季好物推荐"长文，持续收割搜索流量

**公众号（深度测评+社群运营）：** 每周1篇"好物深度测评"长文（图文并茂，附购买链接）| "每月省钱报告"栏目——AI统计推荐好物为粉丝省了多少钱 | 社群运营：建立"校园省钱群"，日常分享优惠信息 | 商业化：好物推荐CPS佣金+品牌合作

### 30天行动路径

**D1-D7（AI工作流搭建期）：** 搭建AI选品→AI写文→AI比价→AI配图的全流程；发布7条视频号好物推荐；公众号发2篇开箱测评。目标：跑通AI提效流程，粉丝300。

**D8-D14（内容质量打磨期）：** 用AI做"价格历史对比图"提升内容专业度；发布"智商税"系列（AI分析差评数据）；优化封面（AI生成+A/B测试）。目标：单条播放稳定2000+，粉丝800。

**D15-D21（特色栏目建立期）：** 推出"AI省钱计算器"栏目（AI计算最优购买方案）；做一次"宿舍改造"AI设计方案内容（高收藏）；联动其他校园号互推。目标：1篇爆款内容，粉丝1800。

**D22-D30（商业化测试期）：** 尝试视频号小店带货（低客单价好物）；接第一个品牌推广（宿舍好物品牌）；AI辅助生成商业化内容，保持质量不降。目标：首笔收入，粉丝3000+。

### 数据来源

本次分析基于 MiniMax联网搜索、Serper(Google)、Tavily、DuckDuckGo、DailyHot热搜聚合 共5个引擎的实时数据，覆盖宿舍好物赛道数据、大学生消费行为研究及AI辅助内容创作案例。`,
      thinking: [
        { step: '搜索中', detail: '正在搜索宿舍好物/省钱博主运营数据...', progress: 10, agents: [{ name: 'MiniMax搜索', status: 'running' }, { name: 'Serper搜索', status: 'running' }, { name: 'DuckDuckGo', status: 'running' }] },
        { step: '搜索完成', detail: '找到 79 条数据，来自 5 个引擎，含好物赛道分析与AI提效工具评测', progress: 35, agents: [{ name: 'MiniMax搜索', status: 'done', count: 19 }, { name: 'Serper搜索', status: 'done', count: 22 }, { name: 'Tavily搜索', status: 'done', count: 17 }] },
        { step: '构建知识图谱', detail: '正在分析AI提效方案与好物推荐内容生态...', progress: 48 },
        { step: '生成报告', detail: 'AI 正在生成好物博主AI提效方案...', progress: 63 },
      ],
      searchStats: { total_raw: 79, total_deduped: 79, engines: { minimax: 19, serper: 22, tavily: 17, ddgs: 12, dailyhot: 9 } },
      graph: {
        nodes: [
          { id: 'center', name: '宿舍好物/省钱', type: 'topic', val: 40, color: '#10b981' },
          { id: 'shipinhao', name: '视频号', type: 'platform', val: 28, color: '#07c160' },
          { id: 'gongzhonghao', name: '公众号', type: 'platform', val: 25, color: '#07c160' },
          { id: 'souyisou', name: '搜一搜', type: 'platform', val: 22, color: '#07c160' },
          { id: 'ai-price', name: 'AI比价', type: 'tool', val: 22, color: '#6366f1' },
          { id: 'ai-copywrite', name: 'AI文案', type: 'tool', val: 20, color: '#6366f1' },
          { id: 'ai-design', name: 'AI设计', type: 'tool', val: 18, color: '#6366f1' },
          { id: 'student', name: '在校大学生', type: 'audience', val: 30, color: '#f59e0b' },
          { id: 'dorm', name: '宿舍场景', type: 'scenario', val: 22, color: '#ef4444' },
          { id: 'budget', name: '省钱需求', type: 'scenario', val: 20, color: '#ef4444' },
          { id: 'unbox', name: '开箱测评', type: 'content', val: 18, color: '#8b5cf6' },
          { id: 'iq-tax', name: '智商税揭秘', type: 'content', val: 16, color: '#8b5cf6' },
          { id: 'seasonal', name: '季节性选品', type: 'strategy', val: 15, color: '#fb923c' },
          { id: 'cps', name: 'CPS带货', type: 'monetize', val: 16, color: '#f472b6' },
          { id: 'community', name: '省钱社群', type: 'strategy', val: 14, color: '#fb923c' },
        ],
        links: [
          { source: 'center', target: 'shipinhao', label: '种草主阵地', strength: 1 },
          { source: 'center', target: 'gongzhonghao', label: '深度测评', strength: 0.8 },
          { source: 'center', target: 'souyisou', label: '搜索获客', strength: 0.8 },
          { source: 'center', target: 'student', label: '目标用户', strength: 1 },
          { source: 'center', target: 'ai-price', label: 'AI比价提效', strength: 0.9 },
          { source: 'center', target: 'ai-copywrite', label: 'AI写文提效', strength: 0.8 },
          { source: 'center', target: 'ai-design', label: 'AI设计提效', strength: 0.7 },
          { source: 'student', target: 'dorm', label: '使用场景', strength: 0.9 },
          { source: 'student', target: 'budget', label: '核心需求', strength: 0.9 },
          { source: 'center', target: 'unbox', label: '主力内容', strength: 0.8 },
          { source: 'center', target: 'iq-tax', label: '差异化内容', strength: 0.7 },
          { source: 'center', target: 'seasonal', label: '选题策略', strength: 0.7 },
          { source: 'center', target: 'cps', label: '商业模式', strength: 0.6 },
          { source: 'gongzhonghao', target: 'community', label: '私域沉淀', strength: 0.6 },
        ],
      },
      sources: [
        { title: '2025年大学生消费与好物推荐行为研究', url: 'https://research.tencent.com/student-consumption-2025' },
        { title: 'AI辅助电商内容创作白皮书', url: 'https://mp.weixin.qq.com/s/ai-ecommerce-content' },
        { title: '视频号好物推荐赛道增长数据', url: 'https://channels.weixin.qq.com/goods-trend' },
      ],
      tokenUsage: { search_tokens: 0, llm_tokens: 0, total_tokens: 0, search_calls: 79, agent_rounds: 2, elapsed_ms: 30500 },
      agentMessages: buildAgentMessages([
        { agent: 'data', round: 1, content: '宿舍好物/省钱赛道：视频号"宿舍好物"播放 15 亿+，公众号"大学生省钱"打开率高于均值 40%。受众 3000 万在校大学生，复购性强（每学期换新）。' },
        { agent: 'content', round: 1, content: 'AI 提效核心场景：选品调研（80% 节省）+ 文案撰写（70%）+ 价格对比（90%）+ 封面设计（35% CTR 提升）。让一人可以日更。' },
        { agent: 'psych', round: 1, content: '大学生消费心理：怕踩雷+省钱+集体安全感。"AI 帮我比价后发现智商税"完美命中"避坑求知"心理。' },
        { agent: 'platform', round: 1, content: '视频号小店是天然带货闭环。建议视频号种草+小店挂链，单次转化率比小红书+淘宝高 30%。' },
        { agent: 'risk', round: 1, content: '风险：好物推荐易陷入"夸夸"模式，损失公信力。建议建立"红黑榜"制度，正反两面都讲。' },
        { agent: 'research', round: 1, content: '参考 @宿舍好物排行榜（视频号 5 万粉），月 GMV 8-15 万。模式：60% 种草+ 30% 红黑榜+ 10% 改造灵感。' },
        { agent: 'advocate', round: 1, content: '我会被"AI 帮我找到的 19.9 平替"这种内容吸引。具体价格+具体效果对比比"网红推荐"更可信。' },
        { agent: 'data', round: 2, content: 'AI 工作流跑通后日更可达，30 天可达 3000+ 粉丝、首笔商业收入。' },
        { agent: 'content', round: 2, content: '差异化建议：建立"数据型好物推荐"——每个推荐附带价格走势、评分对比、AI 自动收集的 5000+ 评价分析。' },
        { agent: 'platform', round: 2, content: '搜一搜核心词："宿舍好物""大学生省钱""宿舍收纳"。每月更新"当季好物"长文持续收割搜索流量。' },
      ]),
      scoreData: arbiterScore({
        total: 80,
        verdict: '推荐',
        summary: '宿舍好物/省钱赛道是商业化最快的赛道之一（CPS 当月可有收入），但同质化严重。建议绑定"AI 提效+数据化"差异化身份，30 天内可达 3000 粉+首笔收入。',
        risks: ['同质化严重需差异化', 'CPS 比例下行风险', '商家对接需谈判能力'],
        actions: [
          'D1-7：搭建 AI 选品+写文+比价+配图全流程',
          'D8-14：测试"价格历史对比图"等差异化内容',
          'D15-21：推出"AI 省钱计算器"特色栏目',
          'D22-30：尝试视频号小店带货+第一个品牌推广',
        ],
        dimensions: [{ name: '商业化速度', score: 95 }, { name: 'AI 提效适配', score: 92 }, { name: '复购性', score: 90 }, { name: '差异化难度', score: 65 }],
        hkrr: [{ name: '钩子', score: 84 }, { name: '认知', score: 78 }, { name: '关系', score: 80 }, { name: '行动', score: 88 }],
      }),
      arbiterThinking: '7 位专家共识：本赛道商业化速度极快，但同质化是最大挑战。建议绑定"AI+数据化"差异点，避免陷入通用好物推荐红海。',
      viralScore: viralScore({
        total: 75,
        pool: '初级流量池',
        poolProb: '70% 概率突破初级，需差异化爆款冲热门池',
        analysis: '宿舍好物在小红书 CES 算法下表现中等：收藏率高（5000+ 评论分析+价格走势引发收藏），但分享率偏低（私人化消费决策）。预期单条 CES 600-900。',
        dimensions: [
          { id: 'title_appeal', name: '标题吸引力', score: 12, max: 15, reason: '"省了 2000 块"具体数字+对比，CTR 14%。' },
          { id: 'emotion', name: '情绪共鸣', score: 11, max: 15, reason: '省钱+避坑双心理，但需个人故事增强代入感。' },
          { id: 'platform_fit', name: '平台适配', score: 12, max: 15, reason: '视频号小店+小红书种草双轨。' },
          { id: 'blue_ocean', name: '竞争蓝海', score: 5, max: 10, reason: '通用好物推荐红海，需 AI+数据化差异化。' },
          { id: 'timeliness', name: '时效窗口', score: 8, max: 10, reason: '开学/换季/期末高峰，全年都有需求。' },
          { id: 'hook_strength', name: 'Hook 强度', score: 7, max: 10, reason: '"花 200 找到 19.9 平替"对比强烈。' },
          { id: 'info_density', name: '信息密度', score: 8, max: 10, reason: '价格+评分+对比+教程信息完整。' },
          { id: 'originality', name: '原创空间', score: 6, max: 10, reason: '需个人使用场景才能突围。' },
          { id: 'completion_predict', name: '完播预测', score: 4, max: 5, reason: '30-60 秒短视频长度合理。' },
        ],
        strengths: ['商业化速度最快', 'AI 提效效果显著', '复购性强'],
        weaknesses: ['同质化严重', '需对抗"网红推荐"印象', '需谈判商家合作'],
        tips: ['绑定"AI 比价+数据化"差异点', '每月做一次"智商税"系列负面爆款', '建立"省钱计算器"工具栏目', '与品牌方谈差异化合作'],
      }),
      wechatStrategy: wechatStrategy({
        videoTips: [
          '周二/四/六 20:00 双发（学生晚间高峰）',
          '前 3 秒展示价格对比图（19.9 vs 200）',
          '#宿舍好物 #大学生省钱 #宿舍收纳',
          '视频号小店挂链直接带货',
          '结尾 CTA："你宿舍最缺什么？评论区告诉我"',
        ],
        videoAlgorithm: '视频号好物类内容靠"完播率+小店点击率"双指标。前 3 秒的"价格对比"最关键，能立刻抓住注意力，完播率提升 35%。',
        videoBest: [
          '建立"AI 比价"固定栏目',
          '"宿舍改造 AI 设计方案"高收藏内容',
          '直播"宿舍好物开箱"',
          '与其他校园博主互推',
        ],
        officialKws: ['宿舍好物', '大学生省钱', '宿舍收纳', '宿舍必备', '开学清单', '夏天宿舍神器'],
        officialFmt: '每周 1 篇深度测评长文（图文并茂+购买链接）+"每月省钱报告"栏目',
        officialTips: [
          '"AI 工具库+好物库"双 IP 强化记忆',
          '"每月省钱报告"AI 统计为粉丝省了多少钱',
          '建立"校园省钱群"日常分享优惠',
          '与品牌方谈 CPS 抽佣+品牌推广',
        ],
        searchKws: ['女生宿舍必买', '男生宿舍好物', '生活费1500怎么花', '开学必备清单'],
        searchOpt: [
          '布局季节词（开学/夏天/冬天/期末）',
          '抢占新品发布窗口期',
          '每月更新"当季好物推荐"长文',
          '与抖音/小红书同步分发',
        ],
        privateFunnel: [
          '公众号关注 → 校园省钱群',
          '群内每日分享优惠信息',
          '群活跃 → 商家优惠券+CPS 转化',
          '高粘性 → 品牌合作内容共创',
        ],
        privateTips: [
          '群每周三 19:00 分享"本周好物 TOP3"',
          '群规明确，杜绝过度营销',
          '建立"宿舍生活实验室"线下活动',
          '与高校官方店铺谈合作',
        ],
      }),
    },
  },
  {
    id: 'student-ai-startup',
    title: 'AI时代大学生自媒体创业',
    prompt: 'AI时代大学生自媒体创业方向分析',
    emoji: '🚀',
    result: {
      role: 'assistant',
      content: `### 赛道机会评分：8.9/10

AI时代，大学生自媒体创业迎来历史性窗口期：内容生产成本降低80%+、一人公司成为可能、微信生态提供从内容到商业化的完整闭环。2025年微信视频号创作者中，25岁以下占比提升至28%（同比+12pp），公众号新注册个人号中大学生比例达35%。核心判断：AI不是替代创作者，而是让"有想法但缺执行力"的大学生具备了与专业团队竞争的能力。

### 内容策略

**六大创业方向评估：**

| 方向 | 市场规模 | 启动难度 | AI提效倍数 | 变现周期 | 推荐指数 |
|------|---------|---------|-----------|---------|---------|
| AI工具评测KOC | ★★★★ | ★★☆ | 3x | 1-2月 | ⭐⭐⭐⭐⭐ |
| 校园垂类媒体 | ★★★★★ | ★★★ | 4x | 2-3月 | ⭐⭐⭐⭐⭐ |
| 知识付费/课程 | ★★★★ | ★★★★ | 5x | 3-6月 | ⭐⭐⭐⭐ |
| AI辅助设计服务 | ★★★ | ★★☆ | 8x | 1月 | ⭐⭐⭐⭐ |
| 垂直社群运营 | ★★★★ | ★★★ | 2x | 2-4月 | ⭐⭐⭐⭐ |
| MCN/内容代运营 | ★★★★★ | ★★★★★ | 6x | 4-6月 | ⭐⭐⭐ |

**方向一：AI工具评测KOC（推荐首选）**
- 优势：零成本启动、内容迭代快、技术门槛低
- AI应用：AI生成测评框架+AI剪辑视频+AI做对比图表
- 变现：品牌合作、工具推广佣金、付费社群

**方向二：校园垂类媒体（高壁垒推荐）**
- 优势：本地流量垄断、商业化路径明确
- AI应用：AI批量生成本地内容+AI管理多账号+AI数据分析
- 变现：校园商家广告、活动策划、品牌校园推广

**方向三：AI知识付费（高天花板）**
- 优势：边际成本趋零、可规模化
- AI应用：AI辅助课程制作+AI生成讲义+AI批改作业
- 变现：课程销售、1v1咨询、训练营

**标题建议：**
1. 大学生用AI创业月入过万，这3个方向最靠谱 (预估CTR: 15%)
2. AI时代最适合大学生的5个自媒体创业方向（附启动成本分析） (预估CTR: 13%)
3. 我大三休学做AI自媒体，半年营收20万的真实经历 (预估CTR: 14%)
4. 2026年大学生创业不需要启动资金了——AI改变了什么？ (预估CTR: 12%)
5. 别去实习了！AI时代大学生自媒体创业完全指南 (预估CTR: 11%)

**开场Hook：**
1. "两年前做自媒体需要一个团队，现在只需要你+AI。我用亲身经历告诉你，大学生AI创业的时代真的来了" (+42%留存)
2. "如果你是大学生，还没有开始你的AI自媒体项目，你正在错过这个时代最大的红利" (+38%留存)

### 微信生态策略

**视频号（个人IP打造）：** 定位："大学生AI创业者"人设，记录创业过程 | 内容：创业日记+方法论分享+数据复盘 | 频率：每周3条 | AI应用：AI生成视频脚本+AI剪辑+AI数据分析 | 目标：建立个人品牌，吸引同类创业者

**搜一搜（精准获客）：** 核心词：大学生创业、AI创业、自媒体创业 | 长尾词：大学生怎么做自媒体、AI时代赚钱方法、大学生副业推荐 | 策略：公众号输出"AI创业指南"系列长文，抢占搜一搜排名

**公众号（知识沉淀+商业化）：** 输出"AI自媒体创业手册"系列（10篇以上）| 建立"AI创业者"社群，收费/免费分层 | 推出AI自媒体工具包（付费产品）| 接收品牌合作和咨询

**三位一体商业模式：**

视频号（获客）→ 公众号（沉淀）→ 社群（变现）← 搜一搜（长尾流量补充）

### 30天行动路径

**D1-D7（方向确定+MVP验证）：** 选定1个创业方向（建议从AI工具评测切入）；搭建AI工作流；发布7条内容验证市场反应。目标：明确方向+验证需求+粉丝200。

**D8-D14（内容体系搭建）：** 确定固定栏目（如"每日AI创业日记""每周AI工具推荐"）；公众号发布3篇深度文章；开始运营个人朋友圈。目标：稳定更新节奏+粉丝600。

**D15-D21（流量突破+社群启动）：** 蹭AI行业热点（新产品发布等）；建立微信社群（先免费，50人种子群）；视频号做1次直播分享。目标：1条爆款内容+社群50人+粉丝1500。

**D22-D30（商业化测试）：** 推出首个付费产品（AI工具包/小课程/付费社群）；测试广告变现（接第一个AI工具推广）；复盘首月数据，制定第二月计划。目标：首笔创业收入+粉丝3000+，验证商业模式。

### 数据来源

本次分析基于 MiniMax联网搜索、Serper(Google)、Tavily、DuckDuckGo、DailyHot热搜聚合 共5个引擎的实时数据，覆盖大学生创业趋势、AI自媒体案例、微信生态创作者数据及自媒体商业化路径分析。`,
      thinking: [
        { step: '搜索中', detail: '正在搜索AI时代大学生创业案例与行业数据...', progress: 10, agents: [{ name: 'MiniMax搜索', status: 'running' }, { name: 'Serper搜索', status: 'running' }, { name: 'Tavily搜索', status: 'running' }] },
        { step: '搜索完成', detail: '找到 86 条数据，来自 5 个引擎，含创业案例、行业报告及微信生态数据', progress: 35, agents: [{ name: 'MiniMax搜索', status: 'done', count: 21 }, { name: 'Serper搜索', status: 'done', count: 23 }, { name: 'Tavily搜索', status: 'done', count: 19 }] },
        { step: '构建知识图谱', detail: '正在分析创业方向、商业模式及微信生态闭环...', progress: 52 },
        { step: '生成报告', detail: 'AI 正在生成自媒体创业方向分析报告...', progress: 66 },
      ],
      searchStats: { total_raw: 86, total_deduped: 86, engines: { minimax: 21, serper: 23, tavily: 19, ddgs: 13, dailyhot: 10 } },
      graph: {
        nodes: [
          { id: 'center', name: 'AI自媒体创业', type: 'topic', val: 40, color: '#6366f1' },
          { id: 'shipinhao', name: '视频号', type: 'platform', val: 28, color: '#07c160' },
          { id: 'gongzhonghao', name: '公众号', type: 'platform', val: 26, color: '#07c160' },
          { id: 'souyisou', name: '搜一搜', type: 'platform', val: 20, color: '#07c160' },
          { id: 'ai-tool-koc', name: 'AI工具评测', type: 'direction', val: 25, color: '#8b5cf6' },
          { id: 'campus-media', name: '校园垂类媒体', type: 'direction', val: 22, color: '#8b5cf6' },
          { id: 'knowledge-pay', name: '知识付费', type: 'direction', val: 20, color: '#8b5cf6' },
          { id: 'ai-design', name: 'AI设计服务', type: 'direction', val: 18, color: '#8b5cf6' },
          { id: 'student', name: '大学生创业者', type: 'audience', val: 30, color: '#f59e0b' },
          { id: 'ai-efficiency', name: 'AI降本提效', type: 'advantage', val: 22, color: '#10b981' },
          { id: 'one-person', name: '一人公司', type: 'model', val: 20, color: '#ef4444' },
          { id: 'community', name: '付费社群', type: 'monetize', val: 18, color: '#f472b6' },
          { id: 'brand-collab', name: '品牌合作', type: 'monetize', val: 16, color: '#f472b6' },
          { id: 'course', name: '课程产品', type: 'monetize', val: 15, color: '#f472b6' },
          { id: 'wechat-loop', name: '微信生态闭环', type: 'strategy', val: 24, color: '#07c160' },
        ],
        links: [
          { source: 'center', target: 'shipinhao', label: '获客渠道', strength: 0.9 },
          { source: 'center', target: 'gongzhonghao', label: '内容沉淀', strength: 0.9 },
          { source: 'center', target: 'souyisou', label: '搜索流量', strength: 0.7 },
          { source: 'center', target: 'student', label: '创业主体', strength: 1 },
          { source: 'center', target: 'ai-tool-koc', label: '推荐方向', strength: 0.9 },
          { source: 'center', target: 'campus-media', label: '高壁垒方向', strength: 0.8 },
          { source: 'center', target: 'knowledge-pay', label: '高天花板', strength: 0.7 },
          { source: 'center', target: 'ai-design', label: '技能变现', strength: 0.6 },
          { source: 'center', target: 'ai-efficiency', label: '核心优势', strength: 1 },
          { source: 'ai-efficiency', target: 'one-person', label: '使能', strength: 0.9 },
          { source: 'center', target: 'community', label: '变现路径', strength: 0.7 },
          { source: 'center', target: 'brand-collab', label: '变现路径', strength: 0.6 },
          { source: 'center', target: 'course', label: '变现路径', strength: 0.6 },
          { source: 'shipinhao', target: 'wechat-loop', label: '闭环组件', strength: 0.8 },
        ],
      },
      sources: [
        { title: '2025年中国大学生创业趋势报告', url: 'https://research.tencent.com/student-startup-2025' },
        { title: '微信生态创作者年度白皮书', url: 'https://mp.weixin.qq.com/s/creator-whitepaper-2025' },
        { title: 'AI自媒体商业化案例研究（N=50）', url: 'https://example.com/ai-media-business-cases' },
      ],
      tokenUsage: { search_tokens: 0, llm_tokens: 0, total_tokens: 0, search_calls: 86, agent_rounds: 2, elapsed_ms: 34800 },
      agentMessages: buildAgentMessages([
        { agent: 'data', round: 1, content: 'AI 时代大学生创业窗口期：内容生产成本降 80%，一人公司成为可能。微信视频号 25 岁以下创作者占比同比+12pp，机会窗口巨大。' },
        { agent: 'content', round: 1, content: '6 个方向中，"AI 工具评测 KOC"是首选（启动难度低 + 提效 3x + 1-2 月变现）；"校园垂类媒体"是高壁垒选项（壁垒+商业化清晰）。' },
        { agent: 'psych', round: 1, content: '大学生创业心理 = 时代红利+焦虑+尝试欲。"AI 时代不创业你就落伍了"这种煽动性内容易刷屏但信任度低，建议主打"真实记录"派。' },
        { agent: 'platform', round: 1, content: '微信生态三件套（视频号+公众号+搜一搜）+社群，是大学生创业最低成本闭环。每日精力总投入可控制在 4 小时内。' },
        { agent: 'risk', round: 1, content: '风险：休学创业风险高。建议"低风险副业型"——保持学业+利用碎片时间运营，用 AI 提效降低时间成本。' },
        { agent: 'research', round: 1, content: '案例研究：50 个大学生 AI 自媒体样本，平均 3 个月达 5000 粉，6 个月开始月入 1-3 万，1 年内 30% 实现月入 5 万+。' },
        { agent: 'advocate', round: 1, content: '我作为大学生会先尝试"AI 工具评测"这种轻量方向，验证可行性后再扩展。创业不要一上来就 all in。' },
        { agent: 'data', round: 2, content: '建议先做 30 天的"AI 工具评测"，验证商业模式，再决定是否扩展校园媒体。MVP 思维。' },
        { agent: 'content', round: 2, content: '内容矩阵：视频号（个人 IP）+公众号（深度沉淀）+社群（变现）+搜一搜（长尾流量）。三位一体，互相导流。' },
        { agent: 'platform', round: 2, content: '搜一搜核心词：大学生创业、AI 创业、自媒体创业、大学生副业。每月 4-8 篇 SEO 长文，30 天可出词 15+。' },
      ]),
      scoreData: arbiterScore({
        total: 89,
        verdict: '强烈推荐',
        summary: 'AI 时代大学生自媒体创业是历史性机会窗口：内容成本极低+商业化路径清晰+微信生态闭环。但需轻启动、验证后扩展，避免休学风险。专家共识度 89%。',
        risks: ['创业不可冲动需验证 MVP', '内容生产持续性挑战', '商业化转化率需测试'],
        actions: [
          'D1-7：选定 1 个方向（建议 AI 工具评测），搭建工作流',
          'D8-14：固定栏目+稳定更新节奏',
          'D15-21：流量突破+社群启动',
          'D22-30：商业化测试（首个付费产品+广告变现）',
        ],
        dimensions: [{ name: '时代机会', score: 95 }, { name: '可行性', score: 85 }, { name: '商业化', score: 90 }, { name: '风险可控', score: 78 }],
        hkrr: [{ name: '钩子', score: 87 }, { name: '认知', score: 90 }, { name: '关系', score: 85 }, { name: '行动', score: 92 }],
      }),
      arbiterThinking: '本选题方向具有强时代背景红利，KOC 大学生身份+AI 工具加持下，月入过万门槛大幅降低。建议轻启动验证 MVP，避免一开始休学等高风险动作。',
      viralScore: viralScore({
        total: 86,
        pool: '热门流量池',
        poolProb: '82% 概率突破热门池',
        analysis: '大学生 AI 创业内容在视频号+公众号双平台 CES 表现优秀：分享率高（同龄人焦虑共鸣）、收藏率高（记笔记），评论互动质量高（求问求建议）。预期单条 CES 1200+，进热门池。',
        dimensions: [
          { id: 'title_appeal', name: '标题吸引力', score: 13, max: 15, reason: '"月入过万""大学生创业""3 个方向最靠谱"具备多重钩子。' },
          { id: 'emotion', name: '情绪共鸣', score: 13, max: 15, reason: '焦虑+希望双重情绪命中大学生痛点。' },
          { id: 'platform_fit', name: '平台适配', score: 13, max: 15, reason: '视频号+公众号双轨，搜一搜长尾辅助。' },
          { id: 'blue_ocean', name: '竞争蓝海', score: 7, max: 10, reason: '大学生创业内容偏多，但"AI+具体方向"仍蓝海。' },
          { id: 'timeliness', name: '时效窗口', score: 9, max: 10, reason: 'AI 时代红利+毕业季求职焦虑双高峰。' },
          { id: 'hook_strength', name: 'Hook 强度', score: 9, max: 10, reason: '"两年前需要团队，现在只需要你+AI"对比强烈。' },
          { id: 'info_density', name: '信息密度', score: 9, max: 10, reason: '6 个方向+市场规模+难度+变现信息完整。' },
          { id: 'originality', name: '原创空间', score: 8, max: 10, reason: '需个人创业故事+真实数据增强可信度。' },
          { id: 'completion_predict', name: '完播预测', score: 5, max: 5, reason: '清单类内容完播率高（用户想看完所有项）。' },
        ],
        strengths: ['时代红利窗口期', 'AI 提效门槛低', '商业模式清晰'],
        weaknesses: ['同质化创业内容多', '需个人案例支撑', '信任建立需时间'],
        tips: ['绑定"大学生 AI 创业者"个人 IP', '记录创业过程（数据透明）', '建立"AI 创业方法论"系列', '定期分享真实数据复盘'],
      }),
      wechatStrategy: wechatStrategy({
        videoTips: [
          '每周 3 条创业日记/方法论',
          'AI 生成视频脚本+AI 剪辑',
          '#大学生创业 #AI创业 #自媒体',
          '建立个人品牌人设',
          '记录数据复盘培养信任',
        ],
        videoAlgorithm: '创业类内容靠"完播率+评论质量"双指标。建议每条视频提出"行动问题"引导评论："你最想尝试哪个方向？"评论质量提升 3x。',
        videoBest: [
          '"AI 创业日记"每周 3 条',
          '直播"AI 工具实操"展示真实使用',
          '每月做一次"复盘"长视频',
          '与其他校园创业者互推',
        ],
        officialKws: ['大学生创业', 'AI创业', '自媒体创业', '大学生副业', 'AI 时代赚钱'],
        officialFmt: '"AI 自媒体创业手册"系列长文（10+ 篇连载），结构：方向分析 → 启动成本 → 实操步骤 → 案例 → 风险提示',
        officialTips: [
          '建立"AI 创业者"分层社群',
          '推出 AI 自媒体工具包（付费产品）',
          '接收品牌合作和咨询',
          '与孵化器、创业大赛联动',
        ],
        searchKws: ['大学生 怎么做自媒体', 'AI 时代 赚钱', '大学生 副业 推荐'],
        searchOpt: [
          '抢占"AI 创业 大学生"长尾词',
          '每月更新"创业方向年度报告"长文',
          '深度长文 SEO 占据搜索结果前 3',
          '与抖音/小红书同步分发',
        ],
        privateFunnel: [
          '视频号关注 → 公众号"创业资料包"',
          '公众号关注 → 免费创业者社群（50 人种子）',
          '群活跃 → 付费小课程/咨询',
          '高活跃 → 内容共创/合伙',
        ],
        privateTips: [
          '社群按"创业阶段"分级（萌芽期/启动期/起量期）',
          '每月公开数据复盘培养信任',
          '提供"AI 工具包+模板"作为付费产品',
          '定期组织线下"创业者饭局"',
        ],
      }),
    },
  },
]
