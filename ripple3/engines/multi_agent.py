"""Multi-agent prediction engine — 7 specialized agents discuss in parallel.

Orchestrates multiple AI agent personas that independently analyze a topic
in parallel (asyncio.gather), then engage in a structured cross-discussion,
followed by an arbiter and audience judge for final consensus prediction.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from core.llm import chat, chat_stream, chat_deep_stream
from core.intent import _filter_think_tags

log = logging.getLogger(__name__)


@dataclass
class AgentPersona:
    id: str
    name: str
    role: str
    emoji: str
    system_prompt: str
    color: str


AGENTS = [
    AgentPersona(
        id="analyst",
        name="数据分析师",
        role="从数据和趋势角度分析",
        emoji="📊",
        color="#6366f1",
        system_prompt="""你是一位资深数据分析师。你的分析风格：
- 用数据说话，关注具体数字和趋势
- 分析搜索量、竞争度、增长率等量化指标
- 对比历史数据，找出规律
- 语气专业但简洁，每次发言 200-300 字
- 直接给出你的判断和依据
- 最后用一个词总结你的态度：看好/中立/谨慎""",
    ),
    AgentPersona(
        id="creator",
        name="内容策划师",
        role="从创意和内容质量角度评估",
        emoji="🎨",
        color="#ec4899",
        system_prompt="""你是一位顶级内容策划师。你的分析风格：
- 关注内容的创意性、差异化和可执行性
- 评估标题吸引力、Hook 设计、叙事结构
- 提供具体的内容优化建议
- 语气生动有趣，善用比喻
- 每次发言 200-300 字，直接给结论
- 最后用一个词总结你的态度：看好/中立/谨慎""",
    ),
    AgentPersona(
        id="psychologist",
        name="用户心理专家",
        role="从受众心理和传播角度分析",
        emoji="🧠",
        color="#f59e0b",
        system_prompt="""你是一位用户心理学专家。你的分析风格：
- 分析目标受众的心理需求和行为模式
- 评估内容的情绪共鸣度和分享动机
- 关注用户痛点、好奇心、社交货币
- 预测用户看到内容后的反应
- 每次发言 200-300 字，洞察深刻
- 最后用一个词总结你的态度：看好/中立/谨慎""",
    ),
    AgentPersona(
        id="operator",
        name="平台运营专家",
        role="从平台算法和分发角度评估",
        emoji="⚙️",
        color="#10b981",
        system_prompt="""你是一位社媒平台运营专家。你的分析风格：
- 深谙各平台算法推荐机制
- 评估内容在不同平台的分发潜力
- 关注发布时间、标签策略、互动设计
- 分析平台流量池机制和冷启动策略
- 每次发言 200-300 字，实操导向
- 最后用一个词总结你的态度：看好/中立/谨慎""",
    ),
    AgentPersona(
        id="risk",
        name="风险评估师",
        role="从风险和可持续性角度审视",
        emoji="🛡️",
        color="#ef4444",
        system_prompt="""你是一位内容风控专家。你的分析风格：
- 识别内容合规风险、舆论争议风险
- 评估话题的时效性和可持续性
- 关注过度承诺、误导、侵权等问题
- 提供风险缓解建议
- 每次发言 200-300 字，审慎客观
- 最后用一个词总结你的态度：看好/中立/谨慎""",
    ),
    AgentPersona(
        id="industry",
        name="行业研究员",
        role="从行业趋势和竞争格局角度分析",
        emoji="🔬",
        color="#8b5cf6",
        system_prompt="""你是一位行业研究员，擅长宏观趋势洞察。你的分析风格：
- 从行业发展阶段和竞争格局切入
- 对比国内外类似内容的表现
- 评估赛道天花板和增长空间
- 关注供给侧和需求侧的匹配度
- 每次发言 200-300 字，视野宏观
- 最后用一个词总结你的态度：看好/中立/谨慎""",
    ),
    AgentPersona(
        id="audience",
        name="用户代言人",
        role="模拟真实用户视角给出反馈",
        emoji="👤",
        color="#06b6d4",
        system_prompt="""你是一位普通用户的代言人，代表真实受众发声。你的分析风格：
