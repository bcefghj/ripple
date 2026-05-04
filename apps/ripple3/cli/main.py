"""Ripple 3.0 CLI — interactive KOC content assistant.

Commands:
  ripple idea     — generate topic ideas for a domain
  ripple predict  — score ideas for viral potential
  ripple distill  — distill a blogger's style
  ripple create   — generate a full content package
  ripple flow     — end-to-end: idea → predict → create
  ripple radar    — scan domain ecosystem + blogger discovery
  ripple skills   — list saved style skills
  ripple ui       — launch the Gradio Web UI
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich import box

app = typer.Typer(
    name="ripple",
    help="Ripple 3.0 — KOC 内容灵感助手",
    no_args_is_help=True,
)
console = Console()


def _run(coro):
    return asyncio.run(coro)


# ── radar ──────────────────────────────────────────────────────────────────

@app.command()
def radar(
    domain: str = typer.Argument(..., help="内容领域，如 '美食探店' '职场效率'"),
):
    """扫描领域生态 — 博主推荐 + 热门话题 + 蓝海机会"""
    from engines.idea_engine import scan_radar

    console.print(Panel(f"[bold cyan]同行雷达扫描中...[/] 领域: {domain}", title="🔍 同行雷达"))
    report = _run(scan_radar(domain))

    console.print(Panel(
        f"[bold]{report.ecosystem_summary}[/]",
        title="📊 领域生态综述",
        border_style="cyan",
    ))

    if report.top_bloggers:
        table = Table(title="👤 推荐关注的博主/达人", box=box.ROUNDED)
        table.add_column("博主", style="cyan", min_width=12)
        table.add_column("量级", width=8)
        table.add_column("平台", width=20)
        table.add_column("风格", min_width=25)
        table.add_column("值得学习", min_width=25)

        for b in report.top_bloggers:
            table.add_row(
                b.name,
                b.follower_tier,
                ", ".join(b.platforms),
                b.content_style[:40],
                "; ".join(b.learning_points[:2])[:50],
            )
        console.print(table)

    if report.trending_topics:
        console.print(Panel(
            "\n".join(f"  🔥 {t}" for t in report.trending_topics),
            title="热门话题", border_style="yellow",
        ))

    if report.rising_angles:
        console.print(Panel(
            "\n".join(f"  📈 {a}" for a in report.rising_angles),
            title="上升趋势", border_style="green",
        ))

    if report.content_gaps:
        console.print(Panel(
            "\n".join(f"  💎 {g}" for g in report.content_gaps),
            title="蓝海机会", border_style="magenta",
        ))

    console.print(f"\n[dim]数据来源: {len(report.raw_peer_sources)} 条内容搜索 + "
                  f"{len(report.raw_blogger_sources)} 条博主搜索 + "
                  f"{len(report.raw_news)} 条新闻[/]")


# ── idea ────────────────────────────────────────────────────────────────────

@app.command()
def idea(
    domain: str = typer.Argument(..., help="你的内容领域，如 '美食探店' '职场效率' '数码测评'"),
    context: str = typer.Option("", "--context", "-c", help="补充信息（可选）"),
    count: int = typer.Option(12, "--count", "-n", help="生成选题数量"),
):
    """扫描同行 + AI 灵感发散 → 生成选题点子"""
    from engines.idea_engine import generate_ideas

    console.print(Panel(f"[bold cyan]同行雷达扫描中...[/] 领域: {domain}", title="🔍 选题灵感引擎"))

    ideas = _run(generate_ideas(domain, user_context=context, count=count))

    if not ideas:
        console.print("[red]未生成任何选题，请检查网络或API配置[/]")
        raise typer.Exit(1)

    table = Table(title=f"💡 {domain} — {len(ideas)} 个选题灵感", box=box.ROUNDED)
    table.add_column("#", style="bold", width=3)
    table.add_column("选题标题", style="cyan", min_width=30)
    table.add_column("切入角度", min_width=20)
    table.add_column("形式", width=12)
    table.add_column("灵感来源", min_width=20)

    for i, it in enumerate(ideas, 1):
        table.add_row(str(i), it.title, it.angle[:50], it.format_suggestion, it.inspiration_source[:40])

    console.print(table)

    _save_temp("_last_ideas.json", [
        {"title": it.title, "angle": it.angle, "audience": it.audience,
         "format_suggestion": it.format_suggestion, "inspiration_source": it.inspiration_source}
        for it in ideas
    ])
    console.print("[dim]选题已缓存，可运行 ripple predict 进行爆款预测[/]")


# ── predict ─────────────────────────────────────────────────────────────────

@app.command()
def predict(
    domain: str = typer.Argument("", help="领域（留空则使用上次 idea 结果）"),
    platform: str = typer.Option("小红书", "--platform", "-p", help="目标平台"),
):
    """对选题进行 12 维度爆款潜力评分（含 HKRR 模型）"""
    from engines.idea_engine import TopicIdea
    from engines.viral_predictor import predict_viral

    cached = _load_temp("_last_ideas.json")
    if not cached:
        console.print("[red]请先运行 ripple idea <领域> 生成选题[/]")
        raise typer.Exit(1)

    ideas = [TopicIdea(**item) for item in cached]
    if not domain:
        domain = "（来自上次扫描）"

    console.print(Panel(f"[bold magenta]爆款潜力预测中...[/] {len(ideas)} 个选题 → {platform}", title="🔮 爆款预测引擎"))
    predicted = _run(predict_viral(ideas, domain, target_platform=platform))

    if not predicted:
        console.print("[red]预测失败[/]")
        raise typer.Exit(1)

    for rank, p in enumerate(predicted, 1):
        s = p.score
        lines = [f"[bold]{p.idea.title}[/]\n"]

        for dim in s.all_dimensions:
            lines.append(f"  {dim.name:8s} {_bar(dim.score)} {dim.score}")
            if dim.reasoning:
                lines.append(f"           [dim]{dim.reasoning[:60]}[/dim]")

        lines.append(f"\n  综合: [bold]{s.total}/100[/]  {s.star_rating}  {s.verdict}")
        if s.overall_suggestion:
            lines.append(f"  建议: {s.overall_suggestion[:80]}")
        if s.competitor_analysis:
            lines.append(f"  竞品: {s.competitor_analysis[:80]}")

        color = "green" if s.total >= 80 else "yellow" if s.total >= 60 else "red"
        console.print(Panel("\n".join(lines), title=f"#{rank}", border_style=color))

    _save_temp("_last_predicted.json", [
        {"title": p.idea.title, "angle": p.idea.angle, "score": p.score.total,
         "verdict": p.score.verdict, "suggestion": p.score.overall_suggestion}
        for p in predicted
    ])
    console.print("[dim]预测结果已缓存，可选择某个选题运行 ripple create[/]")


# ── distill ─────────────────────────────────────────────────────────────────

@app.command()
def distill(
    blogger: str = typer.Argument(..., help="博主名称"),
    domain: str = typer.Option("", "--domain", "-d", help="博主领域"),
):
    """蒸馏博主风格方法论 — 粘贴内容样本，输入 END 结束"""
    from engines.style_distill import distill_style

    console.print(Panel(f"[bold green]风格蒸馏[/] 博主: {blogger}", title="🧪 蒸馏引擎"))
    console.print("请粘贴博主的内容样本（可多篇，每篇之间用 '---' 分隔，输入 END 结束）:")

    lines: list[str] = []
    try:
        for line in sys.stdin:
            if line.strip() == "END":
                break
            lines.append(line.rstrip())
    except EOFError:
        pass

    text = "\n".join(lines)
    if not text.strip():
        console.print("[red]未输入任何内容样本[/]")
        raise typer.Exit(1)

    samples = [s.strip() for s in text.split("---") if s.strip()]
    console.print(f"[dim]收到 {len(samples)} 篇样本，开始蒸馏...[/]")

    skill = _run(distill_style(blogger, domain, samples))

    console.print(Panel(
        f"[bold]博主: {skill.blogger}[/]  领域: {skill.domain}\n\n"
        f"[cyan]标题公式:[/]\n" + "\n".join(f"  - {f}" for f in skill.title_formulas) + "\n\n"
        f"[cyan]内容结构:[/]\n  {skill.content_structure}\n\n"
        f"[cyan]语气特征:[/]\n" + "\n".join(f"  - {t}" for t in skill.tone_features) + "\n\n"
        f"[cyan]Hook手法:[/]\n" + "\n".join(f"  - {h}" for h in skill.hooks) + "\n\n"
        f"[cyan]Emoji风格:[/] {skill.emoji_style}",
        title=f"✨ 蒸馏结果 — {skill.skill_id}",
        border_style="green",
    ))

    _save_temp("_last_skill_id.txt", skill.skill_id)


# ── create ──────────────────────────────────────────────────────────────────

@app.command()
def create(
    topic: str = typer.Argument(..., help="选题标题"),
    angle: str = typer.Option("", "--angle", "-a", help="切入角度"),
    skill_id: str = typer.Option("", "--skill", "-s", help="使用的风格Skill ID"),
    user_idea: str = typer.Option("", "--idea", "-i", help="你自己的想法（可选）"),
    no_cover: bool = typer.Option(False, "--no-cover", help="跳过封面图生成"),
    no_screen: bool = typer.Option(False, "--no-screen", help="跳过AI点映团评审"),
):
    """生成完整内容包：大纲 + 文案 + 点映团评审 + 封面图 + 多平台版本"""
    from engines.content_create import create_content
    from engines.style_distill import load_skill

    if not skill_id:
        last = _load_temp_text("_last_skill_id.txt")
        if last:
            skill_id = last
            console.print(f"[dim]使用上次蒸馏的风格: {skill_id}[/]")

    skill = None
    if skill_id:
        skill = _run(load_skill(skill_id))
        if skill:
            console.print(f"[green]已加载风格Skill: {skill.blogger}[/]")
        else:
            console.print(f"[yellow]未找到Skill {skill_id}，使用通用风格[/]")

    console.print(Panel(f"[bold blue]内容创作中...[/] {topic}", title="✍️ 内容创作引擎"))

    pkg = _run(create_content(
        topic, angle, skill=skill, user_idea=user_idea,
        generate_cover=not no_cover,
        run_screening=not no_screen,
    ))

    console.print(Panel(
        "[cyan]候选标题:[/]\n" + "\n".join(f"  {i+1}. {t}" for i, t in enumerate(pkg.candidate_titles)),
        title="📝 内容包",
        border_style="blue",
    ))

    console.print(Panel(pkg.body[:3000], title="正文（前3000字）", border_style="dim"))

    if pkg.screening:
        sc = pkg.screening
        console.print(Panel(
            f"[cyan]路人视角:[/]\n{sc.passerby_review}\n\n"
            f"[cyan]同行视角:[/]\n{sc.peer_review}\n\n"
            f"综合评分: [bold]{sc.overall_score}/100[/]\n\n"
            f"[green]优势:[/] {'; '.join(sc.strengths[:3])}\n"
            f"[yellow]不足:[/] {'; '.join(sc.weaknesses[:3])}\n"
            f"[cyan]建议:[/] {'; '.join(sc.suggestions[:3])}",
            title="🎬 AI 点映团评审",
            border_style="yellow",
        ))

    if pkg.cover_paths:
        console.print(f"\n[green]封面图已保存:[/] {', '.join(str(p) for p in pkg.cover_paths)}")

    for pv in pkg.platform_versions:
        tags_str = " ".join(pv.tags[:5])
        console.print(Panel(
            f"[bold]{pv.title}[/]\n\n{pv.body[:500]}\n\n[dim]{tags_str}[/]",
            title=f"📱 {pv.platform}",
            border_style="cyan",
        ))


# ── flow (end-to-end) ──────────────────────────────────────────────────────

@app.command()
def flow(
    domain: str = typer.Argument(..., help="内容领域"),
    platform: str = typer.Option("小红书", "--platform", "-p", help="目标平台"),
    skill_id: str = typer.Option("", "--skill", "-s", help="使用的风格Skill ID"),
    auto: bool = typer.Option(False, "--auto", help="自动选择排名第一的选题"),
    no_cover: bool = typer.Option(False, "--no-cover", help="跳过封面图生成"),
):
    """一键全流程: 雷达 → 灵感 → 预测 → 创作"""
    from engines.idea_engine import generate_ideas, scan_radar
    from engines.viral_predictor import predict_viral
    from engines.content_create import create_content
    from engines.style_distill import load_skill

    console.print(Panel(
        f"[bold]领域: {domain}  平台: {platform}[/]",
        title="🚀 Ripple 全流程",
        border_style="magenta",
    ))

    # Step 0: Radar
    console.print("\n[bold cyan]Step 0/4  同行雷达扫描...[/]")
    report = _run(scan_radar(domain))
    console.print(f"[green]✓ 发现 {len(report.top_bloggers)} 位博主, "
                  f"{len(report.trending_topics)} 个热门话题[/]")

    # Step 1: Ideas
    console.print("\n[bold cyan]Step 1/4  生成选题灵感...[/]")
    ideas = _run(generate_ideas(domain, radar_report=report))
    if not ideas:
        console.print("[red]选题生成失败[/]")
        raise typer.Exit(1)
    console.print(f"[green]✓ 生成 {len(ideas)} 个选题[/]")

    # Step 2: Predict
    console.print("\n[bold magenta]Step 2/4  爆款潜力预测...[/]")
    predicted = _run(predict_viral(ideas, domain, target_platform=platform))
    if not predicted:
        console.print("[red]预测失败[/]")
        raise typer.Exit(1)

    table = Table(title="📊 爆款预测排行", box=box.ROUNDED)
    table.add_column("#", width=3)
    table.add_column("选题", min_width=30)
    table.add_column("得分", width=8)
    table.add_column("评价", width=6)
    table.add_column("建议", min_width=20)

    for i, p in enumerate(predicted[:10], 1):
        s = p.score
        table.add_row(str(i), p.idea.title, f"{s.total}", s.verdict, s.overall_suggestion[:40])
    console.print(table)

    # Choose topic
    if auto:
        chosen_idx = 0
    else:
        console.print("\n选择一个选题（输入编号，默认1）:")
        try:
            raw = input("> ").strip()
            chosen_idx = max(0, int(raw) - 1) if raw else 0
        except (ValueError, EOFError):
            chosen_idx = 0

    chosen = predicted[min(chosen_idx, len(predicted) - 1)]
    console.print(f"\n[green]已选择:[/] {chosen.idea.title} ({chosen.score.total}分)")

    # Load skill
    skill = None
    if skill_id:
        skill = _run(load_skill(skill_id))
        if skill:
            console.print(f"[green]使用风格: {skill.blogger}[/]")

    # Step 3: Create
    console.print("\n[bold blue]Step 3/4  生成内容包...[/]")
    pkg = _run(create_content(
        chosen.idea.title,
        chosen.idea.angle,
        skill=skill,
        viral_score=chosen.score.total,
        generate_cover=not no_cover,
    ))

    console.print(Panel(
        "[cyan]候选标题:[/]\n" + "\n".join(f"  {i+1}. {t}" for i, t in enumerate(pkg.candidate_titles)) +
        f"\n\n[dim]正文 {len(pkg.body)} 字[/]",
        title="✅ 内容包已生成",
        border_style="green",
    ))

    if pkg.screening:
        console.print(f"[yellow]点映团评分: {pkg.screening.overall_score}/100[/]")

    if pkg.cover_paths:
        console.print(f"[green]封面图:[/] {', '.join(str(p) for p in pkg.cover_paths)}")

    for pv in pkg.platform_versions:
        console.print(f"  📱 {pv.platform}: {pv.title}")

    console.print(f"\n[bold green]全流程完成！[/] 内容包保存在 output/content/")


# ── skills ──────────────────────────────────────────────────────────────────

@app.command()
def skills():
    """列出已保存的风格 Skill"""
    from core.store import list_skills as _list

    items = _run(_list())
    if not items:
        console.print("[dim]暂无已保存的风格Skill。运行 ripple distill <博主名> 来创建。[/]")
        return

    table = Table(title="🗂️ 已保存的风格Skill", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("博主")
    table.add_column("领域")
    table.add_column("创建时间")
    for s in items:
        table.add_row(s["id"], s["blogger"], s["domain"], s["created_at"][:19])
    console.print(table)


# ── ui ──────────────────────────────────────────────────────────────────────

@app.command()
def ui(
    port: int = typer.Option(7860, "--port", help="Web UI 端口"),
    share: bool = typer.Option(False, "--share", help="创建公共链接"),
):
    """启动 Gradio Web UI"""
    from ui.app import create_app, CSS, THEME

    console.print(Panel(
        f"[bold green]启动 Web UI...[/]\n"
        f"地址: http://localhost:{port}",
        title="🌐 Ripple Web UI",
    ))

    web_app = create_app()
    web_app.launch(
        server_name="0.0.0.0", server_port=port, share=share,
        css=CSS, theme=THEME,
    )


# ── helpers ─────────────────────────────────────────────────────────────────

def _bar(value: int, width: int = 20) -> str:
    filled = round(value / 100 * width)
    if value >= 80:
        color = "green"
    elif value >= 60:
        color = "yellow"
    else:
        color = "red"
    return f"[{color}]{'█' * filled}{'░' * (width - filled)}[/{color}]"


def _temp_dir() -> Path:
    p = Path(__file__).resolve().parent.parent / "output" / ".cache"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _save_temp(name: str, data) -> None:
    path = _temp_dir() / name
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_temp(name: str) -> list | dict | None:
    path = _temp_dir() / name
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_temp_text(name: str) -> str:
    path = _temp_dir() / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


if __name__ == "__main__":
    app()
