"""Checkpointed job store for long-running analysis work.

Mirrors the notebooks' checkpoint conventions: work is chunked, progress is
persisted after every batch, and interrupted jobs resume from the last
checkpoint. Delegated-mode coding jobs also queue work packets here so the
driving model can process them batch by batch.
"""

import json
import os
import re
import tempfile
import time
import uuid
from pathlib import Path

DEFAULT_ROOT = Path.home() / ".ai-anthro-toolkit" / "jobs"

# What create() issues: a lowercase kind, a hyphen, eight hex digits. Anything
# else came from a typo or an invention, and must not become a path.
_JOB_ID = re.compile(r"[a-z][a-z_]*-[0-9a-f]{8}")
_ID_HELP = ("Job IDs look like coding-1a2b3c4d and come back from "
            "start_codebook_job, start_coding_job, or ratify_codebook; pass "
            "the one those returned.")


class UnknownJobError(ValueError):
    """A well-formed job ID this store never issued (or has since lost)."""


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

    def _dir(self, job_id: str, create: bool = False) -> Path:
        """The job's directory, refusing IDs this store did not issue.

        Reads never create: a mistyped ID used to leave an empty directory
        behind and surface a bare FileNotFoundError, and an ID containing
        "../" reached outside the root.
        """
        if not isinstance(job_id, str) or not _JOB_ID.fullmatch(job_id):
            raise ValueError(f"{job_id!r} is not a job ID. {_ID_HELP}")
        d = self.root / job_id
        if create:
            d.mkdir(parents=True, exist_ok=True)
        elif not (d / "job.json").is_file():
            raise UnknownJobError(
                f"No job {job_id!r} in this server's job store "
                f"({self.root}). {_ID_HELP}")
        return d

    def create(self, kind: str, payload: dict) -> str:
        job_id = f"{kind}-{uuid.uuid4().hex[:8]}"
        d = self._dir(job_id, create=True)
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
