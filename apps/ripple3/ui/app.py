"""Ripple 3.0 — Modern single-page chat UI.

Replaces the 6-tab layout with a ChatGPT/Gemini-style conversational
interface. All features are accessible through natural language — the
intent router automatically dispatches to the right engine.
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
    dispatch_chat,
)

log = logging.getLogger(__name__)


# ── CSS ──────────────────────────────────────────────────────────────────────

CSS = """
/* ── Global ────────────────────────────────────────── */
.gradio-container {
    max-width: 960px !important;
    margin: 0 auto !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
                 sans-serif !important;
}

/* Hide default footer */
footer { display: none !important; }

/* ── Header ────────────────────────────────────────── */
.ripple-header {
    text-align: center;
    padding: 24px 16px 8px;
}
.ripple-header h1 {
    font-size: 28px !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #3B82F6, #8B5CF6) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    margin-bottom: 4px !important;
}
.ripple-header p {
    color: #64748b !important;
    font-size: 15px !important;
    margin: 0 !important;
}

/* ── Welcome cards ─────────────────────────────────── */
.welcome-area {
    max-width: 720px;
    margin: 20px auto 8px;
}
.welcome-grid {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 12px !important;
    padding: 0 8px;
}
.welcome-card {
    border: 1px solid #e2e8f0 !important;
    border-radius: 14px !important;
    padding: 18px 16px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    background: #ffffff !important;
    text-align: left !important;
}
.welcome-card:hover {
    border-color: #3B82F6 !important;
    box-shadow: 0 2px 12px rgba(59,130,246,0.12) !important;
    transform: translateY(-1px) !important;
}
.welcome-card .card-icon {
    font-size: 24px;
    margin-bottom: 6px;
}
.welcome-card .card-title {
    font-weight: 600 !important;
    font-size: 15px !important;
    color: #1e293b !important;
    margin-bottom: 4px !important;
}
.welcome-card .card-desc {
    font-size: 13px !important;
    color: #64748b !important;
    line-height: 1.4 !important;
}

/* ── Chat area ─────────────────────────────────────── */
.chat-area {
    max-width: 960px;
    margin: 0 auto;
}
#chatbot {
    border: none !important;
    box-shadow: none !important;
}
#chatbot .message {
    border-radius: 16px !important;
    padding: 14px 18px !important;
    line-height: 1.65 !important;
    font-size: 15px !important;
}
#chatbot .user {
    background: linear-gradient(135deg, #3B82F6, #6366F1) !important;
    color: white !important;
    border-radius: 16px 16px 4px 16px !important;
}
#chatbot .bot {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 16px 16px 16px 4px !important;
}
#chatbot .bot table {
    font-size: 13px !important;
    border-collapse: collapse !important;
    width: 100% !important;
    margin: 8px 0 !important;
}
#chatbot .bot table th,
#chatbot .bot table td {
    padding: 6px 10px !important;
    border: 1px solid #e2e8f0 !important;
    text-align: left !important;
}
#chatbot .bot table th {
    background: #f1f5f9 !important;
    font-weight: 600 !important;
}

/* ── Input area ────────────────────────────────────── */
.input-area {
    max-width: 720px;
    margin: 0 auto;
}
.input-area textarea {
    border-radius: 24px !important;
    padding: 14px 20px !important;
    font-size: 15px !important;
    border: 2px solid #e2e8f0 !important;
    transition: border-color 0.2s !important;
}
.input-area textarea:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
}

/* ── Quick actions ─────────────────────────────────── */
.quick-actions {
    display: flex !important;
    gap: 8px !important;
    flex-wrap: wrap !important;
    justify-content: center !important;
    padding: 4px 8px 12px !important;
}
.quick-actions button {
    border-radius: 20px !important;
    padding: 6px 16px !important;
    font-size: 13px !important;
    border: 1px solid #e2e8f0 !important;
    background: white !important;
    color: #475569 !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
}
.quick-actions button:hover {
    border-color: #3B82F6 !important;
    color: #3B82F6 !important;
    background: #eff6ff !important;
}

