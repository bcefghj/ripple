"""A/B Title Simulator — multi-agent simulation of click behavior.

Generates title variants, then uses multiple agents to simulate
different user demographics' click decisions, outputting simulated CTR.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from core.llm import chat, chat_deep_stream
from core.intent import _filter_think_tags

log = logging.getLogger(__name__)


@dataclass
class UserPersona:
    id: str
    name: str
    emoji: str
    desc: str
    system_prompt: str


PERSONAS = [
    UserPersona(
        id="young_female",
        name="小红书女生",
        emoji="👩",
        desc="22岁大学生，小红书重度用户",
        system_prompt="""你是一位22岁的女大学生，每天刷小红书2小时。你的特点：
- 喜欢颜值高、实用的内容
- 容易被"变美""省钱""效率"相关标题吸引
- 对标题中有数字的内容更感兴趣
- 反感硬广和标题党
请模拟你的真实反应，对每个标题给出：是否会点击(是/否)、点击欲望(1-10)、原因(一句话)。
输出严格JSON数组格式。""",
    ),
    UserPersona(
        id="tech_male",
        name="科技宅",
        emoji="🧑‍💻",
        desc="28岁程序员，B站/知乎用户",
        system_prompt="""你是一位28岁的程序员，主要刷B站和知乎。你的特点：
- 喜欢有深度、有干货的内容
- 对标题里有技术细节的内容更感兴趣
- 反感低质量标题党和情绪化内容
- 看重内容的准确性和逻辑性
请模拟你的真实反应，对每个标题给出：是否会点击(是/否)、点击欲望(1-10)、原因(一句话)。
输出严格JSON数组格式。""",
    ),
    UserPersona(
        id="middle_age",
        name="中年职场人",
        emoji="👔",
        desc="35岁企业管理者，微信/视频号用户",
        system_prompt="""你是一位35岁的企业中层管理者，主要看微信公众号和视频号。你的特点：
- 关注效率、管理、行业趋势
- 喜欢"有洞察力"的内容
- 对实用工具和方法论感兴趣
- 会分享好内容到工作群
请模拟你的真实反应，对每个标题给出：是否会点击(是/否)、点击欲望(1-10)、原因(一句话)。
输出严格JSON数组格式。""",
    ),
    UserPersona(
        id="mom",
        name="年轻宝妈",
        emoji="👩‍👦",
        desc="30岁全职妈妈，抖音/视频号用户",
        system_prompt="""你是一位30岁的全职妈妈，常刷抖音和视频号。你的特点：
- 关注育儿、家庭、生活技巧
- 喜欢正能量、温暖的内容
- 碎片化阅读，标题必须一秒抓住注意力
- 会转发好内容到妈妈群
请模拟你的真实反应，对每个标题给出：是否会点击(是/否)、点击欲望(1-10)、原因(一句话)。
输出严格JSON数组格式。""",
    ),
    UserPersona(
        id="student",
        name="高中生",
        emoji="🎒",
        desc="17岁高中生，抖音/B站用户",
        system_prompt="""你是一位17岁的高中生，主要刷抖音和B站。你的特点：
- 喜欢有趣、搞笑、震撼的内容
- 注意力极短，3秒内决定看不看
- 喜欢meme文化和网络梗
- 反感说教和无聊的内容
请模拟你的真实反应，对每个标题给出：是否会点击(是/否)、点击欲望(1-10)、原因(一句话)。
输出严格JSON数组格式。""",
    ),
]


async def generate_title_variants(topic: str, domain: str = "") -> list[str]:
    """Generate 5-8 title variants using different strategies."""
    messages = [
        {
            "role": "system",
            "content": """你是标题大师。为给定主题生成6个不同策略的标题变体。

策略：
1. 数字型（如"5个方法..."）
2. 悬念型（如"原来...的秘密是..."）
3. 共鸣型（如"为什么我们都..."）
4. 争议型（如"XXX 是骗局吗？"）
5. 教程型（如"手把手教你..."）
6. 对比型（如"A vs B，到底该选哪个？"）

