#!/usr/bin/env python3
"""The proof stamp: which model files the provers last passed on.

Usage:
    stamp.py --check                       exit 0 when formal/stamp.json matches the files now
    stamp.py --snapshot FILE               record the files as they are, before the provers run
    stamp.py --write --snapshot FILE       write formal/stamp.json from FILE, after the provers pass
    (each also takes --root DIR, the project folder; default: the folder above this script's folder)

The stamp covers every file under formal/ except build output and the stamp itself: the models,
the verdicts they printed, the check scripts, and formal/modeled.txt. The offline gate runs --check,
so a change to a model fails the gate until the provers have passed on it. Only formal/check.sh
writes the stamp: it takes a snapshot first, runs the provers, and then writes from that snapshot,
which is refused when any file changed in between, so an edit made while the provers ran is never
recorded as proved.

formal/modeled.txt lists the code files the models cover (one path or glob per line, relative to
the project folder, # for comments). The code is not hashed: the conformance tests hold it to the
models' verdicts, and the pre-push hook runs the provers when a push changes a listed file. Every
line must match a file, so a renamed code file cannot drop out of the list unnoticed.

new_gate.py installs this file into a project as formal/stamp.py. Edit the plugin's copy.
Standard library only; runs on Python 3.9 or later.

Exit codes: 0 ok, 1 the stamp is missing, stale or refused, 2 usage error.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
from pathlib import Path

SKIP_DIRS = {".lake", "__pycache__", "states", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
SKIP_FILES = {"stamp.json", ".DS_Store"}


class StampError(Exception):
    pass


def covered(root: Path) -> list[str]:
    """Every file the stamp covers, as sorted paths relative to the project folder.

    Raises when formal/modeled.txt is missing, empty, or has a line that matches no file in the project.
    """
    listing = root / "formal" / "modeled.txt"
    if not listing.is_file():
        raise StampError("no formal/modeled.txt: list the code files the models cover, one path or glob per line")
    entries = [line.split("#", 1)[0].strip() for line in listing.read_text(encoding="utf-8").splitlines()]
    entries = [e for e in entries if e]
    if not entries:
        raise StampError("formal/modeled.txt lists no files, so nothing says which code the models cover")
    files: set[str] = set()
    base = root.resolve()
    for entry in entries:
        found = [Path(p) for p in glob.glob(str(root / entry), recursive=True) if Path(p).is_file()]
        for path in found:
            try:
                path.resolve().relative_to(base)
            except ValueError:
                raise StampError(f"formal/modeled.txt: {entry} is outside the project") from None
        if not found:
            if os.path.isabs(entry) or ".." in Path(entry).parts:
                raise StampError(f"formal/modeled.txt: {entry} is outside the project")
            raise StampError(f"formal/modeled.txt: {entry} matches no file (renamed or deleted?)")
    for folder, dirs, names in os.walk(root / "formal"):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in names:
            if name not in SKIP_FILES and not name.endswith(".pyc"):
                files.add((Path(folder) / name).relative_to(root).as_posix())
    return sorted(files)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(root: Path) -> dict[str, str]:
    return {rel: digest(root / rel) for rel in covered(root)}


def identities(root: Path, rels: list[str]) -> dict[str, list[int]]:
    """Modification time, inode and size: a file rewritten with the same bytes still differs here."""
    out = {}
    for rel in rels:
        st = (root / rel).stat()
        out[rel] = [st.st_mtime_ns, st.st_ino, st.st_size]
    return out


def differences(recorded: dict[str, str], now: dict[str, str]) -> list[str]:
    out = [f"changed: {rel}" for rel in sorted(recorded) if rel in now and now[rel] != recorded[rel]]
    out += [f"added: {rel}" for rel in sorted(set(now) - set(recorded))]
    out += [f"removed: {rel}" for rel in sorted(set(recorded) - set(now))]
    return out


def load(path: Path, what: str, keys: tuple[str, ...] = ("files",)) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise StampError(f"no {what}") from None
    except (OSError, ValueError):
        raise StampError(f"{what} cannot be read") from None
    if not isinstance(data, dict) or not all(isinstance(data.get(k), dict) for k in keys):
        raise StampError(f"{what} cannot be read")
    return data


def check(root: Path) -> list[str]:
    """Differences between the stamp and the files now; empty when the provers passed on these files."""
    now = hashes(root)
    recorded = load(root / "formal" / "stamp.json", "formal/stamp.json")["files"]
    return differences(recorded, now)


def snapshot(root: Path, out: Path) -> int:
    files = hashes(root)
    out.write_text(json.dumps({"files": files, "ids": identities(root, sorted(files))}), encoding="utf-8")
    return len(files)


def write(root: Path, snap: Path) -> int:
    taken = load(snap, f"snapshot {snap}", ("files", "ids"))
    now = hashes(root)
    moved = [d.split(": ", 1)[1] for d in differences(taken["files"], now)]
    ids = identities(root, [rel for rel in sorted(now) if rel in taken["files"]])
    moved += [rel for rel, ident in ids.items() if taken["ids"].get(rel) != ident and rel not in moved]
    if moved:
        raise StampError("changed while the provers ran: " + ", ".join(sorted(moved)) + "; run formal/check.sh again")
    target = root / "formal" / "stamp.json"
    text = json.dumps({"version": 1, "files": taken["files"]}, indent=1, sort_keys=True) + "\n"
    tmp = target.with_name("stamp.json.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)
    return len(taken["files"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent, help="the project folder")
    parser.add_argument("--check", action="store_true", help="compare formal/stamp.json with the files")
    parser.add_argument("--write", action="store_true", help="write formal/stamp.json from --snapshot")
    parser.add_argument("--snapshot", type=Path, help="the snapshot file to record, or to write the stamp from")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2
    modes = [args.check, args.write, args.snapshot is not None and not args.write]
    if sum(modes) != 1 or (args.write and args.snapshot is None) or (args.check and args.snapshot is not None):
        print("stamp: give exactly one of --check, --snapshot FILE, or --write --snapshot FILE", file=sys.stderr)
        return 2
    if not args.root.is_dir():
        print(f"stamp: {args.root} is not a folder", file=sys.stderr)
        return 2
    try:
        if args.check:
            found = check(args.root)
            if found:
                print("stamp: FAILED: the provers have not passed on the models as they are:", file=sys.stderr)
                for line in found:
                    print(f"  {line}", file=sys.stderr)
                print(
                    "  Run formal/check.sh where the provers are installed; "
                    "it rewrites formal/stamp.json when they pass.",
                    file=sys.stderr,
                )
                return 1
            count = len(load(args.root / "formal" / "stamp.json", "formal/stamp.json")["files"])
            print(f"stamp ok: {count} files as proved")
        elif args.write:
            print(f"stamp written: {write(args.root, args.snapshot)} files")
        else:
            print(f"snapshot: {snapshot(args.root, args.snapshot)} files")
    except StampError as err:
        hint = "; run formal/check.sh" if str(err).startswith("no formal/stamp.json") else ""
        print(f"stamp: FAILED: {err}{hint}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
