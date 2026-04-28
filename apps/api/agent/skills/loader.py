"""Skills 加载器 - YAML frontmatter 渐进披露

借鉴 Claude Code Skills:
- 启动只读 frontmatter (description, when_to_use, allowed_tools)
- 调用 /skill 或模型触发时加载正文
- context: fork 让技能在子代理跑

参考:
- Claude Code Skills 文档
- agentskills.io 标准
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from loguru import logger


@dataclass
class SkillFrontmatter:
    """Skill 元信息 (启动时只读这部分)"""
    name: str
    description: str
    when_to_use: Optional[str] = None
    allowed_tools: List[str] = field(default_factory=list)
    requires_toolsets: List[str] = field(default_factory=list)
    paths_globs: List[str] = field(default_factory=list)  # 路径条件
    context_fork: bool = False  # 在子代理执行
    disable_model_invocation: bool = False
    triggers: List[str] = field(default_factory=list)  # 关键词触发


@dataclass
class Skill:
    """完整 Skill (含正文,按需加载)"""
    frontmatter: SkillFrontmatter
    body: str
    file_path: Path


class SkillLoader:
    """Skills 发现与加载"""

    def __init__(self, roots: List[Path]):
        self.roots = roots
        self._cache: Dict[str, Skill] = {}

    def discover(self) -> List[SkillFrontmatter]:
        """发现所有可用 skills (只读 frontmatter)"""
        results = []
        for root in self.roots:
            if not root.exists():
                continue
            for skill_md in root.rglob("SKILL.md"):
                try:
                    fm, _ = self._parse(skill_md)
                    results.append(fm)
                except Exception as e:
                    logger.warning(f"解析 {skill_md} 失败: {e}")
        return results

    def load(self, skill_name: str) -> Optional[Skill]:
        """按名加载完整 Skill"""
        if skill_name in self._cache:
            return self._cache[skill_name]

        for root in self.roots:
            for skill_md in root.rglob("SKILL.md"):
                try:
                    fm, body = self._parse(skill_md)
                    if fm.name == skill_name:
                        skill = Skill(frontmatter=fm, body=body, file_path=skill_md)
                        self._cache[skill_name] = skill
                        return skill
                except Exception:
                    continue
        return None

    def list_for_prompt(self) -> str:
        """生成给 LLM 看的 skills 清单(简短)"""
        skills = self.discover()
        if not skills:
            return "[无可用 skills]"
        lines = ["## 可用 Skills (调用 /skill <name> 查看详情)\n"]
        for s in skills:
            triggers = f" (触发: {', '.join(s.triggers)})" if s.triggers else ""
            lines.append(f"- **{s.name}**: {s.description}{triggers}")
        return "\n".join(lines)

    @staticmethod
    def _parse(skill_md: Path) -> Tuple[SkillFrontmatter, str]:
        content = skill_md.read_text(encoding="utf-8")
        if not content.startswith("---"):
            raise ValueError(f"{skill_md} 必须以 YAML frontmatter 开始 (---)")

        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError(f"{skill_md} frontmatter 格式错误")

        meta = yaml.safe_load(parts[1]) or {}
        body = parts[2].strip()

        fm = SkillFrontmatter(
            name=meta.get("name", skill_md.parent.name),
            description=meta.get("description", ""),
            when_to_use=meta.get("when_to_use"),
            allowed_tools=meta.get("allowed_tools", []) or [],
            requires_toolsets=meta.get("requires_toolsets", []) or [],
            paths_globs=meta.get("paths_globs", []) or [],
            context_fork=meta.get("context_fork", False),
            disable_model_invocation=meta.get("disable_model_invocation", False),
            triggers=meta.get("triggers", []) or [],
        )
        return fm, body