- 用普通人的语言评价，不说行业黑话
- "作为一个刷小红书/B站的人，我会不会停下来看这个？"
- 关注内容是否有用、是否有趣、是否值得转发
- 评估"第一眼吸引力"和"看完后的感受"
- 每次发言 200-300 字，真实接地气
- 最后用一个词总结你的态度：看好/中立/谨慎""",
    ),
]

ARBITER_SYSTEM = """你是多 Agent 讨论的首席仲裁者。根据 7 位专家的讨论意见，逐步分析并给出最终综合评估。

请先展示你的思考过程，然后输出严格 JSON。

思考过程要求：
1. 逐一总结每位专家的核心观点和态度
2. 找出共识点和分歧点
3. 权衡各方意见，说明你的评分逻辑

最终输出格式（严格 JSON）：
{
  "total_score": 75,
  "verdict": "值得做",
  "summary": "一段话总结各方观点和最终结论",
  "dimensions": [
    {"name": "话题热度", "score": 80},
    {"name": "竞争蓝海", "score": 70},
    {"name": "情绪共鸣", "score": 85},
    {"name": "实用价值", "score": 75},
    {"name": "标题吸引力", "score": 80},
    {"name": "平台适配", "score": 70},
    {"name": "原创空间", "score": 65},
    {"name": "时效窗口", "score": 60}
  ],
  "hkrr": [
    {"name": "H-快乐度", "score": 70},
    {"name": "K-知识量", "score": 80},
    {"name": "R-共鸣感", "score": 85},
    {"name": "R-节奏感", "score": 75}
  ],
  "key_risks": ["风险1", "风险2"],
  "action_items": ["建议1", "建议2", "建议3"]
}"""


async def _run_agent_round1(
    agent: AgentPersona,
    discussion_prompt: str,
) -> tuple[AgentPersona, str]:
    """Run a single agent's first-round analysis. Returns (agent, content)."""
    messages = [
        {"role": "system", "content": agent.system_prompt},
        {"role": "user", "content": discussion_prompt},
    ]
    resp = await chat(messages, temperature=0.7, max_tokens=800)
    from core.intent import _filter_think_content
    content = _filter_think_content(resp.content)
    return agent, content


