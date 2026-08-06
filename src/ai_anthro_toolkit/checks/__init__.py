"""Standing checks over the durable artifacts this toolkit produces.

A researcher who needs these does not know that is the name of the thing
that would have saved them, so they are written on their behalf rather than
waiting to be asked. What they are called, and why anyone writes them, is
worth saying once at the moment one first fires, and not before.

Two things govern what a check may claim. It declares whether it could ever
teach anything: a ``mirror`` check restates what was already specified and
is epistemically empty, while a ``surprise-capable`` check can surface a
commitment the researcher never stated. And no check reports an all-clear on
a question it cannot settle; the verdict is confirmed, refuted, or cannot
tell.

A check can only occasion a teachback. The moment itself is the researcher
deciding whether the commitment a check names is one they actually hold, and
that decision is never the machine's.
"""

from .registry import (  # noqa: F401
    AmbiguousArtifact,
    CANNOT_TELL,
    CLASS_CODEBOOK,
    CLASS_CODED,
    Check,
    CheckReport,
    CheckResult,
    FIRED,
    MARK_MIRROR,
    MARK_STANCE,
    MARK_SURPRISE,
    NOT_APPLICABLE,
    OK,
    PROVENANCE_KEY,
    by_name,
    codebook_checksum,
    detect_artifact_class,
    for_class,
    provenance_stanza,
    records_of,
    run_checks,
    stanza_of,
)

# Importing these registers their checks. The registry is assembled at import
# time so that a check can never be present in the codebase but absent from
# the completeness tests.
from . import codebook_checks  # noqa: F401,E402
from . import coded_data_checks  # noqa: F401,E402


def __getattr__(name):
    # REGISTRY is rebound by register() as each check module imports, so it
    # is read from the module on every access rather than served as the
    # empty tuple captured here at import time. Everything else falls
    # through to registry so a name added there does not have to be added
    # in two places to be reachable.
    from . import registry as _registry
    try:
        return getattr(_registry, name)
    except AttributeError:
        raise AttributeError(name) from None
