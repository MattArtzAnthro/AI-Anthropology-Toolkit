"""Checkpointed job store for long-running analysis work.

Mirrors the notebooks' checkpoint conventions: work is chunked, progress is
persisted after every batch, and interrupted jobs resume from the last
checkpoint. Delegated-mode coding jobs also queue work packets here so the
driving model can process them batch by batch.
"""

import errno
import json
import os
import re
import tempfile
import threading
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows: msvcrt's byte-range lock instead
    fcntl = None  # type: ignore[assignment]
try:
    import msvcrt
except ImportError:
    msvcrt = None  # type: ignore[assignment]

# How long a call waits for a job another call holds before it is refused. A codebook's last
# batch can hold its job for minutes while an embedding model downloads.
LOCK_TIMEOUT = 120.0
_POLL = 0.05

DEFAULT_ROOT = Path.home() / ".ai-anthro-toolkit" / "jobs"

# What create() issues: a lowercase kind, a hyphen, eight hex digits. Anything
# else came from a typo or an invention, and must not become a path.
_JOB_ID = re.compile(r"[a-z][a-z_]*-[0-9a-f]{8}")
_ID_HELP = ("Job IDs look like coding-1a2b3c4d and come back from "
            "start_codebook_job, start_coding_job, or ratify_codebook; pass "
            "the one those returned.")


# One re-entrant lock per job folder, shared by every JobStore in the process, and a count of
# how deeply the thread holding it has entered, so the file lock is taken once.
_guard = threading.Lock()
_locks: dict[str, threading.RLock] = {}
_depth = threading.local()


def _busy(job_id: str) -> str:
    return (f"{job_id} is held by another call that has not finished in {LOCK_TIMEOUT:.0f} "
            "seconds (a codebook's last batch can take minutes while an embedding model "
            "downloads). Nothing was recorded; try again when it has finished.")


def _try_lock(fh, root: Path) -> bool:
    """Take the job's file lock without waiting; False when another process holds it."""
    try:
        if fcntl is not None:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError as exc:
        if exc.errno in (errno.EAGAIN, errno.EWOULDBLOCK, errno.EACCES, errno.EDEADLK):
            return False
        if exc.errno in (errno.ENOLCK, errno.ENOTSUP, errno.EOPNOTSUPP):
            raise RuntimeError(
                f"The job store at {root} is on a file system that takes no file locks (a "
                "network share mounted without locking), so two calls could overwrite each "
                "other's work. Keep the job store on a local disk.") from exc
        raise
    return True


def _lock_file(path: Path, job_id: str, root: Path, deadline: float):
    """Open the job's lock file and take its lock, polling until `deadline`."""
    fh = open(path, "a+", encoding="utf-8")  # noqa: SIM115
    try:
        while not _try_lock(fh, root):
            if time.monotonic() >= deadline:
                raise RuntimeError(_busy(job_id))
            time.sleep(_POLL)
    except BaseException:
        fh.close()
        raise
    return fh


def _unlock(fh) -> None:
    if fcntl is not None:
        fcntl.flock(fh, fcntl.LOCK_UN)
    else:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)


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

    @contextmanager
    def locked(self, job_id: str) -> Iterator[None]:
        """Hold the job for one read-change-write, against other threads and other server
        processes that share this job store.

        mcp 2.x runs each sync tool in a worker thread, so two calls on one job can
        interleave their reads and writes, and a second host's server can share the store.
        Re-entrant within a thread. Refuses an ID the store did not issue, and refuses with a
        RuntimeError, having changed nothing, when another call holds the job for longer than
        LOCK_TIMEOUT seconds or the file system takes no file locks. The file lock is flock,
        or msvcrt's on Windows.
        """
        d = self._dir(job_id)
        # The folder itself, not its spelling: on a case-insensitive disk, or through a
        # symlink, two roots can name one folder, and a thread nesting both must not wait on
        # its own file lock.
        st = d.stat()
        key = f"{st.st_dev}:{st.st_ino}"
        with _guard:
            lock = _locks.setdefault(key, threading.RLock())
        deadline = time.monotonic() + LOCK_TIMEOUT
        if not lock.acquire(timeout=LOCK_TIMEOUT):
            raise RuntimeError(_busy(job_id))
        held: dict[str, int] = _depth.__dict__.setdefault("held", {})
        held[key] = held.get(key, 0) + 1
        fh = None
        try:
            if held[key] == 1 and (fcntl is not None or msvcrt is not None):
                fh = _lock_file(d / ".lock", job_id, self.root, deadline)
            yield
        finally:
            held[key] -= 1
            if fh is not None:
                _unlock(fh)
                fh.close()
            lock.release()

    @staticmethod
    def new_id(kind: str) -> str:
        """An ID for a job of this kind, to name before create() makes it."""
        return f"{kind}-{uuid.uuid4().hex[:8]}"

    def create(self, kind: str, payload: dict, job_id: str | None = None) -> str:
        """Make a job, under `job_id` (from new_id) if given; a job that exists is kept."""
        job_id = job_id or self.new_id(kind)
        if not job_id.startswith(f"{kind}-"):
            raise ValueError(f"{job_id!r} is not an ID for a {kind} job.")
        d = self._dir(job_id, create=True)
        if (d / "job.json").is_file():
            return job_id
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
        with self.locked(job_id):  # read, change, write: two at once would lose a field
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