async def run_multi_agent_discussion(
    topic: str,
    domain: str,
    platform: str,
    search_context: str,
) -> AsyncIterator[dict]:
    """Orchestrate a multi-agent discussion about a topic.

    Phase 1: All agents analyze in PARALLEL (asyncio.gather)
    Phase 2: Cross-discussion with awareness of others' opinions
    Phase 3: Arbiter streams thinking process, then outputs score

    Yields dicts with structure:
        {"type": "agent_start", "agent": {...}}
        {"type": "agent_speak", "agent": {...}, "content": "...", "round": 1}
        {"type": "arbiter_thinking", "content": "..."}
        {"type": "arbiter_result", "data": {...}}
    """
    discussion_prompt = f"""讨论主题: 评估选题「{topic}」的爆款潜力
领域: {domain or '综合'}
目标平台: {platform or '小红书'}

参考数据:
{search_context[:4000]}

请从你的专业角度，深入分析这个选题的优势和劣势，给出你的判断。"""

    for agent in AGENTS:
        yield {
            "type": "agent_start",
            "agent": {"id": agent.id, "name": agent.name, "emoji": agent.emoji, "color": agent.color},
        }

    tasks = [_run_agent_round1(agent, discussion_prompt) for agent in AGENTS]
    round1_results = await asyncio.gather(*tasks, return_exceptions=True)

    all_opinions: list[str] = []
    for result in round1_results:
        if isinstance(result, Exception):
            log.warning("Agent round 1 failed: %s", result)
            continue
        agent, content = result
        all_opinions.append(f"{agent.emoji} {agent.name}: {content}")
        yield {
            "type": "agent_speak",
            "agent": {"id": agent.id, "name": agent.name, "emoji": agent.emoji, "color": agent.color},
            "content": content,
            "round": 1,
        }

    round2_context = "\n\n".join(all_opinions)

    async def _run_agent_round2(agent: AgentPersona) -> tuple[AgentPersona, str]:
        rebuttal_prompt = f"""以下是第一轮各位专家的意见：

{round2_context}

现在是第二轮讨论。请针对其他专家的观点：
1. 明确指出你赞同或反对谁的观点（点名）
2. 补充你的新洞察
3. 给出最终建议
保持 150-200 字。最后用一个词总结态度：看好/中立/谨慎"""

        messages = [
            {"role": "system", "content": agent.system_prompt},
            {"role": "user", "content": rebuttal_prompt},
        ]
        resp = await chat(messages, temperature=0.6, max_tokens=500)
        from core.intent import _filter_think_content
        content = _filter_think_content(resp.content)
        return agent, content

    round2_tasks = [_run_agent_round2(agent) for agent in AGENTS]
    round2_results = await asyncio.gather(*round2_tasks, return_exceptions=True)

    for result in round2_results:
        if isinstance(result, Exception):
            continue
        agent, content = result
        all_opinions.append(f"{agent.emoji} {agent.name}（第二轮）: {content}")
        yield {
            "type": "agent_speak",
            "agent": {"id": agent.id, "name": agent.name, "emoji": agent.emoji, "color": agent.color},
            "content": content,
            "round": 2,
        }

    yield {"type": "arbiter_start"}

    arbiter_prompt = f"""选题: {topic}
领域: {domain or '综合'}
平台: {platform or '小红书'}

专家讨论记录:
{chr(10).join(all_opinions)}

请先展示你的思考过程（逐一分析每位专家的观点），然后给出最终 JSON 评估。"""

    arbiter_messages = [
        {"role": "system", "content": ARBITER_SYSTEM},
        {"role": "user", "content": arbiter_prompt},
    ]

    arbiter_full = ""
    async for chunk in _filter_think_tags(chat_deep_stream(arbiter_messages, temperature=0.2, max_tokens=4000)):
        arbiter_full += chunk
        yield {"type": "arbiter_thinking", "content": arbiter_full}

    try:
        from core.llm import _extract_json
        result = _extract_json(arbiter_full)
        yield {"type": "arbiter_result", "data": _validate_arbiter(result)}
    except Exception as exc:
        log.warning("Arbiter JSON parse failed: %s", exc)
        yield {
            "type": "arbiter_result",
            "data": {
                "total_score": 70,
                "verdict": "需进一步分析",
                "summary": arbiter_full[:500] if arbiter_full else "专家意见尚未达成完全共识，建议进一步调研。",
                "dimensions": [{"name": d, "score": 70} for d in ["话题热度", "竞争蓝海", "情绪共鸣", "实用价值", "标题吸引力", "平台适配", "原创空间", "时效窗口"]],
                "hkrr": [{"name": d, "score": 70} for d in ["H-快乐度", "K-知识量", "R-共鸣感", "R-节奏感"]],
                "key_risks": [],
                "action_items": [],
            },
        }


def _validate_arbiter(data: dict | list) -> dict:
    if isinstance(data, list):
        data = data[0] if data else {}

    data.setdefault("total_score", 70)
    data.setdefault("verdict", "需进一步分析")
    data.setdefault("summary", "")
    data.setdefault("dimensions", [])
    data.setdefault("hkrr", [])
    data.setdefault("key_risks", [])
    data.setdefault("action_items", [])

    return data


# ── Feature-specific agent presets ────────────────────────────────────────────

RADAR_AGENTS = [
    AgentPersona(
        id="data_analyst", name="数据分析师", role="数据和趋势分析", emoji="📊", color="#6366f1",
        system_prompt="""你是数据分析师，从搜索数据中提取关键趋势和数字洞察。
要求：
- 必须引用搜索数据中的具体内容作为证据（标注编号如"数据#3"）
- 用数字说话：提及具体的数量、比例、趋势方向
- 如果数据不足以支撑结论，明确说"基于有限数据推测"
每次发言200-300字。""",
    ),
    AgentPersona(
        id="content_planner", name="内容策划师", role="内容策划建议", emoji="🎨", color="#ec4899",
        system_prompt="""你是内容策划师，评估领域内容形式和创作机会。
要求：
- 引用搜索数据中看到的实际内容案例
- 提出具体可执行的内容方向（不要泛泛而谈）
- 评估每个方向的难度和预期效果
每次发言200-300字。""",
    ),
    AgentPersona(
        id="platform_expert", name="平台运营专家", role="平台策略", emoji="⚙️", color="#10b981",
        system_prompt="""你是平台运营专家，精通各平台算法推荐机制。
你掌握的核心知识：
- 小红书CES评分: 关注×8 + 评论×4 + 转发×4 + 收藏×1 + 点赞×1
- 流量池阶梯: 冷启动(100-500曝光,CTR>=3%) → 初级(1k-5k) → 热门(1w+)
- 搜索流量占比已达50%，搜索转化率是推荐的4.1倍
要求：
- 基于搜索数据分析各平台的流量分布
- 给出具体的发布策略（时间、标签、互动设计）
每次发言200-300字。""",
    ),
]

