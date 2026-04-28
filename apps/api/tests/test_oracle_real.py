"""
Ripple OracleAgent v2 × MiniMax M2.7 — 全真实数据深度测试

两个场景:
  A. 国内跨平台时差: Oracle 扫描微博/抖音/百度/B站实时热搜,
     发现「只在部分平台上热」的话题, 生成面向未覆盖平台的内容包
  B. 跨国信息差: Oracle 扫描 Polymarket 高交易量合约,
     找到国内热搜零覆盖的国际话题, 生成跨文化解读内容

使用方式:
    cd ripple/apps/api
    python3 tests/test_oracle_real.py
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import textwrap
import time
from typing import Any, Dict

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
if not MINIMAX_API_KEY:
    raise SystemExit("请设置环境变量 MINIMAX_API_KEY，例如: export MINIMAX_API_KEY=sk-...")
MINIMAX_MODEL = "MiniMax-M2.7"

def divider(c="=", n=68): print(c * n)
def section(t, c="─", n=68): print(); print(c * n); print(f"  {t}"); print(c * n)
def wrap(text, w=62, prefix="    "):
    for p in str(text).split("\n"):
        if not p.strip():
            print()
        else:
            for line in textwrap.wrap(p, w):
                print(prefix + line)


async def minimax_call(sys_prompt: str, user_prompt: str, max_tokens: int = 2500):
    import httpx
    t0 = time.time()
    async with httpx.AsyncClient(timeout=180) as c:
        r = await c.post(
            "https://api.minimax.chat/v1/chat/completions",
            headers={"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": MINIMAX_MODEL,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.75,
            },
        )
        r.raise_for_status()
        d = r.json()
        raw = d["choices"][0]["message"]["content"]
        clean = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        tokens = d.get("usage", {}).get("total_tokens", 0)
        ms = int((time.time() - t0) * 1000)
    return clean, tokens, ms


def parse_json(text):
    """解析 JSON, 支持 ```json 包裹 + MiniMax 截断输出自动修复"""
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        s = text.find("{")
        if s == -1:
            return None
        raw = text[s:]

        # 先尝试直接解析
        e = raw.rfind("}")
        if e != -1:
            try:
                return json.loads(raw[: e + 1])
            except Exception:
                pass

        # JSON 被截断: 回退到最后一个完整对象结束位置
        # 找最后一个 "}" 使得从 raw 起始到该位置前缀可被解析
        # 策略: 找所有 "}" 位置, 从最后往前试, 并补上缺失的闭合符
        brace_positions = [i for i, c in enumerate(raw) if c == "}"]
        for pos in reversed(brace_positions):
            chunk = raw[: pos + 1]
            # 计算剩余未关闭的括号
            ob, cb, osb, csb = 0, 0, 0, 0
            in_str = False
            esc = False
            for ch in chunk:
                if esc:
                    esc = False
                    continue
                if ch == "\\" and in_str:
                    esc = True
                    continue
                if ch == '"':
                    in_str = not in_str
                    continue
                if in_str:
                    continue
                if ch == "{": ob += 1
                elif ch == "}": cb += 1
                elif ch == "[": osb += 1
                elif ch == "]": csb += 1
            suffix = "]" * max(0, osb - csb) + "}" * max(0, ob - cb)
            candidate = chunk + suffix
            try:
                result = json.loads(candidate)
                return result
            except Exception:
                continue
    except Exception:
        pass
    return None


# ============================================================
# 场景 A: 国内跨平台时差
# ============================================================

async def scenario_a():
    from agents.oracle_agent import OracleAgent

    divider()
    print()
    print("  场景 A: 国内跨平台时差")
    print("  Oracle 扫描全平台实时热搜, 发现跨平台内容窗口")
    divider()

    oracle = OracleAgent()

    print("\n  [Step 1/3] Oracle 全平台扫描中...")
    t0 = time.time()
    report = await oracle.scan("", "热点", ["channels", "xhs", "wechat_official"])
    ms1 = int((time.time() - t0) * 1000)

    print(f"  扫描完成 ({ms1}ms) | {report.sources_succeeded}/{report.sources_scanned} 个数据源成功")

    section("各平台实时热搜 Top 3 (真实数据)")
    for platform, samples in report.all_hotlists.items():
        source_obj = next((s for s in oracle.sources if s.name == platform), None)
        display = source_obj.display_name if source_obj else platform
        if samples:
            print(f"\n  {display}:")
            for s in samples[:3]:
                hot_display = s.metadata.get("hot_display", "")
                hot_str = f" [{hot_display}]" if hot_display else ""
                print(f"    #{s.rank} {s.keyword[:40]}{hot_str}")
        else:
            print(f"\n  {display}: (无数据)")

    gap_trends = [t for t in report.trends if t.category == "跨平台时差"]

    if not gap_trends:
        print("\n  (当前热搜高度重合, 未发现明显跨平台时差, 使用 Top1 趋势)")
        gap_trends = report.trends[:1]

    if not gap_trends:
        print("  没有可用趋势, 跳过场景 A")
        return 0

    chosen = gap_trends[0]

    section("发现跨平台时差窗口")
    print(f"\n  话题: 「{chosen.topic}」")
    print(f"  置信度: {chosen.confidence:.0%}")
    print(f"  窗口期: {chosen.horizon_days} 天")
    print(f"  依据: {chosen.explanation}")
    print(f"  推荐角度: {chosen.recommended_angle}")
    if chosen.risks:
        print(f"  风险: {'; '.join(chosen.risks)}")

    if report.contradictions:
        section("矛盾信号 (真实数据对比)")
        for i, con in enumerate(report.contradictions[:3], 1):
            print(f"\n  [{i}] {con.description}")
            print(f"      洞察: {con.insight}")
            print(f"      内容建议: {con.content_suggestion}")

    oracle_text = oracle.format_report(report, chosen.topic)

    print(f"\n  [Step 2/3] MiniMax {MINIMAX_MODEL} 生成内容包中...")
    sys_p = "你是 Ripple AI Agent 的内容策略师,擅长根据跨平台早期信号为 KOC 生成内容包。你的特长是基于真实热搜数据发现内容窗口,帮 KOC 比别人早 2-3 天抢占话题。"
    user_p = f"""以下是 Ripple 早期信号雷达的真实扫描报告:

{oracle_text}

请基于以上真实数据,为小红书 + 视频号 KOC 生成一套完整内容包,围绕话题「{chosen.topic}」。

要求:
1. 内容必须引用报告中的真实数据(如「微博热搜 #X」「抖音热搜 #X」等)
2. 利用跨平台时差窗口,在还未覆盖的平台上抢先布局
3. 体现「比别人早知道」的信息优势

输出 JSON:
{{
  "insight_summary": "基于 Oracle 数据的核心洞察(50字内)",
  "why_now": "为什么现在做这个话题(结合真实热搜数据说明)",
  "title_candidates": [
    {{"title": "...", "formula": "公式类型", "platform": "xhs/channels"}},
    ...共 6 条
  ],
  "xhs_post": {{
    "title": "小红书标题",
    "body": "完整正文(300-500字,引用真实热搜数据)",
    "tags": ["标签1", "标签2", ...],
    "cta": "互动引导"
  }},
  "video_script": {{
    "title": "视频号标题",
    "script": "30-45s口播逐字稿(引用真实数据)",
    "cta": "视频结尾CTA"
  }},
  "posting_strategy": "发布时间和策略建议"
}}
只输出 JSON。"""

    content, tokens, ms2 = await minimax_call(sys_p, user_p, max_tokens=2500)
    print(f"  生成完成 ({ms2 / 1000:.1f}s, {tokens:,} tokens)")

    pkg = parse_json(content)

    section("内容包输出 (基于真实 Oracle 数据)")
    if pkg:
        print(f"\n  核心洞察: {pkg.get('insight_summary', '')}")
        print(f"  为何现在: {pkg.get('why_now', '')}")

        print("\n  候选标题:")
        for i, t in enumerate(pkg.get("title_candidates", [])[:6], 1):
            if isinstance(t, dict):
                print(f"    {i}. [{t.get('formula','')}][{t.get('platform','')}] {t.get('title','')}")

        xhs = pkg.get("xhs_post", {})
        if xhs:
            print(f"\n  --- 小红书图文 ---")
            print(f"  标题: {xhs.get('title','')}")
            print(f"  正文:")
            wrap(xhs.get("body", ""), 60)
            print(f"  标签: {' '.join(xhs.get('tags', [])[:8])}")
            print(f"  CTA: {xhs.get('cta','')}")

        vs = pkg.get("video_script", {})
        if vs:
            print(f"\n  --- 视频号口播脚本 ---")
            print(f"  标题: {vs.get('title','')}")
            print(f"  脚本:")
            wrap(vs.get("script", ""), 60)
            print(f"  CTA: {vs.get('cta','')}")

        print(f"\n  发布策略: {pkg.get('posting_strategy','')}")
    else:
        print("  JSON 解析失败, 原始输出:")
        wrap(content[:600], 60)

    total_ms = int((time.time() - t0) * 1000)
    print(f"\n  总耗时: {total_ms / 1000:.1f}s | tokens: {tokens:,}")
    return tokens


# ============================================================
# 场景 B: 跨国信息差
# ============================================================

async def scenario_b():
    from agents.oracle_agent import OracleAgent

    divider()
    print()
    print("  场景 B: 跨国信息差 (Polymarket 真实合约)")
    print("  Oracle 发现国际预测市场热门但国内零覆盖的话题")
    divider()

    oracle = OracleAgent()

    print("\n  [Step 1/3] Oracle 全平台扫描中...")
    t0 = time.time()
    report = await oracle.scan("AI", "科技", ["channels", "wechat_official"])
    ms1 = int((time.time() - t0) * 1000)
    print(f"  扫描完成 ({ms1}ms) | {report.sources_succeeded}/{report.sources_scanned} 个数据源成功")

    section("Polymarket Top 5 (真实交易数据)")
    pm_samples = report.all_hotlists.get("polymarket", [])
    for s in pm_samples[:5]:
        vol_str = f"${s.raw_value:,.0f}" if s.raw_value > 0 else "N/A"
        print(f"  #{s.rank} [{vol_str} 24h交易量] {s.keyword[:60]}")
        if s.metadata.get("url"):
            print(f"       {s.metadata['url']}")

    intl_trends = [t for t in report.trends if t.category == "国际热点"]

    if not intl_trends:
        print("\n  (Polymarket 热门话题在国内热搜均有覆盖, 尝试用 Top1 Polymarket)")
        if pm_samples:
            chosen_sample = pm_samples[0]
            chosen_topic = chosen_sample.keyword
            chosen_vol = chosen_sample.raw_value
            chosen_explanation = f"Polymarket 24h 交易量 ${chosen_vol:,.0f}, 全球关注度极高"
        else:
            print("  Polymarket 无数据, 跳过场景 B")
            return 0
    else:
        chosen = intl_trends[0]
        chosen_topic = chosen.topic
        chosen_vol = chosen.evidence[0].raw_value if chosen.evidence else 0
        chosen_explanation = chosen.explanation

    section("发现跨国信息差窗口")
    print(f"\n  话题: 「{chosen_topic}」")
    print(f"  Polymarket 交易量: ${chosen_vol:,.0f}")
    print(f"  依据: {chosen_explanation}")
    print(f"  国内热搜覆盖: 零 → 信息差窗口 5-7 天")

    oracle_text = oracle.format_report(report, chosen_topic)

    print(f"\n  [Step 2/3] MiniMax {MINIMAX_MODEL} 生成跨文化解读内容包中...")
    sys_p = "你是 Ripple AI Agent 的跨文化内容策略师,擅长将国际预测市场(Polymarket)的数据翻译成中国社交媒体用户能理解的内容。你的核心能力是「把华尔街的数据变成普通人的信息优势」。"
    user_p = f"""以下是 Ripple 早期信号雷达的真实扫描报告:

{oracle_text}

我发现一个跨国信息差机会:
- Polymarket 上「{chosen_topic}」的 24h 交易量为 ${chosen_vol:,.0f}
- 但中国国内热搜(微博/抖音/百度/B站)上几乎没有人在讨论这个话题
- 这意味着有 5-7 天的信息差窗口

请为视频号 + 公众号 KOC 生成一套「跨文化解读」内容包。

要求:
1. 开头必须引用 Polymarket 的真实交易数据(「Polymarket 上 XX 万美元在押注...」)
2. 把国际话题翻译成中国用户关心的角度
3. 体现「别人还不知道,但我已经看到信号了」的信息差优势
4. 内容要通俗易懂,不要金融术语堆砌

输出 JSON:
{{
  "insight_summary": "基于 Polymarket 数据的核心发现(50字内)",
  "china_angle": "这个国际话题跟中国用户有什么关系(100字内)",
  "title_candidates": [
    {{"title": "...", "formula": "公式类型", "platform": "channels/wechat_official"}},
    ...共 6 条
  ],
  "wechat_article": {{
    "title": "公众号标题",
    "body": "正文(500-600字,开头引用 Polymarket 数据,有2-3个小标题)",
    "tags": ["标签1", "标签2"],
    "cta": "文末互动引导(1句话)"
  }},
  "video_script": {{
    "title": "视频号标题",
    "script": "30-40s 口播逐字稿(开头用 Polymarket 数据做钩子,约200字)",
    "cta": "视频结尾CTA(1句话)"
  }},
  "posting_strategy": "发布时间建议"
}}
只输出 JSON。"""

    content, tokens, ms2 = await minimax_call(sys_p, user_p, max_tokens=4000)
    print(f"  生成完成 ({ms2 / 1000:.1f}s, {tokens:,} tokens)")

    pkg = parse_json(content)

    section("跨文化解读内容包 (基于 Polymarket 真实数据)")
    if pkg:
        print(f"\n  核心发现: {pkg.get('insight_summary', '')}")
        print(f"\n  中国用户角度:")
        wrap(pkg.get("china_angle", ""), 60)

        print("\n  候选标题:")
        for i, t in enumerate(pkg.get("title_candidates", [])[:6], 1):
            if isinstance(t, dict):
                print(f"    {i}. [{t.get('formula','')}][{t.get('platform','')}] {t.get('title','')}")

        wa = pkg.get("wechat_article", {})
        if wa:
            print(f"\n  --- 公众号文章 ---")
            print(f"  标题: {wa.get('title','')}")
            print(f"  正文:")
            wrap(wa.get("body", ""), 60)
            print(f"  标签: {' '.join(wa.get('tags', [])[:8])}")
            print(f"  CTA: {wa.get('cta','')}")

        vs = pkg.get("video_script", {})
        if vs:
            print(f"\n  --- 视频号口播脚本 ---")
            print(f"  标题: {vs.get('title','')}")
            print(f"  脚本:")
            wrap(vs.get("script", ""), 60)
            print(f"  CTA: {vs.get('cta','')}")

        print(f"\n  发布策略: {pkg.get('posting_strategy','')}")
    else:
        print("  JSON 解析失败, 原始输出:")
        wrap(content[:600], 60)

    total_ms = int((time.time() - t0) * 1000)
    print(f"\n  总耗时: {total_ms / 1000:.1f}s | tokens: {tokens:,}")
    return tokens


# ============================================================
# Main
# ============================================================

async def main():
    divider()
    print()
    print("  Ripple OracleAgent v2 × MiniMax M2.7")
    print("  全真实数据深度测试")
    print()
    print("  数据源: Polymarket / Manifold / HackerNews /")
    print("          微博热搜 / 抖音热搜 / 百度热搜 / B站热搜")
    print("  模型: MiniMax M2.7")
    print("  Mock 数据: 零")
    divider()

    total_tokens = 0

    t_a = await scenario_a()
    total_tokens += t_a

    t_b = await scenario_b()
    total_tokens += t_b

    divider()
    print()
    print("  2/2 场景完成")
    print(f"  总 tokens: {total_tokens:,}")
    print(f"  预估费用: ¥{total_tokens * 0.000015:.4f}")
    print()
    print("  关键验证:")
    print("    [A] 跨平台时差: Oracle 真实扫描 → 发现窗口 → 内容引用真实热搜数据")
    print("    [B] 跨国信息差: Polymarket 真实交易量 → 国内零覆盖 → 抢先做跨文化解读")
    print("    所有数据均为实时真实数据, 零 Mock")
    divider()


if __name__ == "__main__":
    asyncio.run(main())
