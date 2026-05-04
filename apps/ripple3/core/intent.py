"""Intent recognition router — classifies user messages and dispatches to engines.

Uses a lightweight LLM call to classify intent, then routes to the
appropriate engine pipeline. Keeps latency low with a focused prompt.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from collections.abc import AsyncIterator

from core.llm import chat_stream, chat_deep_stream
from adapters.search import (
    search_peers, search_bloggers, search_news,
    search_competition, search_trending,
)

log = logging.getLogger(__name__)


@dataclass
class IntentResult:
    intent: str  # radar | idea | predict | create | distill | chat
    domain: str = ""
    topic: str = ""
    platform: str = ""
    extra: dict = field(default_factory=dict)


_ROUTER_SYSTEM = """你是 Ripple 的意图识别模块。根据用户消息和对话上下文，判断用户想要什么。

只返回一个 JSON 对象（不要 markdown），格式：
{"intent":"<类型>","domain":"<领域>","topic":"<选题>","platform":"<平台>"}

可选 intent 类型：
- "radar": 用户想了解某个领域的内容生态、博主推荐、行业分析
- "idea": 用户想要选题灵感、话题推荐
- "predict": 用户想评估某个选题/标题的爆款潜力
- "create": 用户想创作内容、写文案、生成多平台内容
- "distill": 用户想分析某个博主的风格、提炼方法论
- "chat": 普通对话、问答、闲聊、不确定要做什么

判断规则：
- 如果用户提到"领域""行业""同行""博主""达人"→ radar
- 如果用户提到"选题""灵感""话题""点子""想做什么内容" → idea
- 如果用户提到"能火吗""爆款""评估""预测""这个标题怎么样" → predict
- 如果用户提到"写""创作""文案""内容""小红书文""帮我出" → create
- 如果用户提到"风格""蒸馏""写作方法""学习某博主" → distill
- 如果无法明确判断，返回 "chat"
- domain：从上下文中提取领域（如美食、数码），没有就留空
- topic：从上下文中提取具体选题/标题，没有就留空
- platform：提到的目标平台（小红书/视频号/公众号/抖音/B站），没有就留空"""


async def classify_intent(
    message: str,
    history: list[dict],
) -> IntentResult:
    """Fast intent classification via LLM."""
    context_summary = ""
    if history:
        recent = history[-6:]
        context_parts = []
        for h in recent:
            role = "用户" if h["role"] == "user" else "助手"
            content = h["content"][:200]
            context_parts.append(f"{role}: {content}")
        context_summary = "\n".join(context_parts)

    user_msg = f"对话上下文:\n{context_summary}\n\n最新用户消息: {message}" if context_summary else f"用户消息: {message}"

    messages = [
        {"role": "system", "content": _ROUTER_SYSTEM},
        {"role": "user", "content": user_msg},
    ]

    full = ""
    async for chunk in chat_stream(messages, temperature=0.1, max_tokens=200):
        full += chunk

    try:
        full = full.strip()
        # Strip <think>...</think> blocks from reasoning models
        import re
        full = re.sub(r"<think>.*?</think>", "", full, flags=re.DOTALL).strip()
        if full.startswith("```"):
            lines = full.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            full = "\n".join(lines).strip()
        start = full.find("{")
        end = full.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(full[start:end])
        else:
            data = _fallback_classify(message)
    except (json.JSONDecodeError, ValueError):
        log.warning("Intent parse failed, using fallback: %s", full[:200])
        data = _fallback_classify(message)

    return IntentResult(
        intent=data.get("intent", "chat"),
        domain=data.get("domain", ""),
        topic=data.get("topic", ""),
        platform=data.get("platform", ""),
        extra=data,
    )


def _fallback_classify(message: str) -> dict:
    """Keyword-based fallback when LLM parsing fails."""
    msg = message.lower()
    domain = ""

    domain_keywords = [
        "美食", "数码", "科技", "职场", "穿搭", "健身", "育儿",
        "旅行", "家居", "护肤", "化妆", "读书", "投资", "宠物",
    ]
    for kw in domain_keywords:
        if kw in msg:
            domain = kw
            break

    if any(w in msg for w in ["领域", "行业", "同行", "博主", "达人", "生态", "想做"]):
        return {"intent": "radar", "domain": domain}
    if any(w in msg for w in ["选题", "灵感", "话题", "点子", "想写什么"]):
        return {"intent": "idea", "domain": domain}
    if any(w in msg for w in ["能火", "爆款", "评估", "预测", "怎么样", "分数"]):
        return {"intent": "predict", "domain": domain}
    if any(w in msg for w in ["写", "创作", "文案", "内容", "笔记", "帮我出"]):
        return {"intent": "create", "domain": domain}
    if any(w in msg for w in ["风格", "蒸馏", "方法论", "学习"]):
        return {"intent": "distill", "domain": domain}
    return {"intent": "chat", "domain": domain}


# ── Engine dispatch: yields streaming markdown ─────────────────────────────

async def dispatch_radar(domain: str, history: list[dict]) -> AsyncIterator[str]:
    """Run peer radar analysis for a domain."""
    yield f"**正在分析「{domain}」领域的内容生态...**\n\n"

    peer_data = search_peers(domain)
    blogger_data = search_bloggers(domain)
    news_data = search_news(domain)
    trending = search_trending()

    peer_text = _fmt_search("同行内容", peer_data[:15])
    blogger_text = _fmt_search("博主/达人", blogger_data[:15])
    news_text = _fmt_news(news_data[:10])
    trend_text = _fmt_trending(trending)

    system_msg = """你是 Ripple — 一位懂行的社媒内容顾问。用户想了解一个领域的内容生态。

