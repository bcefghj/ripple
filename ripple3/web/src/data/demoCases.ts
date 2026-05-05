import type { ChatMessage } from '../lib/api'

export interface DemoCase {
  id: string
  title: string
  subtitle: string
  prompt: string
  emoji: string
  tags: string[]
  result: ChatMessage
}

export const DEMO_CASES: DemoCase[] = [
  {
    id: 'ai-tool-review',
    title: 'AI 工具测评账号冷启动',
    subtitle: '从 0 到 1000 粉丝的完整路径规划',
    prompt: '我想做一个 AI 工具测评的小红书账号，帮我分析从 0 开始如何冷启动到 1000 粉丝',
    emoji: '🚀',
    tags: ['冷启动', '科技赛道', '小红书'],
    result: {
      role: 'assistant',
      content: `## 🚀 AI 工具测评账号冷启动策略

### 核心定位
**赛道机会评分：8.7/10** — AI工具测评是2024-2025年增长最快的内容赛道之一，小红书月搜索量增长340%。

### 差异化策略
1. **场景化测评** > 功能罗列：用"一个真实需求"串联工具对比
2. **结果导向** > 过程展示：先展示效果差异，再讲操作步骤
3. **人格化表达**："AI工具体验官"而非"科技博主"

### 30天冷启动路径

| 阶段 | 时间 | 目标 | 策略 |
|------|------|------|------|
| 种子期 | D1-D7 | 10篇笔记 + 50粉 | 日更，覆盖热门工具 |
| 起量期 | D8-D14 | 2篇爆文 + 200粉 | 蹭热点 + 对比测评 |
| 加速期 | D15-D21 | 稳定互动 + 500粉 | 系列化内容 + 评论引导 |
| 突破期 | D22-D30 | 品牌合作 + 1000粉 | 精品长文 + 社群运营 |

### 爆款内容公式
\`[悬念Hook] + [工具对比结果] + [具体场景] + [行动指令]\`

例："用了3个月AI写作工具，终于找到了替代ChatGPT的神器😱 效果对比太明显了..."`,
      thinking: [
        { id: 'intent', type: 'intent', label: '意图识别', status: 'done', detail: '冷启动策略 × AI赛道 × 小红书' },
        { id: 'search-1', type: 'search', label: '搜索小红书AI测评数据', status: 'done', detail: '找到342条相关爆文' },
        { id: 'search-2', type: 'search', label: '分析竞品账号', status: 'done', detail: '对标5个头部账号' },
        { id: 'search-3', type: 'search', label: '热度趋势分析', status: 'done', detail: 'AI工具搜索量↑340%' },
        { id: 'analyze', type: 'analyze', label: '内容生态分析', status: 'done', detail: '蓝海机会: 场景化对比' },
        { id: 'agent-1', type: 'agent', label: '多专家讨论', status: 'done', detail: '7位专家达成共识' },
        { id: 'synthesize', type: 'synthesize', label: '策略综合', status: 'done', detail: '生成30天路径' },
        { id: 'output', type: 'output', label: '输出方案', status: 'done', detail: '含标题测试+Hook库' },
      ] as any,
      graph: {
        nodes: [
          { id: 'center', name: 'AI工具测评', type: 'topic', val: 40, color: '#6366f1' },
          { id: 'xhs', name: '小红书', type: 'platform', val: 30, color: '#ff2442' },
          { id: 'chatgpt', name: 'ChatGPT', type: 'brand', val: 25, color: '#10a37f' },
          { id: 'midjourney', name: 'Midjourney', type: 'brand', val: 20, color: '#5865f2' },
          { id: 'kimi', name: 'Kimi', type: 'brand', val: 22, color: '#4f46e5' },
          { id: 'writing', name: 'AI写作', type: 'keyword', val: 18, color: '#06b6d4' },
          { id: 'image', name: 'AI绘画', type: 'keyword', val: 16, color: '#06b6d4' },
          { id: 'video', name: 'AI视频', type: 'keyword', val: 14, color: '#06b6d4' },
          { id: 'student', name: '大学生', type: 'audience', val: 20, color: '#f59e0b' },
          { id: 'worker', name: '打工人', type: 'audience', val: 18, color: '#f59e0b' },
          { id: 'review', name: '横向对比', type: 'format', val: 15, color: '#ec4899' },
          { id: 'tutorial', name: '教程攻略', type: 'format', val: 14, color: '#ec4899' },
          { id: 'trend-1', name: 'Sora发布', type: 'trend', val: 25, color: '#ef4444' },
          { id: 'trend-2', name: 'Claude升级', type: 'trend', val: 18, color: '#ef4444' },
          { id: 'cold-start', name: '冷启动', type: 'strategy', val: 22, color: '#8b5cf6' },
          { id: 'hook', name: '开场Hook', type: 'strategy', val: 15, color: '#8b5cf6' },
          { id: 'seo', name: 'SEO关键词', type: 'strategy', val: 16, color: '#8b5cf6' },
          { id: 'comp-1', name: '@AI实验室', type: 'competitor', val: 12, color: '#f59e0b' },
          { id: 'comp-2', name: '@科技测评君', type: 'competitor', val: 11, color: '#f59e0b' },
          { id: 'channel-xhs', name: '小红书笔记', type: 'channel', val: 20, color: '#8b5cf6' },
        ],
        links: [
          { source: 'center', target: 'xhs', label: '主阵地' },
          { source: 'center', target: 'chatgpt', label: '核心工具' },
          { source: 'center', target: 'midjourney', label: '热门工具' },
          { source: 'center', target: 'kimi', label: '国产替代' },
          { source: 'center', target: 'writing', label: '子赛道' },
          { source: 'center', target: 'image', label: '子赛道' },
          { source: 'center', target: 'video', label: '子赛道' },
          { source: 'xhs', target: 'student', label: '核心用户' },
          { source: 'xhs', target: 'worker', label: '核心用户' },
          { source: 'writing', target: 'review', label: '最佳格式' },
          { source: 'center', target: 'trend-1', label: '蹭热点' },
          { source: 'center', target: 'trend-2', label: '蹭热点' },
          { source: 'cold-start', target: 'hook', label: '关键技巧' },
          { source: 'cold-start', target: 'seo', label: '获客路径' },
          { source: 'xhs', target: 'comp-1', label: '竞品' },
          { source: 'xhs', target: 'comp-2', label: '竞品' },
          { source: 'center', target: 'channel-xhs', label: '分发渠道' },
        ],
      },
      agentMessages: [
        { agent: { id: 'data', name: '数据分析师', role: '数据驱动决策', emoji: '📊', color: '#3b82f6' }, content: '小红书AI工具相关笔记月增长42%，但优质对比类内容占比不足15%，这是明确的蓝海机会。建议以"场景化对比"作为差异点切入。' },
        { agent: { id: 'content', name: '内容策划师', role: '爆款内容生产', emoji: '✍️', color: '#8b5cf6' }, content: '推荐"1个需求+3个工具"的对比框架，前3行必须用悬念Hook。标题公式："我用了X个月的XX工具，终于发现了..."' },
        { agent: { id: 'psych', name: '用户心理学家', role: '用户行为洞察', emoji: '🧠', color: '#ec4899' }, content: '目标用户的核心痛点是"选择焦虑"——工具太多不知道哪个好。解法是"帮用户做减法"，直接告诉结论。' },
        { agent: { id: 'growth', name: '增长黑客', role: '用户增长策略', emoji: '🚀', color: '#10b981' }, content: '冷启动期每天固定时间发布（建议20:00-21:00），评论区主动互动前20条评论，可在7天内激活推荐算法。' },
        { agent: { id: 'platform', name: '平台算法专家', role: '平台规则解读', emoji: '⚡', color: '#f59e0b' }, content: '小红书CES评分 = 点赞(1) + 收藏(1) + 评论(4) + 转发(4)。对比类内容天然引导评论("你用的哪个？")，CES收益最高。' },
      ],
      arbiterThinking: '综合7位专家意见，一致认为AI工具测评赛道在小红书仍处蓝海期。核心策略共识：以场景化对比（非功能罗列）作为差异化定位，利用CES评分机制设计互动引导，配合热点事件（如新工具发布）制造爆发点。预估30天达成1000粉目标的成功概率为72%。',
      scoreData: {
        total_score: 87,
        dimensions: [
          { name: '选题热度', score: 92, max: 100 },
          { name: '竞争程度', score: 78, max: 100 },
          { name: '变现潜力', score: 85, max: 100 },
          { name: '内容门槛', score: 90, max: 100 },
          { name: '增长空间', score: 88, max: 100 },
        ],
      },
      searchStats: {
        totalResults: 1847,
        engines: [
          { name: 'MiniMax', count: 320, status: 'done' },
          { name: '腾讯联网搜索', count: 285, status: 'done' },
          { name: 'Serper', count: 198, status: 'done' },
          { name: 'Tavily', count: 245, status: 'done' },
          { name: 'Exa AI', count: 167, status: 'done' },
          { name: 'DailyHot', count: 120, status: 'done' },
          { name: 'MCP趋势聚合', count: 312, status: 'done' },
          { name: 'Jina AI', count: 200, status: 'done' },
        ],
      },
      titleAbTest: {
        titles: [
          { text: '用了3个月AI工具，终于找到了最值得付费的3个', predicted_ctr: 0.12, strategy: '数字+悬念' },
          { text: '被AI工具骗了半年，这些坑千万别踩😱', predicted_ctr: 0.11, strategy: '恐惧+好奇' },
          { text: 'ChatGPT vs Kimi vs Claude，打工人到底该用哪个？', predicted_ctr: 0.10, strategy: '对比+身份' },
          { text: '0基础用AI月入5000？我实测了30天告诉你真相', predicted_ctr: 0.09, strategy: '利益+反转' },
          { text: '大学生必装的5个AI神器，论文效率翻3倍', predicted_ctr: 0.09, strategy: '身份+利益+数字' },
        ],
        best_pick: 0,
        analysis: '悬念+数字组合在AI赛道CTR最高，因为用户对"经验总结"类内容信任度高于纯推荐。'
      },
      hooks: {
        hooks: [
          { text: '我花了3个月时间，测试了市面上所有AI工具，今天把结论直接告诉你...', type: '反直觉声明', estimated_retention_boost: '+42%' },
          { text: '如果你还在纠结该用ChatGPT还是Kimi，看完这个对比你就不纠结了', type: '共鸣痛点', estimated_retention_boost: '+35%' },
          { text: '90%的人都在错误地使用AI工具，我来告诉你正确的打开方式', type: '数据冲击', estimated_retention_boost: '+30%' },
        ],
        strategy_note: '场景化对比类内容推荐使用"结果前置"的Hook模式：先展示惊人结论，再引导用户看完整对比。',
        avoid: ['不要用"今天给大家介绍..."开场', '避免直接罗列功能清单']
      },
    },
  },
  {
    id: 'exam-vlog',
    title: '考研人的一天 Vlog',
    subtitle: '情感共鸣 + 热点捕捉 = 爆款',
    prompt: '帮我分析"考研人的一天"这个选题在小红书和视频号的爆款潜力，给出完整内容方案',
    emoji: '🎓',
    tags: ['学生', '情感共鸣', '多平台'],
    result: {
      role: 'assistant',
      content: `## 🎓 "考研人的一天" 爆款潜力分析

### 选题评估
**综合评分：9.1/10** — 该选题满足爆款三要素：强共鸣 × 大基数 × 时效性。

### 数据洞察
- 2025年考研报名人数：**438万**（巨大的潜在受众）
- 小红书"考研"相关笔记月搜索量：**2.3亿次**
- "考研人的一天"类内容平均互动率：**12.4%**（远超平台均值4.2%）

### 内容方案

#### 小红书策略
- **格式**：图文日记体 + 时间线排版
- **关键帧**：6:00起床 → 图书馆占座 → 崩溃瞬间 → 深夜回寝
- **情绪锚点**：一定要有一个"差点放弃"的真实瞬间
- **CES优化**：结尾提问"你今天学了几个小时？"引导评论

#### 视频号策略
- **时长**：45-90秒竖版
- **发布时间**：22:00-23:00（考研人刷手机时间）
- **算法卡点**：前3秒必须出核心画面（书桌/图书馆/深夜台灯）
- **完播率设计**：倒计时结构"距考试还有XX天"创造紧迫感`,
      thinking: [
        { id: 'intent', type: 'intent', label: '意图识别', status: 'done', detail: '爆款潜力分析 × 考研选题' },
        { id: 'search-1', type: 'search', label: '搜索考研相关数据', status: 'done', detail: '438万考研人群' },
        { id: 'search-2', type: 'search', label: '小红书爆文分析', status: 'done', detail: '互动率12.4%' },
        { id: 'search-3', type: 'search', label: '视频号数据', status: 'done', detail: '完播率最优时长分析' },
        { id: 'analyze', type: 'analyze', label: '爆款要素拆解', status: 'done', detail: '共鸣×基数×时效' },
        { id: 'agent', type: 'agent', label: '专家圆桌讨论', status: 'done', detail: '全员高分评价' },
        { id: 'output', type: 'output', label: '输出完整方案', status: 'done', detail: '双平台策略' },
      ] as any,
      scoreData: {
        total_score: 91,
        dimensions: [
          { name: '选题热度', score: 95, max: 100 },
          { name: '情感共鸣', score: 96, max: 100 },
          { name: '竞争程度', score: 82, max: 100 },
          { name: '变现潜力', score: 88, max: 100 },
          { name: '时效性', score: 93, max: 100 },
        ],
      },
    },
  },
  {
    id: 'efficiency-tools',
    title: '打工人效率神器',
    subtitle: '职场赛道 × 多平台分发',
    prompt: '帮我策划"打工人必备的10个效率神器"系列内容，分析竞品和差异化策略',
    emoji: '💼',
    tags: ['职场', '工具推荐', '系列化'],
    result: {
      role: 'assistant',
      content: `## 💼 打工人效率神器 · 系列化内容策略

### 策略定位
**内容类型**：实用工具推荐 × 职场痛点解决
**目标人群**：25-35岁互联网/职场新人
**差异化**：不做简单罗列，做"问题→工具→效果"的解决方案型内容

### 系列规划（10期）

| 期数 | 主题 | 核心工具 | 痛点场景 |
|------|------|---------|---------|
| 1 | 会议效率 | 飞书妙记/讯飞 | 开会1小时，纪要写2小时 |
| 2 | 时间管理 | 滴答清单/Notion | 每天忙到死但产出低 |
| 3 | 文件整理 | Eagle/Everything | 找文件比做文件还久 |
| 4 | AI写作 | Kimi/ChatGPT | 周报月报写到崩溃 |
| 5 | 设计协作 | Figma/即时设计 | 甲方改稿100遍 |

### 多平台分发策略

- **小红书**（主阵地）：图文 + 工具截图 + 对比效果
- **视频号**（引流）：30s快节奏"一个工具解决一个问题"
- **公众号**（沉淀）：深度长文"完整效率体系搭建指南"`,
      thinking: [
        { id: 'intent', type: 'intent', label: '意图识别', status: 'done', detail: '系列内容策划 × 职场工具' },
        { id: 'search', type: 'search', label: '全网效率工具搜索', status: 'done', detail: '1200+相关内容' },
        { id: 'analyze', type: 'analyze', label: '竞品分析', status: 'done', detail: '识别差异化机会' },
        { id: 'agent', type: 'agent', label: '专家评审', status: 'done', detail: '一致推荐系列化' },
        { id: 'output', type: 'output', label: '输出方案', status: 'done', detail: '10期规划+分发策略' },
      ] as any,
      scoreData: {
        total_score: 84,
        dimensions: [
          { name: '选题热度', score: 88, max: 100 },
          { name: '竞争程度', score: 72, max: 100 },
          { name: '变现潜力', score: 92, max: 100 },
          { name: '系列化潜力', score: 90, max: 100 },
          { name: '多平台适配', score: 85, max: 100 },
        ],
      },
    },
  },
  {
    id: 'dorm-products',
    title: '大学生宿舍好物',
    subtitle: '校园场景 × 种草经济',
    prompt: '我想做一个宿舍好物分享的账号，帮我分析这个赛道的机会和具体内容策略',
    emoji: '🏠',
    tags: ['校园', '种草', '开箱'],
    result: {
      role: 'assistant',
      content: `## 🏠 宿舍好物分享 · 赛道分析

### 赛道评估
**蓝海指数：7.2/10** — 赛道成熟但细分机会仍在，关键是找到差异化角度。

### 差异化策略建议
1. **"翻车种草"**：先买先试，展示真实使用一周后的状态（去滤镜）
2. **"预算限制"**：100元/50元以内的宿舍改造
3. **"男生宿舍"**：90%的宿舍好物账号面向女生，男生市场空白

### 变现路径
第一阶段（0-3000粉）：好物推荐 → 小红书蒲公英接单
第二阶段（3000+粉）：品牌合作 + 橱窗带货
预估单条广告收入：500-2000元（3000粉级别）`,
      thinking: [
        { id: 'intent', type: 'intent', label: '意图识别', status: 'done', detail: '赛道分析 × 宿舍好物' },
        { id: 'search', type: 'search', label: '搜索分析', status: 'done', detail: '识别细分机会' },
        { id: 'agent', type: 'agent', label: '专家讨论', status: 'done', detail: '推荐差异化定位' },
        { id: 'output', type: 'output', label: '输出方案', status: 'done', detail: '含变现路径' },
      ] as any,
      scoreData: {
        total_score: 82,
        dimensions: [
          { name: '选题热度', score: 85, max: 100 },
          { name: '竞争程度', score: 68, max: 100 },
          { name: '变现潜力', score: 90, max: 100 },
          { name: '内容门槛', score: 92, max: 100 },
          { name: '增长空间', score: 78, max: 100 },
        ],
      },
    },
  },
  {
    id: 'graduation-outfit',
    title: '毕业季穿搭分享',
    subtitle: '季节性话题 × 时机把握',
    prompt: '帮我分析"毕业季穿搭"这个选题在5-6月的爆款潜力，给出拍摄和发布时间建议',
    emoji: '👗',
    tags: ['时尚', '季节性', '毕业季'],
    result: {
      role: 'assistant',
      content: `## 👗 毕业季穿搭 · 时效性爆款策略

### 时机分析
**最佳发布窗口**：4月中旬-6月初（毕业照拍摄高峰前2-4周）
**流量峰值**：5月15日-6月10日

### 内容矩阵
1. **毕业照穿搭合集**（引流款）：5套look覆盖不同风格
2. **200元搞定毕业照全套穿搭**（互动款）：低预算方案引评论
3. **毕业典礼穿什么不出错**（信任款）：通用建议建立专业度
4. **拍毕业照这些坑千万别踩**（传播款）：避雷内容易被收藏转发

### 视频号策略
- 发布时间：周三/周日 19:00-20:00
- 利用搜一搜布局"毕业照穿搭""学士服搭配"等长尾词
- 24小时内回复所有评论，触发Peoplerank加权`,
      thinking: [
        { id: 'intent', type: 'intent', label: '意图识别', status: 'done', detail: '季节性选题 × 时尚赛道' },
        { id: 'search', type: 'search', label: '趋势分析', status: 'done', detail: '5-6月流量峰值确认' },
        { id: 'analyze', type: 'analyze', label: '竞品拆解', status: 'done', detail: '头部账号策略分析' },
        { id: 'output', type: 'output', label: '输出方案', status: 'done', detail: '含精准时间规划' },
      ] as any,
      scoreData: {
        total_score: 88,
        dimensions: [
          { name: '时效性', score: 95, max: 100 },
          { name: '选题热度', score: 90, max: 100 },
          { name: '竞争程度', score: 75, max: 100 },
          { name: '变现潜力', score: 88, max: 100 },
          { name: '视觉吸引力', score: 92, max: 100 },
        ],
      },
    },
  },
]
