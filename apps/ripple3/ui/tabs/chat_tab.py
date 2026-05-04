"""Chat Tab — conversational AI assistant that guides users through the full workflow."""

from __future__ import annotations

import gradio as gr

from core.llm import chat_deep_stream


_SYSTEM = """你是 Ripple 3.0 — KOC 内容灵感助手。你帮助 KOC 博主完成从选题到创作的全流程。

你的能力：
1. **同行雷达**: 分析某个领域的内容生态、推荐值得关注的头部博主
2. **选题灵感**: 生成10-20个有创意的选题点子
3. **爆款预测**: 对选题进行12维度评分（含影视飓风HKRR模型）
4. **风格蒸馏**: 分析博主写作风格，提炼可复用的方法论
5. **内容创作**: 生成完整内容包（文案+封面+多平台适配）

你的工作方式：
- 用中文回答，语气亲和专业
- 如果用户不知道做什么，主动引导他们：先了解领域 → 看同行 → 选题 → 预测 → 创作
- 给出具体、可操作的建议
- 推荐用户使用对应的专业Tab来获得更深度的分析
- 你可以直接帮用户分析选题、评估内容、提供创作建议

对于三类用户：
- 纯小白：引导他们先确定领域，然后用同行雷达了解生态
- 有方向但不会执行：帮他们分析选题方向，推荐用爆款预测
- 有经验的老手：帮他们蒸馏风格、提效创作

重要：你是一个真正有用的助手，不是一个只会说"请去使用XX功能"的引导页。
当用户提问时，直接给出有价值的分析和建议。"""


def build_chat_tab():
    gr.Markdown(
        "### 和 Ripple 聊聊你的内容创作\n"
        "不知道做什么？告诉我你的领域，我帮你从零开始。\n"
        "已有方向？直接问我，我帮你分析选题、评估爆款潜力。"
    )

    async def respond(message: str, history: list[dict]):
        history = history or []
        messages = [{"role": "system", "content": _SYSTEM}]
        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": message})

        partial = ""
        async for chunk in chat_deep_stream(messages, max_tokens=4096, temperature=0.7):
            partial += chunk
            yield partial

    gr.ChatInterface(
        fn=respond,
        title=None,
        examples=[
            "我对美食探店感兴趣，但不知道做什么内容，能帮我分析一下吗？",
            "我是做职场效率的博主，最近灵感枯竭，有什么新选题推荐？",
            "帮我分析一下「月薪3000吃遍北京」这个选题的爆款潜力",
            "小红书和视频号的内容风格有什么区别？我该怎么适配？",
            "影视飓风的HKRR模型是什么？我怎么用在自己的内容上？",
        ],
        fill_height=True,
    )
