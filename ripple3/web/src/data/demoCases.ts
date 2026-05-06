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

**视频号：**
- 发布时间：周二/四/六 20:00-21:00
- 关键词布局：AI工具、效率提升、工具测评、ChatGPT替代
- 完播率优化：45-90秒时长，前3秒出结论画面

**搜一搜：**
- 核心词：AI工具推荐、AI写作工具、免费AI工具
- 长尾词：学生党AI工具、打工人效率工具、AI工具对比测评

**公众号：**
- 深度长文"AI工具选购指南"系列，布局SEO关键词

### 30天行动路径

**D1-D7（种子期）：** 日更1篇，覆盖ChatGPT/Kimi/Claude/通义千问等热门工具的单品测评。目标：10篇笔记 + 50粉。

**D8-D14（起量期）：** 发布2-3篇对比测评（横评类），蹭新工具发布热点。目标：2篇爆文 + 200粉。

**D15-D21（加速期）：** 做系列化内容"AI工具30天挑战"，每天固定时间更新，培养用户期待。目标：稳定互动 + 500粉。

**D22-D30（突破期）：** 输出1篇精品长文（3000字级别工具大全），开始在评论区引导关注。目标：品牌合作 + 1000粉。

### 数据来源

本次分析基于 MiniMax联网搜索、Serper(Google)、Tavily、DuckDuckGo、DailyHot热搜聚合 共5个引擎的实时数据。`,
      graph: {
        nodes: [
          { id: 'center', name: 'AI工具测评', type: 'topic', val: 40, color: '#6366f1' },
          { id: 'xhs', name: '小红书', type: 'platform', val: 30, color: '#ff2442' },
          { id: 'chatgpt', name: 'ChatGPT', type: 'brand', val: 25, color: '#10a37f' },
          { id: 'kimi', name: 'Kimi', type: 'brand', val: 22, color: '#4f46e5' },
          { id: 'claude', name: 'Claude', type: 'brand', val: 20, color: '#d4a574' },
          { id: 'writing', name: 'AI写作', type: 'keyword', val: 18, color: '#06b6d4' },
          { id: 'image', name: 'AI绘画', type: 'keyword', val: 16, color: '#06b6d4' },
          { id: 'video', name: 'AI视频', type: 'keyword', val: 14, color: '#06b6d4' },
          { id: 'student', name: '大学生', type: 'audience', val: 20, color: '#f59e0b' },
          { id: 'worker', name: '打工人', type: 'audience', val: 18, color: '#f59e0b' },
          { id: 'review', name: '横向对比', type: 'strategy', val: 15, color: '#fb923c' },
          { id: 'tutorial', name: '教程攻略', type: 'strategy', val: 14, color: '#fb923c' },
          { id: 'sora', name: 'Sora', type: 'trend', val: 22, color: '#a78bfa' },
          { id: 'cold-start', name: '冷启动', type: 'strategy', val: 20, color: '#fb923c' },
          { id: 'seo', name: 'SEO关键词', type: 'keyword', val: 16, color: '#06b6d4' },
          { id: 'shipinhao', name: '视频号', type: 'platform', val: 18, color: '#34d399' },
        ],
        links: [
          { source: 'center', target: 'xhs', label: '主阵地' },
          { source: 'center', target: 'chatgpt', label: '核心工具' },
          { source: 'center', target: 'kimi', label: '国产替代' },
          { source: 'center', target: 'claude', label: '竞品' },
          { source: 'center', target: 'writing', label: '子赛道' },
          { source: 'center', target: 'image', label: '子赛道' },
          { source: 'center', target: 'video', label: '子赛道' },
          { source: 'xhs', target: 'student', label: '核心用户' },
          { source: 'xhs', target: 'worker', label: '核心用户' },
          { source: 'center', target: 'review', label: '最佳形式' },
          { source: 'center', target: 'sora', label: '蹭热点' },
          { source: 'cold-start', target: 'seo', label: '获客路径' },
          { source: 'center', target: 'shipinhao', label: '分发渠道' },
          { source: 'writing', target: 'review', label: '适合' },
        ],
      },
    },
  },
  {
    id: 'exam-vlog',
    title: '考研Vlog爆款分析',
    prompt: '帮我分析"考研人的一天"这个选题在小红书和视频号的爆款潜力，给出完整内容方案',
    emoji: '🎓',
    result: {
      role: 'assistant',
      content: `### 赛道机会评分：9.1/10

"考研人的一天"满足爆款三要素：强共鸣 × 大基数(438万考研人) × 时效性。小红书"考研"月搜索量2.3亿次，此类内容平均互动率12.4%，远超平台均值4.2%。

### 内容策略

**差异化定位：**
1. "真实记录型" — 不修饰的日常，展示崩溃和坚持
2. "数据可视化" — 学习时长统计、进度条、倒计时
3. "陪伴感" — 让观众觉得"我不是一个人在战斗"

**标题建议：**
1. 考研倒计时180天｜今天差点放弃了 (预估CTR: 13%)
2. 凌晨5点的图书馆，只有我和保安 (预估CTR: 12%)
3. 考研人的一天：从崩溃到自愈只需要一杯咖啡 (预估CTR: 11%)
4. 二战考研｜所有人都说我疯了 (预估CTR: 10%)
5. 如果你也在考研，请一定看完这条 (预估CTR: 10%)

### 微信生态策略

