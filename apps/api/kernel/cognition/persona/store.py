"""PersonaStore - SQLite 持久化人设向量"""

from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from ...persistence.db import get_conn
from ...types import PersonaDimensions, PersonaVector


class PersonaStore:
    def upsert(self, vector: PersonaVector) -> PersonaVector:
        with get_conn() as conn:
            existing = conn.execute(
                "SELECT vector_id, version FROM persona_vectors WHERE user_id = ? AND branch = ?",
                (vector.user_id, vector.branch),
            ).fetchone()
            if existing:
                vector.version = existing["version"] + 1
                conn.execute(
                    """UPDATE persona_vectors SET 
                    embedding = ?, dimensions = ?, sample_count = ?, drift_score = ?,
                    locked = ?, notes = ?, last_updated = ?, version = ?
                    WHERE vector_id = ?""",
                    (
                        json.dumps(vector.embedding),
                        json.dumps(vector.dimensions.model_dump()),
                        vector.sample_count,
                        vector.drift_score,
                        int(vector.locked),
                        vector.notes,
                        datetime.utcnow().isoformat(),
                        vector.version,
                        existing["vector_id"],
                    ),
                )
            else:
                vid = f"pv_{uuid4().hex[:8]}"
                conn.execute(
                    """INSERT INTO persona_vectors
                    (vector_id, user_id, branch, parent_branch, version,
                     embedding, dimensions, sample_count, drift_score,
                     locked, notes, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        vid, vector.user_id, vector.branch, vector.parent_branch,
                        vector.version,
                        json.dumps(vector.embedding),
                        json.dumps(vector.dimensions.model_dump()),
                        vector.sample_count, vector.drift_score,
                        int(vector.locked), vector.notes,
                        datetime.utcnow().isoformat(),
                    ),
                )
            conn.commit()
        return vector

    def get(self, user_id: str, branch: str = "main") -> Optional[PersonaVector]:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM persona_vectors WHERE user_id = ? AND branch = ? ORDER BY version DESC LIMIT 1",
                (user_id, branch),
            ).fetchone()
            if not row:
                return None
            return PersonaVector(
                user_id=row["user_id"],
                branch=row["branch"],
                parent_branch=row["parent_branch"],
                version=row["version"],
                embedding=json.loads(row["embedding"] or "[]"),
                dimensions=PersonaDimensions(**json.loads(row["dimensions"])),
                sample_count=row["sample_count"],
                drift_score=row["drift_score"],
                locked=bool(row["locked"]),
                notes=row["notes"] or "",
                last_updated=datetime.fromisoformat(row["last_updated"]),
            )

    def list_branches(self, user_id: str) -> List[str]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT branch FROM persona_vectors WHERE user_id = ?",
                (user_id,),
            ).fetchall()
            return [r["branch"] for r in rows]

    def add_sample(self, user_id: str, content: str, platform: str = "", metrics: Optional[dict] = None) -> str:
        sid = f"smp_{uuid4().hex[:8]}"
        with get_conn() as conn:
            conn.execute(
                """INSERT INTO persona_samples 
                (sample_id, user_id, content, platform, metrics, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (sid, user_id, content, platform,
                 json.dumps(metrics or {}), datetime.utcnow().isoformat()),
            )
            conn.commit()
        return sid

    def list_samples(self, user_id: str, limit: int = 50) -> List[str]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT content FROM persona_samples WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
            return [r["content"] for r in rows]


_singleton: Optional[PersonaStore] = None


def get_persona_store() -> PersonaStore:
    global _singleton
    if _singleton is None:
        _singleton = PersonaStore()
    return _singleton
