"""Create Tab — full content creation with streaming output and cover image display."""

from __future__ import annotations

import gradio as gr

from engines.content_create import create_content_stream
from engines.style_distill import load_skill


def build_create_tab():
    gr.Markdown(
        "### 内容创作 — 一键生成完整内容包\n"
        "输入选题信息，AI 会按流程输出：\n"
        "1. 内容大纲（含情绪曲线设计）\n"
        "2. 3个候选标题\n"
        "3. 完整正文（1500-2500字）\n"
        "4. 多平台适配版本（视频号/公众号/小红书/抖音）\n"
        "5. AI 点映团评审意见"
    )

    with gr.Row():
        topic_input = gr.Textbox(
            label="选题标题",
            placeholder="如：月薪3000吃遍北京——7天不重复的工作餐攻略",
            scale=3,
        )
        angle_input = gr.Textbox(
            label="切入角度",
            placeholder="如：省钱攻略+真实体验",
            scale=2,
        )

    with gr.Row():
        skill_input = gr.Textbox(
            label="风格 Skill ID（可选）",
            placeholder="来自蒸馏Tab的 Skill ID，留空使用通用风格",
            scale=2,
        )
        idea_input = gr.Textbox(
            label="你自己的想法（可选）",
            placeholder="你想在文章中加入的个人经历、观点...",
            scale=3,
        )

    score_input = gr.Slider(
        minimum=0, maximum=100, value=0, step=1,
        label="爆款预测分（来自预测Tab，0=未评估）",
    )

    create_btn = gr.Button("✍️ 开始创作", variant="primary")

    status = gr.Markdown("", visible=False)
    output = gr.Markdown(
        value="*输入选题后点击创作，AI 将流式输出完整内容包...*",
    )

    async def run_create(topic, angle, skill_id, user_idea, score):
        if not topic.strip():
            yield {
                status: gr.update(value="⚠️ 请输入选题标题", visible=True),
                output: gr.update(),
            }
            return

        skill = None
        if skill_id.strip():
            try:
                skill = await load_skill(skill_id.strip())
                if skill:
                    yield {
                        status: gr.update(
                            value=f"✅ 已加载风格: {skill.blogger}，开始创作...",
                            visible=True,
                        ),
                        output: gr.update(value=""),
                    }
                else:
                    yield {
                        status: gr.update(
                            value=f"⚠️ 未找到 Skill {skill_id}，使用通用风格...",
                            visible=True,
                        ),
                        output: gr.update(value=""),
                    }
            except Exception:
                pass

        if not skill:
            yield {
                status: gr.update(
                    value="✍️ 使用通用风格，开始创作...",
                    visible=True,
                ),
                output: gr.update(value=""),
            }

        full_text = ""
        try:
            async for chunk in create_content_stream(
                topic.strip(),
                angle.strip() or "通用角度",
                skill=skill,
                user_idea=user_idea.strip(),
                viral_score=int(score) if score > 0 else None,
            ):
                full_text += chunk
                yield {
                    status: gr.update(
                        value="✍️ AI 正在创作内容...",
                        visible=True,
                    ),
                    output: gr.update(value=full_text),
                }
        except Exception as e:
            yield {
                status: gr.update(value=f"❌ 创作失败: {e}", visible=True),
                output: gr.update(),
            }
            return

        yield {
            status: gr.update(value="✅ 内容创作完成!", visible=True),
            output: gr.update(value=full_text),
        }

    create_btn.click(
        fn=run_create,
        inputs=[topic_input, angle_input, skill_input, idea_input, score_input],
        outputs=[status, output],
    )
