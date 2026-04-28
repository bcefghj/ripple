"""Ripple Streamlit MVP Demo

这是一个独立运行的 Streamlit 应用,作为大赛 Demo 的安全回退方案。
即使 Next.js / Tauri 没准备好,也能展示完整功能。

启动:
    cd apps/streamlit_demo
    pip install streamlit plotly pandas requests
    streamlit run app.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path

import streamlit as st

# 把 apps/api 加入 path,直接复用所有 Agent
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from agents.oracle_agent import OracleAgent  # noqa: E402

# ============ Page Config ============

st.set_page_config(
    page_title="Ripple — KOC 早期信号雷达",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============ Sidebar ============

with st.sidebar:
    st.markdown("# 🌊 Ripple 涟漪")
    st.markdown("**KOC 早期信号雷达 + 多 Agent 内容工厂**")
    st.divider()
    st.markdown("### 关于产品")
    st.markdown(
        "**「资本永远先于舆论。」**\n\n"
        "Ripple 借鉴金融界 Digital Oracle 的早期信号思想,"
        "用 12 个数据源并行扫描「刚开始升温」的话题,"
        "在热搜出现前 7-14 天发现机会。"
    )
    st.divider()
    st.markdown("### 灵感谱系")
    st.markdown(
        "- [Digital Oracle](https://github.com/komako-workshop/digital-oracle) — 早期信号\n"
        "- Claude Code 51 万行 — 架构纪律\n"
        "- [MiroFish](https://github.com/666ghj/MiroFish) — 群体仿真\n"
        "- [BettaFish](https://github.com/666ghj/BettaFish) — 多 Agent 辩论"
    )
    st.divider()
    st.markdown("### 12 Agent 工厂")
    st.markdown("""
    **Phase 1 - 信号感知**
    - 🔮 OracleAgent
    - 🔥 TrendScoutAgent
    - 🎨 StyleDecoderAgent

    **Phase 2 - 决策辩论**
    - 💬 ForumDebateAgent
    - 🎯 TopicStrategistAgent

    **Phase 3 - 内容生产**
    - ✍️ ScriptWriterAgent
    - 🖼 VisualProducerAgent
    - 📦 MaterialCuratorAgent

    **Phase 4 - 审查发布**
    - ✓ FactCheckerAgent
    - 🛡 RiskReviewerAgent
    - 🌐 SimPredictorAgent
    - 📊 InsightAnalystAgent
    """)


# ============ Main Title ============

st.markdown("""
<div style='text-align: center; padding: 2rem 0;'>
    <h1 style='font-size: 3rem; margin-bottom: 0;'>🌊 Ripple 涟漪</h1>
    <p style='font-size: 1.3rem; color: #475569; margin-top: 0.5rem;'>
        KOC 的 Bloomberg Terminal — 在热搜前发现下一个爆款
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
> 「KOC 追热点永远慢半拍,等看到热搜时已经红海。Ripple 用 12 个数据源并行扫描刚开始升温的话题,
> 让你提前 7-14 天发现机会,12 个 Agent 协作生成可发布的多平台内容包。」
""")

# ============ Tabs ============

tab_oracle, tab_demo, tab_agents, tab_about = st.tabs([
    "🔮 早期信号雷达 (Oracle)",
    "🚀 完整 Demo (12 Agent)",
    "🧠 Agent 架构展示",
    "📖 关于 Ripple",
])


# ============ Tab: Oracle ============

with tab_oracle:
    st.markdown("### 🔮 早期信号雷达 — Ripple 的核心创新")
    st.markdown(
        "**借鉴 Digital Oracle:** 真信号在搜索量、资本流、预测市场,"
        "不在已经爆的热搜。\n\n"
        "**12 数据源并行扫描:** Polymarket / Kalshi / Manifold / 微信指数 / 百度指数 / "
        "巨量算数 / 小红书灵感 / 微博实时 / HackerNews / GitHub Trending / Reddit / X"
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        topic_seed = st.text_input(
            "种子话题(关键词或场景)",
            value="美妆 冬季",
            help="例如:美妆 / 数码 / 学习 / 生活方式",
        )
    with col2:
        category = st.selectbox(
            "赛道",
            ["美妆", "数码", "学习", "生活", "知识", "搞笑", "本地", "通用"],
            index=0,
        )
    with col3:
        platforms = st.multiselect(
            "目标平台",
            ["channels", "wechat_official", "xhs", "douyin", "bilibili", "weibo"],
            default=["channels", "xhs", "douyin"],
        )

    if st.button("🔍 扫描早期信号", type="primary", use_container_width=True):
        with st.spinner(f"正在并行扫描 12 个数据源..."):
            oracle = OracleAgent()
            try:
                report = asyncio.run(oracle.scan(topic_seed, category, platforms))

                st.success(
                    f"✓ 扫描完成: {report.sources_succeeded}/{report.sources_scanned} 个数据源,"
                    f"耗时 {report.scan_time_ms} ms"
                )

                if not report.trends:
                    st.warning("当前没有强信号检测到,建议跟踪现有热点或扩大关键词")
                else:
                    st.markdown(f"### Top {len(report.trends)} 早期信号")

                    for i, trend in enumerate(report.trends, 1):
                        with st.expander(
                            f"#{i} {trend.topic} · 置信度 {trend.confidence:.2f} · "
                            f"窗口期 {trend.horizon_days} 天",
                            expanded=(i <= 3),
                        ):
                            col_a, col_b = st.columns([2, 1])
                            with col_a:
                                st.markdown(f"**类别:** {trend.category}")
                                st.markdown(f"**推荐角度:** {trend.recommended_angle}")
                                st.markdown(f"**最佳平台:** {', '.join(trend.best_platforms)}")
                                st.markdown(f"**说明:**\n{trend.explanation}")

                                if trend.risks:
                                    st.warning("**风险:**\n" + "\n".join(f"- {r}" for r in trend.risks))

                            with col_b:
                                st.metric("置信度", f"{trend.confidence:.2f}")
                                st.metric("窗口期", f"{trend.horizon_days} 天")
                                st.metric("信号源数", len(set(e.source for e in trend.evidence)))

                                st.markdown("**信号依据:**")
                                for e in trend.evidence[:5]:
                                    st.markdown(
                                        f"- `{e.source}`: {e.normalized:.2f} (Δ {e.delta:.2f})"
                                    )
            except Exception as ex:
                st.error(f"扫描失败: {ex}")


# ============ Tab: Demo ============

with tab_demo:
    st.markdown("### 🚀 12 Agent 完整工厂演示")
    st.markdown(
        "选好选题方向 → 12 个 Agent 协作 → 输出完整内容包"
        "(标题×10 / 封面×5 / 多平台脚本 / 合规审查 / 早期信号报告)"
    )

    st.info(
        "💡 完整 12 Agent 流水线需要 LLM API(MiniMax/混元/Claude)。"
        "请先在 `.env` 配置 `MINIMAX_API_KEY`,然后启动 FastAPI 后端:\n"
        "```bash\ncd apps/api\nuvicorn main:app --reload --port 8000\n```"
    )

    api_base = st.text_input("Backend API", value="http://localhost:8000")

    col1, col2 = st.columns(2)
    with col1:
        demo_topic = st.text_input("种子话题", value="珂润洗颜泡沫")
        demo_category = st.selectbox(
            "赛道",
            ["美妆", "数码", "学习", "生活", "知识", "搞笑", "本地", "通用"],
            key="demo_cat",
        )
    with col2:
        demo_platforms = st.multiselect(
            "目标平台",
            ["channels", "wechat_official", "xhs", "douyin", "bilibili", "weibo"],
            default=["xhs", "channels", "douyin"],
            key="demo_plat",
        )
        demo_context = st.text_area("KOC 背景(可选)", height=100, placeholder="例如:护肤博主,粉丝1.2万")

    if st.button("🚀 启动 12 Agent 流水线", type="primary", use_container_width=True, key="demo_btn"):
        import requests
        try:
            with st.spinner("12 Agent 协作中..."):
                resp = requests.post(
                    f"{api_base}/api/v1/ripple/run",
                    json={
                        "topic_seed": demo_topic,
                        "category": demo_category,
                        "target_platforms": demo_platforms,
                        "koc_context": demo_context,
                    },
                    timeout=180,
                )
                if resp.status_code != 200:
                    st.error(f"调用失败 ({resp.status_code}): {resp.text}")
                else:
                    data = resp.json()

                    st.success(f"✓ 完成! 用时 {data['duration_ms']} ms")

                    # 各 Phase 展示
                    if data.get("oracle_report"):
                        with st.expander("📡 Phase 1 - 早期信号雷达", expanded=True):
                            st.json(data["oracle_report"])

                    if data.get("style_card"):
                        with st.expander("🎨 KOC 风格卡片"):
                            st.json(data["style_card"])

                    if data.get("topic_strategy"):
                        with st.expander("🎯 选题策略", expanded=True):
                            st.json(data["topic_strategy"])

                    if data.get("content_package"):
                        with st.expander("✍️ 多平台内容包", expanded=True):
                            st.json(data["content_package"])

                    if data.get("compliance"):
                        with st.expander("🛡 合规审查"):
                            st.json(data["compliance"])

                    if data.get("simulation"):
                        with st.expander("🌐 群体仿真预测"):
                            st.json(data["simulation"])

                    if data.get("insight"):
                        with st.expander("📊 归因报告", expanded=True):
                            st.markdown(data["insight"].get("executive_summary", ""))

        except requests.exceptions.ConnectionError:
            st.error(
                f"无法连接到 {api_base}。请先启动后端:\n"
                "```bash\ncd apps/api && uvicorn main:app --reload --port 8000\n```"
            )
        except Exception as ex:
            st.error(f"调用失败: {ex}")


# ============ Tab: Agents ============

with tab_agents:
    st.markdown("### 🧠 12 Agent 架构展示")

    st.markdown("""
    Ripple 的架构 100% 借鉴 Claude Code 51 万行代码:
    - **TAOR 主循环** (Think-Act-Observe-Repeat)
    - **五层记忆系统** (KOC.md / memdir / extractMemories / findRelevantMemories / 上下文注入)
    - **四层压缩** (Snip → Microcompact → Collapse → Auto-compact)
    - **Hooks 系统** (PreToolUse / PostToolUse / Stop / PreCompact / Permission)
    - **Skills 渐进披露** (YAML frontmatter + skills_list / skill_view)
    - **Subagent** (Task = 同构子循环)
    """)

    st.code("""
