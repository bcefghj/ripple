"""端到端集成测试 - 使用 Mock LLM 跑通 12 Agent 完整流水线

不依赖真实 LLM Key,验证编排层、并发、错误处理、数据流均正常。
"""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================
# Mock LLM - 模拟不同 agent 的真实输出
# ============================================================

class MockLLM:
    """Mock LLM,根据消息内容返回不同的 JSON 结果"""

    def __init__(self):
        self.call_count = 0
        self.calls: List[Dict[str, Any]] = []

    async def __call__(self, messages, **kwargs) -> Dict[str, Any]:
        self.call_count += 1
        last_user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = m.get("content", "")
                break
        # 兼容 system prompt 也参与路由
        sys_prompt = ""
        for m in messages:
            if m.get("role") == "system":
                sys_prompt += " " + m.get("content", "")
        self.calls.append({"turn": self.call_count, "preview": last_user[:120]})

        content = self._route(sys_prompt + " " + last_user)
        return {
            "message": {"role": "assistant", "content": content},
            "tool_calls": [],
            "stop_reason": "completed",
            "usage": {"total_tokens": 200, "cost_usd": 0.0008},
        }

    def _route(self, prompt: str) -> str:
        p = prompt.lower()
        # ScriptWriter 内容包 - 优先匹配,因为它包含多种关键词
        if ("脚本" in prompt or "scriptwriter" in p or "title_candidates" in p
                or "10 个标题候选" in prompt or "封面文案" in prompt):
            return json.dumps({
                "title_candidates": [
                    "黄金能买吗?对冲基金已用脚投票",
                    "比央视早 7 天,Polymarket 在告诉你什么",
                    "金价 3000 不是梦?数据从不撒谎",
                    "投资人不愿明说的黄金真相",
                    "为什么聪明人偷偷买黄金",
                    "这周必看的黄金 3 张图",
                    "黄金 vs AI,普通人怎么选",
                    "央视报道前,资本在做什么",
                    "金价信号:对冲基金净多头创新高",
                    "黄金不香了吗?数据讲个反故事",
                ],
                "platforms": {
                    "channels": {
                        "title": "黄金能买吗?对冲基金已用脚投票",
                        "body": "本期我们用 Polymarket 上一份真实合约数据,告诉你为什么对冲基金正悄悄加仓黄金。提前 7 天捕获信号,这就是数据的力量。",
                        "tags": ["黄金", "投资", "宏观经济", "对冲基金"],
                        "cta": "关注获取每日早期信号",
                    },
                    "wechat_official": {
                        "title": "比央视早 7 天:对冲基金正在悄悄买黄金",
                        "body": "## 资本走在舆论之前\n\n本周 Polymarket 上'金价超 3000'合约 24 小时上涨 18%...",
                        "tags": ["黄金", "宏观"],
                        "cta": "点击在看",
                    },
                    "xhs": {
                        "title": "金价要爆了?数据告诉你对冲基金在做什么",
                        "body": "姐妹们今天聊个硬核话题:为什么聪明人都在买黄金",
                        "tags": ["黄金", "投资", "理财"],
                        "cta": "收藏不亏",
                    },
                    "douyin": {
                        "title": "黄金 3000 不是梦,数据讲个反故事",
                        "body": "30 秒讲清楚:对冲基金净多头创新高,普通人怎么办?",
                        "tags": ["黄金", "财经"],
                        "cta": "点赞关注",
                    },
                },
                "cover_descriptions": [
                    {"style": "高对比", "main_text": "黄金能买吗?", "color_palette": "金黑", "description": "金条+蜡烛图剪影"},
                    {"style": "数据图", "main_text": "+18% 24h", "color_palette": "红绿", "description": "Polymarket 截图"},
                    {"style": "人物特写", "main_text": "聪明钱在动", "color_palette": "金白", "description": "投资人剪影+金条"},
                ],
                "rhythm_notes": "前 3 秒用悬念问句,中段用数据对比,结尾留白引导互动",
            }, ensure_ascii=False)
        # StyleDecoder 提取风格
        if "style" in p or "persona" in p or "tone" in p or "风格卡片" in prompt:
            return json.dumps({
                "persona": "理性投资观察者",
                "tone": "克制、数据驱动",
                "topics": ["黄金", "AI 泡沫", "宏观经济"],
                "structure": "钩子-数据-观点-反问",
                "examples": ["关于黄金的另一种思路", "AI 真的是泡沫吗"],
                "do": ["用数据支撑论点", "保持克制"],
                "dont": ["避免感叹号", "避免标题党"],
            }, ensure_ascii=False)
        # Forum 主持/专家
        if "辩论" in prompt or "主持" in prompt or "专家" in prompt or "debate" in p:
            return json.dumps({
                "stance": "建议优先做'黄金能买吗'选题,因为提前 7 天捕获了对冲基金信号",
                "evidence": "Polymarket 上'金价超3000'合约 24h 涨 18%",
                "objection": "需要警惕标题党,正文用真实数据",
                "summary": "建议主选黄金选题",
                "final_decision": "执行'黄金能买吗'选题",
            }, ensure_ascii=False)
        # TopicStrategist
        if "选题策略" in prompt or "primary_topic" in p or "strategist" in p:
            return json.dumps({
                "primary_topic": "黄金能买吗?对冲基金正在悄悄做的事",
                "angle": "提前 7 天信号 - 资本走在舆论之前",
                "narrative": "用 Polymarket 真实合约数据,对照央视新闻舆论时间差",
                "target_audience": "25-40 岁理性投资者",
                "confidence": 0.82,
                "why_now": "对冲基金净多头本周已超 2024 峰值",
                "risks": ["数据可能有滞后", "需注意监管"],
            }, ensure_ascii=False)
        # FactChecker
        if "事实核查" in prompt or "factcheck" in p or "fact" in p:
            return json.dumps({
                "overall_pass": True,
                "issues": [],
                "suggestions": ["建议补充 Polymarket 合约链接"],
                "confidence": 0.88,
            }, ensure_ascii=False)
        # Risk Reviewer
        if "合规" in prompt or "风险审查" in prompt or "risk" in p or "compliance" in p:
            return json.dumps({
                "overall_pass": True,
                "risks": [],
                "ai_label_required": True,
                "platform_specific_notes": {"channels": "需添加 AI 标识"},
                "fix_suggestions": ["在结尾标注'本视频包含 AI 生成内容'"],
            }, ensure_ascii=False)
        return json.dumps({"result": "mock-default", "ok": True}, ensure_ascii=False)


