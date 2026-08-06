# Releasing

This repository has two release tracks that ship from one commit:

| Track | Version lives in | Consumers |
|---|---|---|
| Package `ai-anthropology-toolkit` | `pyproject.toml`, `src/ai_anthro_toolkit/__init__.py`, `.mcp.json`, `AGENTS.md`, `GEMINI.md` | PyPI, and the MCP server the plugin registers |
| Claude Code plugin `ai-anthropology` | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | The marketplace clone and every installed copy |

They are versioned independently. Bump whichever changed, and both when both did.

## The order, and why it is not negotiable

**Upload the package to PyPI before pushing the commit.**

The package version is pinned inside files that ship in the same commit as the
code: `.mcp.json` registers the MCP server through `uvx --from
"ai-anthropology-toolkit[data]==X"`, and `AGENTS.md` and `GEMINI.md` repeat
that pin. Pushing first publishes a pin to a version that does not exist yet,
and every fresh install fails until the upload lands.

Because the package must be built and uploaded from the version-bumped tree,
the sequence is: bump, verify, upload, then push.

**Do not run `claude plugin update` while a pinned package version is
unpublished.** The drift checker will correctly report the install as behind.
The report is right and acting on it is still wrong, because it installs a
plugin whose MCP server cannot resolve its own dependency.

## Before building

- [ ] `python3 -m unittest discover -s tests -t .` — the full suite, green.
- [ ] A CHANGELOG entry exists for every version being bumped. No bump without one.
- [ ] All package-version references agree. `tests/test_repo.py::test_package_version_consistency` checks this; run it rather than trusting a grep.
- [ ] Any new MCP tool is registered in `toolkit_info()["tool_families"]` and in the tool-name sets in `tests/package/`, and the stated tool count in `CLAUDE.md` matches.

## Verifying the build

**A green test suite is not a release check.** The suite runs against whatever
is already installed in the working environment, so it cannot see what a fresh
dependency resolve would choose. It has stayed green through a release that
was broken for every new installer.

```bash
python3 -m build --outdir dist
python3 -m venv /tmp/relcheck && /tmp/relcheck/bin/pip install dist/*.whl
/tmp/relcheck/bin/python -c "import ai_anthro_toolkit as t; \
  from ai_anthro_toolkit.mcp.server import main; print(t.__version__)"
ls /tmp/relcheck/bin | grep ai-anthro    # every console script present
```

- [ ] Clean-venv install succeeds and the MCP server imports.
- [ ] Every console script in `[project.scripts]` exists in the venv and runs.
- [ ] `python3 -m twine check dist/*` passes. A PyPI version number cannot be reclaimed once used, so metadata errors are caught here or not at all.

## Uploading

```bash
python3 -m twine upload dist/*
```

## Verifying the upload

**Neither PyPI read path proves a fresh upload landed.** Both are CDN-cached
and they lag by different amounts. The per-version JSON returns 404 for
minutes after a successful upload, and `pip index versions` has continued
naming the previous release as latest well after the new one was accepted.
Treat a negative result from either as "not yet visible," never as "the upload
failed," and never re-upload on that basis.

The check that settles it is a real resolve **against the extras-qualified
spec the plugin actually invokes**:

```bash
uvx --refresh --from "ai-anthropology-toolkit[data]==X" \
  python -c "from ai_anthro_toolkit.mcp.server import main; print('ok')"
```

Verify the extras-qualified form specifically. A bare `==X` resolves earlier
than `[data]==X` does, so checking the simplified spec produces a false
all-clear on the exact thing that is still broken.

- [ ] The extras-qualified spec resolves and the MCP server imports from it.

## Pushing, then syncing

- [ ] Push the commit.
- [ ] `claude plugin marketplace update ai-anthropology`
- [ ] `claude plugin update ai-anthropology@ai-anthropology`
- [ ] Restart for the plugin change to apply.
- [ ] Run the drift check. It should be silent.

## Same-version content drift

A commit that changes only package code, docs, or tests leaves the plugin
version unmoved. The installed copy then keeps the previous commit's content
under an unchanged version number, and nothing reports a mismatch, because the
versions agree.

`claude plugin marketplace update` does not fix this. It needs uninstall and
reinstall. The cheaper habit is to bump the plugin version whenever plugin
content changes at all, so the mismatch can never form.

## Standing constraints

**`mcp` must stay bounded: `mcp>=1.2,<2`.** Version 2.0.0 removed
`mcp.server.fastmcp`, which `src/ai_anthro_toolkit/mcp/server.py` imports, so
an unbounded requirement resolves to a version where the server dies at
import. `tests/package/test_consistency.py::TestDependencyBounds` asserts the
bound and the import. The test suite alone cannot catch a regression here,
because it runs against the already-installed `mcp`; the clean-venv step is
what catches it.

**`TestDataSourcesLive` is not a release gate.** Scholarly APIs return 503 and
429 under repeated full-suite runs while passing when hit fresh. Read its
status, do not block on it.
