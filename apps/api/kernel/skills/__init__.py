"""Skill Library - Markdown 加载 + 自进化 + 版本化 (仿 Claude Code)

设计:
- 每个 skill 是一个 markdown 文件,头部有 YAML frontmatter
- 按需加载 (Planner 决定何时调用哪个 skill)
- 后台 Dream 任务可以从成功执行中提炼新 skill
- 版本化 (skill 改动有 git-like 版本)
"""

from .loader import SkillLibrary, Skill, get_skill_library

__all__ = ["SkillLibrary", "Skill", "get_skill_library"]