**视频号：**
- 发布时间：22:00-23:00（考研人休息刷手机时间）
- 时长：45-90秒竖版
- 完播率设计：倒计时结构"距考试还有XX天"

**搜一搜：**
- 核心词：考研日常、考研vlog、考研人的一天
- 长尾词：考研作息时间表、考研图书馆、考研崩溃怎么办

### 30天行动路径

**D1-D7：** 日更考研日常，建立"陪伴感"人设。
**D8-D14：** 加入情绪爆点（崩溃/感动瞬间），目标出1篇爆文。
**D15-D21：** 做系列"30天考研挑战"，培养用户追更习惯。
**D22-D30：** 输出经验总结类干货，提升账号专业度。

### 数据来源

基于 5 个搜索引擎实时数据分析。`,
      graph: {
        nodes: [
          { id: 'center', name: '考研Vlog', type: 'topic', val: 35, color: '#6366f1' },
          { id: 'xhs', name: '小红书', type: 'platform', val: 28, color: '#ff2442' },
          { id: 'shipinhao', name: '视频号', type: 'platform', val: 22, color: '#34d399' },
          { id: 'daily', name: '日常记录', type: 'strategy', val: 20, color: '#fb923c' },
          { id: 'emotion', name: '情感共鸣', type: 'strategy', val: 25, color: '#fb923c' },
          { id: 'student', name: '考研人', type: 'audience', val: 30, color: '#f59e0b' },
          { id: 'library', name: '图书馆', type: 'keyword', val: 15, color: '#06b6d4' },
          { id: 'countdown', name: '倒计时', type: 'keyword', val: 14, color: '#06b6d4' },
        ],
        links: [
          { source: 'center', target: 'xhs', label: '主阵地' },
          { source: 'center', target: 'shipinhao', label: '分发' },
          { source: 'center', target: 'daily', label: '形式' },
          { source: 'center', target: 'emotion', label: '核心卖点' },
          { source: 'center', target: 'student', label: '目标受众' },
          { source: 'emotion', target: 'student', label: '引发共鸣' },
          { source: 'center', target: 'library', label: '场景' },
          { source: 'center', target: 'countdown', label: '紧迫感' },
        ],
      },
    },
  },
  {
    id: 'efficiency-tools',
    title: '打工人效率神器',
    prompt: '帮我策划"打工人必备的 10 个效率神器"系列内容，分析竞品和差异化策略',
    emoji: '💼',
    result: {
      role: 'assistant',
      content: `### 赛道机会评分：8.4/10

职场效率工具赛道竞争中等偏高，但"系列化+场景化"内容仍有差异化空间。核心优势：变现路径清晰（工具推广佣金）。

### 内容策略

**差异化定位：**
1. "问题→工具→效果" 解决方案式（非简单罗列）
2. "预算限制"角度：免费/低价替代方案
3. "Before & After" 可视化效率对比

**系列规划（10期）：**
1. 会议效率 — 飞书妙记/讯飞（痛点：开会1h，纪要写2h）
2. 时间管理 — 滴答清单/Notion（痛点：忙到死但产出低）
3. AI写作 — Kimi/ChatGPT（痛点：周报月报写到崩溃）
4. 文件整理 — Eagle/Everything（痛点：找文件比做文件还久）
5. 设计协作 — Figma/即时设计（痛点：甲方改稿100遍）

**标题建议：**
1. 用了这个工具后，我每天准时下班了 (预估CTR: 11%)
2. 打工人必看！5个免费效率神器，省下3小时/天 (预估CTR: 10%)

### 微信生态策略

**多平台分发：**
- 小红书（主）：图文 + 工具截图 + 效果对比
- 视频号（引流）：30s"一个工具解决一个问题"
- 公众号（沉淀）：深度长文"完整效率体系搭建"

### 30天行动路径

**D1-D7：** 发布前3期内容，测试哪个话题互动最高。
**D8-D14：** 根据数据反馈，加大爆款方向投入。
**D15-D21：** 做合集/总结类内容，提升账号被搜索概率。
**D22-D30：** 开始接工具推广合作，测试变现。

### 数据来源

基于 5 个搜索引擎实时数据分析。`,
      graph: {
        nodes: [
          { id: 'center', name: '效率工具', type: 'topic', val: 35, color: '#6366f1' },
          { id: 'meeting', name: '会议效率', type: 'keyword', val: 18, color: '#06b6d4' },
          { id: 'time', name: '时间管理', type: 'keyword', val: 16, color: '#06b6d4' },
          { id: 'ai-write', name: 'AI写作', type: 'keyword', val: 20, color: '#06b6d4' },
          { id: 'worker', name: '打工人', type: 'audience', val: 25, color: '#f59e0b' },
          { id: 'xhs', name: '小红书', type: 'platform', val: 22, color: '#ff2442' },
          { id: 'notion', name: 'Notion', type: 'brand', val: 15, color: '#f87171' },
          { id: 'feishu', name: '飞书', type: 'brand', val: 14, color: '#f87171' },
        ],
        links: [
          { source: 'center', target: 'meeting', label: '子话题' },
          { source: 'center', target: 'time', label: '子话题' },
          { source: 'center', target: 'ai-write', label: '子话题' },
          { source: 'center', target: 'worker', label: '目标用户' },
          { source: 'center', target: 'xhs', label: '主阵地' },
          { source: 'time', target: 'notion', label: '推荐工具' },
          { source: 'meeting', target: 'feishu', label: '推荐工具' },
        ],
      },
    },
  },
]
