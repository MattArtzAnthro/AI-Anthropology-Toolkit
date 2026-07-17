"""Checkpointed job store for long-running analysis work.

Mirrors the notebooks' checkpoint conventions: work is chunked, progress is
persisted after every batch, and interrupted jobs resume from the last
checkpoint. Delegated-mode coding jobs also queue work packets here so the
driving model can process them batch by batch.
"""

import json
import time
import uuid
from pathlib import Path

DEFAULT_ROOT = Path.home() / ".ai-anthro-toolkit" / "jobs"


class JobStore:
    def __init__(self, root: Path | str = DEFAULT_ROOT):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _dir(self, job_id: str) -> Path:
        d = self.root / job_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def create(self, kind: str, payload: dict) -> str:
        job_id = f"{kind}-{uuid.uuid4().hex[:8]}"
        d = self._dir(job_id)
        (d / "job.json").write_text(json.dumps({
            "job_id": job_id,
            "kind": kind,
            "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "status": "in_progress",
            "processed": 0,
            "total": payload.get("total", 0),
            "payload": payload,
        }, indent=2), encoding="utf-8")
        return job_id

    def read(self, job_id: str) -> dict:
        return json.loads((self._dir(job_id) / "job.json").read_text(encoding="utf-8"))

    def update(self, job_id: str, **fields) -> dict:
        state = self.read(job_id)
        state.update(fields)
        (self._dir(job_id) / "job.json").write_text(
            json.dumps(state, indent=2), encoding="utf-8")
        return state

    def status(self, job_id: str) -> dict:
        state = self.read(job_id)
        total = state.get("total") or 0
        done = state.get("processed") or 0
        return {
            "job_id": job_id,
            "kind": state.get("kind"),
            "status": state.get("status"),
            "processed": done,
            "total": total,
            "pct": round(100 * done / total, 1) if total else None,
        }

    def save_artifact(self, job_id: str, name: str, content: str) -> Path:
        p = self._dir(job_id) / name
        p.write_text(content, encoding="utf-8")
        return p

    def load_artifact(self, job_id: str, name: str) -> str | None:
        p = self._dir(job_id) / name
        return p.read_text(encoding="utf-8") if p.exists() else None

    def complete(self, job_id: str) -> dict:
        return self.update(job_id, status="complete")
