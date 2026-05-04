"""Style Distill — analyse blogger style and extract a reusable Skill profile.

Two modes:
  1. "Learn from others": provide sample posts from a blogger you admire.
  2. "Learn from self":   provide your own past posts to extract your style.

The distilled Skill is a methodology card, NOT content to copy.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from core.config import SKILLS_DIR
from core.llm import chat_json
from core import store

log = logging.getLogger(__name__)


@dataclass
class StyleSkill:
    skill_id: str
    blogger: str
    domain: str
    title_formulas: list[str]
    content_structure: str
    tone_features: list[str]
    topic_preferences: list[str]
    hooks: list[str]
    emoji_style: str
    raw: dict = field(default_factory=dict)


_SYSTEM_PROMPT = """你是一位资深内容策划与写作教练。你的任务是"蒸馏"一位博主的写作方法论。

蒸馏 ≠ 抄袭。你要提炼的是可复用的**创作框架和方法论**，而不是具体的内容。

分析维度：
1. **title_formulas**: 标题公式模板（3-5个），例如"数字+经验年限+技巧类型"
2. **content_structure**: 内容结构框架描述（总分总？故事型？教程型？清单型？）
3. **tone_features**: 语气和修辞特征（口语化？专业？幽默？亲和？犀利？）
4. **topic_preferences**: 选题偏好模式（偏好哪些类型的话题？避免什么？）
5. **hooks**: 常用的开头Hook手法（提问？反常识？数据？故事？）
6. **emoji_style**: emoji使用风格（密集/适度/极少，常用哪些emoji）

要求：
- 每个维度都要有具体的描述和示例
- 标题公式要抽象化（不包含具体内容，只保留结构模板）
- 分析要基于提供的内容样本，不要凭空猜测"""


async def distill_style(
    blogger_name: str,
    domain: str,
    sample_posts: list[str],
) -> StyleSkill:
    """Analyse sample posts and produce a reusable StyleSkill."""
    if not sample_posts:
        raise ValueError("At least one sample post is required for distillation")

    posts_text = "\n\n---\n\n".join(
        f"【样本 {i+1}】\n{post}" for i, post in enumerate(sample_posts)
    )

    user_msg = f"""## 博主信息
- 博主名称: {blogger_name}
- 所在领域: {domain}

## 内容样本
{posts_text}

## 任务
请蒸馏出这位博主的写作方法论Skill档案。

返回JSON对象，包含以下字段：
- title_formulas: 字符串数组，3-5个标题公式模板
- content_structure: 字符串，内容结构框架描述
- tone_features: 字符串数组，语气和修辞特征
- topic_preferences: 字符串数组，选题偏好模式
- hooks: 字符串数组，常用的开头Hook手法
- emoji_style: 字符串，emoji使用风格描述

只返回JSON对象。"""

    result = await chat_json(
        [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.4,
        max_tokens=3000,
    )

    skill_id = _make_id(blogger_name)
    skill = StyleSkill(
        skill_id=skill_id,
        blogger=blogger_name,
        domain=domain,
        title_formulas=result.get("title_formulas", []),
        content_structure=result.get("content_structure", ""),
        tone_features=result.get("tone_features", []),
        topic_preferences=result.get("topic_preferences", []),
        hooks=result.get("hooks", []),
        emoji_style=result.get("emoji_style", ""),
        raw=result,
    )

    await _persist(skill)
    return skill


async def _persist(skill: StyleSkill) -> None:
    skill_dict = {
        "blogger": skill.blogger,
        "domain": skill.domain,
        "title_formulas": skill.title_formulas,
        "content_structure": skill.content_structure,
        "tone_features": skill.tone_features,
        "topic_preferences": skill.topic_preferences,
        "hooks": skill.hooks,
        "emoji_style": skill.emoji_style,
    }
    await store.save_skill(skill.skill_id, skill.blogger, skill.domain, skill_dict)

    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    path = SKILLS_DIR / f"{skill.skill_id}.json"
    path.write_text(json.dumps(skill_dict, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Skill persisted: %s → %s", skill.skill_id, path)


async def load_skill(skill_id: str) -> StyleSkill | None:
    data = await store.get_skill(skill_id)
    if not data:
        return None
    return StyleSkill(
        skill_id=skill_id,
        blogger=data.get("blogger", ""),
        domain=data.get("domain", ""),
        title_formulas=data.get("title_formulas", []),
        content_structure=data.get("content_structure", ""),
        tone_features=data.get("tone_features", []),
        topic_preferences=data.get("topic_preferences", []),
        hooks=data.get("hooks", []),
        emoji_style=data.get("emoji_style", ""),
        raw=data,
    )


def _make_id(name: str) -> str:
    import re, hashlib
    clean = re.sub(r"\W+", "_", name).strip("_").lower()
    short_hash = hashlib.md5(name.encode()).hexdigest()[:6]
    return f"{clean}_{short_hash}"
