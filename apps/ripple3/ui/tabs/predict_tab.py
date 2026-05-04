"""Predict Tab — viral potential prediction with deep analysis."""

from __future__ import annotations

import gradio as gr

from engines.idea_engine import TopicIdea
from engines.viral_predictor import predict_single_stream


def build_predict_tab():
    gr.Markdown(
        "### 爆款潜力预测 — 12维度深度评分\n"
        "输入选题信息，AI 会搜索竞品数据，用 **8基础维度 + 影视飓风HKRR模型** 进行深度评估。\n"
        "每个维度都会给出评分理由、数据证据和提升建议。"
    )

    with gr.Row():
        title_input = gr.Textbox(
            label="选题标题",
            placeholder="如：月薪3000吃遍北京——7天不重复的工作餐攻略",
            scale=3,
        )
        domain_input = gr.Textbox(
            label="所属领域",
            placeholder="如：美食探店",
            scale=2,
        )

    with gr.Row():
        angle_input = gr.Textbox(
            label="切入角度",
            placeholder="如：省钱实用攻略+个人体验",
            scale=3,
        )
        audience_input = gr.Textbox(
            label="目标受众",
            placeholder="如：在北京工作的年轻打工人",
            scale=2,
        )

    with gr.Row():
        format_input = gr.Textbox(
            label="内容形式",
            placeholder="如：图文清单",
            scale=2,
        )
        platform_input = gr.Dropdown(
            choices=["小红书", "视频号", "公众号", "抖音", "B站"],
            value="小红书",
            label="目标平台",
            scale=1,
        )

    predict_btn = gr.Button("🔮 开始预测", variant="primary")

    status = gr.Markdown("", visible=False)
    output = gr.Markdown(
        value="*输入选题后点击预测，AI 将实时输出12维度分析报告...*",
    )

    async def run_predict(title, domain, angle, audience, format_sug, platform):
        if not title.strip():
            yield {
                status: gr.update(value="⚠️ 请输入选题标题", visible=True),
                output: gr.update(),
            }
            return

        idea = TopicIdea(
            title=title.strip(),
            angle=angle.strip() or "通用角度",
            audience=audience.strip() or "泛人群",
            format_suggestion=format_sug.strip() or "图文",
            inspiration_source="用户输入",
        )

        yield {
            status: gr.update(
                value="🔍 搜索竞品数据...",
                visible=True,
            ),
            output: gr.update(value=""),
        }

        full_text = ""
        try:
            async for chunk in predict_single_stream(
                idea,
                domain.strip() or "综合",
                target_platform=platform,
            ):
                full_text += chunk
                yield {
                    status: gr.update(
                        value="🔮 AI 正在逐维度深度分析...",
                        visible=True,
                    ),
                    output: gr.update(value=full_text),
                }
        except Exception as e:
            yield {
                status: gr.update(value=f"❌ 预测失败: {e}", visible=True),
                output: gr.update(),
            }
            return

        yield {
            status: gr.update(value="✅ 预测分析完成!", visible=True),
            output: gr.update(value=full_text),
        }

    predict_btn.click(
        fn=run_predict,
        inputs=[title_input, domain_input, angle_input,
                audience_input, format_input, platform_input],
        outputs=[status, output],
    )
