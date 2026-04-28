"""FastAPI v2 - SSE 流式 Chat + Persona + Replay + BYOK"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..types import RunContext
from ..event_bus import EventBus
from ..orchestration import get_orchestrator
from ..cognition.persona import get_persona_manager
from ..persistence.memory import get_memory_system
from ..persistence.db import init_db, get_conn, get_db_path
from ..reasoning.replay import get_replay_store


router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.on_event("startup")
async def _startup() -> None:
    init_db()


# ============ Models ============


class ChatRequest(BaseModel):
    query: str
    user_id: str = "anonymous"
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    persona_branch: str = "main"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CalibrateRequest(BaseModel):
    user_id: str
    samples: List[str]
    branch: str = "main"
    notes: str = ""


class IngestRequest(BaseModel):
    user_id: str
    content: str
    branch: str = "main"


class BranchRequest(BaseModel):
    user_id: str
    branch_name: str
    parent: str = "main"


class MergeRequest(BaseModel):
    user_id: str
    from_branch: str
    into_branch: str = "main"
    alpha: float = 0.3


class BYOKRequest(BaseModel):
    user_id: str
    provider: str
    api_key: str
    user_passphrase: str


# ============ /chat (SSE) ============


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "kernel": "ripple-os",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """流式对话端点 - 返回 SSE 流"""
    ctx = RunContext(
        user_id=req.user_id,
        project_id=req.project_id,
        session_id=req.session_id or f"sess_{uuid4().hex[:8]}",
        query=req.query,
        persona_branch=req.persona_branch,
        metadata=req.metadata,
    )
    bus = EventBus(trace_id=ctx.trace_id, buffer_size=2048)

    orchestrator = get_orchestrator()

    async def runner():
        try:
            await orchestrator.run(ctx, bus)
        except Exception as e:
            await bus.error(f"runner crashed: {e}")
            await bus.done(status="error")

    async def event_stream():
        runner_task = asyncio.create_task(runner())
        try:
            async for event in bus.stream():
                yield event.to_sse()
        finally:
            if not runner_task.done():
                runner_task.cancel()
                try:
                    await runner_task
                except (asyncio.CancelledError, Exception):
                    pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ============ /persona ============


@router.post("/persona/calibrate")
async def persona_calibrate(req: CalibrateRequest):
    pm = get_persona_manager()
    if not req.samples:
        raise HTTPException(400, "samples required")
    vec = await pm.calibrate(
        user_id=req.user_id,
        samples=req.samples,
        branch=req.branch,
        notes=req.notes,
    )
    return {
        "user_id": vec.user_id,
        "branch": vec.branch,
        "version": vec.version,
        "sample_count": vec.sample_count,
        "dimensions": vec.dimensions.model_dump(),
    }


@router.post("/persona/ingest")
async def persona_ingest(req: IngestRequest):
    pm = get_persona_manager()
    vec, drift = await pm.ingest(req.user_id, req.content, branch=req.branch)
    return {
        "vector": {
            "user_id": vec.user_id,
            "branch": vec.branch,
            "version": vec.version,
            "sample_count": vec.sample_count,
            "drift_score": vec.drift_score,
            "dimensions": vec.dimensions.model_dump(),
        },
        "drift": {
            "similarity": drift.similarity,
            "drift_score": drift.drift_score,
            "warning": drift.warning,
            "block": drift.block,
            "explanation": drift.explanation,
        },
    }


@router.get("/persona/{user_id}")
async def persona_get(user_id: str, branch: str = "main"):
    pm = get_persona_manager()
    vec = pm.get(user_id, branch)
    if vec is None:
        raise HTTPException(404, "Persona not found")
    return {
        "user_id": vec.user_id,
        "branch": vec.branch,
        "version": vec.version,
        "sample_count": vec.sample_count,
        "dimensions": vec.dimensions.model_dump(),
        "embedding_preview": vec.embedding[:20] if vec.embedding else [],
        "embedding_size": len(vec.embedding),
        "drift_score": vec.drift_score,
        "last_updated": vec.last_updated.isoformat(),
    }


@router.get("/persona/{user_id}/branches")
async def persona_branches(user_id: str):
    pm = get_persona_manager()
    return {"branches": pm.list_branches(user_id)}


@router.post("/persona/branch")
async def persona_branch(req: BranchRequest):
    pm = get_persona_manager()
    try:
        vec = pm.branch(req.user_id, req.branch_name, parent=req.parent)
        return {"branch": vec.branch, "parent": req.parent}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/persona/merge")
async def persona_merge(req: MergeRequest):
    pm = get_persona_manager()
    try:
        vec = pm.merge(req.user_id, req.from_branch, into_branch=req.into_branch, alpha=req.alpha)
        return {"branch": vec.branch, "version": vec.version}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/persona/drift_check")
async def persona_drift_check(req: IngestRequest):
    pm = get_persona_manager()
    drift = await pm.check_drift(req.user_id, req.content, branch=req.branch)
    return {
        "similarity": drift.similarity,
        "drift_score": drift.drift_score,
        "warning": drift.warning,
        "block": drift.block,
        "explanation": drift.explanation,
    }


# ============ /replay ============


@router.get("/replay/runs")
async def replay_runs(user_id: Optional[str] = None, limit: int = 50):
    store = get_replay_store()
    return {"runs": store.list_runs(user_id=user_id, limit=limit)}


@router.get("/replay/{run_id}")
async def replay_get(run_id: str):
    store = get_replay_store()
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(404, "Run not found")
    nodes = store.get_nodes(run_id)
    valid = store.verify_merkle_chain(run_id)
    return {"run": run, "nodes": nodes, "merkle_valid": valid, "node_count": len(nodes)}


# ============ /memory ============


@router.get("/memory/{user_id}")
async def memory_list(
    user_id: str,
    layer: Optional[str] = None,
    project_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 50,
):
    ms = get_memory_system()
    layers = [layer] if layer else None
    entries = ms.recall(
        user_id=user_id,
        layers=layers,
        project_id=project_id,
        session_id=session_id,
        top_k=limit,
    )
    return {
        "entries": [
            {
                "id": e.memory_id, "layer": e.layer, "key": e.key,
                "content": e.content[:300], "importance": e.importance,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ]
    }


@router.post("/memory/write")
async def memory_write(payload: Dict[str, Any]):
    ms = get_memory_system()
    entry = ms.write(
        layer=payload.get("layer", "user"),
        user_id=payload["user_id"],
        key=payload["key"],
        content=payload["content"],
        importance=payload.get("importance", 0.5),
        project_id=payload.get("project_id"),
        session_id=payload.get("session_id"),
        metadata=payload.get("metadata"),
    )
    return {"memory_id": entry.memory_id}


# ============ /tools ============


@router.get("/tools")
async def list_tools():
    from ..action import get_registry
    reg = get_registry()
    tools = []
    for tool in reg.list_tools():
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "permission": tool.permission_level.value,
            "tags": tool.tags,
        })
    return {"tools": tools, "count": len(tools)}


# ============ /skills ============


@router.get("/skills")
async def list_skills():
    from ..skills import get_skill_library
    lib = get_skill_library()
    skills = []
    for s in lib.list_all():
        skills.append({
            "name": s.name,
            "description": s.description,
            "triggers": s.triggers,
            "tags": s.tags,
            "version": s.version,
        })
    return {"skills": skills, "count": len(skills)}


# ============ /byok ============


@router.post("/byok")
async def byok_add(req: BYOKRequest):
    """BYOK 真实落地 - 加密存储到 SQLite"""
    try:
        from utils.crypto import encrypt
    except ImportError:
        from ..persistence.crypto_fallback import encrypt  # type: ignore

    encrypted = encrypt(req.api_key, req.user_passphrase)
    key_id = f"key_{uuid4().hex[:8]}"

    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?)",
            (req.user_id, datetime.utcnow().isoformat()),
        )
        conn.execute(
            """INSERT INTO user_api_keys 
            (key_id, user_id, provider, encrypted_key, encrypted_at, revoked)
            VALUES (?, ?, ?, ?, ?, 0)""",
            (key_id, req.user_id, req.provider, encrypted,
             datetime.utcnow().isoformat()),
        )
        conn.execute(
            """INSERT INTO audit_log 
            (user_id, action, resource, timestamp, metadata)
            VALUES (?, 'byok.add', ?, ?, ?)""",
            (req.user_id, req.provider,
             datetime.utcnow().isoformat(),
             json.dumps({"key_id": key_id})),
        )
        conn.commit()

    return {
        "success": True,
        "key_id": key_id,
        "provider": req.provider,
        "encrypted_size_bytes": len(encrypted),
        "note": "API Key 已用 Argon2id + AES-256-GCM 加密落库",
    }


@router.get("/byok/{user_id}")
async def byok_list(user_id: str):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT key_id, provider, encrypted_at, revoked 
            FROM user_api_keys WHERE user_id = ? ORDER BY encrypted_at DESC""",
            (user_id,),
        ).fetchall()
        return {
            "keys": [
                {
                    "key_id": r["key_id"],
                    "provider": r["provider"],
                    "encrypted_at": r["encrypted_at"],
                    "revoked": bool(r["revoked"]),
                }
                for r in rows
            ]
        }


@router.delete("/byok/{key_id}")
async def byok_revoke(key_id: str):
    with get_conn() as conn:
        conn.execute("UPDATE user_api_keys SET revoked = 1 WHERE key_id = ?", (key_id,))
        conn.commit()
    return {"success": True, "key_id": key_id, "revoked": True}


# ============ /audit ============


@router.get("/audit/{user_id}")
async def audit_log(user_id: str, limit: int = 100):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT action, resource, timestamp, metadata 
            FROM audit_log WHERE user_id = ? ORDER BY log_id DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        return {"logs": [dict(r) for r in rows]}
