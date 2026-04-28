"""Replay Store - SQLite 持久化执行图"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from ...types import ReplayNode, CognitivePhase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS replay_runs (
    run_id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    project_id TEXT,
    query TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT DEFAULT 'running',
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS replay_nodes (
    node_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    parent_ids TEXT NOT NULL DEFAULT '[]',
    phase TEXT NOT NULL,
    actor TEXT NOT NULL,
    input_hash TEXT,
    input_summary TEXT,
    output_summary TEXT,
    rejected_alternatives TEXT DEFAULT '[]',
    duration_ms INTEGER DEFAULT 0,
    timestamp TEXT NOT NULL,
    metadata TEXT,
    merkle_hash TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES replay_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_nodes_run ON replay_nodes(run_id);
CREATE INDEX IF NOT EXISTS idx_runs_trace ON replay_runs(trace_id);
CREATE INDEX IF NOT EXISTS idx_runs_user ON replay_runs(user_id);
"""


class ReplayStore:
    """SQLite 替放存储"""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if db_path is None:
            db_path = Path.home() / ".ripple" / "replay.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(_SCHEMA)
            conn.commit()

    def start_run(
        self,
        run_id: str,
        trace_id: str,
        user_id: str,
        query: str,
        project_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        from datetime import datetime
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO replay_runs 
                (run_id, trace_id, user_id, project_id, query, started_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (run_id, trace_id, user_id, project_id, query,
                 datetime.utcnow().isoformat(), json.dumps(metadata or {})),
            )
            conn.commit()

    def finish_run(self, run_id: str, status: str = "ok") -> None:
        from datetime import datetime
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE replay_runs SET finished_at = ?, status = ? WHERE run_id = ?",
                (datetime.utcnow().isoformat(), status, run_id),
            )
            conn.commit()

    def write_node(self, run_id: str, node: ReplayNode) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO replay_nodes
                (node_id, run_id, parent_ids, phase, actor,
                 input_hash, input_summary, output_summary,
                 rejected_alternatives, duration_ms, timestamp, metadata, merkle_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    node.node_id, run_id,
                    json.dumps(node.parent_ids), node.phase.value, node.actor,
                    node.input_hash, node.input_summary, node.output_summary,
                    json.dumps(node.rejected_alternatives), node.duration_ms,
                    node.timestamp.isoformat(), json.dumps(node.metadata, default=str),
                    node.merkle_hash(),
                ),
            )
            conn.commit()

    def get_run(self, run_id: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM replay_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_nodes(self, run_id: str) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM replay_nodes WHERE run_id = ? ORDER BY timestamp",
                (run_id,),
            ).fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d["parent_ids"] = json.loads(d.get("parent_ids") or "[]")
                d["rejected_alternatives"] = json.loads(d.get("rejected_alternatives") or "[]")
                d["metadata"] = json.loads(d.get("metadata") or "{}")
                result.append(d)
            return result

    def list_runs(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if user_id:
                rows = conn.execute(
                    "SELECT * FROM replay_runs WHERE user_id = ? ORDER BY started_at DESC LIMIT ?",
                    (user_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM replay_runs ORDER BY started_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    def verify_merkle_chain(self, run_id: str) -> bool:
        """验证某次 run 的所有节点 Merkle 一致 - 防篡改证明"""
        nodes = self.get_nodes(run_id)
        for n in nodes:
            stored_hash = n.get("merkle_hash", "")
            recomputed = ReplayNode(
                node_id=n["node_id"],
                parent_ids=n["parent_ids"],
                phase=CognitivePhase(n["phase"]),
                actor=n["actor"],
                input_hash=n.get("input_hash") or "",
                input_summary=n.get("input_summary") or "",
                output_summary=n.get("output_summary") or "",
                rejected_alternatives=n["rejected_alternatives"],
                duration_ms=n["duration_ms"],
            ).merkle_hash()
            if stored_hash != recomputed:
                return False
        return True


_store_singleton: Optional[ReplayStore] = None


def _get_store() -> ReplayStore:
    global _store_singleton
    if _store_singleton is None:
        _store_singleton = ReplayStore()
    return _store_singleton
