"""Command line for the standing checks.

The command exists so the checks are *standing* rather than one-time: a
researcher can re-run them on an artifact months later, from a directory
they were handed, without the pipeline that produced it.

It refuses to guess. A misdetected artifact returns findings about the wrong
questions, and a quiet run over the wrong questions reads exactly like a
clean bill of health.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from . import generated, registry
from .registry import (AmbiguousArtifact, CANNOT_TELL, CLASS_CODEBOOK,
                       CLASS_CODED, FIRED, MARK_MIRROR, NOT_APPLICABLE, OK,
                       PROVENANCE_KEY, PROVENANCE_SIDECAR)

_TEACHING = (
    "\nChecks like these are called linters. They are worth having because "
    "the failures they catch are the ones you cannot see by reading."
)

_READABLE = {".json", ".csv"}

# A project's own checks, written by tool-building from the researcher's
# Stage 4 answers. Data, never code: it is validated against a fixed
# vocabulary and nothing in it is executed.
PROJECT_CHECKS = "instrument-checks.json"


def load_project_checks(path: Path):
    """Register a project's own checks, if it has any beside the artifact."""
    document = path.parent / PROJECT_CHECKS
    if not document.exists():
        return None
    try:
        payload = json.loads(document.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise LoadError(f"{document} could not be read: {error}")
    try:
        built = generated.register_document(payload)
    except ValueError as error:
        raise LoadError(f"{document}: {error}")
    return payload, built


class LoadError(Exception):
    pass


def load_artifact(path: Path) -> object:
    """Load an artifact, folding in its provenance sidecar where one exists."""
    if path.is_dir():
        for name in ("result.json", "codebook.json", "entries.json"):
            candidate = path / name
            if candidate.exists():
                return load_artifact(candidate)
        raise LoadError(
            f"{path} holds no artifact I know how to read. I looked for "
            f"result.json, codebook.json, and entries.json.")

    if not path.exists():
        raise LoadError(f"{path} does not exist.")

    suffix = path.suffix.lower()
    if suffix not in _READABLE:
        raise LoadError(
            f"I cannot read {suffix or 'that'} files yet, only "
            f"{' and '.join(sorted(_READABLE))}. Export the artifact to one "
            f"of those and point me at it; I would rather say this than "
            f"read it badly.")

    if suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            records = list(csv.DictReader(handle))
    else:
        records = json.loads(path.read_text(encoding="utf-8"))

    stanza = _sidecar_for(path)
    if stanza is not None:
        return {PROVENANCE_KEY: stanza, "records": records}
    return records


# The names a producer writes, used only when a stanza predates the
# artifact_file field and cannot say for itself what it describes.
_PRODUCED_NAMES = {"result.json", "codebook.json", "entries.json"}


def _sidecar_for(path: Path) -> dict | None:
    """The provenance stanza describing *this* artifact, or None.

    A sidecar sits in a directory that may hold several artifacts. Attaching
    it to whichever file was opened would have the checks report on one
    artifact using another one's codebook, and report it as settled.
    """
    sidecar = path.parent / PROVENANCE_SIDECAR
    if not sidecar.exists():
        return None
    try:
        stanza = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(stanza, dict):
        return None

    named = str(stanza.get("artifact_file") or "")
    if named:
        return stanza if named == path.name else None
    # No claim about what it describes: attach it only to the files a
    # producer is known to write, and never to a neighbour.
    return stanza if path.name in _PRODUCED_NAMES else None


def _embedder():
    """The distinctness comparison, or None when its model is not installed.

    None is reported as "cannot tell" rather than absorbed silently, because
    an unrun check and a check that found nothing are different findings.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return lambda texts: model.encode(list(texts))


_SYMBOL = {FIRED: "!", OK: "ok", CANNOT_TELL: "?", NOT_APPLICABLE: "-"}


def render(report) -> str:
    lines = [f"{report.artifact_class}: {len(report.results)} checks"]
    for result in report.results:
        lines.append(f"  [{_SYMBOL.get(result.verdict, ' ')}] {result.message}")

    if report.mirror_only:
        lines.append(
            "\nEverything that ran here only confirms what was already "
            "specified. Nothing ran that could have told you something you "
            "had not already assumed, so read this as a formatting pass "
            "rather than as a second opinion.")
    if report.undetermined:
        lines.append(
            f"\n{len(report.undetermined)} check(s) could not be run. Those "
            f"are unrun, not passed.")
    if report.fired:
        lines.append(_TEACHING)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-anthro-check",
        description="Run the standing checks over a codebook or a coded "
                    "dataset, and say what they could not settle.")
    parser.add_argument("path", type=Path,
                        help="artifact file, or a job directory containing one")
    parser.add_argument("--kind", choices=[CLASS_CODEBOOK, CLASS_CODED],
                        default=None,
                        help="name the artifact class rather than letting me "
                             "detect it; required when detection is ambiguous")
    parser.add_argument("--codebook", type=Path, default=None,
                        help="the codebook a coded dataset should be checked "
                             "against, when it carries no provenance")
    exclusivity = parser.add_mutually_exclusive_group()
    exclusivity.add_argument(
        "--distinct-codes", dest="expect_distinct", action="store_true",
        default=None,
        help="you hold codes to be mutually exclusive, so near-duplicates "
             "are a finding")
    exclusivity.add_argument(
        "--overlapping-codes", dest="expect_distinct", action="store_false",
        help="you hold overlapping codes deliberately, so closeness between "
             "two of them is not a finding")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    try:
        artifact = load_artifact(args.path)
        codebook = load_artifact(args.codebook) if args.codebook else None
        project = load_project_checks(args.path)
    except LoadError as error:
        print(error, file=sys.stderr)
        return 2

    if project and not args.kind:
        payload, built = project
        args.kind = payload.get("artifact") or args.kind
        if built.unenforceable:
            print(f"{len(built.unenforceable)} commitment(s) you settled "
                  f"cannot be checked from the data alone:")
            for item in built.unenforceable:
                print(f"  [-] {item.commitment}: {item.why}")
            print()

    try:
        report = registry.run_checks(
            artifact,
            artifact_class=args.kind,
            codebook=codebook,
            expect_distinct_codes=args.expect_distinct,
            embedder=_embedder(),
        )
    except AmbiguousArtifact as error:
        print(f"{error} Re-run with --kind "
              f"{' or --kind '.join(error.candidates)}.", file=sys.stderr)
        return 2
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
