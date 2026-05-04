"""Idea Tab — generate topic ideas with streaming output."""

from __future__ import annotations

import gradio as gr

from engines.idea_engine import generate_ideas_stream


def build_idea_tab():
    gr.Markdown(
        "### 选题灵感引擎 — AI 帮你想 10+ 个选题点子\n"
        "输入你的领域，AI 会基于同行雷达数据和最新趋势，\n"
        "生成一批有创意的选题方向，每个都标注灵感来源。"
    )

    with gr.Row():
        domain_input = gr.Textbox(
            label="内容领域",
            placeholder="如：美食探店、职场效率...",
            scale=3,
        )
        context_input = gr.Textbox(
            label="补充信息（可选）",
            placeholder="你的特长、受众特点、想避免的方向...",
            scale=3,
        )
        count_input = gr.Slider(
            minimum=5, maximum=20, value=12, step=1,
            label="选题数量",
            scale=1,
        )

    gen_btn = gr.Button("💡 生成选题灵感", variant="primary")

    status = gr.Markdown("", visible=False)
    output = gr.Markdown(
        value="*输入领域后点击生成，AI 将流式输出选题灵感...*",
    )

    async def run_generate(domain: str, context: str, count: int):
        if not domain.strip():
            yield {
                status: gr.update(value="⚠️ 请输入内容领域", visible=True),
                output: gr.update(),
            }
            return

        yield {
            status: gr.update(
                value="🔍 搜索同行数据 + 最新动态...",
                visible=True,
            ),
            output: gr.update(value=""),
        }

        full_text = ""
        try:
            async for chunk in generate_ideas_stream(
                domain.strip(),
                user_context=context.strip(),
                count=int(count),
            ):
                full_text += chunk
                yield {
                    status: gr.update(
                        value="💡 AI 正在构思选题...",
                        visible=True,
                    ),
                    output: gr.update(value=full_text),
                }
        except Exception as e:
            yield {
                status: gr.update(value=f"❌ 生成失败: {e}", visible=True),
                output: gr.update(),
            }
            return

        yield {
            status: gr.update(value="✅ 选题生成完成!", visible=True),
            output: gr.update(value=full_text),
        }

    gen_btn.click(
        fn=run_generate,
        inputs=[domain_input, context_input, count_input],
        outputs=[status, output],
    )