# ============================================================
# E2E Tests
# ============================================================

async def test_orchestrator_full_pipeline():
    """完整 12 Agent 流水线"""
    from agents.orchestrator import RippleOrchestrator

    mock = MockLLM()
    orch = RippleOrchestrator(llm_call=mock)

    output = await orch.run(
        topic_seed="黄金 vs AI 投资",
        category="财经",
        target_platforms=["channels", "wechat_official", "xhs", "douyin"],
        koc_works=[
            {"title": "黄金的另一种思路", "body": "当大家都在追 AI,黄金的真实需求曲线是?"},
            {"title": "为什么我不追热点", "body": "用数据看穿叙事,聪明钱在动..."},
        ],
        koc_context="一个理性投资观察 KOC,粉丝 5 万",
        request_id="e2e-test-001",
    )

    assert output.request_id == "e2e-test-001"
    assert output.topic_seed == "黄金 vs AI 投资"
    assert output.completed_at is not None
    assert output.duration_ms > 0
    assert output.oracle_report is not None, "OracleReport 应该有输出"
    assert "trends" in output.oracle_report
    assert output.insight is not None, "InsightReport 必须输出"

    print(f"✓ E2E 完整流水线通过")
    print(f"  - Mock LLM 调用次数: {mock.call_count}")
    print(f"  - 流水线耗时: {output.duration_ms} ms")
    print(f"  - 错误数: {len(output.errors)}")
    print(f"  - Oracle 趋势: {len(output.oracle_report.get('trends', []))}")
    print(f"  - 热点话题: {len(output.hot_topics)}")
    if output.topic_strategy:
        print(f"  - 选题: {output.topic_strategy.get('primary_topic', 'N/A')[:60]}")
    if output.content_package:
        platforms = output.content_package.get("platforms", {})
        titles = output.content_package.get("title_candidates", [])
        print(f"  - 标题数: {len(titles)}")
        print(f"  - 平台数: {len(platforms)}")
    print(f"  - 封面: {len(output.cover_images)}")
    print(f"  - 素材: {len(output.materials)}")
    if output.errors:
        for e in output.errors[:3]:
            print(f"  - error: {e}")

    return output


