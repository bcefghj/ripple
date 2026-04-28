"""
Ripple × MiniMax 真实 API 实测
3 个符合腾讯 AI 赛题 5 的场景:
  1. 视频号 KOC - 科技 / AI 评测
  2. 公众号 KOC - 职场成长
  3. 小红书 + 视频号 双平台 KOC - 宠物萌宠

使用方式:
    cd ripple/apps/api
    python3 tests/test_real_minimax.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
if not MINIMAX_API_KEY:
    raise SystemExit("请设置环境变量 MINIMAX_API_KEY，例如: export MINIMAX_API_KEY=sk-...")
MINIMAX_API_BASE = "https://api.minimax.chat/v1"
MINIMAX_MODEL = "MiniMax-M2.7"


async def minimax_call(messages, temperature=0.7, max_tokens=1500) -> Dict[str, Any]:
    """直接调用 MiniMax API"""
    import httpx

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{MINIMAX_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {MINIMAX_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MINIMAX_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        r.raise_for_status()
        data = r.json()

    raw_content = data["choices"][0]["message"]["content"]
    # 去掉推理模型的 <think>...</think> 标签,只保留正式回复
    import re as _re
    clean = _re.sub(r"<think>.*?</think>", "", raw_content, flags=_re.DOTALL).strip()
    usage = data.get("usage", {})
    return {
        "message": {"role": "assistant", "content": clean},
        "tool_calls": [],
        "stop_reason": "completed",
        "usage": {
            "total_tokens": usage.get("total_tokens", 0),
            "cost_usd": usage.get("total_tokens", 0) * 0.000002,
        },
        "_raw_content": clean,
    }


# ============================================================
# 三个测试场景
# ============================================================

SCENARIOS = [
    {
        "id": "scenario_1",
        "name": "🤖 视频号 KOC - AI & 科技评测",
        "topic_seed": "国内大模型哪家最强？普通人怎么选",
        "category": "科技",
        "target_platforms": ["channels", "wechat_official"],
        "koc_context": "专注 AI 工具评测的视频号 KOC,粉丝 3.2 万,理工背景,风格:数据说话、不贩卖焦虑",
        "koc_works": [
            {"title": "DeepSeek vs GPT-4o,我用了 30 天后的结论", "body": "不吹不黑,纯测试对比,从代码/写作/分析三维度来看..."},
            {"title": "国产大模型实测:月之暗面 Kimi 到底行不行", "body": "我用 Kimi 做了 20 个真实任务,结果出乎意料..."},
        ],
    },
    {
        "id": "scenario_2",
        "name": "💼 公众号 KOC - 职场 & 效率",
        "topic_seed": "职场人用 AI 提效的真实方法，不是那种套话",
        "category": "职场",
        "target_platforms": ["wechat_official", "channels"],
        "koc_context": "大厂 PM 出身的公众号创作者,粉丝 2.1 万,主写职场干货,风格:结构清晰、有具体操作步骤",
        "koc_works": [
            {"title": "我用 AI 把周报时间从 2 小时压到 15 分钟", "body": "具体 prompt 公开:第一步让 AI 整理周维度任务..."},
            {"title": "互联网 PM 的 AI 工具箱,2026 年最新版", "body": "我现在每天用到的工具就这 5 个..."},
        ],
    },
    {
        "id": "scenario_3",
        "name": "🐱 小红书 + 视频号 双平台 - 宠物萌宠",
        "topic_seed": "猫咪突然不吃饭，铲屎官最怕的事怎么处理",
        "category": "宠物",
        "target_platforms": ["xhs", "channels", "wechat_official"],
        "koc_context": "养猫 3 年的双平台 KOC,小红书 8 万粉+视频号 1.2 万粉,风格:温暖可爱、夹带专业知识,爱用 emoji",
        "koc_works": [
            {"title": "我家橘猫得了肥胖症后的减肥日记", "body": "配合兽医制定的减重计划,历经 3 个月...🐱"},
            {"title": "花 2000 元踩过的猫粮坑,不要再买这些了", "body": "亲测避坑指南来了,各价位段推荐..."},
        ],
    },
]


# ============================================================
# 单场景测试(精简版 - 4 Agent串联)
# ============================================================

async def run_scenario(s: dict) -> dict:
    """
    精简版 4 Agent 串联:
    OracleAgent(模拟) → StyleDecoder(真实LLM) → TopicStrategist(真实LLM) → ScriptWriter(真实LLM)
    """
    print(f"\n{'='*65}")
    print(f"  {s['name']}")
    print(f"  话题种子: 「{s['topic_seed']}」")
    print(f"  目标平台: {' / '.join(s['target_platforms'])}")
    print(f"{'='*65}")

    result = {"scenario": s["name"], "topic_seed": s["topic_seed"], "steps": {}}
    total_tokens = 0

    # ── Step 1: OracleAgent(快速模拟,无网络) ──
    t0 = time.time()
    print(f"\n📡 [Step 1/4] OracleAgent 早期信号扫描...")
    from agents.oracle_agent import OracleAgent
    oracle = OracleAgent()
    oracle_report = await oracle.scan(s["topic_seed"], s["category"], s["target_platforms"])
    top_trend = oracle_report.trends[0] if oracle_report.trends else None
    ms1 = int((time.time() - t0) * 1000)
    print(f"   ✓ 扫描完成 ({ms1}ms) - 发现 {len(oracle_report.trends)} 个趋势")
    if top_trend:
        print(f"   📈 Top 1: [{top_trend.confidence:.0%}] {top_trend.topic}")
        print(f"   💡 推荐角度: {top_trend.recommended_angle}")
    result["steps"]["oracle"] = {
        "trends_count": len(oracle_report.trends),
        "top_trend": top_trend.topic if top_trend else "无",
        "top_confidence": f"{top_trend.confidence:.0%}" if top_trend else "0%",
        "recommended_angle": top_trend.recommended_angle if top_trend else "",
    }

    # ── Step 2: StyleDecoder(真实 MiniMax) ──
    print(f"\n🎨 [Step 2/4] StyleDecoder 风格学习 → MiniMax {MINIMAX_MODEL}...")
    t2 = time.time()
    works_text = "\n".join([f"【{w['title']}】{w['body'][:80]}" for w in s["koc_works"]])
    style_messages = [
        {"role": "system", "content": "你是一个专业的内容风格分析师,擅长从 KOC 的历史作品中提炼风格卡片。"},
        {"role": "user", "content": f"""分析以下 KOC 的历史作品,提炼风格卡片。

