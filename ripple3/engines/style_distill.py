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
    mental_model: str = ""
    decision_heuristics: list[str] = field(default_factory=list)
    anti_patterns: list[str] = field(default_factory=list)
    honesty_boundaries: str = ""
    raw: dict = field(default_factory=dict)


_SYSTEM_PROMPT = """你是一位资深内容策划与写作教练。你的任务是"蒸馏"一位博主的创作方法论。

蒸馏 ≠ 抄袭。你要提炼的是可复用的**创作框架和认知模型**。

## 五层认知蒸馏模型（参考女娲Skill方法论）

### 第1层：表达 DNA
1. **title_formulas**: 标题公式模板（3-5个），例如"数字+经验年限+技巧类型"
2. **content_structure**: 内容结构框架（总分总？故事型？教程型？清单型？）
3. **tone_features**: 语气特征（口语化？专业？幽默？亲和？犀利？）+ 节奏、用词偏好、标点风格
4. **hooks**: 常用的开头Hook手法（提问？反常识？数据？故事？）
5. **emoji_style**: emoji使用风格（密集/适度/极少，常用哪些emoji）

### 第2层：心智模型
6. **mental_model**: 这位博主如何看待自己的领域和受众？认知框架是什么？
   例如："认为新手最缺的不是技巧而是信心" / "把复杂知识当成故事来讲"

### 第3层：决策启发式
7. **topic_preferences**: 选题判断规则和优先级
8. **decision_heuristics**: 追热点的方式、话题切入角度、内容取舍的决策规则

### 第4层：反模式
9. **anti_patterns**: 什么内容不做、价值底线、明确拒绝的方向

### 第5层：诚实边界
10. **honesty_boundaries**: 能力局限的诚实声明、不擅长什么

要求：
- 每个维度都要有具体的描述和示例
- 标题公式要抽象化（不包含具体内容，只保留结构模板）
- 分析要基于提供的内容样本，不要凭空猜测
- 如果某些层级信息不足，诚实标注"信息不足，需要更多样本"
- 输出JSON对象"""


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
请用五层认知蒸馏模型，蒸馏出这位博主的完整创作方法论Skill档案。

返回JSON对象，包含以下字段：
- title_formulas: 字符串数组，3-5个标题公式模板
- content_structure: 字符串，内容结构框架描述
- tone_features: 字符串数组，语气特征+节奏+用词偏好+标点风格
- topic_preferences: 字符串数组，选题偏好模式
- hooks: 字符串数组，常用的开头Hook手法
- emoji_style: 字符串，emoji使用风格描述
- mental_model: 字符串，博主的认知框架和看待领域的方式
- decision_heuristics: 字符串数组，追热点方式、话题切入角度、内容取舍规则
- anti_patterns: 字符串数组，什么不做、价值底线
- honesty_boundaries: 字符串，能力局限声明

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
        mental_model=result.get("mental_model", ""),
        decision_heuristics=result.get("decision_heuristics", []),
        anti_patterns=result.get("anti_patterns", []),
        honesty_boundaries=result.get("honesty_boundaries", ""),
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
        "mental_model": skill.mental_model,
        "decision_heuristics": skill.decision_heuristics,
        "anti_patterns": skill.anti_patterns,
        "honesty_boundaries": skill.honesty_boundaries,
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
        mental_model=data.get("mental_model", ""),
        decision_heuristics=data.get("decision_heuristics", []),
        anti_patterns=data.get("anti_patterns", []),
        honesty_boundaries=data.get("honesty_boundaries", ""),
        raw=data,
    )


def _make_id(name: str) -> str:
    import re, hashlib
    clean = re.sub(r"\W+", "_", name).strip("_").lower()
    short_hash = hashlib.md5(name.encode()).hexdigest()[:6]
    return f"{clean}_{short_hash}"