async def test_orchestrator_streaming():
    """流式输出 - 验证 WebSocket 兼容"""
    from agents.orchestrator import RippleOrchestrator

    mock = MockLLM()
    orch = RippleOrchestrator(llm_call=mock)

    events = []
    async for event in orch.run_streaming(
        topic_seed="AI 是不是泡沫?",
        category="科技",
        target_platforms=["channels", "wechat_official"],
        request_id="e2e-stream-001",
    ):
        events.append(event)

    event_types = [e.get("event") for e in events]
    assert "start" in event_types
    assert "complete" in event_types

    phases = [e for e in events if e.get("event") == "phase_start"]
    assert len(phases) >= 4

    agent_starts = [e for e in events if e.get("event") == "agent_start"]
    agent_dones = [e for e in events if e.get("event") == "agent_done"]
    assert len(agent_starts) >= 5

    print(f"✓ 流式流水线通过")
    print(f"  - 总事件数: {len(events)}")
    print(f"  - Phase 数: {len(phases)}")
    print(f"  - Agent start: {len(agent_starts)}, done: {len(agent_dones)}")


async def test_oracle_agent_standalone():
    """OracleAgent 单独运行"""
    from agents.oracle_agent import OracleAgent

    oracle = OracleAgent()
    report = await oracle.scan(
        topic_seed="黄金",
        category="财经",
        target_platforms=["channels"],
    )

    assert report.scan_time_ms > 0
    assert isinstance(report.trends, list)
    print(f"✓ OracleAgent 单独运行 - {len(report.trends)} 个趋势, 用时 {report.scan_time_ms}ms")


async def test_skills_progressive_disclosure():
    """Skills 渐进披露 - 只加载 frontmatter,按需展开 body"""
    from agent.skills.loader import SkillLoader

    skills_root = Path(__file__).parent.parent / "agent" / "skills"
    loader = SkillLoader([skills_root])
    summaries = loader.discover()  # 只读 frontmatter

    assert len(summaries) >= 5
    expected = {"oracle-early-signal", "viral-formula-library", "koc-content-package",
                "copyright-asset-library", "ai-detection-bypass"}
    found = {s.name for s in summaries}
    assert expected.issubset(found), f"缺少 skill: {expected - found}"

    # 按需加载完整 body
    full = loader.load("oracle-early-signal")
    assert full is not None
    assert len(full.body) > 100, "Skill body 应该有实质内容"
    assert full.frontmatter.name == "oracle-early-signal"

    # list_for_prompt 输出
    prompt_text = loader.list_for_prompt()
    assert "oracle-early-signal" in prompt_text

    print(f"✓ Skills 渐进披露 - {len(summaries)} 个 skills, body={len(full.body)} 字符")


async def test_memory_system_basic():
    """记忆系统基础写入/检索"""
    from agent.memory_system import InstructionMemory, MemdirStore

    tmpdir = Path(tempfile.mkdtemp(prefix="ripple_mem_"))

    # Layer 1: 指令记忆
    inst = InstructionMemory(tmpdir)
    user_md = inst.get_user_md()
    koc_md = inst.get_koc_md()
    brand_md = inst.get_brand_md()
    assert "USER.md" in user_md or "KOC" in user_md or "画像" in user_md
    assert len(koc_md) > 0
    assert len(brand_md) > 0

    inst.write_user_md("# USER.md\n姓名: 测试 KOC\n粉丝: 5 万")
    assert "测试 KOC" in inst.get_user_md()

    # Layer 2: memdir
    store = MemdirStore(tmpdir)
    p1 = store.write_memory(
        category="inspirations",
        title="对冲基金正在悄悄买黄金",
        content="Polymarket 合约 24h 涨 18%,值得做选题",
        tags=["黄金", "early-signal"],
    )
    p2 = store.write_memory(
        category="works",
        title="为什么我不追热点",
        content="用数据看穿叙事...",
        tags=["复盘", "理性"],
    )
    assert p1.exists() and p2.exists()

    entries = store.scan()
    assert len(entries) >= 2

    inspirations = store.scan(category="inspirations")
    assert any("黄金" in e.title for e in inspirations)

    index = store.get_index()
    assert "对冲基金" in index or "黄金" in index

    print(f"✓ MemorySystem - 指令层 + memdir({len(entries)} 条) 通过")


async def test_compression_pipeline_basic():
    """四层压缩管线 - 阈值与基础调用"""
    from agent.compression import CompressionConfig, CompressionPipeline

    cfg = CompressionConfig()
    pipeline = CompressionPipeline(cfg, effective_window_tokens=128_000)

    auto_th = pipeline.get_autocompact_threshold()
    block_th = pipeline.get_blocking_threshold()
    assert 0 < auto_th < block_th

    msgs = [
        {"role": "user", "content": "x" * 100},
        {"role": "assistant", "content": "y" * 100},
    ]
    out = pipeline.apply_tool_result_budget(msgs)
    assert isinstance(out, list)

    print(f"✓ CompressionPipeline - autocompact={auto_th}, block={block_th}")


