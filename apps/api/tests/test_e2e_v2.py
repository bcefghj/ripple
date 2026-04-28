"""E2E Test v2 - 4 真实场景跑 Ripple 2.0 Kernel

场景:
1. 美妆 KOC: 测评向, 二线女性受众
2. 财经 KOC: 黄金 / 股市
3. 科技 KOC: AI / DeepSeek 新模型
4. 校园 KOC: 大学生话题

每个场景跑完整 orchestrator,输出保存到 docs/demo_outputs/。
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from kernel.types import RunContext
from kernel.event_bus import EventBus
from kernel.orchestration import get_orchestrator
from kernel.persistence.db import init_db


SCENARIOS = [
    {
        "name": "scenario_a_beauty_koc",
        "user_id": "demo_beauty",
        "query": "我是测评向美妆 KOC,粉丝 5000,目标受众是 25-30 岁二线女性,这周该发什么内容",
        "samples": [
            "今天测评了一款新粉底液,sephora 入手的。先说结论:油皮慎入,干皮真神。",
            "上周直播聊了下我用过的 5 支腮红,最贵的不一定最好。我个人最爱 NARS 的 Orgasm。",
            "其实我以前踩过雷,所以现在每次出新品都要先看成分。",
        ],
    },
    {
        "name": "scenario_b_finance_koc",
        "user_id": "demo_finance",
        "query": "未来一周黄金价格会涨吗 我作为财经 KOC 要发什么角度",
        "samples": [
            "金价突破历史高点这事, 我看了 50 年的数据告诉你, 这不是一次性的。",
            "最近的美元强势, 黄金为什么没跌反涨? 我画了张图给你说清楚。",
            "我要泼个冷水, 现在追金价高位, 风险 / 收益比已经不划算了。",
        ],
    },
    {
        "name": "scenario_c_tech_koc",
        "user_id": "demo_tech",
        "query": "DeepSeek 又出新模型了 帮我从一句话把它做成小红书+视频号+B站三个版本",
        "samples": [
            "这个模型有意思的不是它跑分多高, 而是它的训练成本怎么压到 1/10。",
            "AI 编程这事, 我自己实操了 3 个月, 来给你说说哪些场景真的好用。",
            "为什么大公司都在内卷 Agent? 我用一张图给你讲明白。",
        ],
    },
    {
        "name": "scenario_d_campus_koc",
        "user_id": "demo_campus",
        "query": "我是大三学生想做校园博主 这周末发什么不会被骂",
        "samples": [
            "其实考研不是唯一出路, 我身边走了不同路的同学,都活得不错。",
            "宿舍关系这事我觉得真没必要硬磕, 大家都是临时室友, 互相舒服就行。",
            "校园里那些被神化的牛人, 其实背后都很不容易, 我想聊聊真实的故事。",
        ],
    },
]


async def run_scenario(scenario: dict) -> dict:
    print(f"\n{'='*70}")
    print(f"场景: {scenario['name']}")
    print(f"用户: {scenario['user_id']}")
    print(f"查询: {scenario['query']}")
    print(f"{'='*70}")

    from kernel.cognition.persona import get_persona_manager
    pm = get_persona_manager()
    if scenario.get("samples"):
        try:
            pv = await pm.calibrate(
                scenario["user_id"], scenario["samples"], branch="main",
                notes=f"scenario {scenario['name']}",
            )
            print(f"  ✓ 人设校准: v{pv.version}, {pv.sample_count} 样本")
        except Exception as e:
            print(f"  ⚠ 人设校准失败: {e}")

    ctx = RunContext(
        user_id=scenario["user_id"],
        query=scenario["query"],
    )
    bus = EventBus(trace_id=ctx.trace_id)
    orch = get_orchestrator()

    events_log = []

    async def consumer():
        async for evt in bus.stream():
            events_log.append({
                "type": evt.event_type.value,
                "ts": evt.timestamp,
                "payload": str(evt.payload)[:600],
            })
            if evt.event_type.value in ("thinking", "agent_start", "agent_end"):
                summary = (
                    evt.payload.get("text") or
                    evt.payload.get("agent") or
                    evt.payload.get("step") or ""
                )
                print(f"  [{evt.event_type.value}] {summary[:80]}")

    consumer_task = asyncio.create_task(consumer())
    start = time.time()
    result = await orch.run(ctx, bus)
    await consumer_task
    elapsed = time.time() - start

    print(f"\n✓ 完成 (耗时 {elapsed:.1f}s)")
    print(f"  Run ID: {result.get('run_id')}")
    print(f"  Replay 节点数: {len(result.get('replay_dag', {}).get('nodes', []))}")
    print(f"  最终结论 (前 300 字):")
    print(f"  {result.get('final_summary', '')[:300]}")

    return {
        "scenario": scenario,
        "result": {
            "run_id": result.get("run_id"),
            "trace_id": result.get("trace_id"),
            "final_summary": result.get("final_summary"),
            "elapsed_seconds": elapsed,
            "step_count": len(result.get("results", {})),
            "replay_node_count": len(result.get("replay_dag", {}).get("nodes", [])),
        },
        "events_count": len(events_log),
    }


async def main():
    init_db()
    output_dir = Path(__file__).parent.parent.parent.parent / "docs" / "demo_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_results = []

    for scenario in SCENARIOS:
        try:
            result = await run_scenario(scenario)
            all_results.append(result)
        except Exception as e:
            import traceback
            print(f"  ✗ 场景失败: {e}")
            traceback.print_exc()
            all_results.append({"scenario": scenario, "error": str(e)})

    output_file = output_dir / f"e2e_v2_{timestamp}.json"
    output_file.write_text(json.dumps(all_results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n\n保存所有结果到 {output_file}")

    md_file = output_dir / f"e2e_v2_{timestamp}.md"
    md_lines = ["# Ripple 2.0 E2E 真实场景测试", "",
                f"运行时间: {timestamp}", "", f"场景数: {len(all_results)}", ""]
    for r in all_results:
        s = r["scenario"]
        md_lines.append(f"## {s['name']}")
        md_lines.append(f"**用户**: `{s['user_id']}`")
        md_lines.append(f"**查询**: {s['query']}")
        if "result" in r:
            res = r["result"]
            md_lines.append(f"**Run ID**: `{res.get('run_id')}`")
            md_lines.append(f"**耗时**: {res.get('elapsed_seconds', 0):.1f}s")
            md_lines.append(f"**步骤数**: {res.get('step_count')}")
            md_lines.append(f"**Replay 节点**: {res.get('replay_node_count')}")
            md_lines.append("")
            md_lines.append("**最终结论**:")
            md_lines.append("")
            md_lines.append(res.get("final_summary", "")[:1500])
        else:
            md_lines.append(f"**错误**: {r.get('error')}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")
    md_file.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"保存 Markdown 到 {md_file}")


if __name__ == "__main__":
    asyncio.run(main())
