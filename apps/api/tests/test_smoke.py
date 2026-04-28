"""Smoke 测试 - 验证基础导入与初始化"""

import sys
from pathlib import Path

# 把 apps/api 加入 path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_import_state():
    """LoopState / Terminal 枚举"""
    from agent.state import (
        AutoCompactTracking,
        ContinueReason,
        LoopState,
        Terminal,
        TerminalReason,
        ToolUseContext,
        Transition,
    )
    
    state = LoopState()
    assert state.turn_count == 1
    
    terminal = Terminal(reason=TerminalReason.COMPLETED)
    assert terminal.is_success()
    
    print("✓ state.py imports OK")


def test_import_compression():
    """四层压缩管线"""
    from agent.compression import CompressionConfig, CompressionPipeline, estimate_tokens
    
    cfg = CompressionConfig()
    pipeline = CompressionPipeline(cfg, effective_window_tokens=128000)
    
    assert pipeline.get_autocompact_threshold() > 0
    assert pipeline.get_blocking_threshold() > pipeline.get_autocompact_threshold()
    
    msgs = [{"role": "user", "content": "hello"}]
    tokens = estimate_tokens(msgs)
    assert tokens > 0
    
    print("✓ compression.py imports OK")


def test_import_hooks():
    """Hooks 系统"""
    from agent.hooks import (
        HookEvent,
        HookRegistry,
        HookResult,
        PermissionDecision,
        install_default_hooks,
    )
    
    registry = HookRegistry()
    install_default_hooks(registry)
    
    assert len(registry._handlers) > 0
    print("✓ hooks.py imports OK")


def test_import_memory_system():
    """五层记忆系统"""
    from agent.memory_system import (
        InstructionMemory,
        MemdirStore,
        MemoryEntry,
    )
    
    print("✓ memory_system.py imports OK")


def test_import_skills_loader():
    """Skills 加载器"""
    from agent.skills.loader import Skill, SkillFrontmatter, SkillLoader
    
    skills_root = Path(__file__).parent.parent / "agent" / "skills"
    loader = SkillLoader([skills_root])
    skills = loader.discover()
    
    # 应该发现 5 个 SKILL.md
    assert len(skills) >= 5, f"应有至少 5 个 skills, 实际 {len(skills)}"
    
    skill_names = [s.name for s in skills]
    expected = [
        "oracle-early-signal",
        "koc-content-package",
        "viral-formula-library",
        "copyright-asset-library",
        "ai-detection-bypass",
    ]
    for e in expected:
        assert e in skill_names, f"Skill {e} 未找到"
    
    print(f"✓ skills/loader.py OK - 发现 {len(skills)} 个 skills: {skill_names}")


def test_import_oracle_agent():
    """OracleAgent"""
    from agents.oracle_agent import (
        ManifoldSource,
        OracleAgent,
        OracleReport,
        PolymarketSource,
        SignalSample,
        TrendCandidate,
    )
    
    oracle = OracleAgent()
    assert len(oracle.sources) >= 9
    print(f"✓ OracleAgent OK - {len(oracle.sources)} 个数据源")


def test_import_all_agents():
    """所有 12 Agent 导入"""
    from agents.fact_checker_agent import FactCheckerAgent
    from agents.forum_debate_agent import ForumDebateAgent
    from agents.insight_analyst_agent import InsightAnalystAgent
    from agents.material_curator_agent import MaterialCuratorAgent
    from agents.oracle_agent import OracleAgent
    from agents.risk_reviewer_agent import RiskReviewerAgent
    from agents.script_writer_agent import ScriptWriterAgent
    from agents.sim_predictor_agent import SimPredictorAgent
    from agents.style_decoder_agent import StyleDecoderAgent
    from agents.topic_strategist_agent import TopicStrategistAgent
    from agents.trend_scout_agent import TrendScoutAgent
    from agents.visual_producer_agent import VisualProducerAgent
    
    print("✓ All 12 Agents import OK")


def test_import_orchestrator():
    """编排器"""
    
    async def fake_llm(messages, **kwargs):
        return {
            "message": {"role": "assistant", "content": "fake response"},
            "tool_calls": [],
            "stop_reason": "completed",
            "usage": {"total_tokens": 100, "cost_usd": 0.001},
        }
    
    from agents.orchestrator import RippleOrchestrator
    orch = RippleOrchestrator(llm_call=fake_llm)
    print("✓ RippleOrchestrator init OK")


def test_import_agent_loop():
    """主循环"""
    from agent.agent_loop import AgentLoop, StreamEvent
    
    async def fake_llm(messages, **kwargs):
        return {
            "message": {"role": "assistant", "content": "fake"},
            "tool_calls": [],
            "stop_reason": "completed",
            "usage": {"total_tokens": 10},
        }
    
    loop = AgentLoop(llm_call=fake_llm, max_turns=5)
    print("✓ AgentLoop init OK")


def test_crypto():
    """加密工具"""
    from utils.crypto import decrypt, encrypt
    
    plain = "sk-test-key-1234"
    password = "user-pass-2026"
    
    encrypted = encrypt(plain, password)
    decrypted = decrypt(encrypted, password)
    assert decrypted == plain
    
    # 错误密码必须失败
    try:
        decrypt(encrypted, "wrong-password")
        assert False, "错误密码应该失败"
    except Exception:
        pass
    
    print("✓ crypto.py OK")


if __name__ == "__main__":
    print("=" * 60)
    print("Ripple Smoke 测试")
    print("=" * 60)
    
    tests = [
        test_import_state,
        test_import_compression,
        test_import_hooks,
        test_import_memory_system,
        test_import_skills_loader,
        test_import_oracle_agent,
        test_import_all_agents,
        test_import_orchestrator,
        test_import_agent_loop,
        test_crypto,
    ]
    
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"✗ {t.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 60)
    if failed == 0:
        print(f"✓ 全部 {len(tests)} 个测试通过!")
    else:
        print(f"✗ {failed}/{len(tests)} 个测试失败")
        sys.exit(1)
