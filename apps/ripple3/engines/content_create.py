"""Content Create — two-step creation + AI screening team.

Step 1: Generate detailed outline (user can review/adjust)
Step 2: Write full content based on outline + style skill
Step 3: AI screening team evaluates the content (like 影视飓风's AI点映团)
Step 4: Multi-platform adaptation + cover image generation
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path

from core.config import CONTENT_DIR
from core.llm import chat_json, chat_deep_json, chat_deep_stream, chat_deep
from core.image_gen import generate_image
from core import store
from engines.style_distill import StyleSkill

log = logging.getLogger(__name__)


@dataclass
class PlatformContent:
    platform: str
    title: str
    body: str
    tags: list[str] = field(default_factory=list)


@dataclass
class ContentOutline:
    hook: str
    sections: list[dict]
    emotion_curve: str
    key_data_points: list[str]
    call_to_action: str


@dataclass
class ScreeningResult:
    passerby_review: str
    peer_review: str
    overall_score: int
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]


@dataclass
class ContentPackage:
    topic: str
    candidate_titles: list[str]
    body: str
    outline: ContentOutline | None = None
    screening: ScreeningResult | None = None
    cover_prompt: str = ""
    cover_paths: list[Path] = field(default_factory=list)
    platform_versions: list[PlatformContent] = field(default_factory=list)


# ── Step 1: Outline Generation ──────────────────────────────────────────────

_OUTLINE_SYSTEM = """你是一位资深内容策划专家。你的任务是为选题生成详细的内容大纲。

大纲必须包含：
1. **hook**: 开头Hook（前3句话的设计，必须在3秒内抓住注意力）
2. **sections**: 内容段落数组，每段包含:
   - heading: 段落标题
   - core_point: 核心论点（1句话）
   - details: 需要展开的具体内容（包括案例、数据、故事）
   - emotion: 这段想唤起的情绪（好奇/共鸣/惊讶/认同/实用感/期待...）
3. **emotion_curve**: 情绪曲线描述（如"好奇→共鸣→惊讶→实用→温暖"）
4. **key_data_points**: 文中需要用到的关键数据/案例/事实
5. **call_to_action**: 结尾的行动号召（互动引导）

参考影视飓风HKRR模型设计内容节奏:
- H(Happiness): 哪里放爽点/有趣的内容
- K(Knowledge): 哪里放干货/实用信息
- R(Resonance): 哪里打情感共鸣
- R(Rhythm): 整体节奏怎么把控（信息密度、松紧交替）"""


async def generate_outline(
    topic_title: str,
    topic_angle: str,
    *,
    skill: StyleSkill | None = None,
    user_idea: str = "",
    viral_score: int | None = None,
) -> ContentOutline:
    """Generate a detailed content outline for review."""
    skill_section = _format_skill(skill) if skill else "（无指定风格，使用优质通用风格）"

    user_msg = f"""## 选题
标题: {topic_title}
角度: {topic_angle}
"""
    if viral_score is not None:
        user_msg += f"爆款预测分: {viral_score}/100\n"
    if user_idea:
        user_msg += f"\n## 用户自己的想法\n{user_idea}\n"
    user_msg += f"""
## 风格方法论
{skill_section}

## 任务
生成详细的内容大纲，返回JSON对象：
{{
  "hook": "开头Hook设计（2-3句话）",
  "sections": [
    {{"heading": "段落标题", "core_point": "核心论点", "details": "展开内容", "emotion": "情绪"}}
  ],
  "emotion_curve": "情绪曲线描述",
  "key_data_points": ["数据点1", "数据点2"],
  "call_to_action": "结尾行动号召"
}}
只返回JSON。"""

    result = await chat_deep_json(
        [
            {"role": "system", "content": _OUTLINE_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=4096,
    )

    return ContentOutline(
        hook=result.get("hook", ""),
        sections=result.get("sections", []),
        emotion_curve=result.get("emotion_curve", ""),
        key_data_points=result.get("key_data_points", []),
        call_to_action=result.get("call_to_action", ""),
    )


# ── Step 2: Full Content Writing ────────────────────────────────────────────

_WRITE_SYSTEM = """你是一位顶级社交媒体内容创作者。你的任务是根据给定的大纲和风格，写出一篇高质量的完整文章。

写作要求：
- 严格按照大纲的结构和情绪曲线来写
- 每一段都要有具体的细节、案例或数据（不要用A/B/C代替真实品牌名）
- 语言生动有趣，避免"AI味"
- 开头必须在3句话内建立Hook
- 如果有风格方法论(Skill)，严格匹配其语气和结构
- 全文1500-2500字，信息密度高
- 使用真实的品牌名、产品名、人物名（如果涉及）
- 段落之间要有自然过渡
- 每300-400字要有一个"爽点"或"共鸣点"来维持阅读