KOC 背景: {s['koc_context']}

历史作品:
{works_text}

请输出 JSON,包含以下字段:
- persona: 人设定位(一句话)
- tone: 表达风格(3-5 个关键词)
- signature_phrases: 标志性表达(3 个例子)
- do: 坚持做的(3 条)
- dont: 避免的(3 条)
- title_formula: 常用标题公式

只输出 JSON,不要解释。"""}
    ]
    style_resp = await minimax_call(style_messages, temperature=0.5, max_tokens=800)
    ms2 = int((time.time() - t2) * 1000)
    total_tokens += style_resp["usage"]["total_tokens"]
    try:
        raw = style_resp["_raw_content"]
        # 提取 JSON 部分
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        style_card = json.loads(raw.strip())
    except Exception:
        style_card = {"persona": style_resp["_raw_content"][:200], "tone": "未解析"}
    print(f"   ✓ 风格学习完成 ({ms2}ms, {style_resp['usage']['total_tokens']} tokens)")
    print(f"   🎭 人设: {style_card.get('persona', 'N/A')}")
    print(f"   🗣  风格: {style_card.get('tone', 'N/A')}")
    result["steps"]["style"] = style_card

    # ── Step 3: TopicStrategist(真实 MiniMax) ──
    print(f"\n🧠 [Step 3/4] TopicStrategist 选题策略 → MiniMax...")
    t3 = time.time()
    oracle_summary = f"早期信号:Top趋势「{top_trend.topic}」({top_trend.confidence:.0%}置信度),推荐角度:{top_trend.recommended_angle},最佳平台:{','.join(top_trend.best_platforms)}" if top_trend else "无早期信号"
    strategy_messages = [
        {"role": "system", "content": "你是一位专业的社媒内容策略师,擅长结合早期信号和 KOC 风格制定选题策略。"},
        {"role": "user", "content": f"""根据以下信息,制定一份精准的选题策略。

【早期信号雷达输出】
{oracle_summary}

【KOC 风格卡片】
人设: {style_card.get('persona', '')}
风格: {style_card.get('tone', '')}
背景: {s['koc_context']}

【目标平台】{', '.join(s['target_platforms'])}

请输出 JSON:
- primary_topic: 最终选定的选题(一句话,有钩子)
- angle: 切入角度
- why_now: 为什么现在做(结合早期信号)
- target_audience: 目标受众画像
- narrative: 内容叙事框架(3-5 步)
- confidence: 选题信心(0-1)

只输出 JSON。"""}
    ]
    strategy_resp = await minimax_call(strategy_messages, temperature=0.6, max_tokens=800)
    ms3 = int((time.time() - t3) * 1000)
    total_tokens += strategy_resp["usage"]["total_tokens"]
    try:
        raw = strategy_resp["_raw_content"]
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        strategy = json.loads(raw.strip())
    except Exception:
        strategy = {"primary_topic": strategy_resp["_raw_content"][:200]}
    print(f"   ✓ 选题策略完成 ({ms3}ms, {strategy_resp['usage']['total_tokens']} tokens)")
    print(f"   📌 选题: {strategy.get('primary_topic', 'N/A')}")
    print(f"   🎯 角度: {strategy.get('angle', 'N/A')}")
    print(f"   ⏰ 为何现在: {strategy.get('why_now', 'N/A')}")
    result["steps"]["strategy"] = strategy

    # ── Step 4: ScriptWriter(真实 MiniMax) ──
    print(f"\n✍️  [Step 4/4] ScriptWriter 内容生成 → MiniMax...")
    t4 = time.time()
    platform_guides = {
        "channels": "视频号:15-60s 短视频脚本,口播风格,有钩子句",
        "wechat_official": "公众号:800-1500字 图文正文,有结构有小标题",
        "xhs": "小红书:200-400字 图文 + 5个话题标签,首图文案",
        "douyin": "抖音:15-60s 短视频脚本,节奏更快,用流行梗",
    }
    platforms_needed = {p: platform_guides.get(p, p) for p in s["target_platforms"]}
    script_messages = [
        {"role": "system", "content": f"你是一位专业的多平台内容创作者,擅长根据 KOC 风格生成适配不同平台的内容包。风格要求:{style_card.get('persona', '')}，{style_card.get('tone', '')}"},
        {"role": "user", "content": f"""根据以下选题策略,生成完整内容包。

