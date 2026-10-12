"""Offline smoke run of the Colab notebooks.

    python3.12 -m unittest tests.package.test_notebooks_smoke -v

Every notebook builds an ipywidgets interface and does its network or model
work only when a button is clicked. Running each notebook's code cells top to
bottom therefore exercises everything a researcher hits before the first
click: imports, configuration, function and class definitions, and the
construction of the interface. A NameError, a renamed import, or a top-level
call that breaks on load fails here.

What makes it safe to run anywhere: shell and magic lines (`!pip install`,
`%matplotlib`) are dropped, `google.colab` is replaced with an inert stand-in,
and sockets are closed for the duration, so a cell that reached for the
network on load would fail the test rather than call out. A notebook whose
third-party dependencies are not installed here is skipped with the missing
module named, and a floor on how many actually ran stops a broken environment
from passing by skipping everything.
"""

import ast
import contextlib
import importlib.util
import io
import json
import socket
import sys
import types
import unittest
import warnings
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
NOTEBOOKS = sorted((REPO / "notebooks").glob("*.ipynb"))

# The smoke run needs these to build the interface at all; without them it
# cannot tell a broken notebook from a missing widget library.
HARNESS_MODULES = ("ipywidgets", "IPython", "openpyxl")

# With the test extra installed, at least this many notebooks must execute.
MIN_EXECUTED = 12

# Notebooks whose run-all executes a live query rather than waiting for a
# click: the smoke run stops before that cell. Each entry names the cell.
LIVE_FROM_CELL = {
    "PubMed_Literature_Harvester.ipynb": 8,  # "EXECUTE PIPELINE" searches PubMed
}


def _code_cells(path):
    nb = json.loads(path.read_text(encoding="utf-8"))
    for index, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        lines = [line for line in source.splitlines()
                 if not line.lstrip().startswith(("!", "%"))]
        yield index, "\n".join(lines)


def _imported_modules(path):
    """Top-level module names a notebook imports, from its syntax tree."""
    names = set()
    for _, source in _code_cells(path):
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                if node.module == "google":
                    # `from google import genai` needs google.genai, which the
                    # Colab stand-in does not provide.
                    names.update(f"google.{alias.name}" for alias in node.names)
                else:
                    names.add(node.module.split(".")[0])
    return names


def _installed(name):
    try:
        return name in sys.modules or importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def _missing(modules):
    stand_ins = {"google", "google.colab"}
    return sorted(m for m in modules - stand_ins if not _installed(m))


def _colab_stub():
    google = types.ModuleType("google")
    colab = types.ModuleType("google.colab")
    colab.files = mock.MagicMock(name="google.colab.files")
    colab.drive = mock.MagicMock(name="google.colab.drive")
    colab.userdata = mock.MagicMock(name="google.colab.userdata")
    colab.output = mock.MagicMock(name="google.colab.output")
    google.colab = colab
    return {"google": google, "google.colab": colab,
            "google.colab.files": colab.files, "google.colab.drive": colab.drive,
            "google.colab.userdata": colab.userdata, "google.colab.output": colab.output}


def _no_network(*args, **kwargs):
    raise OSError("network access is blocked during the notebook smoke run")


@contextlib.contextmanager
def _offline():
    with mock.patch.object(socket.socket, "connect", _no_network), \
            mock.patch.object(socket, "create_connection", _no_network), \
            mock.patch.object(socket, "getaddrinfo", _no_network):
        yield


@contextlib.contextmanager
def _colab_installed():
    # Only the stand-in keys are added and removed. Restoring all of
    # sys.modules (as mock.patch.dict does) would unload numpy and pandas
    # after the first notebook, and numpy cannot be imported twice.
    stub = _colab_stub()
    saved = {name: sys.modules[name] for name in stub if name in sys.modules}
    sys.modules.update(stub)
    try:
        yield
    finally:
        for name in stub:
            sys.modules.pop(name, None)
        sys.modules.update(saved)


def execute_notebook(path, stop_before=None, namespace=None):
    """Run the code cells of `path` in one namespace; return the cell count.

    Cells from index `stop_before` on are not run.
    """
    if namespace is None:
        namespace = {}
    namespace.setdefault("__name__", "__notebook__")
    ran = 0
    with _colab_installed(), _offline(), \
            contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for index, source in _code_cells(path):
            if stop_before is not None and index >= stop_before:
                break
            try:
                exec(compile(source, f"{path.name}[cell {index}]", "exec"), namespace)
            except Exception as error:
                raise AssertionError(
                    f"{path.name} cell {index} failed on load: "
                    f"{type(error).__name__}: {error}") from error
            ran += 1
    return ran


class TestNotebookSmoke(unittest.TestCase):
    def setUp(self):
        missing = _missing(set(HARNESS_MODULES))
        if missing:
            self.skipTest(f"smoke harness needs {', '.join(missing)} "
                          "(installed by the test extra)")

    def test_every_runnable_notebook_loads_offline(self):
        self.assertEqual(len(NOTEBOOKS), 23)
        executed, skipped = [], {}
        for path in NOTEBOOKS:
            missing = _missing(_imported_modules(path))
            if missing:
                skipped[path.name] = missing
                continue
            with self.subTest(notebook=path.name):
                ran = execute_notebook(path, stop_before=LIVE_FROM_CELL.get(path.name))
                self.assertGreater(ran, 0)
                executed.append(path.name)
        self.assertGreaterEqual(
            len(executed), MIN_EXECUTED,
            f"only {len(executed)} notebooks ran; skipped for missing modules: {skipped}")

    def test_live_cells_listed_here_still_exist(self):
        for name, index in LIVE_FROM_CELL.items():
            nb = json.loads((REPO / "notebooks" / name).read_text(encoding="utf-8"))
            self.assertEqual(nb["cells"][index]["cell_type"], "code", name)

    def test_pubmed_request_failure_names_the_cause(self):
        # When every attempt failed, the retry helper used to reach
        # `r.raise_for_status()` with `r` never assigned (UnboundLocalError).
        path = REPO / "notebooks" / "PubMed_Literature_Harvester.ipynb"
        if _missing(_imported_modules(path)):
            self.skipTest("PubMed notebook dependencies not installed")
        namespace = {}
        execute_notebook(path, stop_before=LIVE_FROM_CELL[path.name], namespace=namespace)
        with mock.patch.object(namespace["time"], "sleep"), _offline():
            with self.assertRaises(RuntimeError) as ctx:
                namespace["ncbi_get"]("esearch.fcgi", {"db": "pubmed"}, max_retries=2)
        self.assertIn("Could not reach NCBI", str(ctx.exception))

    def test_a_notebook_that_breaks_on_load_is_caught(self):
        broken = {"cells": [
            {"cell_type": "code", "source": ["!pip install nothing\n", "import json\n"]},
            {"cell_type": "code", "source": ["undefined_helper()\n"]},
        ], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
        self._roundtrip_fails(broken, "NameError")

    def test_a_notebook_that_calls_out_on_load_is_caught(self):
        reaching = {"cells": [
            {"cell_type": "code",
             "source": ["import socket\n",
                        "socket.create_connection(('example.org', 80))\n"]},
        ], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
        self._roundtrip_fails(reaching, "network access is blocked")

    def _roundtrip_fails(self, notebook, expected):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Broken.ipynb"
            path.write_text(json.dumps(notebook), encoding="utf-8")
            with self.assertRaises(AssertionError) as ctx:
                execute_notebook(path)
        self.assertIn(expected, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
