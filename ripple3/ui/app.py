"""Ripple 3.0 — Modern single-page chat UI with responsive design.

All features accessible through natural language — the intent router
automatically dispatches to the right engine with parallel search.
"""

from __future__ import annotations

import sys
import asyncio
import logging
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import gradio as gr

from core.intent import (
    classify_intent,
    dispatch_radar,
    dispatch_idea,
    dispatch_predict,
    dispatch_create,
    dispatch_distill,
    dispatch_chat,
)
from core import store

log = logging.getLogger(__name__)


# ── Load CSS from external file ──────────────────────────────────────────────

_CSS_PATH = Path(__file__).parent / "style.css"
CSS = _CSS_PATH.read_text(encoding="utf-8") if _CSS_PATH.exists() else ""

THEME = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="violet",
    neutral_hue="slate",
    font=gr.themes.GoogleFont("Inter"),
)


# ── Welcome card data ────────────────────────────────────────────────────────

WELCOME_CARDS = [
    {
        "icon": "🔍",
        "title": "探索领域",
        "desc": "了解你感兴趣领域的内容生态、热门博主和入场机会",
        "prompt": "我对美食探店感兴趣，帮我分析一下这个领域的内容生态",
    },
    {
        "icon": "💡",
        "title": "发现选题",
        "desc": "AI 帮你想出有创意的选题点子，每个都有数据支撑",
        "prompt": "帮我想10个职场效率类的选题灵感",
    },
    {
        "icon": "🔮",
        "title": "评估选题",
        "desc": "12维度深度评分，告诉你这个选题能不能火",
        "prompt": "帮我评估一下「月薪3000吃遍北京」这个选题的爆款潜力",
    },
    {
        "icon": "✍️",
        "title": "创作内容",
        "desc": "从选题到多平台文案，一站式完成内容创作",
        "prompt": "帮我写一篇关于「5个提升工作效率的AI工具推荐」的小红书笔记",
    },
]


# ── App builder ──────────────────────────────────────────────────────────────

