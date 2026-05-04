"""Distill Tab — extract writing methodology from blogger samples."""

from __future__ import annotations

import asyncio

import gradio as gr

from engines.style_distill import distill_style


def build_distill_tab():
    gr.Markdown(
        "### 风格蒸馏 — 提炼博主的写作方法论\n"
        "两种模式：\n"
        "- **学别人**: 粘贴你欣赏的博主的内容样本，AI 提炼出 TA 的方法论\n"
        "- **学自己**: 粘贴你自己的过往内容，AI 帮你发现自己的风格特征\n\n"
        "蒸馏输出的是**方法论框架**（标题公式、内容结构、语气特征），不是让你变成别人。"
    )

    with gr.Row():
        blogger_input = gr.Textbox(
            label="博主名称",
            placeholder="如：影视飓风 / 我自己",
            scale=2,
        )
        domain_input = gr.Textbox(
            label="博主领域",
            placeholder="如：科技数码 / 职场效率",
            scale=2,
        )

    samples_input = gr.Textbox(
        label="内容样本（可粘贴多篇，每篇之间用 --- 分隔）",
        placeholder="在这里粘贴博主的1-3篇代表性内容...\n\n---\n\n第二篇内容...",
        lines=15,
    )

    distill_btn = gr.Button("🧪 开始蒸馏", variant="primary")

    status = gr.Markdown("", visible=False)
    output = gr.Markdown(
        value="*粘贴内容样本后点击蒸馏，AI 将分析并提炼写作方法论...*",
    )

    async def run_distill(blogger: str, domain: str, samples_text: str):
        if not blogger.strip():
            yield {
                status: gr.update(value="⚠️ 请输入博主名称", visible=True),
                output: gr.update(),
            }
            return
        if not samples_text.strip():
            yield {
                status: gr.update(value="⚠️ 请粘贴至少一篇内容样本", visible=True),
                output: gr.update(),
            }
            return

        samples = [s.strip() for s in samples_text.split("---") if s.strip()]
        if not samples:
            yield {
                status: gr.update(value="⚠️ 未检测到有效内容样本", visible=True),
                output: gr.update(),
            }
            return

        yield {
            status: gr.update(
                value=f"🧪 正在蒸馏 {blogger} 的风格（{len(samples)} 篇样本）...",
                visible=True,
            ),
            output: gr.update(value=""),
        }

        try:
            skill = await distill_style(
                blogger.strip(),
                domain.strip() or "综合",
                samples,
            )
        except Exception as e:
            yield {
                status: gr.update(value=f"❌ 蒸馏失败: {e}", visible=True),
                output: gr.update(),
            }
            return

        report = f"""## 🧪 蒸馏结果 — {skill.blogger}

**Skill ID**: `{skill.skill_id}` （可在内容创作中引用）
**领域**: {skill.domain}

---

### 📝 标题公式模板
"""
        for i, f in enumerate(skill.title_formulas, 1):
            report += f"{i}. {f}\n"

        report += f"""
### 📐 内容结构框架
{skill.content_structure}

### 🎭 语气与修辞特征
"""
        for t in skill.tone_features:
            report += f"- {t}\n"

        report += "\n### 🎣 Hook 手法\n"
        for h in skill.hooks:
            report += f"- {h}\n"

        report += "\n### 🎯 选题偏好\n"
        for p in skill.topic_preferences:
            report += f"- {p}\n"

        report += f"\n### 😊 Emoji 风格\n{skill.emoji_style}\n"

        report += f"""
---
> 💡 **使用提示**: 在"内容创作"Tab 中，输入 Skill ID `{skill.skill_id}`，
> AI 会用这套方法论来指导内容生成。
"""

        yield {
            status: gr.update(value="✅ 蒸馏完成!", visible=True),
            output: gr.update(value=report),
        }

    distill_btn.click(
        fn=run_distill,
        inputs=[blogger_input, domain_input, samples_input],
        outputs=[status, output],
    )
