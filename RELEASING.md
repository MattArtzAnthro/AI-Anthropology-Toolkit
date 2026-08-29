# Releasing

```bash
python3 -m scripts.release --dry-run   # everything except the upload
python3 -m scripts.release             # the real thing
```

**Use the script.** It performs the steps below in the one order that works,
refuses to continue when a step fails, and prints "safe to push" only after
the uploaded version has been observed to resolve. Four consecutive releases
shipped pins ahead of the upload while this document existed and said not to,
including the commit that added it. A checklist you have to remember is a gate
that becomes a form.

The rest of this file explains what the script does and why, which is what you
need when a step fails or when the release is unusual enough to run by hand.

This repository has three release tracks that ship from one commit:

| Track | Version lives in | Consumers |
|---|---|---|
| Package `ai-anthropology-toolkit` | `pyproject.toml`, `src/ai_anthro_toolkit/__init__.py`, both `.mcp.json` files, `AGENTS.md`, `GEMINI.md` | PyPI, and the MCP server both plugins register |
| Claude Code plugin `ai-anthropology` | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | The marketplace clone and every installed copy |
| Codex plugin `ai-anthropology` | `plugins/ai-anthropology/.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json` | Codex plugin installs and their bundled skills/MCP registration |

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
- [ ] `tests/test_codex_plugin.py` confirms every mirrored skill and the MCP registration are byte-identical to their canonical source, and that the tool reference names exactly the registered tools.
- [ ] If any skill under `skills/` changed, regenerate the Codex mirror rather than editing the copy: `python3 -m scripts.sync_codex_mirror`. `--check` reports drift without writing, and `tests/test_sync_codex_mirror.py` fails if the committed mirror is stale.

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
- [ ] Configure this repository as a local Codex marketplace if needed: `codex plugin marketplace add .`
- [ ] Install or refresh it: `codex plugin add ai-anthropology@personal`
- [ ] Start a new Codex task; plugin skills and tools are discovered at task startup.

## Live data-source check

CI skips every test that calls a third-party service (`AAT_SKIP_LIVE_SCRAPERS`),
because those fail for reasons unrelated to the code and a red build nobody
trusts is worse than no build. That trade moves the check here rather than
removing it: nothing else verifies that the registrars and scrapers still
answer the way the toolkit expects.

Run the live suites once, without the flag, before uploading:

```bash
python3 -m unittest tests.package.test_datasources_citation \
                    tests.package.test_datasources_collectors \
                    tests.package.test_datasources_scrapers \
                    tests.package.test_datasources_youtube
```

- [ ] They pass, or each failure is understood as upstream rather than ours.
- [ ] A metered refusal (OpenAlex 429, a rate-limited scraper) is upstream and
      does not block the release. A changed response *shape* does: that is the
      toolkit reading a source wrong, and it will reach users.

Re-running a transient failure is legitimate here. Suppressing a persistent one
is not — if a source has genuinely changed, the release is what carries the fix.

## Codex live-host smoke test

Unit tests prove the bundle is internally consistent. They cannot prove that
Codex Desktop can launch `uvx`, complete MCP discovery, or surface the MCP App.
Run this check in the actual desktop host after installing the plugin:

- [ ] On the first new task after install, the server initializes and `tools/list` exposes exactly 34 tools (not only the resource).
- [ ] `resources/list` includes `ui://ai-anthropology/network-view`.
- [ ] Call `toolkit_info` and one small non-network tool successfully.
- [ ] Start a second new task and repeat tool discovery. This catches startup/cache behavior that an in-process retry hides.
- [ ] If the resource appears but tools do not, restart Codex and retest before changing the server; record whether failure was first-run-only.
- [ ] Confirm the desktop host can resolve the exact bundled `uvx --from "ai-anthropology-toolkit[data]==X"` command. Success in an interactive shell is not evidence that the desktop process has the same PATH or environment.

These are manual release checks, not silently skipped unit tests. A host outage
or permission prompt should be reported as such rather than converted into a
passing result.

## Same-version content drift

A commit that changes only package code, docs, or tests leaves the plugin
version unmoved. The installed copy then keeps the previous commit's content
under an unchanged version number, and nothing reports a mismatch, because the
versions agree.

`claude plugin marketplace update` does not fix this. It needs uninstall and
reinstall. The cheaper habit is to bump the plugin version whenever plugin
content changes at all, so the mismatch can never form.

## Standing constraints

**`mcp` must stay bounded on both sides: `mcp>=2.1,<3`.** The server is built
on MCP Python SDK 2.x (`MCPServer`, which SDK 1.x does not have; 2.0.0 removed
`mcp.server.fastmcp`, which the server imported before 3.7.0). A requirement
open at the top resolves to whatever the next major release removes or
renames. `tests/package/test_consistency.py::TestDependencyBounds` asserts
the bound and that the server is an `MCPServer`. The test suite alone cannot
catch a regression here, because it runs against the already-installed
`mcp`; the clean-venv step is what catches it.

**`TestDataSourcesLive` is not a release gate.** Scholarly APIs return 503 and
429 under repeated full-suite runs while passing when hit fresh. Read its
status, do not block on it.
