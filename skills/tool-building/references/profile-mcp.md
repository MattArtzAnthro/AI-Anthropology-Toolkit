# Profile: MCP Tools and Servers

Adding a data source or an analysis stage to the toolkit's MCP server. The
interface contract makes correctness unusually checkable, which is what makes this
family worth doing early.

## What governs, and a caveat that matters

**There is no conventions document for the package.** Skills have
`skills/DESIGN.md`. The package has nothing equivalent, so the pattern below is
**observed across the ten existing collectors rather than declared anywhere**.

That distinction is not pedantry. It means a specification for this family cannot
quote a governing rule the way a skill specification can, and it means two
contributors could derive the pattern differently and both be defensible. Say so
in the specification's prior-decisions section rather than citing a document that
does not exist.

| Element | Source |
|---|---|
| Conventions | Observed in `src/ai_anthro_toolkit/datasources/`, ten collectors |
| Structural checks | `tests/package/test_consistency.py` |
| Behavioural checks | `tests/package/test_datasources_collectors.py` |

## The observed pattern

Verified across all ten collectors at the time of writing:

- **Every collector carries a module docstring.** Ten of ten.
- **Every collector is small**, 56 to 185 lines, one source per file.
- **Raw HTTP calls pass an explicit timeout.** This one is enforced by a test, and
  it applies only to `requests.get` and `requests.post`.
- **Failures raise with guidance rather than returning empty.** A scraper that
  returns nothing on a rate-limit looks like a source with no results, which is
  the wrong answer delivered silently.

## Exact commands

The package suite needs the package installed, which the repository-level suites
do not:

```
pip install -e ".[data,test]" nltk
python3 -m unittest discover -s tests/package -t . -v
```

That is what CI installs, verbatim, so it is what reproduces a CI failure locally.
`pyproject.toml` also defines a `chunking` extra, which the package job does not
install; add it only if your work touches local transcript chunking.

The repository-level suites still apply to anything you touch outside `src/`:

```
python3 -m unittest tests.test_repo tests.test_skill_routing tests.test_spec_pack -v
```

## Reading-check anchors for this family

- Conventions, such as they are: `src/ai_anthro_toolkit/datasources/` and any one
  collector as the worked example
- Structural checks: `tests/package/test_consistency.py`
- Registry the tool must appear in: `src/ai_anthro_toolkit/mcp/server.py`
- Catalog that must stay in step: `src/ai_anthro_toolkit/catalog.py`

Because there is no governing document to quote, quote a **collector** instead.
Naming the file you patterned yours on is the closest available equivalent, and it
is checkable.

## What the checks catch

`test_consistency.py` enforces four things worth knowing before you write:

- Tool families match the registry exactly, so a tool added in one place and not
  the other fails
- Every tool has a description
- The server instructions name only tools that exist
- The notebook catalog and the notebooks directory agree in both directions

## Two gaps, and they are the reason to read this before starting

**Live endpoints are not tested in CI.** `AAT_SKIP_LIVE_SCRAPERS` exists because
datacenter addresses are the blocked class and library retry loops can hang a
runner. So a new collector **passes CI while never having contacted the thing it
collects from**. Test it locally against the real endpoint and record that you
did, because no gate will ask.

**The timeout rule has a hole in exactly the wrong place.** It is enforced for
`requests.get` and `requests.post`. Five of the ten collectors reach their source
through a third-party client instead, and those are the scraper-based ones, which
are both the most likely to hang and the ones CI skips. If your collector uses a
library rather than raw HTTP, the timeout guard does not cover you and you are
responsible for the equivalent.

## What no check here can settle

- **Whether the data is what it claims to be.** A collector can return
  well-formed records that are the wrong records, and every check will pass.
- **Whether the source may be collected from at all.** Terms of service, rate
  limits as a matter of courtesy rather than capability, and whether the material
  concerns people are all judgments, and the ethics pass exists for the third.
- **Whether one more source is worth the maintenance.** Every collector is a
  dependency on someone else's endpoint continuing to behave.
- **Whether the failure messages help.** A test can confirm that an error was
  raised. Only a person can tell whether it tells a researcher what to do next.
