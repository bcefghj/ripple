"""Skill Library Loader - 解析 markdown skill 文件"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Skill:
    name: str
    description: str
    triggers: List[str] = field(default_factory=list)
    body: str = ""
    file_path: str = ""
    version: int = 1
    tags: List[str] = field(default_factory=list)

    def matches(self, query: str) -> bool:
        q = query.lower()
        if any(t.lower() in q for t in self.triggers):
            return True
        return False


def _parse_frontmatter(text: str) -> tuple[Dict, str]:
    """解析 YAML frontmatter"""
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    fm_block = text[3:end].strip()
    body = text[end + 3:].strip()

    fm = {}
    for line in fm_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip("\"'")

    return fm, body


class SkillLibrary:
    def __init__(self, skill_dir: Optional[Path] = None) -> None:
        if skill_dir is None:
            module_dir = Path(__file__).parent
            skill_dir = module_dir / "library"
        skill_dir.mkdir(parents=True, exist_ok=True)
        self.skill_dir = skill_dir
        self._skills: Dict[str, Skill] = {}
        self.reload()

    def reload(self) -> None:
        self._skills.clear()
        for f in self.skill_dir.rglob("*.md"):
            try:
                text = f.read_text(encoding="utf-8")
                fm, body = _parse_frontmatter(text)
                triggers_raw = fm.get("triggers", "") or ""
                triggers = [t.strip() for t in triggers_raw.split(",") if t.strip()]
                tags_raw = fm.get("tags", "") or ""
                tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
                skill = Skill(
                    name=fm.get("name", f.stem),
                    description=fm.get("description", ""),
                    triggers=triggers,
                    body=body,
                    file_path=str(f),
                    version=int(fm.get("version", 1) or 1),
                    tags=tags,
                )
                self._skills[skill.name] = skill
            except Exception:
                continue

    def list_all(self) -> List[Skill]:
        return list(self._skills.values())

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def find_for_query(self, query: str, top_k: int = 3) -> List[Skill]:
        matched = [s for s in self._skills.values() if s.matches(query)]
        return matched[:top_k]

    def add_or_update(self, skill: Skill) -> None:
        path = self.skill_dir / f"{skill.name}.md"
        triggers_str = ", ".join(skill.triggers)
        tags_str = ", ".join(skill.tags)
        text = (
            f"---\n"
            f"name: {skill.name}\n"
            f"description: {skill.description}\n"
            f"triggers: {triggers_str}\n"
            f"tags: {tags_str}\n"
            f"version: {skill.version}\n"
            f"---\n\n{skill.body}"
        )
        path.write_text(text, encoding="utf-8")
        self._skills[skill.name] = skill


_singleton: Optional[SkillLibrary] = None


def get_skill_library() -> SkillLibrary:
    global _singleton
    if _singleton is None:
        _singleton = SkillLibrary()
    return _singleton