请用自然、口语化的方式输出分析（像一位有经验的前辈在和新手聊天），包含：

## 这个领域现在是什么状况
（用2-3段话概括，包括主流内容形式、受众画像、近期变化）

## 值得关注的博主/达人
（每位博主：名字、平台、风格特点、值得学习的点。推荐5-8位）

## 最近大家都在聊什么
（热门话题 + 为什么火）

## 哪些方向还有机会
（蓝海机会，有需求但好内容不多的方向）

## 给你的建议
（作为新手KOC，从哪里切入最好？2-3条具体建议）

要求：基于搜索数据分析，不编造博主。语气亲和，像朋友聊天，不要太正式。"""

    user_msg = f"""领域: {domain}

搜索到的同行内容:
{peer_text}

博主/达人信息:
{blogger_text}

最新动态:
{news_text}

当前热搜趋势:
{trend_text}

请输出分析。"""

    async for chunk in _filter_think_tags(chat_deep_stream(
        [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=6000, temperature=0.6,
    )):
        yield chunk


async def dispatch_idea(domain: str, context: str, history: list[dict]) -> AsyncIterator[str]:
    """Generate topic ideas for a domain."""
    yield f"**正在为「{domain}」领域搜索灵感素材...**\n\n"

    peer_data = search_peers(domain)
    news_data = search_news(domain)
    trending = search_trending()

    peer_text = _fmt_search("同行内容", peer_data[:15])
    news_text = _fmt_news(news_data[:10])
    trend_text = _fmt_trending(trending)

    prev_context = ""
    for h in reversed(history):
        if h["role"] == "assistant" and len(h["content"]) > 200:
            prev_context = h["content"][:2000]
            break

    system_msg = """你是 Ripple — 一位超有创意的内容策划师。帮用户想出10-15个选题点子。

每个选题格式：
### N. 「标题」
- **为什么值得做**: 一句话说明
- **怎么切入**: 具体角度
- **适合谁看**: 目标受众
- **内容形式**: 图文/视频/清单等
- **灵感来源**: 搜索数据中的哪条启发了你

最后推荐 TOP 3 最值得做的选题，说明理由。