同时生成：
1. 3个候选标题（运用Hook技巧：数字/反差/悬念/共鸣）
2. 英文封面图生成提示词（详细描述画面、色彩、构图、情绪）
3. 四个平台的适配版本"""


async def write_full_content(
    topic_title: str,
    topic_angle: str,
    outline: ContentOutline,
    *,
    skill: StyleSkill | None = None,
    user_idea: str = "",
    viral_score: int | None = None,
) -> dict:
    """Write full content based on outline."""
    skill_section = _format_skill(skill) if skill else "（无指定风格，使用优质通用风格）"

    outline_text = f"""Hook: {outline.hook}
情绪曲线: {outline.emotion_curve}

段落:
"""
    for i, sec in enumerate(outline.sections, 1):
        if isinstance(sec, dict):
            outline_text += f"{i}. {sec.get('heading', '')}\n"
            outline_text += f"   核心: {sec.get('core_point', '')}\n"
            outline_text += f"   内容: {sec.get('details', '')}\n"
            outline_text += f"   情绪: {sec.get('emotion', '')}\n"

    outline_text += f"\n关键数据: {', '.join(outline.key_data_points)}"
    outline_text += f"\n行动号召: {outline.call_to_action}"

    user_msg = f"""## 选题
标题: {topic_title}
角度: {topic_angle}

## 已确认的大纲
{outline_text}

## 风格方法论
{skill_section}
"""
    if user_idea:
        user_msg += f"\n## 用户想法\n{user_idea}\n"

    user_msg += """
## 任务
基于以上大纲，写出完整的内容包。返回JSON对象：
{
  "candidate_titles": ["标题1", "标题2", "标题3"],
  "body": "完整正文（1500-2500字）",
  "cover_prompt": "Detailed English prompt for AI cover image generation, including composition, colors, mood, style...",
  "platforms": {
    "shipinhao": {"title": "...", "body": "视频号短文案100-200字", "tags": ["#标签"]},
    "gongzhonghao": {"title": "...", "body": "公众号完整长文（重新排版，不要占位说明）", "tags": ["#标签"]},
    "xiaohongshu": {"title": "...", "body": "小红书风格（emoji+分段+种草）", "tags": ["#标签1", "#标签2"]},
    "douyin": {"title": "...", "body": "抖音超短文案50-100字", "tags": ["#标签"]}
  }
}
只返回JSON。"""

    return await chat_deep_json(
        [
            {"role": "system", "content": _WRITE_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=8192,
    )


# ── Step 3: AI Screening Team (点映团) ──────────────────────────────────────

_SCREENING_SYSTEM = """你是"AI 点映团"，3 位虚拟评审模拟真实用户反馈。

**路人** — 会点进来吗？看完会分享吗？哪里想退出？
**同行博主** — 有新意吗？差异化在哪？有什么值得学习/明显不足？
**运营专家** — 算法会推荐吗？点击率和完读率预估？

综合给出：overall_score(0-100), strengths(3-5), weaknesses(3-5), suggestions(3-5)。
语气直接坦率，像真实的内容评审会议，不要客套。"""


async def screen_content(
    title: str,
    body: str,
    *,
    platform: str = "小红书",
) -> ScreeningResult:
    """Run AI screening team on the generated content."""
    user_msg = f"""## 待评审内容
标题: {title}
目标平台: {platform}

正文:
{body[:3000]}

请以三个角色分别评审，然后给出综合评分。

