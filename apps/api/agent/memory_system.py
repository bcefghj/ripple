"""五层记忆系统 - 借鉴 Claude Code 51 万行代码

五层架构:
- Layer 1: 指令记忆 (CLAUDE.md / KOC.md / USER.md / BRAND.md) - 项目级持久规则
- Layer 2: 文件存储 (memdir) - 灵感库 / 素材库 / 作品库
- Layer 3: 自动提取 (extractMemories) - stopHooks 后台提取知识
- Layer 4: 智能检索 (findRelevantMemories) - Sonnet 侧查 select 5 条
- Layer 5: 上下文注入 - 拼装到 system prompt

参考:
- CN-SEC 记忆系统架构深度拆解
- claude-code-from-source/ch11-memory.md
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import yaml
from loguru import logger


# ============================================================
# Layer 1: 指令记忆 (KOC.md / USER.md / BRAND.md)
# ============================================================

MAX_INCLUDE_DEPTH = 5  # 防止 @include 死循环


class InstructionMemory:
    """Layer 1: 项目级指令记忆
    
    加载顺序(从低到高,后者覆盖前者):
    - Managed (系统级,不可改)
    - User (~/.ripple/USER.md)
    - Project (./.ripple/KOC.md, ./.ripple/BRAND.md)
    - Local (.ripple/local.md, gitignore)
    - AutoMem (运行时自动写入)
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "instructions").mkdir(exist_ok=True)

    def get_user_md(self) -> str:
        """加载 USER.md (KOC 个人画像)"""
        path = self.root / "instructions" / "USER.md"
        return self._safe_read(path) or self._default_user_template()

    def get_koc_md(self) -> str:
        """加载 KOC.md (KOC 工作模式偏好)"""
        path = self.root / "instructions" / "KOC.md"
        return self._safe_read(path) or self._default_koc_template()

    def get_brand_md(self) -> str:
        """加载 BRAND.md (品牌调性 / 合规红线)"""
        path = self.root / "instructions" / "BRAND.md"
        return self._safe_read(path) or self._default_brand_template()

    def write_user_md(self, content: str) -> None:
        path = self.root / "instructions" / "USER.md"
        path.write_text(content, encoding="utf-8")

    def write_koc_md(self, content: str) -> None:
        path = self.root / "instructions" / "KOC.md"
        path.write_text(content, encoding="utf-8")

    def write_brand_md(self, content: str) -> None:
        path = self.root / "instructions" / "BRAND.md"
        path.write_text(content, encoding="utf-8")

    def _safe_read(self, path: Path) -> Optional[str]:
        if not path.exists():
            return None
        try:
            return self._process_includes(path.read_text(encoding="utf-8"), depth=0, seen=set())
        except Exception as e:
            logger.warning(f"读取 {path} 失败: {e}")
            return None

    def _process_includes(self, content: str, depth: int, seen: set) -> str:
        """处理 @include path/to/file 指令"""
        if depth >= MAX_INCLUDE_DEPTH:
            return content + "\n[Max include depth reached]"

        def replace_include(m: re.Match) -> str:
            include_path = self.root / m.group(1).strip()
            if str(include_path) in seen:
                return f"[Circular include: {m.group(1)}]"
            seen.add(str(include_path))
            if include_path.exists():
                inner = include_path.read_text(encoding="utf-8")
                return self._process_includes(inner, depth + 1, seen)
            return f"[Missing include: {m.group(1)}]"

        return re.sub(r"@include\s+([^\s]+)", replace_include, content)

    @staticmethod
    def _default_user_template() -> str:
        return """# USER.md - KOC 个人画像

## 基础信息
- 姓名: [待填写]
- 主要赛道: [美妆/数码/学习/生活/知识/搞笑/本地]
- 当前粉丝量: [待填写]
- 月平均收入: [待填写]

## 平台偏好
- 主战场: [视频号/小红书/抖音/B站/公众号]
- 辅助平台: [...]
- 最不熟悉: [...]

## 创作风格
- 内容形态: [图文/短视频/中长视频/直播]
- 语言风格: [口语化/专业/幽默/温暖/犀利]
- 标志性表达: [口头禅/常用 emoji/典型句式]

## 商业目标
- 短期(1-3 月): [...]
- 中期(6-12 月): [...]
- 长期(2-3 年): [...]
"""

    @staticmethod
    def _default_koc_template() -> str:
        return """# KOC.md - 工作模式偏好

## 创作流程偏好
- 灵感来源: [早期信号雷达/竞品观察/生活体验]
- 选题决策: [AI 推荐/手动选/混合]
- 文案风格: [AI 生成 + 人工调整 / 完全 AI / 完全人工]
- 封面风格: [模板化/AI 生成/手动设计]

## 时间节奏
- 每日产出: [1 条/2 条/3 条以上]
- 发布时间: [固定/动态/AI 推荐]
- 复盘频率: [每日/每周/每月]

## 工具偏好
- 剪辑: [剪映/Premiere/Final Cut/无]
- 设计: [Canva/Figma/PS/无]
- 数据分析: [千瓜/飞瓜/Ripple/无]
"""

    @staticmethod
    def _default_brand_template() -> str:
        return """# BRAND.md - 品牌调性与合规红线

## 调性约束
- 必须坚持的: [...]
- 必须避免的: [...]

## 合规红线
- 不可碰的话题: [政治敏感/医疗承诺/未经验证的财经]
- 必须的标识: [AI 生成内容必须显式声明]
- 版权约束: [音乐/图片/视频素材必须有授权来源]

## 品牌方合作
- 接单赛道: [...]
- 拒绝赛道: [...]
- 报价区间: [...]
"""