要求：
- 标题要像真正的爆款标题（用数字/反差/悬念/共鸣）
- 覆盖不同角度和形式
- 考虑视频号和小红书的内容偏好
- 灵感基于搜索数据，不凭空想象"""

    user_msg = f"""领域: {domain}
{f'用户补充: {context}' if context else ''}

搜索数据:
{peer_text}

最新动态:
{news_text}

热搜趋势:
{trend_text}

{f'之前的领域分析（供参考）: {prev_context[:1000]}' if prev_context else ''}

请生成选题灵感。"""

    async for chunk in _filter_think_tags(chat_deep_stream(
        [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=6000, temperature=0.8,
    )):
        yield chunk


async def dispatch_predict(topic: str, domain: str, platform: str, history: list[dict]) -> AsyncIterator[str]:
    """Predict viral potential for a topic."""
    yield f"**正在搜索「{topic}」的竞品数据...**\n\n"

    comp_data = search_competition(topic)
    comp_text = "\n".join(
        f"- 【{r.title}】{r.snippet[:120]}\n  {r.url}"
        for r in comp_data[:10]
    ) or "（未找到直接竞品）"

    platform = platform or "小红书"

    system_msg = """你是 Ripple — 一位数据驱动的内容分析师。用12维度模型评估选题的爆款潜力。

分析框架：
**8个基础维度 + 影视飓风HKRR模型4维度**

对每个维度给出：分数(0-100) + 一句话理由 + 提升建议

输出格式：

## 选题评估：「标题」

### 综合评分：XX/100  ⭐⭐⭐⭐

### 基础维度
| 维度 | 分数 | 评价 |
|------|------|------|
| 话题热度 | XX | ... |
| 竞争蓝海 | XX | ... |
| 情绪共鸣 | XX | ... |
| 实用价值 | XX | ... |
| 标题吸引力 | XX | ... |
| 平台适配 | XX | ... |
| 原创空间 | XX | ... |
| 时效窗口 | XX | ... |

### HKRR 模型
| 维度 | 分数 | 评价 |
|------|------|------|
| H-快乐度 | XX | ... |
| K-知识量 | XX | ... |
| R-共鸣感 | XX | ... |
| R-节奏感 | XX | ... |

### 竞品分析
（分析已有内容的竞争格局）

### 差异化建议
（怎么做出不一样的内容？3条具体建议）

### 最终判断
（🔥强烈推荐 / ✅值得做 / ⚠️需调整 / ❌不建议）+ 理由

要求：每个维度引用竞品数据作为证据。"""

    user_msg = f"""选题: {topic}
领域: {domain or '综合'}
目标平台: {platform}

竞品搜索数据:
{comp_text}

请输出完整评估报告。"""

    async for chunk in _filter_think_tags(chat_deep_stream(
        [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=6000, temperature=0.3,
    )):
        yield chunk


async def dispatch_create(topic: str, domain: str, platform: str, history: list[dict]) -> AsyncIterator[str]:
    """Create full content package for a topic."""
    yield f"**正在为「{topic}」创作内容...**\n\n"

    prev_context = ""
    for h in reversed(history):
        if h["role"] == "assistant" and len(h["content"]) > 200:
            prev_context = h["content"][:2000]
            break

    platform = platform or "小红书"

    system_msg = """你是 Ripple — 一位顶级内容创作者。按以下流程输出完整内容包：

## 内容大纲
（Hook设计 + 段落结构 + 情绪曲线）

## 候选标题
1. ...（数字型）
2. ...（悬念型）
3. ...（共鸣型）

## 完整正文
（1500-2500字，信息密度高，有真实案例和数据，避免AI味）

## 多平台版本

### 小红书版
（emoji风格，种草语气，带标签）

### 视频号版
（短文案100-200字，适合口播）

### 公众号版
（完整长文，重新排版）

### 抖音版
（超短文案50-100字，开头即高潮）

## AI 点映团评审
### 路人会怎么看？
### 同行会怎么看？
### 综合评分与改进建议