返回JSON:
{{
  "passerby_review": "路人评审意见",
  "peer_review": "同行评审意见",
  "overall_score": 85,
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["不足1", "不足2"],
  "suggestions": ["建议1", "建议2"]
}}
只返回JSON。"""

    result = await chat_deep_json(
        [
            {"role": "system", "content": _SCREENING_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=3000,
    )

    return ScreeningResult(
        passerby_review=result.get("passerby_review", ""),
        peer_review=result.get("peer_review", ""),
        overall_score=result.get("overall_score", 0),
        strengths=result.get("strengths", []),
        weaknesses=result.get("weaknesses", []),
        suggestions=result.get("suggestions", []),
    )


# ── Full pipeline ───────────────────────────────────────────────────────────

async def create_content(
    topic_title: str,
    topic_angle: str,
    *,
    skill: StyleSkill | None = None,
    user_idea: str = "",
    viral_score: int | None = None,
    generate_cover: bool = True,
    run_screening: bool = True,
) -> ContentPackage:
    """Full pipeline: outline → write → screen → images → persist."""
    outline = await generate_outline(
        topic_title, topic_angle,
        skill=skill, user_idea=user_idea, viral_score=viral_score,
    )

    result = await write_full_content(
        topic_title, topic_angle, outline,
        skill=skill, user_idea=user_idea, viral_score=viral_score,
    )

    pkg = ContentPackage(
        topic=topic_title,
        candidate_titles=result.get("candidate_titles", [topic_title]),
        body=result.get("body", ""),
        outline=outline,
        cover_prompt=result.get("cover_prompt", ""),
    )

    platforms = result.get("platforms", {})
    for key, label in [("shipinhao", "视频号"), ("gongzhonghao", "公众号"),
                       ("xiaohongshu", "小红书"), ("douyin", "抖音")]:
        p = platforms.get(key, {})
        if p:
            pkg.platform_versions.append(PlatformContent(
                platform=label,
                title=p.get("title", ""),
                body=p.get("body", ""),
                tags=p.get("tags", []),
            ))

    if run_screening and pkg.body:
        try:
            pkg.screening = await screen_content(
                pkg.candidate_titles[0] if pkg.candidate_titles else topic_title,
                pkg.body,
            )
        except Exception as exc:
            log.warning("Screening failed: %s", exc)

    if generate_cover and pkg.cover_prompt:
        try:
            safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in topic_title[:30])
            paths = await generate_image(
                pkg.cover_prompt,
                filename=f"cover_{safe_name}.png",
                aspect_ratio="3:4",
                n=3,
            )
            pkg.cover_paths = paths
        except Exception as exc:
            log.warning("Cover image generation failed: %s", exc)

    await _persist(pkg, skill)
    return pkg


async def create_content_stream(
    topic_title: str,
    topic_angle: str,
    *,
    skill: StyleSkill | None = None,
    user_idea: str = "",
    viral_score: int | None = None,
) -> AsyncIterator[str]:
    """Streaming version — yields markdown as content is being created."""
    skill_section = _format_skill(skill) if skill else "（无指定风格，使用优质通用风格）"

    system_msg = """你是一位顶级社交媒体内容创作专家。请按以下流程输出完整内容包（Markdown格式）：

## 📋 内容大纲
（先展示大纲结构和情绪曲线设计）

## 📝 候选标题
1. ...
2. ...
3. ...

## 📄 正文
（完整正文，1500-2500字，段落之间用空行分隔）

## 🎨 封面图设计
（描述3种不同风格的封面方案）

## 📱 多平台适配

### 视频号版本
...

### 公众号版本
...

### 小红书版本
...

### 抖音版本
...

## 🎬 AI点映团评审
### 路人视角
...
### 同行视角
...
### 综合评分与建议
...

写作要求：
- 正文有具体细节、真实案例、数据支撑
- 避免用A/B/C代替品牌名
- 每个平台版本独立撰写，不是简单删减
- 公众号版本是完整排版的长文
- 小红书版本带emoji和种草语气"""

    user_msg = f"""## 选题
标题: {topic_title}
角度: {topic_angle}
"""
    if viral_score is not None:
        user_msg += f"爆款预测分: {viral_score}/100\n"
    if user_idea:
        user_msg += f"\n## 用户想法\n{user_idea}\n"
    user_msg += f"\n## 风格方法论\n{skill_section}\n"
    user_msg += "\n请按流程输出完整内容包。"

    async for chunk in chat_deep_stream(
        [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=8192,
        temperature=0.7,
    ):
        yield chunk


# ── persistence ─────────────────────────────────────────────────────────────

async def _persist(pkg: ContentPackage, skill: StyleSkill | None) -> None:
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in pkg.topic[:40])
    path = CONTENT_DIR / f"{safe}.json"

    screening_data = None
    if pkg.screening:
        screening_data = {
            "passerby_review": pkg.screening.passerby_review,
            "peer_review": pkg.screening.peer_review,
            "overall_score": pkg.screening.overall_score,
            "strengths": pkg.screening.strengths,
            "weaknesses": pkg.screening.weaknesses,
            "suggestions": pkg.screening.suggestions,
        }

    data = {
        "topic": pkg.topic,
        "candidate_titles": pkg.candidate_titles,
        "body": pkg.body,
        "cover_prompt": pkg.cover_prompt,
        "cover_paths": [str(p) for p in pkg.cover_paths],
        "screening": screening_data,
        "platforms": [
            {"platform": pv.platform, "title": pv.title, "body": pv.body, "tags": pv.tags}
            for pv in pkg.platform_versions
        ],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    score = pkg.screening.overall_score if pkg.screening else None
    await store.save_content(
        topic=pkg.topic,
        score=score,
        content=json.dumps(data, ensure_ascii=False),
        platform="all",
        skill_id=skill.skill_id if skill else None,
    )


# ── helpers ─────────────────────────────────────────────────────────────────

def _format_skill(skill: StyleSkill) -> str:
    lines = [
        f"博主: {skill.blogger}  领域: {skill.domain}",
        "",
        "### 标题公式",
        *[f"- {f}" for f in skill.title_formulas],
        "",
        f"### 内容结构\n{skill.content_structure}",
        "",
        "### 语气特征",
        *[f"- {f}" for f in skill.tone_features],
        "",
        "### Hook手法",
        *[f"- {h}" for h in skill.hooks],
        "",
        f"### Emoji风格\n{skill.emoji_style}",
    ]
    return "\n".join(lines)
