"""API routes — SSE streaming endpoints with knowledge graph, multi-agent, and memory."""

from __future__ import annotations

import json
import logging
import traceback
from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.sse import (
    sse_event,
    thinking_event,
    content_event,
    sources_event,
    graph_event,
    score_event,
    agent_speak_event,
    agent_start_event,
    arbiter_thinking_event,
    search_stats_event,
    data_warning_event,
    done_event,
    error_event,
    token_usage_event,
    viral_score_event,
    reflection_event,
    deep_research_event,
    wechat_strategy_event,
    koc_growth_event,
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
from engines.graph_builder import build_knowledge_graph
from engines.multi_agent import run_multi_agent_discussion, run_feature_agents

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    session: dict = {}
    conversation_id: str = ""


class GraphExpandRequest(BaseModel):
    node_id: str
    node_name: str
    node_type: str
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


@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    messages = await store.load_conversation(conv_id)
    if messages is None:
        return {"error": "not found"}
    return {"id": conv_id, "messages": messages}


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    await store.delete_conversation(conv_id)
    return {"ok": True}


# ── Memory ────────────────────────────────────────────────────────────────────

@router.get("/memory")
async def get_memory():
    memory = await store.get_all_memory()
    return {"memory": memory}


@router.post("/memory")
async def update_memory(req: Request):
    data = await req.json()
    for key, value in data.items():
        await store.set_pref(key, value)
    return {"ok": True}


# ── Hot trends ────────────────────────────────────────────────────────────────

@router.get("/trends")
async def get_trends():
    try:
        from adapters.hot_trends import fetch_all_trends
        trends = await fetch_all_trends(limit_per_platform=10)
        result = {}
        for platform, items in trends.items():
            result[platform] = [
                {"title": t.title, "hot_value": t.hot_value, "platform": t.platform, "rank": t.rank}
                for t in items
            ]
        return {"trends": result}
    except Exception as exc:
        log.warning("Trends fetch failed: %s", exc)
        return {"trends": {}, "error": str(exc)}


# ── Graph expand ──────────────────────────────────────────────────────────────

@router.post("/graph/expand")
async def graph_expand(req: GraphExpandRequest):
    """Expand a knowledge graph node — search for more related entities."""
    async def generate() -> AsyncIterator[str]:
        try:
            yield thinking_event("搜索关联内容", f"正在搜索「{req.node_name}」的关联信息...", progress=10)

            from adapters.search import search_parallel_distill, _fan_out_search
            queries = [
                f"{req.node_name} {req.domain} 相关内容",
                f"{req.node_name} 详细介绍 分析",
                f"{req.node_name} 最新动态",
            ]
            if req.node_type == "person":
                queries.extend([
                    f"{req.node_name} 博主 粉丝 作品",
                    f"{req.node_name} 代表作 爆款",
                ])
            elif req.node_type == "topic":
                queries.extend([
                    f"{req.node_name} 热度 趋势",
                    f"{req.node_name} 竞争 分析",
                ])

            results = await _fan_out_search(queries, max_per_query=10)

            yield thinking_event("搜索完成", f"找到 {len(results)} 条关联内容", progress=50)

            search_data = {"peers": results, "bloggers": [], "news": [], "trending": []}
            graph = await build_knowledge_graph(
                f"{req.node_name}（{req.domain}）",
                search_data,
                max_nodes=20,
            )

            yield graph_event(graph["nodes"], graph["links"])
            yield thinking_event("完成", "关联图谱已生成", progress=100)
            yield done_event(intent="graph_expand")

        except Exception as exc:
            log.error("Graph expand error: %s", exc)
            yield error_event(f"展开失败: {exc}")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


# ── Unified chat endpoint ─────────────────────────────────────────────────────

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    async def generate() -> AsyncIterator[str]:
        try:
            message = req.message.strip()
            if not message:
                yield error_event("消息不能为空")
                return

            conv_id = req.conversation_id or store.new_conversation_id()
            yield thinking_event("解析意图", f"理解「{message[:40]}」...", progress=5)

            plain_history = [
                {"role": m["role"], "content": m["content"]}
                for m in req.history[-20:]
            ]

            memory_context = await store.get_pref("memory_summary", "")

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
                async for chunk in _stream_radar(domain, plain_history, memory_context):
                    yield chunk
            elif intent.intent == "idea" and domain:
                async for chunk in _stream_idea(domain, message, plain_history, memory_context):
                    yield chunk
            elif intent.intent == "predict" and topic:
                async for chunk in _stream_predict(topic, domain, platform, plain_history, memory_context):
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
                async for chunk in _stream_chat(message, plain_history, memory_context):
                    yield chunk

            await _save_conversation(conv_id, message, domain, plain_history)
            await _update_memory(domain, topic, intent.intent)

            next_steps = _generate_next_steps(intent.intent, domain, topic)
            yield done_event(intent=intent.intent, domain=domain, topic=topic, conversation_id=conv_id, next_steps=next_steps)

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

def _generate_next_steps(intent: str, domain: str, topic: str) -> list[dict]:
    """Generate contextual next-step suggestions based on completed intent."""
    steps = []
    if intent == "radar":
        steps = [
            {"label": "帮我想选题", "prompt": f"帮我想10个{domain}相关的选题灵感"},
            {"label": "评估选题", "prompt": f"帮我评估一个{domain}领域的选题"},
            {"label": "分析博主", "prompt": f"帮我分析{domain}领域的头部博主风格"},
        ]
    elif intent == "idea":
        if topic:
            steps = [
                {"label": "评估这个选题", "prompt": f"帮我评估「{topic}」这个选题的爆款潜力"},
                {"label": "开始创作", "prompt": f"帮我写一篇关于「{topic}」的内容"},
                {"label": "换个方向", "prompt": f"帮我想更多{domain}的选题灵感"},
            ]
        else:
            steps = [
                {"label": "评估选题", "prompt": f"帮我评估一个{domain}领域的选题"},
                {"label": "深入分析", "prompt": f"帮我分析{domain}领域的内容生态"},
            ]
    elif intent == "predict":
        steps = [
            {"label": "开始创作", "prompt": f"帮我写一篇关于「{topic}」的内容"},
            {"label": "换个选题", "prompt": f"帮我想10个{domain or ''}相关的选题灵感"},
            {"label": "分析竞品", "prompt": f"帮我分析做「{topic}」的竞品博主"},
        ]
    elif intent == "create":
        steps = [
            {"label": "评估爆款潜力", "prompt": f"帮我评估「{topic}」这个选题的爆款潜力"},
            {"label": "换个角度写", "prompt": f"帮我用不同角度重新写「{topic}」"},
            {"label": "想更多选题", "prompt": f"帮我想更多{domain}的选题灵感"},
        ]
    elif intent == "distill":
        steps = [
            {"label": "学习风格写作", "prompt": f"帮我用这位博主的风格写一篇{domain}的内容"},
            {"label": "探索领域", "prompt": f"帮我分析{domain}领域的内容生态"},
        ]
    else:
        steps = [
            {"label": "评估选题", "prompt": f"帮我评估「{topic or '这个话题'}」这个选题的爆款潜力"},
            {"label": "深入分析", "prompt": f"帮我深入分析一下{domain or '这个领域'}的内容生态"},
            {"label": "帮我写内容", "prompt": f"帮我写一篇关于{topic or '这个话题'}的小红书笔记"},
        ]
    return steps


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


async def _stream_radar(domain: str, history: list[dict], memory: str) -> AsyncIterator[str]:
    """Slim radar pipeline: search → graph → report. Target: 30-60s."""
    import time as _time
    _start_time = _time.time()

    # Step 1: Fast parallel search (3-5 engines, 10s timeout)
    yield thinking_event("搜索中", f"正在从多个引擎搜索「{domain}」...", progress=10)

    from adapters.search import search_fast
    search_data = await search_fast(domain)
    results = search_data["results"]
    engine_stats = search_data["engine_stats"]
    total = len(results)

    yield search_stats_event(total, total, engine_stats)
    yield thinking_event("搜索完成", f"找到 {total} 条数据，来自 {len(engine_stats)} 个引擎", progress=35)

    if total < 5:
        yield data_warning_event(f"搜索数据较少（仅 {total} 条），分析结果可能不够全面。")

    # Step 2: Build knowledge graph (single pass, 50-80 nodes)
    yield thinking_event("构建知识图谱", "正在分析事物之间的关联...", progress=45)

    import asyncio
    from engines.graph_builder import build_graph_fast
    try:
        graph_data = await asyncio.wait_for(build_graph_fast(domain, results), timeout=30)
        yield graph_event(graph_data["nodes"], graph_data["links"])
    except Exception as exc:
        log.warning("Graph build failed: %s", exc)

    # Step 3: Generate unified report (single LLM call, structured output)
    yield thinking_event("生成报告", "AI 正在综合分析并生成完整方案...", progress=60)

    citations = CitationList()
    citations.add_from_search(results[:30])

    search_text = "\n".join(
        f"{i+1}. 【{r.title}】{r.snippet[:100]}\n   来源: {r.url}"
        for i, r in enumerate(results[:50])
    )

    system_msg = f"""你是 Ripple — AI 内容增长顾问。用户想了解一个领域的内容生态并获得完整的增长方案。
{f'用户记忆: {memory}' if memory else ''}

基于搜索到的 {total} 条数据，输出一份**结构化分析报告**。

## 必须包含的章节（按此顺序输出）：

### 赛道机会评分
用 1-10 分评估这个赛道，说明理由（市场大小、竞争程度、增长趋势）。

### 内容策略
- 差异化定位建议（2-3 条）
- 推荐的内容形式和风格
- 5 个标题建议（附预估点击率）
- 3 个开场 Hook（附预估留存提升）

### 微信生态策略
基于搜一搜 Peoplerank 算法（账号可信度25% + 内容相关性40% + 用户行为35%）给出：
- 视频号：发布时间、关键词布局、完播率优化
- 搜一搜：核心关键词 + 长尾词列表
- 公众号：格式建议

### 30 天行动路径
按周给出具体可执行的计划（D1-D7, D8-D14, D15-D21, D22-D30）。

### 数据来源
列出本次分析使用的数据引擎和数据量。

**要求**：
- 所有观点基于搜索数据，不编造
- 语气亲和专业，像资深顾问
- 如果数据不足明确说明"""

    user_msg = f"领域: {domain}\n\n搜索数据（{total}条）:\n{search_text}"

    async for chunk in _filter_think_tags(chat_deep_stream(
        [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=6000, temperature=0.6,
    )):
        yield content_event(chunk)

    if citations.citations:
        yield sources_event(citations.to_list())

    elapsed_ms = int((_time.time() - _start_time) * 1000)
    yield token_usage_event(search_calls=total, agent_rounds=0, elapsed_ms=elapsed_ms)
    yield done_event()


async def _stream_idea(domain: str, context: str, history: list[dict], memory: str) -> AsyncIterator[str]:
    yield thinking_event("8层搜索矩阵启动", f"跨引擎搜索「{domain}」灵感素材...", progress=15, agents=[
        {"name": "LLM联网搜索", "status": "running"},
        {"name": "搜索API", "status": "running"},
        {"name": "免费搜索库", "status": "running"},
        {"name": "热搜聚合", "status": "running"},
    ])

    data = await search_parallel_idea(domain)
    total = len(data['peers']) + len(data['news']) + len(data['trending'])

    if total < 10:
        yield data_warning_event(f"搜索数据较少（仅 {total} 条），灵感可能有限。")

    yield thinking_event("搜索完成", f"跨引擎共找到 {total} 条灵感素材", progress=50, agents=[
        {"name": "LLM联网搜索", "status": "done"},
        {"name": "搜索API", "status": "done"},
        {"name": "免费搜索库", "status": "done"},
        {"name": "热搜聚合", "status": "done"},
    ])

    citations = CitationList()
    citations.add_from_search(data["peers"][:30])
    citations.add_from_search(data["news"][:20])

    yield thinking_event("创意人 vs 风控人", "创意发散 + 风险把控 对抗讨论...", progress=55)

    agent_context = f"为「{domain}」领域生成选题灵感，{f'用户要求: {context}' if context else ''}"
    agent_data = _fmt_search("搜索数据", data["peers"][:40]) + "\n" + _fmt_trending(data["trending"])
    async for event in run_feature_agents("idea", agent_context, agent_data):
        if event["type"] == "agent_start":
            yield agent_start_event(event["agent"])
        elif event["type"] == "agent_speak":
            yield agent_speak_event(event["agent"], event["content"], round_num=event.get("round", 1))

    yield thinking_event("AI 创意", f"综合专家意见从 {total} 条数据中生成选题灵感...", progress=65)

    prev_context = ""
    for h in reversed(history):
        if h["role"] == "assistant" and len(h["content"]) > 200:
            prev_context = h["content"][:2000]
            break

    system_msg = f"""你是 Ripple — 一位超有创意的内容策划师。帮用户想出10-15个选题点子。
{f'用户偏好: {memory}' if memory else ''}

每个选题格式：
### N. 「标题」
- **为什么值得做**: 一句话说明
- **怎么切入**: 具体角度
- **适合谁看**: 目标受众
- **内容形式**: 图文/视频/清单等
- **推荐平台**: 视频号/公众号/小红书（说明为什么适合该平台）
- **灵感来源**: 搜索数据中的哪条启发了你

最后推荐 TOP 3 最值得做的选题，说明理由。

**严格要求**：标题要像真正的爆款标题。覆盖不同角度和形式。优先考虑视频号和微信公众号。
所有灵感必须基于搜索数据启发，不得凭空编造数据或案例。"""

    user_msg = f"""领域: {domain}
{f'用户补充: {context}' if context else ''}
搜索数据:\n{_fmt_search("同行内容", data["peers"][:30])}
最新动态:\n{_fmt_news(data["news"][:20])}
热搜趋势:\n{_fmt_trending(data["trending"])}
{f'之前的领域分析: {prev_context[:1000]}' if prev_context else ''}
请生成选题灵感。"""

    async for chunk in _filter_think_tags(chat_deep_stream(
        [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=8000, temperature=0.8,
    )):
        yield content_event(chunk)

    if citations.citations:
        yield sources_event(citations.to_list())


async def _stream_predict(topic: str, domain: str, platform: str, history: list[dict], memory: str) -> AsyncIterator[str]:
    import time as _time
    _start_time = _time.time()

    yield thinking_event("9层搜索矩阵启动", f"跨引擎搜索「{topic}」竞品数据...", progress=15, agents=[
        {"name": "MiniMax搜索", "status": "running"},
        {"name": "LLM联网搜索", "status": "running"},
        {"name": "搜索API", "status": "running"},
        {"name": "免费搜索库", "status": "running"},
        {"name": "平台直连", "status": "running"},
    ])

    data = await search_parallel_predict(topic, domain)
    citations = CitationList()
    citations.add_from_search(data["competition"][:30])

    comp_text = "\n".join(
        f"- 【{r.title}】{r.snippet[:150]}\n  {r.url}"
        for r in data["competition"][:40]
    ) or "（未找到直接竞品）"

    total_comp = len(data['competition'])

    if total_comp < 5:
        yield data_warning_event(f"竞品数据较少（仅 {total_comp} 条），评估结果仅供参考。")

    yield thinking_event("搜索完成", f"找到 {total_comp} 条竞品内容", progress=30, agents=[
        {"name": "MiniMax搜索", "status": "done"},
        {"name": "LLM联网搜索", "status": "done"},
        {"name": "搜索API", "status": "done"},
        {"name": "免费搜索库", "status": "done"},
        {"name": "平台直连", "status": "done"},
    ])

    # CES viral scoring
    yield thinking_event("CES爆款评分", f"运行 19维评分模型（{platform or '小红书'}算法模拟）...", progress=35)
    try:
        from engines.viral_scorer import score_viral_potential, format_score_for_display
        from api.sse import viral_score_event
        viral_score = await score_viral_potential(topic, domain, platform or "小红书", comp_text[:2000])
        yield viral_score_event(format_score_for_display(viral_score))
    except Exception as exc:
        log.warning("Viral scoring failed: %s", exc)

    yield thinking_event("7位AI专家讨论", "专家圆桌会议开始，7位AI专家并行分析...", progress=40, agents=[
        {"name": "📊 数据分析师", "status": "running"},
        {"name": "🎨 内容策划师", "status": "running"},
        {"name": "🧠 用户心理专家", "status": "running"},
        {"name": "⚙️ 平台运营专家", "status": "running"},
        {"name": "🛡️ 风险评估师", "status": "running"},
        {"name": "🔬 行业研究员", "status": "running"},
        {"name": "👤 用户代言人", "status": "running"},
    ])

    async for event in run_multi_agent_discussion(topic, domain, platform, comp_text):
        if event["type"] == "agent_start":
            yield agent_start_event(event["agent"])
        elif event["type"] == "agent_speak":
            yield agent_speak_event(event["agent"], event["content"], round_num=event.get("round", 1))
        elif event["type"] == "arbiter_start":
            yield thinking_event("首席仲裁", "仲裁者正在综合各方意见，生成最终评估...", progress=85)
        elif event["type"] == "arbiter_thinking":
            yield arbiter_thinking_event(event["content"])
        elif event["type"] == "arbiter_result":
            yield score_event(event["data"])

    yield thinking_event("生成报告", "正在生成详细分析报告...", progress=90)

    system_msg = f"""你是 Ripple — 一位数据驱动的内容分析师。基于 7 位AI专家的讨论结果，用简洁的语言总结评估。
{f'用户偏好: {memory}' if memory else ''}

请简要总结：
1. 各专家的核心观点（每人1-2句，标注态度）
2. 关键共识和分歧
3. 具体的行动建议（3-5条，要具体可执行）

不需要重复评分表格（已通过可视化展示），重点放在洞察和建议上。控制在 800 字以内。"""

    user_msg = f"""选题: {topic}
领域: {domain or '综合'}
目标平台: {platform}
竞品数据（{total_comp}条）:\n{comp_text}
请输出总结报告。"""

    async for chunk in _filter_think_tags(chat_deep_stream(
        [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=4000, temperature=0.3,
    )):
        yield content_event(chunk)

    if citations.citations:
        yield sources_event(citations.to_list())

    elapsed_ms = int((_time.time() - _start_time) * 1000)
    yield token_usage_event(
        search_calls=total_comp,
        agent_rounds=2,
        elapsed_ms=elapsed_ms,
    )


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

    yield content_event("\n\n---\n\n")
    yield thinking_event("A/B标题模拟", "多用户画像模拟点击行为...", progress=85)

    async for chunk in run_ab_test(topic, domain):
        yield content_event(chunk)

    yield thinking_event("路人评审团", "模拟真实用户的第一反应...", progress=92)

    async for event in run_feature_agents("create", f"评价关于「{topic}」的内容", f"选题: {topic}\n领域: {domain}"):
        if event["type"] == "agent_start":
            yield agent_start_event(event["agent"])
        elif event["type"] == "agent_speak":
            yield agent_speak_event(event["agent"], event["content"], round_num=event.get("round", 1))


async def _stream_distill(blogger: str, domain: str, history: list[dict]) -> AsyncIterator[str]:
    yield thinking_event("8层搜索矩阵启动", f"跨引擎搜索「{blogger}」的内容和风格...", progress=15, agents=[
        {"name": "LLM联网搜索", "status": "running"},
        {"name": "搜索API", "status": "running"},
        {"name": "免费搜索库", "status": "running"},
    ])

    data = await search_parallel_distill(blogger)
    citations = CitationList()
    citations.add_from_search(data["content"])
    citations.add_from_search(data["profile"])
    total = len(data['content']) + len(data['profile'])

    if total < 5:
        yield data_warning_event(f"关于「{blogger}」的数据较少（仅 {total} 条），分析可能不够全面。")

    yield thinking_event("搜索完成", f"找到 {total} 条内容样本", progress=50, agents=[
        {"name": "LLM联网搜索", "status": "done"},
        {"name": "搜索API", "status": "done"},
        {"name": "免费搜索库", "status": "done"},
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

**严格要求**：基于搜索到的内容分析，不得编造不存在的作品或数据。如果数据有限，诚实说明哪些是推断。"""

    user_msg = f"""博主: {blogger}
领域: {domain or '未知'}
搜索到的内容样本:\n{_fmt_search("内容样本", data["content"][:15])}
博主资料:\n{_fmt_search("博主资料", data["profile"][:10])}
请输出风格蒸馏报告。"""

    async for chunk in _filter_think_tags(chat_deep_stream(
        [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=8000, temperature=0.5,
    )):
        yield content_event(chunk)

    yield thinking_event("语言学家+心理学家", "协作解构博主方法论...", progress=90)

    agent_data = _fmt_search("内容样本", data["content"][:10])
    async for event in run_feature_agents("distill", f"分析博主「{blogger}」的创作风格", agent_data):
        if event["type"] == "agent_start":
            yield agent_start_event(event["agent"])
        elif event["type"] == "agent_speak":
            yield agent_speak_event(event["agent"], event["content"], round_num=event.get("round", 1))

    if citations.citations:
        yield sources_event(citations.to_list())


async def _stream_chat(message: str, history: list[dict], memory: str) -> AsyncIterator[str]:
    search_context = ""
    msg_len = len(message)
    has_topic = msg_len > 4 and any(
        kw not in message for kw in ["你好", "谢谢", "嗯", "哦"]
    )

    if has_topic and msg_len > 6:
        yield thinking_event("联网搜索", f"搜索「{message[:30]}」的最新信息...", progress=10)
        try:
            from adapters.minimax_search import minimax_search_multi
            search_results = await minimax_search_multi([message, f"{message} 最新"], max_per_query=10)
            if search_results:
                lines = []
                for i, r in enumerate(search_results[:10], 1):
                    lines.append(f"{i}. 【{r.title}】\n   {r.snippet}\n   来源: {r.url}")
                search_context = "\n".join(lines)
                yield thinking_event("搜索完成", f"找到 {len(search_results)} 条相关信息", progress=30)
        except Exception:
            pass

    system_msg = f"""你是 Ripple — KOC 内容灵感助手，帮想成为 KOC 的新手完成从选题到创作的全流程。
{f'用户记忆: {memory}' if memory else ''}

你的语气：像一位热心的学姐/学长，亲和、专业、接地气。

你能做什么：
- 分析某个领域的内容生态（告诉我一个领域，如"美食探店"）
- 帮想选题点子（如"帮我想10个职场效率类选题"）
- 评估某个选题能不能火（如"帮我评估这个选题的爆款潜力"）
- 直接帮写内容（视频号/微信公众号/小红书/抖音都行）
- 分析某位博主的创作风格（蒸馏方法论）

如果用户不知道要做什么，主动引导：先聊聊感兴趣的领域 → 看看同行 → 想选题 → 评估 → 出内容。

{'以下是实时搜索到的最新信息，请基于这些信息回答用户的问题：' + chr(10) + search_context if search_context else ''}

直接输出回答，不要输出任何思考过程。"""

    messages = [{"role": "system", "content": system_msg}]
    for h in history[-20:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    async for chunk in _filter_think_tags(chat_deep_stream(messages, max_tokens=4096, temperature=0.7)):
        yield content_event(chunk)


# ── Persistence helpers ───────────────────────────────────────────────────────

async def _save_conversation(conv_id: str, message: str, domain: str, history: list[dict]) -> None:
    try:
        title = message[:30] + ("..." if len(message) > 30 else "")
        all_messages = history + [{"role": "user", "content": message}]
        await store.save_conversation(conv_id, title, all_messages, domain)
    except Exception as exc:
        log.warning("Failed to save conversation: %s", exc)


async def _update_memory(domain: str, topic: str, intent: str) -> None:
    try:
        if domain:
            domains = await store.get_pref("explored_domains", "")
            domain_list = [d.strip() for d in domains.split(",") if d.strip()] if domains else []
            if domain not in domain_list:
                domain_list.append(domain)
                await store.set_pref("explored_domains", ",".join(domain_list[-20:]))

        if topic:
            topics = await store.get_pref("recent_topics", "")
            topic_list = [t.strip() for t in topics.split(",") if t.strip()] if topics else []
            if topic not in topic_list:
                topic_list.append(topic)
                await store.set_pref("recent_topics", ",".join(topic_list[-20:]))

        usage = await store.get_pref("usage_count", "0")
        await store.set_pref("usage_count", str(int(usage) + 1))

        summary_parts = []
        domains = await store.get_pref("explored_domains", "")
        if domains:
            summary_parts.append(f"探索过的领域: {domains}")
        topics = await store.get_pref("recent_topics", "")
        if topics:
            summary_parts.append(f"关注的选题: {topics}")
        if summary_parts:
            await store.set_pref("memory_summary", "; ".join(summary_parts))
    except Exception as exc:
        log.warning("Failed to update memory: %s", exc)


# ── WeChat ecosystem strategy ─────────────────────────────────────────────────

async def _generate_wechat_strategy(domain: str, search_data: dict) -> dict:
    """Generate WeChat ecosystem strategies based on domain analysis."""
    from core.llm import chat_json

    sample_content = "\n".join(
        f"- {r.title}" for r in search_data.get("peers", [])[:15]
    )

    messages = [
        {"role": "system", "content": """你是微信生态运营专家，深度掌握搜一搜 Peoplerank 算法和视频号推荐机制。

## 你必须掌握的算法知识：

### 搜一搜排序（Peoplerank）权重分布：
- 账号可信度 25%：认证账号优先、粉丝量、内容垂直度
- 内容相关性 40%：标题/简介/标签/字幕中关键词的完整匹配优先
- 用户行为 35%：完播率、点赞/评论/转发/分享

### 视频号推荐三维排名：
- 内容相关性 40%：关键词完整匹配优先于部分匹配
- 用户行为 35%：24h内完播率>60%自动提升2-3档位
- 账号权重 25%：垂直领域+原创率>=90%+每周>=3条更新

### 关键优化规则：
- 前3行必须嵌入核心关键词+长尾词
- 结尾设置行动指令引导评论
- 24h内回复前20条评论提升活跃度
- 杜绝关键词堆砌，确保封面与内容一致
- 减少频繁删改已发布内容

基于以上算法知识和领域数据，生成四个维度的具体策略。
严格返回JSON（无markdown包裹）：
{
  "videoAccount": {
    "tips": ["基于算法的具体建议（含数据依据）", ...],
    "algorithm": "视频号推荐算法在该领域的具体应用要点",
    "bestPractices": ["基于Peoplerank的最佳发布实践", ...],
    "publishTiming": "最佳发布时间建议（精确到小时）",
    "keywordLayout": ["核心关键词1", "长尾词1", ...],
    "first24hChecklist": ["发布后24h内的具体行动1", ...]
  },
  "officialAccount": {
    "seoKeywords": ["搜一搜高权重SEO关键词", ...],
    "format": "基于Peoplerank最优的图文格式",
    "tips": ["运营建议1", ...],
    "crossPromotion": "互推策略建议"
  },
  "search": {
    "keywords": ["搜一搜核心关键词（按权重排序）", ...],
    "longTailKeywords": ["长尾关键词1", ...],
    "optimization": ["基于Peoplerank的具体优化步骤", ...]
  },
  "privateDomain": {
    "funnelSteps": ["公域→私域的引流步骤", ...],
    "tips": ["私域运营建议", ...],
    "wechatMoments": "朋友圈传播策略"
  }
}
每个维度给出5-8条具体、可操作的建议，必须包含算法依据。"""},
        {"role": "user", "content": f"领域: {domain}\n该领域热门内容样本:\n{sample_content}"},
    ]

    data = await chat_json(messages, temperature=0.5, max_tokens=3000)
    return data


# ── KOC growth plan ───────────────────────────────────────────────────────────

async def _generate_koc_growth_plan(domain: str, search_data: dict) -> dict:
    """Generate a 30-day KOC growth plan based on domain data."""
    from core.llm import chat_json

    messages = [
        {"role": "system", "content": """你是KOC增长策略师。为一个0基础新手创作者制定30天成长计划。
严格返回JSON（无markdown包裹）：
{
  "currentFollowers": 0,
  "targetFollowers": 1000,
  "daysToTarget": 30,
  "growthCurve": [
    {"day": 1, "followers": 0},
    {"day": 7, "followers": 50},
    {"day": 14, "followers": 200},
    {"day": 21, "followers": 500},
    {"day": 30, "followers": 1000}
  ],
  "weeklyPlan": [
    {"week": 1, "focus": "定位+首发", "posts": 5, "target": "完成账号搭建和首批内容"},
    {"week": 2, "focus": "数据复盘", "posts": 5, "target": "找到数据最好的内容方向"},
    {"week": 3, "focus": "爆款冲刺", "posts": 7, "target": "产出1-2条高互动内容"},
    {"week": 4, "focus": "稳定输出", "posts": 7, "target": "形成稳定更新节奏"}
  ],
  "platformBreakdown": [
    {"platform": "小红书", "percentage": 40, "color": "#FF2442"},
    {"platform": "视频号", "percentage": 30, "color": "#07C160"},
    {"platform": "抖音", "percentage": 20, "color": "#000000"},
    {"platform": "公众号", "percentage": 10, "color": "#576B95"}
  ],
  "contentCalendar": [
    {"day": 1, "type": "图文", "topic": "领域入门科普"},
    {"day": 2, "type": "短视频", "topic": "个人经验分享"},
    {"day": 3, "type": "清单", "topic": "XX推荐合集"}
  ]
}
根据具体领域调整策略和内容日历（给出7天的内容日历）。"""},
        {"role": "user", "content": f"领域: {domain}"},
    ]

    data = await chat_json(messages, temperature=0.5, max_tokens=2048)
    return data