写作要求：
- 用真实品牌名和案例，不用A/B/C代替
- 每300字有一个爽点或共鸣点
- 段落间自然过渡
- 每个平台版本独立撰写"""

    user_msg = f"""选题: {topic}
领域: {domain or '综合'}
目标平台: {platform}

{f'之前的分析（供参考）: {prev_context[:1500]}' if prev_context else ''}

请输出完整内容包。"""

    async for chunk in _filter_think_tags(chat_deep_stream(
        [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=8192, temperature=0.7,
    )):
        yield chunk


async def dispatch_chat(message: str, history: list[dict]) -> AsyncIterator[str]:
    """General chat — guide users through the workflow."""
    system_msg = """你是 Ripple — KOC 内容灵感助手。你帮想成为 KOC 的新手小白完成从选题到创作的全流程。

你的语气：像一位热心的学姐/学长，亲和、专业、接地气。不要说教，不要用"首先、其次、最后"这种格式。

你能做什么（自然地告诉用户，不要列清单）：
- 分析某个领域的内容生态（谁在做、做得好的是谁、什么话题火）
- 帮想选题点子
- 评估某个选题能不能火
- 直接帮写内容（小红书/视频号/公众号/抖音都行）

如果用户不知道要做什么，主动引导：先聊聊感兴趣的领域 → 看看同行在做什么 → 一起想选题 → 评估 → 出内容。

对话中保持上下文连贯。如果上文已经聊过某个领域，后续自动关联。

重要：你是一个真正有价值的助手。当用户问问题时，直接给出有深度的分析和具体建议，而不是说"你可以去用XX功能"。
重要：直接输出回答，不要输出任何思考过程。"""

    messages = [{"role": "system", "content": system_msg}]
    for h in history[-20:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    async for chunk in _filter_think_tags(chat_deep_stream(messages, max_tokens=4096, temperature=0.7)):
        yield chunk


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _filter_think_tags(stream: AsyncIterator[str]) -> AsyncIterator[str]:
    """Strip <think>...</think> blocks from streaming output."""
    buffer = ""
    inside_think = False
    for_check = ""

    async for chunk in stream:
        buffer += chunk
        # Process buffer character by character
        while buffer:
            if inside_think:
                end_idx = buffer.find("</think>")
                if end_idx >= 0:
                    buffer = buffer[end_idx + 8:]
                    inside_think = False
                    continue
                else:
                    buffer = ""
                    break
            else:
                think_idx = buffer.find("<think>")
                if think_idx >= 0:
                    if think_idx > 0:
                        yield buffer[:think_idx]
                    buffer = buffer[think_idx + 7:]
                    inside_think = True
                    continue
                elif "<" in buffer and not buffer.endswith(">"):
                    # Might be a partial <think> tag — hold in buffer
                    partial_idx = buffer.rfind("<")
                    possible = buffer[partial_idx:]
                    if "<think>"[:len(possible)] == possible:
                        if partial_idx > 0:
                            yield buffer[:partial_idx]
                        buffer = possible
                        break
                    else:
                        yield buffer
                        buffer = ""
                        break
                else:
                    yield buffer
                    buffer = ""
                    break

    if buffer and not inside_think:
        yield buffer


def _fmt_search(label: str, results: list) -> str:
    if not results:
        return f"（{label}：未找到数据）"
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. 【{r.title}】\n   {r.snippet}\n   来源: {r.url}")
    return "\n".join(lines)


def _fmt_news(results: list) -> str:
    if not results:
        return "（未找到近期新闻动态）"
    lines = []
    for i, r in enumerate(results, 1):
        date_str = f" ({r.date})" if r.date else ""
        lines.append(f"{i}. 【{r.title}】{date_str}\n   {r.snippet}")
    return "\n".join(lines)


def _fmt_trending(results: list) -> str:
    if not results:
        return "（未获取到热搜数据）"
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. 【{r.title}】 {r.snippet}")
    return "\n".join(lines)
