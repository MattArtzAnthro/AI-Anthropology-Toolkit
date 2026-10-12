"""Checkpointed job store for long-running analysis work.

Mirrors the notebooks' checkpoint conventions: work is chunked, progress is
persisted after every batch, and interrupted jobs resume from the last
checkpoint. Delegated-mode coding jobs also queue work packets here so the
driving model can process them batch by batch.
"""

import json
import os
import tempfile
import time
import uuid
from pathlib import Path

DEFAULT_ROOT = Path.home() / ".ai-anthro-toolkit" / "jobs"


def _write_atomic(path: Path, content: str) -> None:
    """Replace `path` in one step.

    API-mode jobs write from a worker thread while get_job_status and
    get_job_result read from the server's, so a plain truncate-and-write
    lets a reader see an empty or half-written file.
    """
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


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
        _write_atomic(d / "job.json", json.dumps({
            "job_id": job_id,
            "kind": kind,
            "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "status": "in_progress",
            "processed": 0,
            "total": payload.get("total", 0),
            "payload": payload,
        }, indent=2))
        return job_id

    def read(self, job_id: str) -> dict:
        return json.loads((self._dir(job_id) / "job.json").read_text(encoding="utf-8"))

    def update(self, job_id: str, **fields) -> dict:
        state = self.read(job_id)
        state.update(fields)
        _write_atomic(self._dir(job_id) / "job.json", json.dumps(state, indent=2))
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
        _write_atomic(p, content)
        return p

    def load_artifact(self, job_id: str, name: str) -> str | None:
        p = self._dir(job_id) / name
        return p.read_text(encoding="utf-8") if p.exists() else None

    def complete(self, job_id: str) -> dict:
        return self.update(job_id, status="complete")
