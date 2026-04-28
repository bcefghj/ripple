"""Kernel 核心类型定义 - Pydantic v2 全栈类型安全"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# 基础枚举
# ============================================================


class PermissionLevel(str, Enum):
    """工具权限级别 - 仿 Claude Code 权限分层"""
    READ = "read"           # 只读: 数据查询
    WRITE = "write"         # 写入: 持久化数据
    NETWORK = "network"     # 网络: 外部 API 调用
    GENERATE = "generate"   # 生成: LLM 调用
    DESTRUCTIVE = "destructive"  # 破坏性: 不可逆操作


class CognitivePhase(str, Enum):
    """TAOR 认知循环的阶段"""
    SENSE = "sense"
    THINK = "think"
    PLAN = "plan"
    ACT = "act"
    OBSERVE = "observe"
    REFLECT = "reflect"
    UPDATE = "update"


class EventType(str, Enum):
    """统一事件总线类型"""
    THINKING = "thinking"
    AGENT_START = "agent_start"
    AGENT_PROGRESS = "agent_progress"
    AGENT_END = "agent_end"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TOKEN = "token"
    CITATION = "citation"
    REPORT_CARD = "report_card"
    PERSONA_UPDATE = "persona_update"
    REPLAY_NODE = "replay_node"
    DONE = "done"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class CardType(str, Enum):
    """前端卡片类型"""
    TOPIC_PANEL = "topic_panel"
    SIM_RESULT = "sim_result"
    RISK_REWARD = "risk_reward"
    CAMPAIGN_TIMELINE = "campaign_timeline"
    SCRIPT_VARIANTS = "script_variants"
    CITATION_LIST = "citation_list"
    PERSONA_RADAR = "persona_radar"
    REPLAY_GRAPH = "replay_graph"
    TREND_CHAIN = "trend_chain"
    COHORT_BARS = "cohort_bars"
    CROSS_PLATFORM = "cross_platform"


# ============================================================
# Citation 引用 / 信任
# ============================================================


class Citation(BaseModel):
    """信息来源引用 - 反 AI 投毒"""
    model_config = ConfigDict(frozen=False)

    source_id: str = Field(default_factory=lambda: f"cite_{uuid4().hex[:8]}")
    url: str
    title: str = ""
    source_type: Literal[
        "polymarket", "manifold", "hackernews",
        "weibo", "douyin", "baidu", "bilibili",
        "llm_inference", "user_provided", "knowledge_base"
    ] = "knowledge_base"
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    snippet: str = ""
    confidence: float = 1.0
    cross_verified: bool = False
    verification_score: Optional[float] = None

    def merkle_hash(self) -> str:
        """节点级摘要 - 用于防篡改 Replay"""
        payload = f"{self.url}|{self.title}|{self.snippet}|{self.retrieved_at.isoformat()}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


# ============================================================
# Replay Node - 可回放执行图
# ============================================================


class ReplayNode(BaseModel):
    """Replay Graph 的单个节点 - 仿 Merkle Chain"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    node_id: str = Field(default_factory=lambda: f"node_{uuid4().hex[:8]}")
    parent_ids: List[str] = Field(default_factory=list)
    phase: CognitivePhase
    actor: str  # 哪个工具/模块产生
    input_hash: str = ""
    input_summary: str = ""
    output_summary: str = ""
    rejected_alternatives: List[str] = Field(default_factory=list)
    duration_ms: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def merkle_hash(self) -> str:
        """节点摘要 - 含父节点哈希形成链"""
        parents_hash = "|".join(sorted(self.parent_ids))
        payload = (
            f"{self.node_id}|{self.actor}|{self.phase.value}|"
            f"{self.input_hash}|{self.output_summary}|{parents_hash}"
        )
        return hashlib.sha256(payload.encode()).hexdigest()


# ============================================================
# Stream Events - SSE 事件总线
# ============================================================


class StreamEvent(BaseModel):
    """统一事件总线 - 前后端通过 SSE 传输"""
    event_id: str = Field(default_factory=lambda: f"evt_{uuid4().hex[:8]}")
    event_type: EventType
    timestamp: float = Field(default_factory=time.time)
    trace_id: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)

    def to_sse(self) -> str:
        """格式化为 SSE wire format"""
        import json
        data = {
            "type": self.event_type.value,
            "id": self.event_id,
            "ts": self.timestamp,
            "trace": self.trace_id,
            **self.payload,
        }
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# ============================================================
# Tool 工具协议
# ============================================================


class ToolInput(BaseModel):
    """工具输入基类 - 所有工具的入参都继承自它"""
    model_config = ConfigDict(extra="allow")


class ToolOutput(BaseModel):
    """工具输出基类"""
    model_config = ConfigDict(extra="allow")
    success: bool = True
    error: Optional[str] = None
    citations: List[Citation] = Field(default_factory=list)
    duration_ms: int = 0


class ToolSchema(BaseModel):
    """工具描述符 - Tool Registry 用"""
    name: str
    description: str
    permission_level: PermissionLevel = PermissionLevel.READ
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    cost_estimate_ms: int = 1000  # 预估耗时
    cost_estimate_tokens: int = 0


# ============================================================
# Persona Vector
# ============================================================


class PersonaDimensions(BaseModel):
    """人设的可解释维度 - 256 维 embedding 之外的标量解释"""
    formality: float = 0.5  # 正式度
    technicality: float = 0.5  # 专业度
    humor_density: float = 0.5  # 梗密度
    sentence_length_avg: float = 30.0
    emoji_density: float = 0.0
    first_person_freq: float = 0.5
    questions_freq: float = 0.3
    exclamation_freq: float = 0.2
    professional_jargon: float = 0.5
    vulnerability_disclosure: float = 0.3  # 自我袒露度

    def as_vector(self) -> List[float]:
        return [
            self.formality, self.technicality, self.humor_density,
            self.sentence_length_avg / 100.0,  # normalize
            self.emoji_density, self.first_person_freq,
            self.questions_freq, self.exclamation_freq,
            self.professional_jargon, self.vulnerability_disclosure,
        ]


