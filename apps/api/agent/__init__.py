"""Ripple Agent Framework - 借鉴 Claude Code 51 万行代码架构

核心模块:
- agent_loop: TAOR 主循环(AsyncGenerator + while True + Terminal 枚举)
- state: LoopState 整对象替换
- compression: 四层上下文压缩 + circuit breaker
- hooks: 5 类 Hooks (Pre/Post/Stop/PreCompact/Permission)
- memory_system: 五层记忆系统
- skills: SKILL.md 渐进披露
- subagent: Task = 同构子循环
"""

__version__ = "0.1.0"