IDEA_AGENTS = [
    AgentPersona(
        id="creative", name="创意人", role="创意发散", emoji="💡", color="#f59e0b",
        system_prompt="你是创意总监，善于发散性思考，提出大胆、有趣的选题创意。每次发言200-300字。",
    ),
    AgentPersona(
        id="risk_guard", name="风控人", role="风险把控", emoji="🛡️", color="#ef4444",
        system_prompt="你是风控专家，评估每个选题的合规风险和可执行性。选题既要有创意又要安全。每次发言200-300字。",
    ),
]

CREATE_AGENTS = [
    AgentPersona(
        id="passerby_1", name="路人甲", role="年轻白领视角", emoji="👩‍💼", color="#6366f1",
        system_prompt="你是一位25岁的城市白领，日常刷小红书和抖音。评价内容时从'第一眼吸引力'和'实用性'出发。150字以内。",
    ),
    AgentPersona(
        id="passerby_2", name="路人乙", role="大学生视角", emoji="🧑‍🎓", color="#ec4899",
        system_prompt="你是一位20岁的大学生，重度B站和小红书用户。评价内容时关注'是否有趣'和'会不会转发'。150字以内。",
    ),
    AgentPersona(
        id="passerby_3", name="路人丙", role="宝妈视角", emoji="👩‍👦", color="#f59e0b",
        system_prompt="你是一位30岁的宝妈，常看微信公众号和视频号。评价内容时关注'是否实用'和'适不适合分享到妈妈群'。150字以内。",
    ),
]

DISTILL_AGENTS = [
    AgentPersona(
        id="linguist", name="语言学家", role="语言风格解构", emoji="📖", color="#8b5cf6",
        system_prompt="你是语言学专家，分析博主的用词习惯、句式结构、修辞手法和表达DNA。200字以内。",
    ),
    AgentPersona(
        id="psychologist", name="心理学家", role="心理动机分析", emoji="🧠", color="#f59e0b",
        system_prompt="你是心理学家，分析博主的创作动机、与受众的心理契约、情感连接方式。200字以内。",
    ),
]


async def run_feature_agents(
    feature: str,
    context: str,
    search_data: str,
) -> AsyncIterator[dict]:
    """Run feature-specific multi-agent discussion (lighter than predict's full debate).

    Features: radar, idea, create, distill
    Yields the same event format as run_multi_agent_discussion.
    Ripple 6.0: Increased data input to 5000 chars, added evidence citation requirement.
    """
    agent_map = {
        "radar": RADAR_AGENTS,
        "idea": IDEA_AGENTS,
        "create": CREATE_AGENTS,
        "distill": DISTILL_AGENTS,
    }

    agents = agent_map.get(feature, RADAR_AGENTS)

    prompt = f"""讨论主题: {context}

参考数据（请引用具体编号作为证据）:
{search_data[:5000]}

要求：
1. 必须引用上述数据中的具体内容作为你的论据
2. 如果数据中没有支撑你观点的证据，明确说明这是推测
3. 给出具体可执行的建议，不要泛泛而谈"""

    for agent in agents:
        yield {
            "type": "agent_start",
            "agent": {"id": agent.id, "name": agent.name, "emoji": agent.emoji, "color": agent.color},
        }

    tasks = [_run_agent_round1(agent, prompt) for agent in agents]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            log.warning("Feature agent failed: %s", result)
            continue
        agent, content = result
        yield {
            "type": "agent_speak",
            "agent": {"id": agent.id, "name": agent.name, "emoji": agent.emoji, "color": agent.color},
            "content": content,
            "round": 1,
        }
