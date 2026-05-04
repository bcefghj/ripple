"""Radar Tab — peer radar: domain ecosystem analysis + blogger discovery."""

from __future__ import annotations

import gradio as gr

from engines.idea_engine import scan_radar_stream
from core.citations import CitationList


def build_radar_tab():
    gr.Markdown(
        "### 同行雷达 — 看看你的领域里谁在做什么\n"
        "输入你感兴趣的内容领域，AI 会搜索并分析：\n"
        "- 该领域的 **头部博主/达人** 推荐列表\n"
        "- 近期 **热门话题** 和 **上升趋势**\n"
        "- **蓝海机会**（有需求但缺少好内容的方向）\n"
        "- **入场建议**（KOC 新手如何切入）"
    )

    with gr.Row():
        domain_input = gr.Textbox(
            label="内容领域",
            placeholder="如：美食探店、职场效率、数码测评、穿搭、健身、育儿...",
            scale=4,
        )
        scan_btn = gr.Button("🔍 开始扫描", variant="primary", scale=1)

    status = gr.Markdown("", visible=False)
    output = gr.Markdown(
        label="分析报告",
        value="*输入领域后点击扫描，AI 将实时输出分析报告...*",
    )

    async def run_scan(domain: str):
        if not domain.strip():
            yield {
                status: gr.update(value="⚠️ 请输入内容领域", visible=True),
                output: gr.update(),
            }
            return

        yield {
            status: gr.update(
                value="🔍 正在搜索同行内容 + 博主信息 + 最新动态...",
                visible=True,
            ),
            output: gr.update(value=""),
        }

        full_text = ""
        try:
            async for chunk in scan_radar_stream(domain.strip()):
                full_text += chunk
                yield {
                    status: gr.update(
                        value="📊 AI 正在分析领域生态...",
                        visible=True,
                    ),
                    output: gr.update(value=full_text),
                }
        except Exception as e:
            yield {
                status: gr.update(value=f"❌ 分析失败: {e}", visible=True),
                output: gr.update(),
            }
            return

        yield {
            status: gr.update(value="✅ 分析完成!", visible=True),
            output: gr.update(value=full_text),
        }

    scan_btn.click(
        fn=run_scan,
        inputs=[domain_input],
        outputs=[status, output],
    )

    domain_input.submit(
        fn=run_scan,
        inputs=[domain_input],
        outputs=[status, output],
    )
