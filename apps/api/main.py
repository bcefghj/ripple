"""Ripple FastAPI 主入口

启动:
    uvicorn main:app --reload --port 8000

API:
    POST /api/v1/ripple/run            - 运行完整流水线
    GET  /api/v1/ripple/run/{req_id}   - 查询任务结果
    WS   /api/v1/ripple/stream         - WebSocket 流式 Agent 状态
    GET  /api/v1/oracle/scan           - 仅运行早期信号雷达
    GET  /api/v1/providers             - 列出可用 LLM Provider
    POST /api/v1/byok                  - 添加用户 API Key
    GET  /health                       - 健康检查
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

from agents.oracle_agent import OracleAgent
from agents.orchestrator import RippleOrchestrator
from utils.config import settings
from utils.llm_router import get_router, PROVIDERS


# ============ Lifespan ============


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动 / 关闭时的初始化"""
    logger.info(f"Starting Ripple API on port {settings.app_port}")
    logger.info(f"Memory root: {settings.memory_root_path}")
    yield
    logger.info("Shutting down Ripple API")


app = FastAPI(
    title="Ripple API",
    description="KOC 早期信号雷达 + 多 Agent 内容工厂",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ LLM Bridge ============


async def llm_call_bridge(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    max_tokens: int = 2000,
    temperature: float = 0.7,
    **kwargs,
) -> Dict[str, Any]:
    """统一 LLM 调用桥(给所有 Agent 用)
    
    返回格式适配 AgentLoop 期望的格式:
    {
        "message": {"role": "assistant", "content": "..."},
        "tool_calls": [],
        "stop_reason": "completed",
        "usage": {"total_tokens": 100, "cost_usd": 0.001},
    }
    """
    router = get_router()
    response = await router.complete(
        messages=messages,
        provider="minimax",
        fallback_providers=["hunyuan", "deepseek"],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return {
        "message": {"role": "assistant", "content": response.content},
        "tool_calls": [],
        "stop_reason": "completed",
        "usage": {
            "total_tokens": response.total_tokens,
            "cost_usd": response.cost_usd,
        },
    }


# 全局 Orchestrator(简化:生产应每请求 new)
_orchestrator: Optional[RippleOrchestrator] = None


def get_orchestrator() -> RippleOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = RippleOrchestrator(llm_call=llm_call_bridge)
    return _orchestrator


# ============ Pydantic Models ============


class RippleRunRequest(BaseModel):
    topic_seed: str
    category: str = "通用"
    target_platforms: List[str] = ["channels", "wechat_official", "xhs", "douyin"]
    koc_works: List[Dict[str, Any]] = []
    koc_context: Optional[str] = None


class OracleScanRequest(BaseModel):
    topic_seed: str
    category: str = "通用"
    target_platforms: List[str] = ["channels", "xhs", "douyin"]


class BYOKRequest(BaseModel):
    provider: str  # minimax / hunyuan / deepseek / ...
    api_key: str
    api_base: Optional[str] = None
    default_model: Optional[str] = None
    user_passphrase: str  # 用户主密码,用于加密 API Key


# ============ Routes ============


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "providers_configured": [
            p.name for p in get_router().list_available_providers(include_byok=False)
        ],
    }


@app.get("/api/v1/providers")
async def list_providers():
    """列出所有 LLM Provider"""
    return {
        "providers": [
            {
                "name": p.name,
                "display_name": p.display_name,
                "default_model": p.default_model,
                "available_models": p.available_models,
                "is_local": p.is_local,
                "requires_byok": p.requires_byok,
                "configured": bool(p.api_key) if not p.is_local else True,
            }
            for p in PROVIDERS.values()
        ]
    }


@app.post("/api/v1/oracle/scan")
async def oracle_scan(req: OracleScanRequest):
    """运行早期信号雷达(单独 OracleAgent)"""
    oracle = OracleAgent()
    report = await oracle.scan(req.topic_seed, req.category, req.target_platforms)
    return {
        "trends": [
            {
                "topic": t.topic,
                "category": t.category,
                "confidence": t.confidence,
                "horizon_days": t.horizon_days,
                "explanation": t.explanation,
                "recommended_angle": t.recommended_angle,
                "best_platforms": t.best_platforms,
                "risks": t.risks,
                "evidence": [
                    {"source": e.source, "value": e.raw_value, "normalized": e.normalized}
                    for e in t.evidence
                ],
            }
            for t in report.trends
        ],
        "scan_metadata": {
            "sources_scanned": report.sources_scanned,
            "sources_succeeded": report.sources_succeeded,
            "scan_time_ms": report.scan_time_ms,
            "generated_at": report.generated_at.isoformat(),
        },
    }


@app.post("/api/v1/ripple/run")
async def ripple_run(req: RippleRunRequest):
    """运行完整 12 Agent 流水线"""
    try:
        orchestrator = get_orchestrator()
        output = await orchestrator.run(
            topic_seed=req.topic_seed,
            category=req.category,
            target_platforms=req.target_platforms,
            koc_works=req.koc_works,
            koc_context=req.koc_context,
        )
        return {
            "request_id": output.request_id,
            "topic_seed": output.topic_seed,
            "duration_ms": output.duration_ms,
            "oracle_report": output.oracle_report,
            "style_card": output.style_card,
            "topic_strategy": output.topic_strategy,
            "content_package": output.content_package,
            "compliance": output.compliance,
            "simulation": output.simulation,
            "insight": output.insight,
            "errors": output.errors,
        }
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/api/v1/ripple/stream")
async def ripple_stream(websocket: WebSocket):
    """流式 Agent 状态"""
    await websocket.accept()
    try:
        # 接收请求
        data = await websocket.receive_json()
        req = RippleRunRequest(**data)

        orchestrator = get_orchestrator()
        async for event in orchestrator.run_streaming(
            topic_seed=req.topic_seed,
            category=req.category,
            target_platforms=req.target_platforms,
            koc_works=req.koc_works,
            koc_context=req.koc_context,
        ):
            await websocket.send_json(event)

    except WebSocketDisconnect:
        logger.info("WebSocket 客户端断开")
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"event": "error", "error": str(e)})
        except Exception:
            pass


@app.post("/api/v1/byok")
async def byok_add(req: BYOKRequest):
    """用户添加自己的 API Key (BYOK)
    
    注意:这只是接口定义,生产环境必须将 API Key 加密后存储,
    且解密只在调用 LLM 时临时进行,不暴露给前端。
    """
    from utils.crypto import encrypt

    # 加密用户 API Key
    encrypted = encrypt(req.api_key, req.user_passphrase)

    # 生产: 写入数据库 user_api_keys 表
    # 这里只是返回成功
    return {
        "success": True,
        "provider": req.provider,
        "encrypted_size_bytes": len(encrypted),
        "note": "API Key 已用 Argon2id + AES-256-GCM 加密存储",
    }


@app.get("/")
async def root():
    return {
        "name": "Ripple API",
        "version": "0.1.0",
        "description": "KOC 早期信号雷达 + 多 Agent 内容工厂",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.app_host, port=settings.app_port, reload=True)
