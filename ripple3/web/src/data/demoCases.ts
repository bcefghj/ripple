import type { ChatMessage } from '../lib/api'

export interface DemoCase {
  id: string
  title: string
  prompt: string
  emoji: string
  result: ChatMessage
}

export const DEMO_CASES: DemoCase[] = [
  {
    id: 'ai-tool-review',
    title: 'AI 工具测评账号冷启动',
    prompt: '我想做一个 AI 工具测评的小红书账号，帮我分析从 0 开始如何冷启动到 1000 粉丝',
    emoji: '🚀',
    result: {
      role: 'assistant',
      content: `### 赛道机会评分：8.7/10

AI工具测评是2024-2025年增长最快的内容赛道之一，小红书月搜索量增长340%。竞争尚未饱和，优质对比类内容占比不足15%。

### 内容策略

**差异化定位：**
1. "场景化对比测评" — 用一个真实需求串联工具对比（非功能罗列）
2. "结果导向" — 先展示效果差异，再讲操作步骤
3. "AI工具体验官" 人设 — 亲和力 > 专业感

**标题建议：**
1. 用了3个月AI工具，终于找到了最值得付费的3个 (预估CTR: 12%)
2. 被AI工具骗了半年，这些坑千万别踩 (预估CTR: 11%)
3. ChatGPT vs Kimi vs Claude，打工人到底该用哪个？(预估CTR: 10%)
4. 0基础用AI月入5000？我实测了30天告诉你真相 (预估CTR: 9%)
5. 大学生必装的5个AI神器，论文效率翻3倍 (预估CTR: 9%)

**开场Hook：**
1. "我花了3个月时间，测试了市面上所有AI工具，今天把结论直接告诉你..." (+42%留存)
2. "如果你还在纠结该用ChatGPT还是Kimi，看完这个对比你就不纠结了" (+35%留存)
3. "90%的人都在错误地使用AI工具，我来告诉你正确的打开方式" (+30%留存)

### 微信生态策略

**视频号：** 发布时间：周二/四/六 20:00-21:00 | 关键词布局：AI工具、效率提升、工具测评、ChatGPT替代 | 完播率优化：45-90秒时长，前3秒出结论画面

**搜一搜：** 核心词：AI工具推荐、AI写作工具、免费AI工具 | 长尾词：学生党AI工具、打工人效率工具、AI工具对比测评

**公众号：** 深度长文"AI工具选购指南"系列，布局SEO关键词

### 30天行动路径

**D1-D7（种子期）：** 日更1篇，覆盖ChatGPT/Kimi/Claude/通义千问等热门工具的单品测评。目标：10篇笔记 + 50粉。

**D8-D14（起量期）：** 发布2-3篇对比测评（横评类），蹭新工具发布热点。目标：2篇爆文 + 200粉。

**D15-D21（加速期）：** 做系列化内容"AI工具30天挑战"，每天固定时间更新，培养用户期待。目标：稳定互动 + 500粉。

**D22-D30（突破期）：** 输出1篇精品长文（3000字级别工具大全），开始在评论区引导关注。目标：品牌合作 + 1000粉。

### 数据来源

本次分析基于 MiniMax联网搜索、Serper(Google)、Tavily、DuckDuckGo、DailyHot热搜聚合 共5个引擎的实时数据。`,
      thinking: [
        { step: '搜索中', detail: '正在从多个引擎搜索...', progress: 10 },
        { step: '搜索完成', detail: '找到 87 条数据，来自 5 个引擎', progress: 35 },
        { step: '构建知识图谱', detail: '正在分析事物之间的关联...', progress: 45 },
        { step: '生成报告', detail: 'AI 正在综合分析并生成完整方案...', progress: 60 },
      ],
      searchStats: { total_raw: 87, total_deduped: 87, engines: { minimax: 22, serper: 25, tavily: 18, ddgs: 12, dailyhot: 10 } },
      graph: {
        nodes: [
          { id: 'center', name: 'AI工具测评', type: 'topic', val: 40, color: '#6366f1' },
          { id: 'xhs', name: '小红书', type: 'platform', val: 30, color: '#ff2442' },
          { id: 'chatgpt', name: 'ChatGPT', type: 'brand', val: 25, color: '#10a37f' },
          { id: 'kimi', name: 'Kimi', type: 'brand', val: 22, color: '#4f46e5' },
          { id: 'claude', name: 'Claude', type: 'brand', val: 20, color: '#d4a574' },
          { id: 'writing', name: 'AI写作', type: 'topic', val: 18, color: '#06b6d4' },
          { id: 'image', name: 'AI绘画', type: 'topic', val: 16, color: '#06b6d4' },
          { id: 'video', name: 'AI视频', type: 'topic', val: 14, color: '#06b6d4' },
          { id: 'student', name: '大学生', type: 'audience', val: 20, color: '#f59e0b' },
          { id: 'worker', name: '打工人', type: 'audience', val: 18, color: '#f59e0b' },
          { id: 'review', name: '横向对比', type: 'strategy', val: 15, color: '#fb923c' },
          { id: 'tutorial', name: '教程攻略', type: 'strategy', val: 14, color: '#fb923c' },
          { id: 'sora', name: 'Sora', type: 'trend', val: 22, color: '#a78bfa' },
          { id: 'cold-start', name: '冷启动', type: 'strategy', val: 20, color: '#fb923c' },
          { id: 'seo', name: 'SEO关键词', type: 'topic', val: 16, color: '#06b6d4' },
          { id: 'shipinhao', name: '视频号', type: 'platform', val: 18, color: '#34d399' },
        ],
        links: [
          { source: 'center', target: 'xhs', label: '主阵地', strength: 1 },
          { source: 'center', target: 'chatgpt', label: '核心工具', strength: 0.9 },
          { source: 'center', target: 'kimi', label: '国产替代', strength: 0.8 },
          { source: 'center', target: 'claude', label: '竞品', strength: 0.7 },
          { source: 'center', target: 'writing', label: '子赛道', strength: 0.8 },
          { source: 'center', target: 'image', label: '子赛道', strength: 0.7 },
          { source: 'center', target: 'video', label: '子赛道', strength: 0.6 },
          { source: 'xhs', target: 'student', label: '核心用户', strength: 0.9 },
          { source: 'xhs', target: 'worker', label: '核心用户', strength: 0.8 },
          { source: 'center', target: 'review', label: '最佳形式', strength: 0.8 },
          { source: 'center', target: 'sora', label: '蹭热点', strength: 0.6 },
          { source: 'cold-start', target: 'seo', label: '获客路径', strength: 0.7 },
          { source: 'center', target: 'shipinhao', label: '分发渠道', strength: 0.7 },
          { source: 'writing', target: 'review', label: '适合', strength: 0.5 },
        ],
      },
      sources: [
        { title: '2024年AI工具测评赛道分析报告', url: 'https://example.com/ai-tools-2024' },
        { title: '小红书AI内容创作者增长数据', url: 'https://example.com/xhs-ai-creators' },
        { title: 'ChatGPT vs Kimi 全方位对比', url: 'https://example.com/chatgpt-vs-kimi' },
      ],
      tokenUsage: { search_tokens: 0, llm_tokens: 0, total_tokens: 0, search_calls: 87, agent_rounds: 0, elapsed_ms: 34200 },
    },
  },
  {
    id: 'video-account-emotion',
    title: '视频号情感赛道关键词布局',
    prompt: '视频号做情感赛道，搜一搜关键词怎么布局？',
    emoji: '💕',
    result: {
      role: 'assistant',
      content: `### 赛道机会评分：8.2/10

情感赛道在视频号占比高达18%，是仅次于生活和知识类的第三大品类。搜一搜日均情感类搜索超800万次，但优质内容供给不足。

### 内容策略

**差异化定位：**
1. "情绪共鸣型" — 不讲大道理，只说"我懂你"
2. "故事+金句" — 3秒画面+一句扎心文案
3. "治愈系" — 疗愈向内容，夜间流量池

**标题建议：**
1. 成年人的崩溃，都是静悄悄的 (预估CTR: 14%)
2. "你有没有一个，想联系却不敢联系的人？" (预估CTR: 13%)
3. 30岁以后才明白：有些人，见一面少一面 (预估CTR: 12%)
4. 凌晨三点还没睡的人，都在想什么？ (预估CTR: 11%)
5. 原来成年人的社交，是你不找我，我也不找你 (预估CTR: 11%)

### 微信生态策略（搜一搜 Peoplerank 深度拆解）

**算法权重分配：**
- 账号可信度 25%：认证状态、历史内容质量、更新频率
- 内容相关性 40%：标题/描述关键词匹配度、话题标签
- 用户行为 35%：完播率、点赞转发比、评论深度

**搜一搜关键词矩阵（情感赛道）：**

| 关键词层级 | 关键词 | 月搜索量预估 | 竞争度 |
|-----------|--------|------------|--------|
| 核心词 | 情感语录 | 500万+ | 高 |
| 核心词 | 扎心文案 | 300万+ | 高 |
| 长尾词 | 深夜情感电台 | 80万 | 中 |
| 长尾词 | 分手后怎么走出来 | 60万 | 低 |
| 长尾词 | 异地恋 | 150万 | 中 |
| 蓝海词 | 中年人的孤独 | 30万 | 低 |
| 蓝海词 | 职场情感 | 20万 | 极低 |

**视频号发布策略：**
- 黄金时段：21:00-23:30（情感内容峰值）
- 时长：15-45秒（完播率最优区间）
- 封面：暗色调 + 大字金句
- 互动设计：结尾"你呢？"引导评论

### 30天行动路径

**D1-D7：** 每天发布1条15秒情感短视频，测试5种内容形式（文字卡、实拍、AI配音、对话截图、Vlog）
**D8-D14：** 确定2种高效形式，开始标准化生产，布局搜一搜长尾词
**D15-D21：** 蹭情感热点话题，尝试30秒以上内容，提升完播率
**D22-D30：** 建立粉丝社群，引导关注公众号，沉淀私域

### 数据来源

基于 5 个搜索引擎实时数据分析，共获取 72 条相关数据。`,
      thinking: [
        { step: '搜索中', detail: '正在搜索视频号情感赛道...', progress: 10 },
        { step: '搜索完成', detail: '找到 72 条数据', progress: 35 },
        { step: '构建知识图谱', detail: '分析情感赛道关联...', progress: 45 },
        { step: '生成报告', detail: '生成微信生态策略...', progress: 60 },
      ],
      searchStats: { total_raw: 72, total_deduped: 72, engines: { minimax: 18, serper: 20, tavily: 15, ddgs: 10, dailyhot: 9 } },
      graph: {
        nodes: [
          { id: 'center', name: '情感赛道', type: 'topic', val: 35, color: '#f472b6' },
          { id: 'shipinhao', name: '视频号', type: 'platform', val: 30, color: '#34d399' },
          { id: 'souyisou', name: '搜一搜', type: 'platform', val: 28, color: '#34d399' },
          { id: 'emotion-quote', name: '情感语录', type: 'topic', val: 22, color: '#fbbf24' },
          { id: 'night', name: '深夜电台', type: 'strategy', val: 18, color: '#fb923c' },
          { id: 'breakup', name: '分手疗愈', type: 'topic', val: 16, color: '#fbbf24' },
          { id: 'female25', name: '25-35女性', type: 'audience', val: 25, color: '#22d3ee' },
          { id: 'peoplerank', name: 'Peoplerank', type: 'strategy', val: 20, color: '#a78bfa' },
        ],
        links: [
          { source: 'center', target: 'shipinhao', label: '主阵地', strength: 1 },
          { source: 'center', target: 'souyisou', label: 'SEO入口', strength: 0.9 },
          { source: 'center', target: 'emotion-quote', label: '内容形式', strength: 0.8 },
          { source: 'center', target: 'night', label: '时间策略', strength: 0.7 },
          { source: 'center', target: 'female25', label: '核心受众', strength: 0.9 },
          { source: 'souyisou', target: 'peoplerank', label: '算法逻辑', strength: 0.8 },
          { source: 'center', target: 'breakup', label: '子话题', strength: 0.6 },
        ],
      },
      sources: [
        { title: '视频号情感赛道2024年度报告', url: 'https://example.com/video-emotion-2024' },
        { title: '搜一搜Peoplerank算法解析', url: 'https://example.com/peoplerank' },
      ],
      tokenUsage: { search_tokens: 0, llm_tokens: 0, total_tokens: 0, search_calls: 72, agent_rounds: 0, elapsed_ms: 28500 },
    },
  },
  {
    id: 'hot-topic-chase',
    title: '追热点做全平台内容',
    prompt: '谢娜演唱会热点怎么蹭？给我出一个全平台内容方案',
    emoji: '🔥',
    result: {
      role: 'assistant',
      content: `### 赛道机会评分：9.0/10

谢娜成都演唱会是近期顶级娱乐热点：1.5万张门票1分钟售罄，大麦预约17.3万人，50+明星送花篮。热度窗口期约5-7天，适合快速产出。

### 内容策略

**多平台差异化方案：**

| 平台 | 内容方向 | 形式 | 发布时机 |
|------|---------|------|---------|
| 小红书 | 情怀向："我们这代人的青春散场" | 图文 | 演唱会当天/次日 |
| 抖音 | 名场面混剪+林志颖同台高光 | 15秒短视频 | 演唱会进行中 |
| 视频号 | 深度分析："谢娜凭什么？" | 1-3分钟解说 | 次日上午 |
| 公众号 | 万字长文+数据分析 | 深度图文 | 3天内 |
| 微博 | 追热搜话题实时互动 | 短文+图 | 实时跟进 |

**标题建议：**
1. 1分钟售罄、50位明星送花：谢娜演唱会背后藏着什么秘密？(预估CTR: 15%)
2. 半个娱乐圈捧场！成都万人暴雨中喊一个人的名字 (预估CTR: 13%)
3. 从主持人到开演唱会，谢娜用了22年 (预估CTR: 12%)

**开场Hook：**
1. "1.5万张票，1分钟。17万人抢，22:1。这不是演唱会，这是一场跨越20年的青春重逢。" (+45%留存)
2. "当50个明星同时给一个人送花的时候，你就知道，她不只是一个主持人。" (+38%留存)

### 微信生态策略

**视频号：** 发布解说型内容（1-3分钟），配合搜一搜关键词"谢娜演唱会""谢娜成都""林志颖谢娜"

**搜一搜布局：** 核心词"谢娜演唱会"（预估搜索爆发期3天内500万+），长尾词"谢娜演唱会门票""谢娜林志颖""谢娜成都凤凰山"

### 30天行动路径

**D1-D3（爆发期）：** 全力产出3-5条内容，覆盖全平台，蹭最大流量
**D4-D7（长尾期）：** 发布"复盘分析"类内容，收割搜索流量
**D8-D14（转化期）：** 借热点涨的粉丝，用高质量内容留住
**D15-D30（沉淀期）：** 转入常规内容，建立"娱乐+情感"内容矩阵

### 数据来源

基于实时热搜数据 + 5引擎搜索，共获取 95 条相关数据。`,
      thinking: [
        { step: '搜索中', detail: '正在搜索谢娜演唱会相关...', progress: 10 },
        { step: '搜索完成', detail: '找到 95 条数据', progress: 35 },
        { step: '构建知识图谱', detail: '分析热点关联...', progress: 45 },
        { step: '生成报告', detail: '生成全平台方案...', progress: 60 },
      ],
      searchStats: { total_raw: 95, total_deduped: 95, engines: { minimax: 28, serper: 25, tavily: 20, ddgs: 12, dailyhot: 10 } },
      graph: {
        nodes: [
          { id: 'center', name: '谢娜演唱会', type: 'event', val: 40, color: '#f87171' },
          { id: 'xhs', name: '小红书', type: 'platform', val: 22, color: '#ff2442' },
          { id: 'douyin', name: '抖音', type: 'platform', val: 22, color: '#000000' },
          { id: 'shipinhao', name: '视频号', type: 'platform', val: 20, color: '#34d399' },
          { id: 'linzhiying', name: '林志颖', type: 'person', val: 18, color: '#818cf8' },
          { id: 'youth', name: '青春情怀', type: 'trend', val: 25, color: '#a78bfa' },
          { id: 'ticket', name: '1分钟售罄', type: 'event', val: 20, color: '#f87171' },
          { id: 'koc', name: 'KOC追热点', type: 'strategy', val: 22, color: '#fb923c' },
        ],
        links: [
          { source: 'center', target: 'xhs', label: '情怀向', strength: 0.8 },
          { source: 'center', target: 'douyin', label: '混剪向', strength: 0.8 },
          { source: 'center', target: 'shipinhao', label: '分析向', strength: 0.9 },
          { source: 'center', target: 'linzhiying', label: '名场面', strength: 0.7 },
          { source: 'center', target: 'youth', label: '核心情绪', strength: 1 },
          { source: 'center', target: 'ticket', label: '数据亮点', strength: 0.8 },
          { source: 'koc', target: 'center', label: '追热点', strength: 0.9 },
        ],
      },
      sources: [
        { title: '谢娜成都演唱会全记录', url: 'https://example.com/xiena-concert' },
        { title: '微博热搜数据：谢娜演唱会', url: 'https://example.com/weibo-hot' },
      ],
      tokenUsage: { search_tokens: 0, llm_tokens: 0, total_tokens: 0, search_calls: 95, agent_rounds: 0, elapsed_ms: 31800 },
    },
  },
  {
    id: 'beauty-koc-growth',
    title: '美妆KOC突破5万粉',
    prompt: '美妆KOC做到5000粉了，瓶颈期怎么突破到5万？',
    emoji: '💄',
    result: {
      role: 'assistant',
      content: `### 赛道机会评分：7.8/10

美妆赛道竞争激烈但天花板高。5000-5万粉是典型的"内容升级期"，需要从"随手发"升级到"有策略地发"。

### 内容策略

**瓶颈诊断：**
5000粉卡住的常见原因：
1. 内容同质化 — 和其他美妆号没有区别
2. 没有系列化 — 每条内容独立，不成体系
3. 缺乏人设 — 用户记不住你是谁

**突破策略：**
1. "垂直再垂直" — 从"美妆"缩到"黄皮平价腮红" / "学生党日常妆"
2. "内容IP化" — 固定栏目如"每周一拆"、"30秒能学会"
3. "对比型爆款" — 大牌vs平替、网红vs实用

**标题建议：**
1. 黄皮救星！这5支腮红让我告别"脏橘"噩梦 (预估CTR: 13%)
2. 全网都在吹的XX粉底，我帮你们试了7天 (预估CTR: 12%)
3. 月薪3000也能拥有的"贵脸感"妆容 (预估CTR: 11%)

### 微信生态策略

**视频号突破策略：** 把小红书爆文改成30-60秒短视频，搜一搜布局"平价化妆品推荐""学生党美妆"等长尾词

### 30天行动路径

**D1-D7：** 数据复盘，找出历史爆文共性，确定2-3个固定栏目
**D8-D14：** 每天1条栏目内容+1条随机测试内容
**D15-D21：** 根据数据砍掉低效栏目，集中资源做爆款
**D22-D30：** 尝试合作互推+投流测试

### 数据来源

基于 5 个搜索引擎实时数据分析。`,
      thinking: [
        { step: '搜索中', detail: '正在搜索美妆KOC增长...', progress: 10 },
        { step: '搜索完成', detail: '找到 68 条数据', progress: 35 },
        { step: '构建知识图谱', detail: '分析美妆赛道...', progress: 45 },
        { step: '生成报告', detail: '生成增长策略...', progress: 60 },
      ],
      searchStats: { total_raw: 68, total_deduped: 68, engines: { minimax: 15, serper: 20, tavily: 15, ddgs: 10, dailyhot: 8 } },
      graph: {
        nodes: [
          { id: 'center', name: '美妆KOC', type: 'topic', val: 35, color: '#f472b6' },
          { id: 'xhs', name: '小红书', type: 'platform', val: 28, color: '#ff2442' },
          { id: 'compare', name: '对比测评', type: 'strategy', val: 22, color: '#fb923c' },
          { id: 'budget', name: '平价好物', type: 'topic', val: 20, color: '#fbbf24' },
          { id: 'skin', name: '黄皮专属', type: 'topic', val: 18, color: '#fbbf24' },
          { id: 'student', name: '学生党', type: 'audience', val: 22, color: '#22d3ee' },
        ],
        links: [
          { source: 'center', target: 'xhs', label: '主阵地', strength: 1 },
          { source: 'center', target: 'compare', label: '爆款形式', strength: 0.9 },
          { source: 'center', target: 'budget', label: '定位', strength: 0.8 },
          { source: 'center', target: 'skin', label: '垂直', strength: 0.7 },
          { source: 'budget', target: 'student', label: '目标', strength: 0.8 },
        ],
      },
      sources: [
        { title: '小红书美妆赛道2024增长报告', url: 'https://example.com/beauty-growth' },
      ],
      tokenUsage: { search_tokens: 0, llm_tokens: 0, total_tokens: 0, search_calls: 68, agent_rounds: 0, elapsed_ms: 29100 },
    },
  },
  {
    id: 'gongzhonghao-opportunity',
    title: '公众号还有机会吗',
    prompt: '帮我分析"公众号还有机会吗"这个话题做成什么内容',
    emoji: '📱',
    result: {
      role: 'assistant',
      content: `### 赛道机会评分：7.5/10

"公众号还有机会吗"本身就是一个高搜索量的话题（月搜索量50万+），自带流量。这是一个"元话题"——关于内容创作本身的内容，天然吸引创作者群体。

### 内容策略

**这个话题的独特价值：**
搜索这个问题的人 = 潜在内容创作者 = 你的精准用户

**差异化角度：**
1. "数据派" — 用真实数据说话（新增账号数、阅读量变化、广告收入趋势）
2. "案例派" — 2024年新起号成功的5个真实案例
3. "反向观点" — "公众号已死？不，是垃圾号死了"

**标题建议：**
1. 2024年我从0做到10万粉公众号，告诉你还有没有机会 (预估CTR: 14%)
2. 我分析了100个新起号的公众号，发现了3个共同规律 (预估CTR: 12%)
3. 公众号已死？看完这组数据你就不这么想了 (预估CTR: 11%)

### 微信生态策略

**搜一搜精准布局：** "公众号还有机会吗"本身就是搜一搜高频词，可以做系列内容布局：
- "2024公众号还值得做吗"
- "公众号起号攻略"
- "公众号怎么涨粉"
- "公众号赚钱方法"

### 30天行动路径

**D1-D7：** 发布第一篇深度分析"2024公众号生死报告"，用数据说话
**D8-D14：** 连载"新号成功案例拆解"系列
**D15-D21：** 出一份"公众号起号清单"实用工具文
**D22-D30：** 总结"我做这个选题30天的数据"——用自己的增长数据做内容

### 数据来源

基于 5 个搜索引擎实时数据分析。`,
      thinking: [
        { step: '搜索中', detail: '正在搜索公众号机会...', progress: 10 },
        { step: '搜索完成', detail: '找到 63 条数据', progress: 35 },
        { step: '构建知识图谱', detail: '分析内容生态...', progress: 45 },
        { step: '生成报告', detail: '生成策略方案...', progress: 60 },
      ],
      searchStats: { total_raw: 63, total_deduped: 63, engines: { minimax: 14, serper: 18, tavily: 14, ddgs: 10, dailyhot: 7 } },
      graph: {
        nodes: [
          { id: 'center', name: '公众号机会', type: 'topic', val: 35, color: '#34d399' },
          { id: 'wechat', name: '微信生态', type: 'platform', val: 30, color: '#34d399' },
          { id: 'souyisou', name: '搜一搜', type: 'platform', val: 22, color: '#34d399' },
          { id: 'creator', name: '内容创作者', type: 'audience', val: 25, color: '#22d3ee' },
          { id: 'niche', name: '垂直领域', type: 'strategy', val: 20, color: '#fb923c' },
          { id: 'data', name: '数据分析', type: 'strategy', val: 18, color: '#fb923c' },
        ],
        links: [
          { source: 'center', target: 'wechat', label: '所属平台', strength: 1 },
          { source: 'center', target: 'souyisou', label: '流量入口', strength: 0.9 },
          { source: 'center', target: 'creator', label: '目标读者', strength: 0.9 },
          { source: 'center', target: 'niche', label: '突破策略', strength: 0.8 },
          { source: 'center', target: 'data', label: '论证方式', strength: 0.7 },
        ],
      },
      sources: [
        { title: '2024微信公众平台数据报告', url: 'https://example.com/wechat-report' },
      ],
      tokenUsage: { search_tokens: 0, llm_tokens: 0, total_tokens: 0, search_calls: 63, agent_rounds: 0, elapsed_ms: 27300 },
    },
  },
]
