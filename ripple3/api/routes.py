"""API routes — SSE streaming endpoints wrapping existing engines."""

from __future__ import annotations

import json
import logging
import traceback
from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.sse import (
    thinking_event,
    content_event,
    sources_event,
    done_event,
    error_event,
)
from core.intent import classify_intent, _filter_think_tags
from core.llm import chat_stream, chat_deep_stream
from core.citations import CitationList
from core import store
from adapters.search import (
    search_parallel_radar,
    search_parallel_idea,
    search_parallel_predict,
    search_parallel_distill,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


# ── Request models ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    session: dict = {}


class PredictRequest(BaseModel):
    topic: str
    domain: str = ""
    platform: str = "小红书"


class CreateRequest(BaseModel):
    topic: str
    domain: str = ""
    platform: str = "小红书"


class DistillRequest(BaseModel):
    blogger: str
    domain: str = ""


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok", "service": "ripple"}


# ── Conversations ─────────────────────────────────────────────────────────────

@router.get("/conversations")
async def list_conversations():
    items = await store.list_conversations(limit=30)
    return {"conversations": items}


# ── Unified chat endpoint ─────────────────────────────────────────────────────

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    async def generate() -> AsyncIterator[str]:
        try:
            message = req.message.strip()
            if not message:
                yield error_event("消息不能为空")
                return

            yield thinking_event("解析意图", f"理解「{message[:40]}」...", progress=5)

            plain_history = [
                {"role": m["role"], "content": m["content"]}
                for m in req.history[-20:]
            ]

            intent = await classify_intent(message, plain_history)
            domain = intent.domain or req.session.get("domain", "")
            topic = intent.topic or req.session.get("last_topic", "")
            platform = intent.platform or "小红书"

            yield thinking_event(
                "意图识别完成",
                f"意图: {intent.intent} | 领域: {domain or '通用'} | 主题: {topic or '—'}",
                progress=10,
            )

            if intent.intent == "radar" and domain:
                async for chunk in _stream_radar(domain, plain_history):
                    yield chunk
            elif intent.intent == "idea" and domain:
                async for chunk in _stream_idea(domain, message, plain_history):
                    yield chunk
            elif intent.intent == "predict" and topic:
                async for chunk in _stream_predict(topic, domain, platform, plain_history):
                    yield chunk
            elif intent.intent == "create" and (topic or domain):
                create_topic = topic or f"{domain}相关内容"
                async for chunk in _stream_create(create_topic, domain, platform, plain_history):
                    yield chunk
            elif intent.intent == "distill":
                blogger = intent.topic or intent.domain or message
                async for chunk in _stream_distill(blogger, domain, plain_history):
                    yield chunk
            else:
                async for chunk in _stream_chat(message, plain_history):
                    yield chunk

            yield done_event(intent=intent.intent, domain=domain, topic=topic)

        except Exception as exc:
            log.error("Chat error: %s\n%s", exc, traceback.format_exc())
            yield error_event(f"处理出错: {exc}")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Stream helpers ────────────────────────────────────────────────────────────


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
    return "\n".join(f"{i}. 【{r.title}】 {r.snippet}" for i, r in enumerate(results, 1))


async def _stream_radar(domain: str, history: list[dict]) -> AsyncIterator[str]:
    yield thinking_event("并行搜索", f"正在搜索「{domain}」领域数据...", progress=15, agents=[
        {"name": "同行内容", "status": "running"},
        {"name": "博主达人", "status": "running"},
        {"name": "最新动态", "status": "running"},
        {"name": "热搜趋势", "status": "running"},
    ])

    data = await search_parallel_radar(domain)
    peer_count = len(data["peers"])
    blogger_count = len(data["bloggers"])
    news_count = len(data["news"])

    yield thinking_event("搜索完成", f"找到 {peer_count} 条内容 + {blogger_count} 位博主 + {news_count} 条动态", progress=50, agents=[
        {"name": "同行内容", "status": "done", "count": peer_count},
        {"name": "博主达人", "status": "done", "count": blogger_count},
        {"name": "最新动态", "status": "done", "count": news_count},
        {"name": "热搜趋势", "status": "done", "count": len(data["trending"])},
    ])

    citations = CitationList()
    citations.add_from_search(data["peers"][:15])
    citations.add_from_search(data["bloggers"][:15])
    citations.add_from_search(data["news"][:10])

    yield thinking_event("AI 分析", f"AI 正在深度分析「{domain}」领域生态...", progress=60)

    system_msg = f"""你是 Ripple — 一位懂行的社媒内容顾问。用户想了解一个领域的内容生态。
请用自然、口语化的方式输出分析（像一位有经验的前辈在和新手聊天），包含：

## 这个领域现在是什么状况
（用2-3段话概括，包括主流内容形式、受众画像、近期变化。特别关注视频号和微信公众号的趋势）

## 值得关注的博主/达人
（每位博主：名字、平台、风格特点、值得学习的点。推荐5-8位，优先推荐视频号和公众号创作者）

## 最近大家都在聊什么
（热门话题 + 为什么火）

## 哪些方向还有机会
（蓝海机会，有需求但好内容不多的方向，特别是在视频号和微信生态中的机会）

## 给你的建议
（作为新手KOC，从哪里切入最好？2-3条具体建议，考虑微信生态的分发优势）

要求：基于搜索数据分析，不编造博主。语气亲和，像朋友聊天。"""

    user_msg = f"""领域: {domain}
搜索到的同行内容:\n{_fmt_search("同行内容", data["peers"][:15])}
博主/达人信息:\n{_fmt_search("博主/达人", data["bloggers"][:15])}
最新动态:\n{_fmt_news(data["news"][:10])}
当前热搜趋势:\n{_fmt_trending(data["trending"])}
请输出分析。"""

    async for chunk in _filter_think_tags(chat_deep_stream(
        [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=6000, temperature=0.6,
    )):
        yield content_event(chunk)

    if citations.citations:
        yield sources_event(citations.to_list())


async def _stream_idea(domain: str, context: str, history: list[dict]) -> AsyncIterator[str]:
    yield thinking_event("并行搜索", f"搜索「{domain}」灵感素材...", progress=15, agents=[
        {"name": "同行内容", "status": "running"},
        {"name": "最新动态", "status": "running"},
        {"name": "热搜趋势", "status": "running"},
    ])

    data = await search_parallel_idea(domain)

    yield thinking_event("搜索完成", f"找到 {len(data['peers'])} 条内容参考", progress=50, agents=[
        {"name": "同行内容", "status": "done", "count": len(data["peers"])},
        {"name": "最新动态", "status": "done", "count": len(data["news"])},
        {"name": "热搜趋势", "status": "done", "count": len(data["trending"])},
    ])

    citations = CitationList()
    citations.add_from_search(data["peers"][:15])
    citations.add_from_search(data["news"][:10])

    yield thinking_event("AI 创意", f"AI 正在为「{domain}」生成选题灵感...", progress=60)

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
- **推荐平台**: 视频号/公众号/小红书（说明为什么适合该平台）
- **灵感来源**: 搜索数据中的哪条启发了你

最后推荐 TOP 3 最值得做的选题，说明理由。

要求：标题要像真正的爆款标题。覆盖不同角度和形式。优先考虑视频号和微信公众号的内容偏好。"""

    user_msg = f"""领域: {domain}
{f'用户补充: {context}' if context else ''}
搜索数据:\n{_fmt_search("同行内容", data["peers"][:15])}
最新动态:\n{_fmt_news(data["news"][:10])}
热搜趋势:\n{_fmt_trending(data["trending"])}
{f'之前的领域分析: {prev_context[:1000]}' if prev_context else ''}
请生成选题灵感。"""

    async for chunk in _filter_think_tags(chat_deep_stream(
        [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=6000, temperature=0.8,
    )):
        yield content_event(chunk)

    if citations.citations:
        yield sources_event(citations.to_list())


async def _stream_predict(topic: str, domain: str, platform: str, history: list[dict]) -> AsyncIterator[str]:
    yield thinking_event("搜索竞品", f"搜索「{topic}」竞品数据...", progress=15, agents=[
        {"name": "竞品分析", "status": "running"},
        {"name": "热搜趋势", "status": "running"},
    ])

    data = await search_parallel_predict(topic)
    citations = CitationList()
    citations.add_from_search(data["competition"][:10])

    yield thinking_event("搜索完成", f"找到 {len(data['competition'])} 条竞品内容", progress=50, agents=[
        {"name": "竞品分析", "status": "done", "count": len(data["competition"])},
        {"name": "热搜趋势", "status": "done", "count": len(data["trending"])},
    ])

    comp_text = "\n".join(
        f"- 【{r.title}】{r.snippet[:120]}\n  {r.url}"
        for r in data["competition"][:10]
    ) or "（未找到直接竞品）"

    yield thinking_event("AI 评估", f"12维度深度评估「{topic}」的爆款潜力...", progress=60)

    system_msg = """你是 Ripple — 一位数据驱动的内容分析师。用12维度模型评估选题的爆款潜力。

分析框架：**8个基础维度 + 影视飓风HKRR模型4维度**

对每个维度给出：分数(0-100) + 一句话理由 + 提升建议

输出格式：

## 选题评估：「标题」

### 综合评分：XX/100

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
（3条具体建议）

### 最终判断
（强烈推荐 / 值得做 / 需调整 / 不建议）+ 理由

要求：引用竞品数据作为证据。重点分析在视频号和微信公众号上的表现预测。"""

    user_msg = f"""选题: {topic}
领域: {domain or '综合'}
目标平台: {platform}
竞品搜索数据:\n{comp_text}
请输出完整评估报告。"""

    async for chunk in _filter_think_tags(chat_deep_stream(
        [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=6000, temperature=0.3,
    )):
        yield content_event(chunk)

    if citations.citations:
        yield sources_event(citations.to_list())


async def _stream_create(topic: str, domain: str, platform: str, history: list[dict]) -> AsyncIterator[str]:
    yield thinking_event("准备创作", f"为「{topic}」准备内容创作...", progress=15)

    prev_context = ""
    for h in reversed(history):
        if h["role"] == "assistant" and len(h["content"]) > 200:
            prev_context = h["content"][:2000]
            break

    yield thinking_event("AI 创作", f"正在生成「{topic}」的完整内容包...", progress=30)

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

### 视频号版
（短文案100-200字，适合口播，利用微信社交传播优势）

### 微信公众号版
（完整长文，重新排版，适合深度阅读和转发）

### 小红书版
（emoji风格，种草语气，带标签）

### 抖音版
（超短文案50-100字，开头即高潮）

## AI 点映团评审
### 路人会怎么看？
### 同行会怎么看？
### 综合评分与改进建议

写作要求：用真实品牌名。每300字有一个爽点。每个平台版本独立撰写。"""

    user_msg = f"""选题: {topic}
领域: {domain or '综合'}
目标平台: {platform}
{f'之前的分析: {prev_context[:1500]}' if prev_context else ''}
请输出完整内容包。"""

    async for chunk in _filter_think_tags(chat_deep_stream(
        [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=8192, temperature=0.7,
    )):
        yield content_event(chunk)


async def _stream_distill(blogger: str, domain: str, history: list[dict]) -> AsyncIterator[str]:
    yield thinking_event("搜索博主", f"搜索「{blogger}」的内容和风格...", progress=15, agents=[
        {"name": "内容样本", "status": "running"},
        {"name": "博主资料", "status": "running"},
    ])

    data = await search_parallel_distill(blogger)
    citations = CitationList()
    citations.add_from_search(data["content"])
    citations.add_from_search(data["profile"])

    yield thinking_event("搜索完成", f"找到 {len(data['content'])} 条内容样本", progress=50, agents=[
        {"name": "内容样本", "status": "done", "count": len(data["content"])},
        {"name": "博主资料", "status": "done", "count": len(data["profile"])},
    ])

    yield thinking_event("AI 蒸馏", f"正在蒸馏「{blogger}」的创作方法论...", progress=60)

    system_msg = """你是 Ripple — 一位资深内容策划与写作教练。你的任务是"蒸馏"一位博主的创作方法论。

蒸馏 ≠ 抄袭。你要提炼的是可复用的创作框架，包含五个层级：

## 博主画像
（一段话介绍这位博主是谁、做什么领域、核心风格）

## 表达 DNA
- 语气特征、常用句式和节奏、emoji 使用习惯、标点符号风格、用词偏好

## 心智模型
- 如何看待自己的领域和受众
- 认知框架和思维方式

## 决策启发式
- 选题判断规则和优先级
- 追热点的方式和话题切入角度

## 反模式与边界
- 什么内容不做、价值底线
- 能力局限的诚实声明

## 可复用的创作清单
（基于以上分析，给出一个新手可以直接套用的创作检查清单）

要求：基于搜索到的内容分析。如果数据有限，诚实说明哪些是推断。"""

    user_msg = f"""博主: {blogger}
领域: {domain or '未知'}
搜索到的内容样本:\n{_fmt_search("内容样本", data["content"][:10])}
博主资料:\n{_fmt_search("博主资料", data["profile"][:5])}
请输出风格蒸馏报告。"""

    async for chunk in _filter_think_tags(chat_deep_stream(
        [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=6000, temperature=0.5,
    )):
        yield content_event(chunk)

    if citations.citations:
        yield sources_event(citations.to_list())


async def _stream_chat(message: str, history: list[dict]) -> AsyncIterator[str]:
    system_msg = """你是 Ripple — KOC 内容灵感助手，帮想成为 KOC 的新手完成从选题到创作的全流程。

你的语气：像一位热心的学姐/学长，亲和、专业、接地气。

你能做什么：
- 分析某个领域的内容生态（告诉我一个领域，如"美食探店"）
- 帮想选题点子（如"帮我想10个职场效率类选题"）
- 评估某个选题能不能火（如"帮我评估这个选题的爆款潜力"）
- 直接帮写内容（视频号/微信公众号/小红书/抖音都行）
- 分析某位博主的创作风格（蒸馏方法论）

如果用户不知道要做什么，主动引导：先聊聊感兴趣的领域 → 看看同行 → 想选题 → 评估 → 出内容。

直接输出回答，不要输出任何思考过程。"""

    messages = [{"role": "system", "content": system_msg}]
    for h in history[-20:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    async for chunk in _filter_think_tags(chat_deep_stream(messages, max_tokens=4096, temperature=0.7)):
        yield content_event(chunk)