def create_app() -> gr.Blocks:
    with gr.Blocks(
        title="Ripple — KOC 内容灵感助手",
        fill_height=True,
    ) as app:

        # Session state
        session_state = gr.State({
            "domain": "",
            "last_ideas": [],
            "last_topic": "",
            "conv_id": "",
        })

        # ── Sidebar ──────────────────────────────────────────────────────
        with gr.Sidebar(open=False, label="Ripple"):
            gr.Markdown("### Ripple\nKOC 内容灵感助手")
            new_chat_btn = gr.Button("+ 新对话", variant="secondary", size="sm")

            gr.Markdown("---")
            gr.Markdown(
                '<div class="sidebar-section">'
                "<h3>快捷入口</h3>"
                "</div>",
            )
            sidebar_radar = gr.Button("🔍 探索领域", size="sm", variant="secondary")
            sidebar_idea = gr.Button("💡 发现选题", size="sm", variant="secondary")
            sidebar_predict = gr.Button("🔮 评估选题", size="sm", variant="secondary")
            sidebar_create = gr.Button("✍️ 创作内容", size="sm", variant="secondary")
            sidebar_distill = gr.Button("🎨 分析风格", size="sm", variant="secondary")

            gr.Markdown("---")
            gr.Markdown(
                "**使用提示**\n\n"
                "直接用自然语言告诉我你想做什么，\n"
                "比如「我想做美食类内容」或\n"
                "「帮我写一篇小红书笔记」。\n\n"
                "Ripple 会自动理解你的需求。"
            )

        # ── Header ───────────────────────────────────────────────────────
        gr.HTML(
            '<div class="ripple-header">'
            "<h1>Ripple</h1>"
            "<p>你的 KOC 内容灵感助手 — 从选题到创作，对话即完成</p>"
            "</div>"
        )

        # ── Welcome cards (Gradio native buttons) ────────────────────────
        with gr.Group(visible=True, elem_classes=["welcome-area"]) as welcome_group:
            with gr.Row(elem_classes=["welcome-grid"]):
                card_btns = []
                for card in WELCOME_CARDS:
                    btn = gr.Button(
                        f"{card['icon']} {card['title']}\n{card['desc']}",
                        variant="secondary",
                        size="sm",
                        elem_classes=["welcome-card"],
                    )
                    card_btns.append((btn, card["prompt"]))

        # ── Status bar ───────────────────────────────────────────────────
        status_display = gr.Markdown("", visible=False, elem_classes=["status-bar"])

        # ── Chatbot ──────────────────────────────────────────────────────
        chatbot = gr.Chatbot(
            elem_id="chatbot",
            height="60vh",
            show_label=False,
            render_markdown=True,
            placeholder="",
        )

        # ── Quick action buttons ─────────────────────────────────────────
        with gr.Row(elem_classes=["quick-actions"]):
            qa1 = gr.Button("💡 帮我想选题", size="sm")
            qa2 = gr.Button("🔍 分析领域", size="sm")
            qa3 = gr.Button("✍️ 写笔记", size="sm")
            qa4 = gr.Button("📊 评估爆款", size="sm")

        # ── Input ────────────────────────────────────────────────────────
        with gr.Row(elem_classes=["input-area"]):
            msg_input = gr.Textbox(
                placeholder="告诉我你想做什么内容... (Enter 发送)",
                show_label=False,
                container=False,
                scale=8,
                elem_id="msg-input",
                lines=1,
                max_lines=4,
            )
            send_btn = gr.Button("➤", variant="primary", scale=1, min_width=52)

        # ── Chat handler ─────────────────────────────────────────────────
        async def respond(message: str, chat_history: list[dict], state: dict):
            if not message or not message.strip():
                yield chat_history, state, gr.update(), gr.update(visible=True)
                return

            message = message.strip()
            chat_history = chat_history or []
            chat_history.append({"role": "user", "content": message})

            if not state.get("conv_id"):
                state["conv_id"] = store.new_conversation_id()

            yield (
                chat_history,
                state,
                gr.update(value="", visible=False),
                gr.update(visible=False),
            )

            plain_history = [
                {"role": m["role"], "content": m["content"]}
                for m in chat_history[:-1]
            ]

            intent = await classify_intent(message, plain_history)
            log.info("Intent: %s | domain=%s topic=%s", intent.intent, intent.domain, intent.topic)

            if intent.domain:
                state["domain"] = intent.domain
            if intent.topic:
                state["last_topic"] = intent.topic

            domain = intent.domain or state.get("domain", "")
            topic = intent.topic or state.get("last_topic", "")

            if intent.intent == "radar" and domain:
                stream = dispatch_radar(domain, plain_history)
            elif intent.intent == "idea" and domain:
                stream = dispatch_idea(domain, message, plain_history)
            elif intent.intent == "predict" and topic:
                stream = dispatch_predict(topic, domain, intent.platform, plain_history)
            elif intent.intent == "create" and (topic or domain):
                create_topic = topic or f"{domain}相关内容"
                stream = dispatch_create(create_topic, domain, intent.platform, plain_history)
            elif intent.intent == "distill":
                blogger = intent.topic or intent.domain or message
                stream = dispatch_distill(blogger, domain, plain_history)
            else:
                stream = dispatch_chat(message, plain_history)

            chat_history.append({"role": "assistant", "content": ""})

            async for chunk in stream:
                chat_history[-1]["content"] += chunk
                yield (
                    chat_history,
                    state,
                    gr.update(visible=False),
                    gr.update(visible=False),
                )

            # Auto-save content for create/distill/predict intents
            final_content = chat_history[-1]["content"]
            if intent.intent in ("create", "predict", "distill") and len(final_content) > 200:
                try:
                    await store.save_content(
                        topic=topic or domain or message[:50],
                        score=None,
                        content=final_content,
                        platform=intent.platform or "通用",
                    )
                except Exception as exc:
                    log.warning("Failed to save content: %s", exc)

            # Persist conversation
            try:
                title = message[:30] + ("..." if len(message) > 30 else "")
                await store.save_conversation(
                    conv_id=state["conv_id"],
                    title=title,
                    messages=chat_history,
                    domain=state.get("domain", ""),
                )
            except Exception as exc:
                log.warning("Failed to save conversation: %s", exc)

            yield (
                chat_history,
                state,
                gr.update(visible=False),
                gr.update(visible=False),
            )

        inputs = [msg_input, chatbot, session_state]
        outputs = [chatbot, session_state, status_display, welcome_group]

        msg_input.submit(fn=respond, inputs=inputs, outputs=outputs)
        send_btn.click(fn=respond, inputs=inputs, outputs=outputs)

        # ── Welcome card click → set input + auto-submit ─────────────────
        for btn, prompt_text in card_btns:
            btn.click(
                fn=lambda p=prompt_text: p,
                outputs=[msg_input],
            ).then(
                fn=respond,
                inputs=inputs,
                outputs=outputs,
            )

        # ── Quick action handlers ────────────────────────────────────────
        qa1.click(fn=lambda: "帮我想10个选题灵感", outputs=[msg_input])
        qa2.click(fn=lambda: "帮我分析一下这个领域的内容生态", outputs=[msg_input])
        qa3.click(fn=lambda: "帮我写一篇小红书笔记", outputs=[msg_input])
        qa4.click(fn=lambda: "帮我评估这个选题的爆款潜力", outputs=[msg_input])

        # ── Sidebar handlers ─────────────────────────────────────────────
        sidebar_radar.click(fn=lambda: "帮我分析一下这个领域的博主和内容生态", outputs=[msg_input])
        sidebar_idea.click(fn=lambda: "帮我想一些有创意的选题点子", outputs=[msg_input])
        sidebar_predict.click(fn=lambda: "帮我评估这个选题能不能火", outputs=[msg_input])
        sidebar_create.click(fn=lambda: "帮我写一篇完整的内容", outputs=[msg_input])
        sidebar_distill.click(fn=lambda: "帮我分析一下这位博主的创作风格", outputs=[msg_input])

        def clear_chat():
            return (
                [],
                {"domain": "", "last_ideas": [], "last_topic": "", "conv_id": ""},
                gr.update(visible=True),
            )

        new_chat_btn.click(
            fn=clear_chat,
            outputs=[chatbot, session_state, welcome_group],
        )

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    application = create_app()
    application.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        css=CSS,
        theme=THEME,
    )