graph TB
  Entry[Web/Desktop/Mini-Program/PWA] --> Gateway[FastAPI + LiteLLM Proxy]
  Gateway --> Core[query_loop AsyncGenerator + Terminal枚举]
  Core --> Memory[5层记忆系统]
  Core --> Skills[5个 Killer Skills]
  Core --> Agents[12 Agent 工厂]

  Agents --> P1[Phase 1 信号感知<br/>Oracle / TrendScout / StyleDecoder]
  Agents --> P2[Phase 2 决策辩论<br/>ForumDebate / TopicStrategist]
  Agents --> P3[Phase 3 内容生产<br/>ScriptWriter / VisualProducer / MaterialCurator]
  Agents --> P4[Phase 4 审查发布<br/>FactChecker / Risk / SimPredictor / Insight]

  Agents --> Models[LiteLLM Router]
  Models --> M1[MiniMax M2.7 主力]
  Models --> M2[腾讯混元 兜底]
  Models --> M3[BYOK: DeepSeek/豆包/Claude/...]
  Models --> M4[本地: Ollama/LM Studio]
""", language="mermaid")

    st.markdown("### 5 Killer Skills")
    skills = [
        ("oracle-early-signal", "12 数据源 + CUSUM + 矛盾推理 早期信号雷达"),
        ("koc-content-package", "选题确定后生成完整多平台内容包"),
        ("viral-formula-library", "标题学/封面学/节奏学 7 公式 + 5 风格"),
        ("copyright-asset-library", "版权友好素材清单 + 风险检测"),
        ("ai-detection-bypass", "降 AI 味的 15 个具体技巧(保留人味)"),
    ]
    for name, desc in skills:
        st.markdown(f"- **`{name}`**: {desc}")


# ============ Tab: About ============

with tab_about:
    st.markdown("### 📖 关于 Ripple")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **大赛**: 腾讯 PCG 校园 AI 产品创意大赛
        **赛道**: 命题赛道 · 赛题 5
        **题目**: AI + 社媒流量增长,连接 KOC 成长

        **三大差异化**:
        1. **创新性**: 全网首个把"金融早期信号思想"应用到 KOC 内容预测
        2. **AI 原生性**: 12+ 数据源 + 多 Agent 辩论 + 群体仿真,缺一不可
        3. **赛道适配性**: 深度集成腾讯混元 + 元器 + 视频号 + 公众号
        """)

    with col2:
        st.markdown("""
        **核心技术栈**:
        - Python 3.12 + FastAPI + LangGraph + LiteLLM
        - PostgreSQL + pgvector
        - Next.js 15 / Tauri 2 / 微信小程序 / PWA
        - MiniMax M2.7 主力 + 腾讯混元兜底 + BYOK 用户自定义

        **合规**:
        - 《AI 生成合成内容标识办法》全合规
        - STRIDE 威胁建模 + OWASP LLM Top 10 v2 全覆盖
        - 多租户 RLS + Argon2id 加密
        """)

    st.divider()
    st.markdown("### 与现有竞品的根本差异")
    st.dataframe({
        "维度": ["信号视角", "预测时效", "数据源", "AI 形态", "解释能力", "平台战场"],
        "千瓜/飞瓜/Buffer/Jasper": [
            "看已经火的内容",
            "T+0 滞后",
            "单一平台抓取",
            "单 LLM 写文案",
            "黑箱推荐",
            "单平台或全平台浅",
        ],
        "Ripple 涟漪": [
            "看刚开始升温的早期信号",
            "T-7 至 T-14 提前发现",
            "12 数据源并行 + 矛盾推理",
            "12 Agent 协作工厂",
            "每个建议有信号依据 + 置信度",
            "视频号深度 + 全平台覆盖",
        ],
    }, use_container_width=True)


# ============ Footer ============

st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #94a3b8; padding: 2rem 0;'>
        Ripple v0.1 · 2026 · 腾讯 PCG 校园 AI 产品创意大赛 · 赛题 5
    </div>
    """,
    unsafe_allow_html=True,
)