class PersonaVector(BaseModel):
    """KOC 人设向量 - Git for Voice 的核心"""
    user_id: str
    branch: str = "main"  # main / experimental_humor / experimental_technical
    parent_branch: Optional[str] = None
    version: int = 1
    embedding: List[float] = Field(default_factory=list)  # 256 维
    dimensions: PersonaDimensions = Field(default_factory=PersonaDimensions)
    sample_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    drift_score: float = 0.0
    locked: bool = False  # 是否锁定（不再更新）
    notes: str = ""


# ============================================================
# Topic / Signal
# ============================================================


class Topic(BaseModel):
    """选题候选"""
    topic_id: str = Field(default_factory=lambda: f"topic_{uuid4().hex[:8]}")
    title: str
    category: str = "general"
    confidence: float = 0.5
    horizon_days: int = 7
    evidence: List[Citation] = Field(default_factory=list)
    cross_platform_gaps: List[str] = Field(default_factory=list)
    persona_fit_score: float = 0.5
    risk_reward: Optional["RiskRewardScore"] = None
    explanation: str = ""


class RiskRewardScore(BaseModel):
    """选题双头评分"""
    potential_score: float = 0.5  # 0-1 爆款潜力
    risk_score: float = 0.5  # 0-1 翻车风险
    regulatory_sensitivity: Literal["low", "mid", "high"] = "low"
    recommendation: Literal["push", "hedge", "avoid"] = "hedge"
    reasoning: str = ""
    calibrated: bool = False


# ============================================================
# Cohort 受众
# ============================================================


class Cohort(BaseModel):
    """受众群体定义"""
    cohort_id: str
    name: str  # "25-30 岁二线女性"
    age_range: tuple[int, int] = (18, 60)
    gender_bias: Literal["female", "male", "neutral"] = "neutral"
    city_tier: Literal["1", "2", "3", "4+", "all"] = "all"
    interests: List[str] = Field(default_factory=list)
    embedding: List[float] = Field(default_factory=list)


class CohortAffinity(BaseModel):
    """内容对人群的吸引力评分"""
    cohort_id: str
    affinity_score: float  # 0-1
    confidence_interval: tuple[float, float] = (0.0, 1.0)
    sample_size: int = 0
    reasoning: str = ""


# ============================================================
# Campaign 战役
# ============================================================


class CampaignDay(BaseModel):
    """战役图中的一天"""
    day_index: int  # 1-7
    role: Literal[
        "hook", "deepdive", "qa", "ugc",
        "summary", "live_pre", "review", "hotspot_buffer"
    ]
    topic: str
    platform: str
    content_type: str  # 短视频/图文/直播 ...
    expected_kpi: str
    dependencies: List[int] = Field(default_factory=list)
    estimated_effort_hours: float = 1.0


class Campaign(BaseModel):
    """7 天战役图"""
    campaign_id: str = Field(default_factory=lambda: f"camp_{uuid4().hex[:8]}")
    user_id: str
    theme: str
    days: List[CampaignDay] = Field(default_factory=list)
    flow_structure: Dict[str, float] = Field(
        default_factory=lambda: {"acquire": 0.2, "trust": 0.5, "convert": 0.3}
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# Trend Chain 因果链
# ============================================================


class TrendChainStage(BaseModel):
    """因果链的一个阶段"""
    stage: Literal["capital", "international_buzz", "cn_media", "mass_meme"]
    timeframe_days: tuple[int, int]  # (3, 5)
    indicators: List[str] = Field(default_factory=list)  # 哪些信号到达此阶段
    cn_coverage: float = 0.0  # 中文覆盖度 0-1


class TrendChain(BaseModel):
    """资本→国际→中文→大众 因果链"""
    chain_id: str = Field(default_factory=lambda: f"chain_{uuid4().hex[:8]}")
    seed_event: str
    stages: List[TrendChainStage] = Field(default_factory=list)
    current_stage: str = "capital"
    insertion_window: tuple[int, int] = (3, 7)  # 推荐插入时点（天）
    angles: List[str] = Field(default_factory=list)  # 科普向 / 吐槽向 / 玩梗向
    causal_strength: float = 0.5
    historical_precedents: List[Citation] = Field(default_factory=list)


# ============================================================
# SimPredictor 虚拟受众
# ============================================================


class SimPredictionResult(BaseModel):
    """虚拟受众团对一版内容的反馈"""
    content_variant_id: str
    overall_score: float
    cohort_breakdown: List[CohortAffinity] = Field(default_factory=list)
    confidence_interval: tuple[float, float] = (0.0, 1.0)
    completion_rate_estimate: float = 0.5
    controversy_level: float = 0.0
    sample_personas_consulted: int = 5


# ============================================================
# Run Context - 一次执行的上下文
# ============================================================


class RunContext(BaseModel):
    """单次 Agent 运行的上下文 - 所有工具和模块共享"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str = Field(default_factory=lambda: f"run_{uuid4().hex[:8]}")
    trace_id: str = Field(default_factory=lambda: f"trace_{uuid4().hex[:12]}")
    user_id: str = "anonymous"
    project_id: Optional[str] = None
    session_id: str = Field(default_factory=lambda: f"sess_{uuid4().hex[:8]}")
    query: str = ""
    persona_branch: str = "main"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# 解决 forward reference
Topic.model_rebuild()