async def test_hooks_security():
    """Hooks 安全 - 危险工具拦截"""
    from agent.hooks import HookEvent, HookRegistry, install_default_hooks, PermissionDecision

    reg = HookRegistry()
    install_default_hooks(reg)

    # 测试 1: 危险工具 - 应被拦截
    result = await reg.execute_pre_tool(
        tool_name="rm_rf",
        tool_input={"path": "/"},
    )
    assert result.blocking_error is not None or result.permission_decision == PermissionDecision.DENY

    # 测试 2: 安全工具 - 应放行
    safe_result = await reg.execute_pre_tool(
        tool_name="search_inspirations",
        tool_input={"query": "黄金"},
    )
    assert safe_result.blocking_error is None

    print(f"✓ Hooks 安全拦截 - 危险工具被拒绝, 安全工具放行")


async def test_byok_crypto_roundtrip():
    """BYOK 加密 - 全流程"""
    from utils.crypto import decrypt, encrypt, generate_master_key, encrypt_with_master_key, decrypt_with_master_key

    secrets_list = [
        "sk-anthropic-test123456789",
        "sk-or-v1-deepseek-key",
        "ms-tencent-hunyuan-token",
    ]
    password = "user-master-pwd-2026"

    for plain in secrets_list:
        cipher = encrypt(plain, password)
        # 密文必须是 bytes 且不包含明文(转 hex 看)
        assert isinstance(cipher, bytes)
        assert plain.encode() not in cipher
        # 必须能正确解密
        assert decrypt(cipher, password) == plain

    # 错误密码必须失败
    cipher = encrypt(secrets_list[0], password)
    try:
        decrypt(cipher, "wrong-password")
        assert False, "错误密码应该失败"
    except Exception:
        pass

    # master key 模式
    mk = generate_master_key()
    nonce, cipher2 = encrypt_with_master_key("test-content", mk)
    plain2 = decrypt_with_master_key(nonce, cipher2, mk)
    assert plain2 == "test-content"

    print(f"✓ BYOK 加密 - {len(secrets_list)} 个 secret 加解密 + master key 模式通过")


async def test_llm_router_provider_list():
    """LLM Router 多供应商列表"""
    from utils.llm_router import LLMRouter, PROVIDERS

    router = LLMRouter()
    assert len(PROVIDERS) >= 5

    # 主流 Provider 都注册了
    expected = {"minimax", "hunyuan", "deepseek", "doubao", "openai"}
    found = set(PROVIDERS.keys())
    overlap = expected & found
    assert len(overlap) >= 4, f"主流供应商应被支持, 实际找到 {found}"

    # 列出可用的(可能 0 个,因为没有 API Key)
    available = router.list_available_providers(include_byok=True)
    assert isinstance(available, list)

    print(f"✓ LLMRouter - 共注册 {len(PROVIDERS)} 个供应商: {sorted(found)[:6]}")


async def test_agent_loop_basic():
    """主循环 - 单次 turn 完成"""
    from agent.agent_loop import AgentLoop

    async def fake_llm(messages, **kwargs):
        return {
            "message": {"role": "assistant", "content": "完成任务"},
            "tool_calls": [],
            "stop_reason": "completed",
            "usage": {"total_tokens": 50, "cost_usd": 0.0001},
        }

    loop = AgentLoop(llm_call=fake_llm, max_turns=3)
    # 仅验证可初始化与 max_turns 设置
    assert loop.max_turns == 3
    print(f"✓ AgentLoop 基础初始化 - max_turns={loop.max_turns}")


# ============================================================
# Runner
# ============================================================

ASYNC_TESTS = [
    test_oracle_agent_standalone,
    test_skills_progressive_disclosure,
    test_memory_system_basic,
    test_compression_pipeline_basic,
    test_hooks_security,
    test_byok_crypto_roundtrip,
    test_llm_router_provider_list,
    test_agent_loop_basic,
    test_orchestrator_full_pipeline,
    test_orchestrator_streaming,
]


async def main():
    print("=" * 70)
    print("Ripple 端到端集成测试 (Mock LLM)")
    print("=" * 70)

    failed = 0
    passed = 0
    for t in ASYNC_TESTS:
        try:
            await t()
            passed += 1
        except Exception as e:
            print(f"✗ {t.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print("-" * 70)

    print("=" * 70)
    if failed == 0:
        print(f"✓ 全部 {passed} 个 E2E 测试通过!")
    else:
        print(f"✗ {failed}/{len(ASYNC_TESTS)} 个 E2E 测试失败 ({passed} 通过)")
    print("=" * 70)
    return failed


if __name__ == "__main__":
    failed = asyncio.run(main())
    sys.exit(failed)