只输出标题，每行一个，不要编号。""",
        },
        {"role": "user", "content": f"主题: {topic}\n领域: {domain or '综合'}"},
    ]

    try:
        resp = await chat(messages, temperature=0.8, max_tokens=500)
        titles = [line.strip() for line in resp.content.strip().split("\n") if line.strip() and len(line.strip()) > 5]
        return titles[:8]
    except Exception as exc:
        log.warning("Title generation failed: %s", exc)
        return [topic]


async def _simulate_persona(persona: UserPersona, titles: list[str]) -> dict:
    """Simulate a single persona's click behavior on all titles."""
    titles_text = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
    messages = [
        {"role": "system", "content": persona.system_prompt},
        {
            "role": "user",
            "content": f"以下是{len(titles)}个标题，请模拟你的点击反应:\n\n{titles_text}\n\n输出JSON数组，每个元素包含 title_index(1-based)、would_click(boolean)、desire(1-10)、reason(string)。",
        },
    ]

    try:
        resp = await chat(messages, temperature=0.6, max_tokens=1500)
        from core.llm import _extract_json
        result = _extract_json(resp.content)
        return {"persona": persona.id, "name": persona.name, "emoji": persona.emoji, "reactions": result}
    except Exception as exc:
        log.warning("Persona %s simulation failed: %s", persona.name, exc)
        return {"persona": persona.id, "name": persona.name, "emoji": persona.emoji, "reactions": []}


async def run_ab_test(topic: str, domain: str = "") -> AsyncIterator[str]:
    """Stream the full A/B title test process."""
    yield f"## A/B 标题模拟器\n\n"
    yield f"正在为「{topic}」生成标题变体...\n\n"

    titles = await generate_title_variants(topic, domain)
    if not titles:
        yield "标题生成失败。"
        return

    yield "### 标题变体\n\n"
    for i, t in enumerate(titles, 1):
        yield f"{i}. **{t}**\n"
    yield "\n"

    yield f"### 用户群模拟 ({len(PERSONAS)} 个用户画像)\n\n"

    tasks = [_simulate_persona(p, titles) for p in PERSONAS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    title_scores: dict[int, list[int]] = {i: [] for i in range(len(titles))}

    for result in results:
        if isinstance(result, Exception):
            continue
        yield f"**{result['emoji']} {result['name']}** ({next((p.desc for p in PERSONAS if p.id == result['persona']), '')})\n\n"
        reactions = result.get("reactions", [])
        if isinstance(reactions, list):
            for r in reactions:
                if isinstance(r, dict):
                    idx = r.get("title_index", 0) - 1
                    desire = r.get("desire", 5)
                    click = "会点" if r.get("would_click") else "不点"
                    reason = r.get("reason", "")
                    if 0 <= idx < len(titles):
                        title_scores[idx].append(desire)
                        yield f"- 标题{idx+1}: {click} ({desire}/10) — {reason}\n"
        yield "\n"

    yield "### 模拟 CTR 排行\n\n"
    yield "| 排名 | 标题 | 模拟CTR | 平均点击欲望 |\n"
    yield "|------|------|---------|-------------|\n"

    rankings = []
    for idx, scores in title_scores.items():
        if scores:
            avg = sum(scores) / len(scores)
            ctr = sum(1 for s in scores if s >= 6) / len(scores) * 100
        else:
            avg = 0
            ctr = 0
        rankings.append((idx, titles[idx] if idx < len(titles) else "", ctr, avg))

    rankings.sort(key=lambda x: x[2], reverse=True)
    for rank, (idx, title, ctr, avg) in enumerate(rankings, 1):
        yield f"| {rank} | {title[:30]}{'...' if len(title) > 30 else ''} | {ctr:.0f}% | {avg:.1f}/10 |\n"

    yield f"\n**推荐标题**: {rankings[0][1]}\n" if rankings else ""