# ============================================================
# Layer 2: 文件存储 (memdir)
# ============================================================


@dataclass
class MemoryEntry:
    """memdir 内的单条记忆"""
    file_path: Path
    title: str
    content: str
    tags: List[str]
    created_at: datetime
    mtime: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemdirStore:
    """Layer 2: 文件式记忆存储
    
    目录结构:
        memory/
        ├── MEMORY.md              # 索引(< 200 行 / 25KB)
        ├── inspirations/          # 灵感库
        │   ├── 2026-04-28-xxx.md
        │   └── ...
        ├── materials/             # 素材库
        ├── works/                 # 历史作品
        └── debriefs/              # 复盘
    """

    MAX_INDEX_LINES = 200
    MAX_INDEX_BYTES = 25 * 1024
    MAX_SCAN_FILES = 200
    MAX_SCAN_LINES_PER_FILE = 30

    def __init__(self, root: Path):
        self.root = Path(root)
        self.memory_root = self.root / "memory"
        self.memory_root.mkdir(parents=True, exist_ok=True)
        for subdir in ("inspirations", "materials", "works", "debriefs"):
            (self.memory_root / subdir).mkdir(exist_ok=True)
        self.index_path = self.memory_root / "MEMORY.md"

    def write_memory(
        self,
        category: str,  # inspirations / materials / works / debriefs
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
    ) -> Path:
        """写入新记忆 + 更新索引"""
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        safe_title = re.sub(r"[^\w\u4e00-\u9fff-]", "_", title)[:50]
        filename = f"{timestamp}-{safe_title}.md"
        path = self.memory_root / category / filename

        frontmatter = {
            "title": title,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
        }
        full_content = f"---\n{yaml.safe_dump(frontmatter, allow_unicode=True)}---\n\n{content}"
        path.write_text(full_content, encoding="utf-8")

        self._update_index(category, title, path, tags or [])
        return path

    def _update_index(self, category: str, title: str, path: Path, tags: List[str]) -> None:
        """追加索引行(并裁剪到上限)"""
        existing = ""
        if self.index_path.exists():
            existing = self.index_path.read_text(encoding="utf-8")

        new_line = f"- [{category}] {title} → `{path.relative_to(self.memory_root)}` (tags: {', '.join(tags)})"
        lines = existing.split("\n") if existing else ["# Ripple Memory Index", ""]
        lines.append(new_line)

        # 裁剪
        if len(lines) > self.MAX_INDEX_LINES:
            lines = lines[: 2] + [f"[... {len(lines) - self.MAX_INDEX_LINES + 2} 条历史记忆已折叠 ...]"] + lines[-(self.MAX_INDEX_LINES - 3) :]

        new_content = "\n".join(lines)
        if len(new_content.encode("utf-8")) > self.MAX_INDEX_BYTES:
            new_content = new_content[-self.MAX_INDEX_BYTES :]

        self.index_path.write_text(new_content, encoding="utf-8")

    def scan(self, category: Optional[str] = None) -> List[MemoryEntry]:
        """扫描所有记忆(按 mtime 排序,限 200 文件)"""
        entries: List[MemoryEntry] = []
        search_dirs = [self.memory_root / category] if category else [
            self.memory_root / d for d in ("inspirations", "materials", "works", "debriefs")
        ]

        all_files = []
        for d in search_dirs:
            if d.exists():
                all_files.extend(d.glob("*.md"))

        all_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        all_files = all_files[: self.MAX_SCAN_FILES]

        for path in all_files:
            try:
                lines = []
                with open(path, encoding="utf-8") as f:
                    for i, line in enumerate(f):
                        if i >= self.MAX_SCAN_LINES_PER_FILE:
                            break
                        lines.append(line)
                content = "".join(lines)

                meta, body = self._parse_frontmatter(content)
                entries.append(
                    MemoryEntry(
                        file_path=path,
                        title=meta.get("title", path.stem),
                        content=body,
                        tags=meta.get("tags", []),
                        created_at=datetime.fromisoformat(meta.get("created_at", datetime.now().isoformat())),
                        mtime=datetime.fromtimestamp(path.stat().st_mtime),
                        metadata=meta,
                    )
                )
            except Exception as e:
                logger.warning(f"扫描 {path} 失败: {e}")

        return entries

    def read_full(self, path: Path) -> str:
        """完整读取一条记忆"""
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def get_index(self) -> str:
        """读取索引"""
        if self.index_path.exists():
            return self.index_path.read_text(encoding="utf-8")
        return "# Ripple Memory Index\n\n[空]"

    @staticmethod
    def _parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
        """解析 YAML frontmatter"""
        if not content.startswith("---"):
            return {}, content
        try:
            _, fm, body = content.split("---", 2)
            return yaml.safe_load(fm) or {}, body.strip()
        except Exception:
            return {}, content