【选题】{strategy.get('primary_topic', s['topic_seed'])}
【角度】{strategy.get('angle', '')}
【叙事框架】{strategy.get('narrative', '')}
【受众】{strategy.get('target_audience', '')}

【需要输出的平台】
{json.dumps(platforms_needed, ensure_ascii=False, indent=2)}

请输出 JSON:
- title_candidates: 10个候选标题(每个标注公式,如:悬念式/对比式/数字式/痛点式)
- platforms: 对象,每个平台的内容(title/body/tags/cta)
- cover_text: 3个封面主文案候选
- posting_time: 最佳发布时间建议

只输出 JSON。"""}
    ]
    script_resp = await minimax_call(script_messages, temperature=0.75, max_tokens=2000)
    ms4 = int((time.time() - t4) * 1000)
    total_tokens += script_resp["usage"]["total_tokens"]
    try:
        raw = script_resp["_raw_content"]
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        content_pkg = json.loads(raw.strip())
    except Exception:
        content_pkg = {"title_candidates": [], "_raw": script_resp["_raw_content"][:500]}
    ms4_total = int((time.time() - t4) * 1000)
    print(f"   ✓ 内容生成完成 ({ms4_total}ms, {script_resp['usage']['total_tokens']} tokens)")
    result["steps"]["content"] = content_pkg

    total_ms = int((time.time() - t0) * 1000)
    result["total_tokens"] = total_tokens
    result["total_ms"] = total_ms

    # ── 输出摘要 ──
    print(f"\n{'─'*65}")
    print(f"📦 内容包摘要")
    print(f"{'─'*65}")
    titles = content_pkg.get("title_candidates", [])
    if titles:
        print(f"\n🏆 候选标题(共 {len(titles)} 条):")
        for i, t in enumerate(titles[:5], 1):
            if isinstance(t, dict):
                print(f"  {i}. {t.get('title', t)}")
            else:
                print(f"  {i}. {t}")
        if len(titles) > 5:
            print(f"  ... 还有 {len(titles)-5} 条")
    platforms = content_pkg.get("platforms", {})
    if platforms:
        print(f"\n📱 多平台内容:")
        for plat, data in platforms.items():
            if isinstance(data, dict):
                title = data.get("title", "")
                body = data.get("body", "")[:100]
                tags = " ".join(data.get("tags", [])[:5])
                print(f"\n  [{plat}]")
                print(f"    标题: {title}")
                print(f"    正文: {body}...")
                if tags:
                    print(f"    标签: {tags}")
    covers = content_pkg.get("cover_text", [])
    if covers:
        print(f"\n🖼  封面文案候选:")
        for i, c in enumerate(covers[:3], 1):
            print(f"  {i}. {c}")
    posting = content_pkg.get("posting_time", "")
    if posting:
        print(f"\n⏰ 最佳发布时间: {posting}")

    print(f"\n{'─'*65}")
    print(f"⚡ 总耗时: {total_ms/1000:.1f}s | 总 tokens: {total_tokens:,} | 预估费用: ¥{total_tokens * 0.000015:.4f}")
    print(f"{'─'*65}")

    return result


# ============================================================
# Main
# ============================================================

async def main():
    print("\n" + "="*65)
    print("  🌊 Ripple × MiniMax M2.7 真实 API 实测")
    print("  腾讯 PCG 校园 AI 产品创意大赛 · 命题 5")
    print("  模型: MiniMax-Text-01")
    print("="*65)

    all_results = []
    for s in SCENARIOS:
        try:
            r = await run_scenario(s)
            all_results.append({"ok": True, **r})
        except Exception as e:
            print(f"\n❌ {s['name']} 失败: {e}")
            import traceback
            traceback.print_exc()
            all_results.append({"ok": False, "scenario": s["name"], "error": str(e)})

    # 总结
    print("\n" + "="*65)
    print("  📊 测试总结")
    print("="*65)
    total_t = sum(r.get("total_tokens", 0) for r in all_results)
    total_ms = sum(r.get("total_ms", 0) for r in all_results)
    passed = sum(1 for r in all_results if r.get("ok"))
    print(f"  通过: {passed}/{len(SCENARIOS)} 个场景")
    print(f"  总耗时: {total_ms/1000:.1f}s")
    print(f"  总 tokens: {total_t:,}")
    print(f"  预估费用: ¥{total_t * 0.000015:.4f}")
    print("="*65)


if __name__ == "__main__":
    asyncio.run(main())
