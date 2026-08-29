"""Regenerate the Codex plugin's mirrored skills from their canonical source.

    python3 -m scripts.sync_codex_mirror           # rewrite the mirror
    python3 -m scripts.sync_codex_mirror --check   # report drift, write nothing

The Codex plugin carries a byte-identical copy of every portable research
skill, because a plugin has to be installable on its own and cannot reach
outside its own directory. `tests/test_codex_plugin.py` enforces that copy
exactly, which means the mirror can never drift silently.

It can still drift loudly, and that is the problem this solves. Without a
generator, every edit to a skill has to be made twice by hand, and the test
turns a single missed copy into a red build rather than a wrong plugin. The
copy is derived, so it should be produced rather than maintained: edit the
skill under `skills/`, run this, and the test verifies the generator ran
instead of policing whether someone remembered.

`--check` is the same comparison without the write, for CI and for anyone who
wants to know whether the mirror is current before touching it.

Two things stay out of the mirror's way. `ai-anthropology` is the Codex-only
router skill and has no source counterpart, so it is never written or removed.
Anything else in the plugin's skills directory that the source does not have
is deleted, because the test requires the inventories to match and a leftover
skill is exactly the stale copy this is meant to prevent.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCE_SKILLS = REPO / "skills"
PLUGIN = REPO / "plugins" / "ai-anthropology"
PLUGIN_SKILLS = PLUGIN / "skills"

# The Codex-specific entry point. It is authored, not mirrored, so the
# inventory test expects it to be the one directory the source does not have.
ENTRY_SKILL = "ai-anthropology"

# Copied verbatim beside the skills. The plugin registers the same server as
# the repository root, and the test asserts the two files are byte-identical,
# so the pin cannot be bumped in one place only.
MIRRORED_FILES = (".mcp.json",)


def skill_dirs(root: Path) -> dict[str, Path]:
    """Directories the tests treat as skills: those holding a SKILL.md.

    Deliberately the same rule as `tests/test_codex_plugin.py::_skill_dirs`.
    A generator that disagreed with the test about what counts as a skill
    would produce a mirror that fails the check it exists to satisfy.
    """
    if not root.is_dir():
        return {}
    return {
        path.name: path
        for path in root.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }


def tree_files(root: Path) -> dict[Path, Path]:
    return {p.relative_to(root): p for p in root.rglob("*") if p.is_file()}


def differences(source: Path, mirror: Path) -> list[str]:
    """Every way the mirror fails to match the source, as readable lines."""
    out: list[str] = []
    source_skills = skill_dirs(source)
    mirror_skills = skill_dirs(mirror)

    for name in sorted(set(source_skills) - set(mirror_skills)):
        out.append(f"missing from the plugin: skills/{name}")
    for name in sorted(set(mirror_skills) - set(source_skills) - {ENTRY_SKILL}):
        out.append(f"in the plugin but not in the source: skills/{name}")

    for name in sorted(set(source_skills) & set(mirror_skills)):
        src_files = tree_files(source_skills[name])
        dst_files = tree_files(mirror_skills[name])
        for rel in sorted(set(src_files) - set(dst_files)):
            out.append(f"missing file: skills/{name}/{rel}")
        for rel in sorted(set(dst_files) - set(src_files)):
            out.append(f"extra file: skills/{name}/{rel}")
        for rel in sorted(set(src_files) & set(dst_files)):
            # shallow=False: compare contents, not size and mtime. A same-size
            # edit is exactly the drift worth catching, and mtimes differ on
            # every checkout.
            if not filecmp.cmp(src_files[rel], dst_files[rel], shallow=False):
                out.append(f"content differs: skills/{name}/{rel}")

    for name in MIRRORED_FILES:
        src, dst = REPO / name, PLUGIN / name
        if not src.is_file():
            out.append(f"source file is missing: {name}")
        elif not dst.is_file():
            out.append(f"missing from the plugin: {name}")
        elif not filecmp.cmp(src, dst, shallow=False):
            out.append(f"content differs: {name}")
    return out


def sync(source: Path, mirror: Path) -> list[str]:
    """Make the mirror match the source. Returns what was written."""
    written: list[str] = []
    source_skills = skill_dirs(source)
    mirror_skills = skill_dirs(mirror)
    mirror.mkdir(parents=True, exist_ok=True)

    for name in sorted(set(mirror_skills) - set(source_skills) - {ENTRY_SKILL}):
        shutil.rmtree(mirror_skills[name])
        written.append(f"removed skills/{name}")

    for name, src in sorted(source_skills.items()):
        dst = mirror / name
        if dst.exists() and not differences_for_skill(src, dst):
            continue
        # Replace wholesale rather than overlaying, so a file deleted from the
        # source cannot survive in the mirror.
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        written.append(f"wrote skills/{name}")

    for name in MIRRORED_FILES:
        src, dst = REPO / name, PLUGIN / name
        if not src.is_file():
            continue
        if not dst.is_file() or not filecmp.cmp(src, dst, shallow=False):
            shutil.copy2(src, dst)
            written.append(f"wrote {name}")
    return written


def differences_for_skill(src: Path, dst: Path) -> bool:
    src_files, dst_files = tree_files(src), tree_files(dst)
    if set(src_files) != set(dst_files):
        return True
    return any(
        not filecmp.cmp(src_files[rel], dst_files[rel], shallow=False)
        for rel in src_files
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift and exit non-zero; write nothing",
    )
    args = parser.parse_args(argv)

    if not SOURCE_SKILLS.is_dir():
        print(f"no source skills at {SOURCE_SKILLS}", file=sys.stderr)
        return 2

    if args.check:
        drift = differences(SOURCE_SKILLS, PLUGIN_SKILLS)
        if not drift:
            print("Codex mirror is current.")
            return 0
        print(f"Codex mirror is out of date ({len(drift)}):", file=sys.stderr)
        for line in drift:
            print(f"  {line}", file=sys.stderr)
        print(
            "\nRun: python3 -m scripts.sync_codex_mirror",
            file=sys.stderr,
        )
        return 1

    written = sync(SOURCE_SKILLS, PLUGIN_SKILLS)
    if not written:
        print("Codex mirror already current; nothing written.")
        return 0
    for line in written:
        print(f"  {line}")
    print(f"\n{len(written)} change(s). Run the tests before committing:")
    print("  python3 -m unittest tests.test_codex_plugin")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