# ============================================================
# Layer 3: extractMemories (后台提取)
# ============================================================


class MemoryExtractor:
    """Layer 3: 从对话中后台提取知识
    
    策略:
    - 在 stopHooks 后触发(无 tool 的 stop 路径末尾)
    - fork 子代理(maxTurns=5, skipTranscript)
    - 互斥执行(in_progress 时排队 trailing run)
    - hasMemoryWritesSince 时跳过(主代理已写过则不提取)
    """

    def __init__(self, store: MemdirStore, llm_call: Callable[..., Awaitable[Dict]]):
        self.store = store
        self.llm_call = llm_call
        self.in_progress = False
        self.last_extracted_turn: Optional[int] = None

    async def schedule_after_turn(
        self, messages: List[Dict[str, Any]], current_turn: int
    ) -> None:
        """安排后台提取(fire-and-forget)"""
        if self.in_progress:
            logger.debug("提取已在进行中,跳过")
            return
        if self.last_extracted_turn == current_turn:
            return

        self.in_progress = True
        try:
            await self._do_extract(messages)
            self.last_extracted_turn = current_turn
        finally:
            self.in_progress = False

    async def _do_extract(self, messages: List[Dict[str, Any]]) -> None:
        """实际提取逻辑"""
        # 取最近 10 条对话
        recent = messages[-10:]
        conv_text = "\n".join(
            f"[{m.get('role')}]: {str(m.get('content', ''))[:500]}" for m in recent
        )

        prompt = f"""你是 Ripple 的记忆提取助手。从以下 KOC 对话中提取值得长期记住的知识。

对话片段:
{conv_text}

请提取:
1. KOC 的偏好(平台/赛道/风格)
2. KOC 提到的具体事实(粉丝量/收入/工具栈)
3. KOC 表达的痛点或目标
4. 任何"应该记住,以后用得上"的信息

输出 JSON 格式:
{{
  "items": [
    {{"category": "preference|fact|pain_point|goal", "title": "短标题", "content": "详细内容", "tags": ["tag1", "tag2"]}},
    ...
  ]
}}

如果没有值得提取的,返回 {{"items": []}}
"""

        try:
            response = await self.llm_call(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
            )
            content = response.get("message", {}).get("content", "")

            # 简单提取 JSON
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                return

            data = json.loads(json_match.group())
            for item in data.get("items", []):
                self.store.write_memory(
                    category="inspirations" if item.get("category") in ("preference", "goal") else "debriefs",
                    title=item.get("title", "untitled"),
                    content=item.get("content", ""),
                    tags=item.get("tags", []),
                )
            logger.info(f"提取了 {len(data.get('items', []))} 条记忆")
        except Exception as e:
            logger.warning(f"记忆提取失败: {e}")


# ============================================================
# Layer 4: findRelevantMemories (智能检索)
# ============================================================