/* ── Status indicator ──────────────────────────────── */
.status-bar {
    text-align: center;
    padding: 4px;
}
.status-bar p {
    font-size: 13px !important;
    color: #3B82F6 !important;
    animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* ── Sidebar ───────────────────────────────────────── */
.sidebar-section {
    padding: 8px 0;
}
.sidebar-section h3 {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #64748b !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    margin-bottom: 8px !important;
}
.sidebar-section .item {
    padding: 8px 12px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    color: #334155;
}
.sidebar-section .item:hover {
    background: #f1f5f9;
}

/* ── Dark mode adjustments ─────────────────────────── */
.dark .welcome-card {
    background: #1e293b !important;
    border-color: #334155 !important;
}
.dark .welcome-card:hover {
    border-color: #60a5fa !important;
}
.dark .welcome-card .card-title { color: #f1f5f9 !important; }
.dark .welcome-card .card-desc { color: #94a3b8 !important; }
.dark #chatbot .bot {
    background: #1e293b !important;
    border-color: #334155 !important;
}
.dark #chatbot .bot table th { background: #334155 !important; }
.dark .quick-actions button {
    background: #1e293b !important;
    border-color: #334155 !important;
    color: #94a3b8 !important;
}

/* ── Responsive ────────────────────────────────────── */
@media (max-width: 640px) {
    .welcome-grid {
        grid-template-columns: 1fr !important;
    }
    .ripple-header h1 { font-size: 22px !important; }
}
"""


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
        })

        # ── Sidebar ──────────────────────────────────────────────────────
        with gr.Sidebar(open=True, label="Ripple"):
            gr.Markdown(
                "### Ripple\n"
                "KOC 内容灵感助手",
            )
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

        # ── Welcome cards (visible when no messages) ─────────────────────
        with gr.Group(visible=True, elem_classes=["welcome-area"]) as welcome_group:
            gr.HTML(
                '<div class="welcome-grid">'
                + "".join(
                    f'<div class="welcome-card" onclick="'
                    f"document.querySelector('#msg-input textarea').value = '{card['prompt']}';"
                    f"document.querySelector('#msg-input textarea').dispatchEvent(new Event('input'));"
                    f'">'
                    f'<div class="card-icon">{card["icon"]}</div>'
                    f'<div class="card-title">{card["title"]}</div>'
                    f'<div class="card-desc">{card["desc"]}</div>'
                    f"</div>"
                    for card in WELCOME_CARDS
                )
                + "</div>"
            )

        # ── Status bar ───────────────────────────────────────────────────
        status_display = gr.Markdown("", visible=False, elem_classes=["status-bar"])

        # ── Chatbot ──────────────────────────────────────────────────────
        chatbot = gr.Chatbot(
            elem_id="chatbot",
            height=520,
            show_label=False,
            render_markdown=True,
            placeholder="",
        )

        # ── Quick action buttons ─────────────────────────────────────────
        with gr.Row(elem_classes=["quick-actions"]):
            qa1 = gr.Button("💡 帮我想选题", size="sm")
            qa2 = gr.Button("🔍 分析这个领域", size="sm")
            qa3 = gr.Button("✍️ 写小红书笔记", size="sm")
            qa4 = gr.Button("📊 评估爆款潜力", size="sm")

        # ── Input ────────────────────────────────────────────────────────
        with gr.Row(elem_classes=["input-area"]):
            msg_input = gr.Textbox(
                placeholder="告诉我你想做什么内容... (Enter 发送)",
                show_label=False,
                container=False,
                scale=8,
                elem_id="msg-input",
            )
            send_btn = gr.Button("发送", variant="primary", scale=1, min_width=80)

        # ── Chat handler ─────────────────────────────────────────────────
        async def respond(message: str, chat_history: list[dict], state: dict):
            if not message or not message.strip():
                yield chat_history, state, gr.update(), gr.update(visible=True)
                return

            message = message.strip()

            chat_history = chat_history or []
            chat_history.append({"role": "user", "content": message})

            yield (
                chat_history,
                state,
                gr.update(value="", visible=True),
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
            else:
                stream = dispatch_chat(message, plain_history)

            chat_history.append({"role": "assistant", "content": ""})

            async for chunk in stream:
                chat_history[-1]["content"] += chunk
                yield (
                    chat_history,
                    state,
                    gr.update(visible=True),
                    gr.update(visible=False),
                )

            yield (
                chat_history,
                state,
                gr.update(visible=False),
                gr.update(visible=False),
            )

        inputs = [msg_input, chatbot, session_state]
        outputs = [chatbot, session_state, status_display, welcome_group]

        msg_input.submit(
            fn=respond, inputs=inputs, outputs=outputs,
        )
        send_btn.click(
            fn=respond, inputs=inputs, outputs=outputs,
        )

        # ── Quick action handlers ────────────────────────────────────────
        def set_msg(text):
            return text

        qa1.click(fn=lambda: "帮我想10个选题灵感", outputs=[msg_input])
        qa2.click(fn=lambda: "帮我分析一下这个领域的内容生态", outputs=[msg_input])
        qa3.click(fn=lambda: "帮我写一篇小红书笔记", outputs=[msg_input])
        qa4.click(fn=lambda: "帮我评估这个选题的爆款潜力", outputs=[msg_input])

        # ── Sidebar handlers ─────────────────────────────────────────────
        sidebar_radar.click(fn=lambda: "帮我分析一下这个领域的博主和内容生态", outputs=[msg_input])
        sidebar_idea.click(fn=lambda: "帮我想一些有创意的选题点子", outputs=[msg_input])
        sidebar_predict.click(fn=lambda: "帮我评估这个选题能不能火", outputs=[msg_input])
        sidebar_create.click(fn=lambda: "帮我写一篇完整的内容", outputs=[msg_input])

        def clear_chat():
            return [], {"domain": "", "last_ideas": [], "last_topic": ""}, gr.update(visible=True)

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