class MemoryRetriever:
    """Layer 4: 用侧向 LLM 选择相关记忆
    
    策略:
    - 从 manifest 中读所有记忆元信息
    - 用 LLM 选最相关的 N 条(默认 5)
    - 保守策略:不确定时少选
    - 检查文件名白名单防止幻觉
    """

    def __init__(self, store: MemdirStore, llm_call: Callable[..., Awaitable[Dict]]):
        self.store = store
        self.llm_call = llm_call

    async def select_relevant(
        self,
        user_query: str,
        max_count: int = 5,
    ) -> List[MemoryEntry]:
        """从所有记忆中选择最相关的"""
        all_entries = self.store.scan()
        if not all_entries:
            return []

        if len(all_entries) <= max_count:
            return all_entries

        # 构造 manifest 给 LLM
        manifest_lines = []
        valid_filenames = set()
        for e in all_entries:
            fn = e.file_path.name
            valid_filenames.add(fn)
            tags_str = ",".join(e.tags) if e.tags else "无"
            manifest_lines.append(f"- {fn}: 「{e.title}」 (tags: {tags_str})")

        prompt = f"""你是 Ripple 的记忆检索助手。从以下记忆清单中选出与用户问题最相关的最多 {max_count} 条。

用户问题: {user_query}

记忆清单:
{chr(10).join(manifest_lines)}

输出 JSON: {{"selected_filenames": ["xxx.md", ...]}}
保守策略:不确定就少选。最多 {max_count} 条。
"""

        try:
            response = await self.llm_call(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )
            content = response.get("message", {}).get("content", "")
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                return []

            data = json.loads(json_match.group())
            selected = data.get("selected_filenames", [])

            # 校验文件名白名单(防 LLM 幻觉)
            valid_selected = [s for s in selected if s in valid_filenames][:max_count]

            entry_map = {e.file_path.name: e for e in all_entries}
            return [entry_map[fn] for fn in valid_selected if fn in entry_map]
        except Exception as e:
            logger.warning(f"记忆检索失败: {e}")
            return []


# ============================================================
# Layer 5: 上下文注入
# ============================================================


class MemoryContextBuilder:
    """Layer 5: 拼装系统提示
    
    顺序:
    System: 固定段落(操作手册)
    User context: 动态段落(CLAUDE.md + 选中记忆 + 日期等)
    """

    def __init__(
        self,
        instructions: InstructionMemory,
        store: MemdirStore,
        retriever: MemoryRetriever,
    ):
        self.instructions = instructions
        self.store = store
        self.retriever = retriever

    def build_system_preamble(self) -> str:
        """固定的系统级前导(适合 prompt cache)"""
        return """# Ripple Memory System Operations Manual

You have access to a five-layer memory system:
1. **Instruction memory**: Persistent rules from KOC.md / USER.md / BRAND.md
2. **Memdir**: File-based notes in inspirations/materials/works/debriefs
3. **Auto-extracted**: Background extraction of conversation insights
4. **Retrieved**: Selected relevant memories for current turn
5. **Injected**: Available below in user context

## How to use memories
- Reference USER profile when personalizing suggestions
- Cite specific past works when discussing style
- Respect BRAND constraints (compliance red lines)
- Don't repeat info user has shared in previous sessions

## When to write new memories
- KOC explicitly says "记住 X" / "下次都用 Y"
- KOC reveals strong preference or goal
- KOC corrects you significantly
- Don't memorize one-off questions
"""

    async def build_user_context(self, user_query: str, max_relevant: int = 5) -> str:
        """动态构建用户上下文(每轮调用)"""
        parts = []

        parts.append(f"## Current date: {datetime.now().strftime('%Y-%m-%d %H:%M %A')}")

        # USER.md
        user_md = self.instructions.get_user_md()
        if user_md:
            parts.append("## USER profile (USER.md)\n" + user_md)

        # KOC.md
        koc_md = self.instructions.get_koc_md()
        if koc_md:
            parts.append("## Working preferences (KOC.md)\n" + koc_md)

        # BRAND.md
        brand_md = self.instructions.get_brand_md()
        if brand_md:
            parts.append("## Brand constraints (BRAND.md)\n" + brand_md)

        # 检索相关记忆
        relevant = await self.retriever.select_relevant(user_query, max_relevant)
        if relevant:
            parts.append("## Relevant memories")
            for entry in relevant:
                full_content = self.store.read_full(entry.file_path)
                age_days = (datetime.now() - entry.mtime).days
                staleness = f"⚠ {age_days} days old" if age_days > 7 else ""
                parts.append(f"### {entry.title} {staleness}\n{full_content[:1000]}")

        return "\n\n".join(parts)


# ============================================================
# 整合入口
# ============================================================


class MemorySystem:
    """五层记忆系统整合入口"""

    def __init__(self, root: Path, llm_call: Callable[..., Awaitable[Dict]]):
        self.instructions = InstructionMemory(root)
        self.store = MemdirStore(root)
        self.extractor = MemoryExtractor(self.store, llm_call)
        self.retriever = MemoryRetriever(self.store, llm_call)
        self.context_builder = MemoryContextBuilder(
            self.instructions, self.store, self.retriever
        )

    async def build_full_context(self, user_query: str) -> Dict[str, str]:
        """构建完整上下文(返回 system + user_context 字段)"""
        return {
            "system_preamble": self.context_builder.build_system_preamble(),
            "user_context": await self.context_builder.build_user_context(user_query),
        }

    async def post_turn_extract(self, messages: List[Dict[str, Any]], current_turn: int) -> None:
        """轮次后异步提取(fire-and-forget)"""
        await self.extractor.schedule_after_turn(messages, current_turn)
