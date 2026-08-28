"""In-chat network viewer, shared with Gephi AI.

`template.html` and the vendored graphology/sigma.js builds are copied
verbatim from gephi-ai (`mcp-server/gephi_mcp_viewer/`), which is the
canonical source; re-copy to update. `build_app_html()` re-points the page at
this package's own tools at build time, so the file itself stays identical.
`analyze_graph()` is the same visual-QA reader Gephi AI uses.
"""

from __future__ import annotations

import math
import re
import statistics
from importlib import resources

_PKG = "ai_anthro_toolkit.network.viewer"

# Substitutions that turn the Gephi page into this package's page. Tool names
# first; then the product words a person reads.
_REPOINT = (
    ('name: "gephi_view_graph"', 'name: "view_network"'),
    ("The person is viewing the interactive Gephi map in chat.", "The person is viewing the interactive code network in chat."),
    ("In the current Gephi graph, tell me about the node", "In the current code network, tell me about the node"),
    ("in the Gephi map. Their question:", "in the code network. Their question:"),
    ("Refreshing from Gephi…", "Refreshing…"),
    ("Re-fetch the graph from Gephi", "Redraw the network"),
    ("<title>Gephi network view</title>", "<title>Code network view</title>"),
)


def build_app_html() -> str:
    """The static MCP App page (ui://ai-anthropology/network-view)."""
    pkg = resources.files(_PKG)
    html = (pkg / "template.html").read_text(encoding="utf-8")
    html = (html
            .replace("__GRAPHOLOGY_JS__", (pkg / "assets" / "graphology.umd.min.js").read_text(encoding="utf-8"))
            .replace("__SIGMA_JS__", (pkg / "assets" / "sigma.min.js").read_text(encoding="utf-8")))
    for a, b in _REPOINT:
        if a not in html:
            raise RuntimeError(f"viewer template drifted from gephi-ai: {a!r} not found; re-copy and revise _REPOINT")
        html = html.replace(a, b)
    # No desktop to show the node in: drop the button and its handler.
    html = html.replace('<button id="btn-gephi">Show in Gephi</button>', "")
    html = re.sub(r'\n\s*\$\("btn-gephi"\)\.onclick = [^\n]*\n', "\n", html)
    if "gephi_" in html:
        raise RuntimeError("viewer template still references a Gephi tool after re-pointing")
    return _brand(html)


# ── Matt Artz brand: monochrome chrome, brand typefaces, a credit that links back.
# Data colors (node communities) are left alone: they encode the analysis and
# must stay legible and colorblind-safe. Fonts fall back to system faces
# because the sandboxed frame cannot reach Google Fonts.
BRAND_URL = "https://www.mattartz.me"
BRAND_CREDIT = "AI Anthropology Toolkit by Matt Artz"

_BRAND_CSS = """
<style id="brand">
  :root {
    --brand-ink: #1A1A1A; --brand-charcoal: #333333; --brand-graphite: #555555;
    --brand-slate: #767676; --brand-ash: #B0B0B0; --brand-silver: #E0E0E0;
    --brand-pearl: #F3F3F3; --brand-snow: #FAFAFA; --brand-white: #FFFFFF; --brand-black: #0D0D0D;
    --font-sans: "Inter", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
    --font-display: "Cormorant Garamond", Georgia, "Times New Roman", serif;
    --color-background-primary: light-dark(var(--brand-white), var(--brand-ink));
    --color-background-secondary: light-dark(var(--brand-snow), var(--brand-charcoal));
    --color-text-primary: light-dark(var(--brand-charcoal), var(--brand-pearl));
    --color-text-secondary: light-dark(var(--brand-graphite), var(--brand-ash));
    --color-border-primary: light-dark(var(--brand-silver), var(--brand-graphite));
    --color-background-info: light-dark(var(--brand-pearl), var(--brand-charcoal));
    --color-text-info: light-dark(var(--brand-ink), var(--brand-white));
    --border-radius-md: 2px;
  }
  button { border-radius: 2px; background: transparent; border: 1px solid var(--brand-charcoal); color: var(--color-text-primary); font-weight: 500; }
  button:hover { border-color: var(--brand-ink); filter: none; }
  button.active { background: light-dark(var(--brand-ink), var(--brand-pearl)); color: light-dark(var(--brand-white), var(--brand-ink)); border-color: light-dark(var(--brand-ink), var(--brand-pearl)); }
  button.active:hover { background: light-dark(var(--brand-charcoal), var(--brand-white)); }
  .card { border-radius: 2px; box-shadow: none; }
  #legend h4 { font-family: var(--font-sans); font-size: 11px; font-weight: 500; letter-spacing: 0.25em; text-transform: uppercase; }
  #panel h3 { font-family: var(--font-display); font-weight: 400; font-size: 18px; }
  .caption { font-family: var(--font-display); font-weight: 600; letter-spacing: 0.08em; }
  #credit { position: absolute; bottom: 8px; left: 50%; transform: translateX(-50%); z-index: 30; padding: 3px 10px;
            font-family: var(--font-sans); font-size: 11px; font-weight: 500; letter-spacing: 0.2em; text-transform: uppercase;
            color: var(--color-text-secondary); background: color-mix(in srgb, var(--color-background-primary) 90%, transparent);
            border: 1px solid var(--color-border-primary); border-radius: 2px; white-space: nowrap; }
  #credit a { color: inherit; text-decoration: none; border-bottom: 1px solid currentColor; cursor: pointer; }
  #credit a:hover { color: var(--color-text-primary); }
  body.compact #credit { display: none; }
</style>
"""

_BRAND_HTML = (
    '<div id="credit"><a id="credit-link" href="' + BRAND_URL + '" target="_blank" rel="noopener">'
    + BRAND_CREDIT + '</a></div>\n'
)

_BRAND_JS = """
<script>
  // The credit link: hosts that can open links do so through ui/open-link;
  // otherwise the anchor behaves as an ordinary link.
  document.getElementById("credit-link").addEventListener("click", (ev) => {
    if (hostCaps && hostCaps.openLinks) {
      ev.preventDefault();
      request("ui/open-link", { url: "%s" });
    }
  });
</script>
""" % BRAND_URL


def _brand(html: str) -> str:
    for needle in ("</style>\n</head>", '<div id="meta" class="card"></div>', "</body>"):
        if needle not in html:
            raise RuntimeError(f"viewer template drifted from gephi-ai: {needle!r} not found; revise _brand()")
    html = html.replace("</style>\n</head>", "</style>\n" + _BRAND_CSS + "</head>", 1)
    html = html.replace('<div id="meta" class="card"></div>', '<div id="meta" class="card"></div>\n' + _BRAND_HTML, 1)
    html = html.replace("</body>", _BRAND_JS + "</body>", 1)
    return html


def _norm_col(name) -> str:
    """Normalize a column name for id-or-title matching (case/underscore/space)."""
    return str(name).strip().lower().replace("_", " ").replace("-", " ")


def resolve_column_key(graph: dict, name):
    """Map a caller-supplied column name (id, title, or a normalized variant) to
    the key actually used in node["attributes"]. Falls back to the raw name so a
    genuinely absent column still surfaces as 'not found' downstream."""
    if name is None:
        return None
    ak = graph.get("attr_key") or {}
    return ak.get(name) or ak.get(_norm_col(name)) or name



def _luminance(color: str) -> float:
    """Approximate relative luminance (0-1) of 'rgb(r,g,b)' or '#rrggbb' strings."""
    try:
        if color.startswith("rgb"):
            r, g, b = (int(v) for v in color[color.index("(") + 1:color.index(")")].split(","))
        elif color.startswith("#") and len(color) >= 7:
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        else:
            return 0.5
    except ValueError:
        return 0.5
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


def analyze_graph(graph: dict, partition_column: str | None = None) -> dict:
    """Visual-design diagnostics over a parsed graph (see parse_gexf).

    Checks the things that make renders unreadable: invisible node sizes,
    near-white colors on white exports, gradient-instead-of-categorical color
    use, layout extent vs export aspect — and, when partition_column is given,
    whether that grouping is topologically real (within-group edge share vs
    the random baseline) or would mislead if used for coloring.
    """
    nodes, edges = graph["nodes"], graph["edges"]
    warnings = []

    sizes = sorted(n["size"] for n in nodes) or [0.0]
    size_info = {"min": sizes[0], "median": sizes[len(sizes) // 2], "max": sizes[-1],
                 "flat": sizes[0] == sizes[-1]}
    if size_info["min"] < 8:
        warnings.append(
            f"smallest node size is {size_info['min']:g}; sizes under 8 render as "
            "invisible specks — re-run gephi_size_by_ranking with min_size >= 10")
    if size_info["flat"] and len(nodes) > 1:
        warnings.append("all nodes are the same size; size by degree (or another "
                        "ranking) to create visual hierarchy")

    colors = {n["color"] for n in nodes}
    near_white = [c for c in colors if _luminance(c) > 0.85]
    color_info = {"distinct": len(colors), "near_white": len(near_white)}
    if near_white:
        warnings.append(
            f"{len(near_white)} node color(s) are near-white and will be invisible "
            "on white exports — use the validated palette (see gephi_color_by_partition)")
    if len(colors) > 12:
        warnings.append(
            f"{len(colors)} distinct node colors — this looks like a continuous "
            "gradient; if color should show categories, use a categorical palette "
            "(and never double-encode the variable already shown by size)")
    if size_info["flat"] and len(colors) == 1 and len(nodes) > 1:
        # Uniform size and a single color is what a graph looks like straight
        # after loading: nothing has been laid out or styled yet. Exporting it
        # gives the block of overlapping default nodes, not a map.
        warnings.append(
            "looks untouched: every node is the same size and color, so this "
            "graph has been loaded but not laid out or styled — run a layout, "
            "size by degree, and color by community (or /beautify) before exporting")

    finite = [n for n in nodes
              if math.isfinite(n["x"]) and math.isfinite(n["y"])]
    if len(finite) < len(nodes):
        warnings.append(
            f"{len(nodes) - len(finite)} node(s) have non-finite positions — the "
            "layout exploded numerically; reset with Random Layout (1 iteration) "
            "and rerun the force layout")
    xs = [n["x"] for n in finite] or [0.0]
    ys = [n["y"] for n in finite] or [0.0]
    w, h = max(xs) - min(xs), max(ys) - min(ys)

    # Robust extent: hub-and-spoke graphs push a few nodes far outside the
    # cloud, blowing up the bounding box (and with it, export framing). Frame
    # on the main cloud instead: nodes beyond 5x the 90th-percentile radius
    # from the median center are outliers and excluded from suggested_export.
    outlier_keys: list[str] = []
    core = finite
    if len(finite) >= 20:
        cx = statistics.median(xs)
        cy = statistics.median(ys)
        radii = sorted(math.dist((n["x"], n["y"]), (cx, cy)) for n in finite)
        p90 = radii[int(0.9 * (len(radii) - 1))]
        if p90 > 0:
            threshold = 5 * p90
            outlier_keys = [n["key"] for n in finite
                            if math.dist((n["x"], n["y"]), (cx, cy)) > threshold]
            if outlier_keys:
                core = [n for n in finite if n["key"] not in set(outlier_keys)]
    rxs = [n["x"] for n in core] or [0.0]
    rys = [n["y"] for n in core] or [0.0]
    rw, rh = max(rxs) - min(rxs), max(rys) - min(rys)
    aspect = (rw / rh) if rh else 1.0
    long_side = 2000
    if aspect >= 1:
        sug = {"width": long_side, "height": max(800, int(long_side / max(aspect, 0.1) / 10) * 10)}
    else:
        sug = {"width": max(800, int(long_side * aspect / 10) * 10), "height": long_side}
    extent = {"width": round(w, 1), "height": round(h, 1),
              "aspect": round((w / h) if h else 1.0, 2),
              "outliers": {"count": len(outlier_keys),
                           "nodes": sorted(outlier_keys)[:5]},
              "suggested_export": sug}
    if outlier_keys:
        extent["robust"] = {"width": round(rw, 1), "height": round(rh, 1),
                            "aspect": round(aspect, 2)}
        warnings.append(
            f"{len(outlier_keys)} node(s) sit far outside the main cloud (e.g. "
            f"'{sorted(outlier_keys)[0]}') — suggested_export frames the main "
            "cloud, not the full bounding box; to pull them in, raise gravity "
            "temporarily or check whether those nodes belong in the graph")
    # Node presence: when the biggest node is under ~1% of the extent's long
    # side, exports show specks in whitespace (found live: LinLog with a high
    # scalingRatio exploded a 500-node layout to 17k units against size-60 nodes).
    # Judged on the robust extent so a single runaway node doesn't trip it.
    long_side = max(rw, rh, 1.0)
    if len(nodes) > 1 and sizes[-1] / long_side < 0.01:
        warnings.append(
            f"layout is over-spread: largest node ({sizes[-1]:g}) is under 1% of the "
            f"layout extent ({long_side:g}) — nodes will render as specks; lower "
            "scalingRatio and rerun the layout, or raise node sizes")

    result = {
        "nodes": len(nodes), "edges": len(edges),
        "directed": graph.get("directed", False),
        "sizes": size_info, "colors": color_info, "extent": extent,
        "warnings": warnings,
    }

    if partition_column:
        partition_column = resolve_column_key(graph, partition_column)
        group = {n["key"]: n["attributes"].get(partition_column) for n in nodes}
        counted = [g for g in group.values() if g is not None]
        shares = {}
        for g in counted:
            shares[g] = shares.get(g, 0) + 1
        n_total = len(counted) or 1
        baseline = sum((c / n_total) ** 2 for c in shares.values())
        within = sum(1 for e in edges
                     if group.get(e["source"]) is not None
                     and group.get(e["source"]) == group.get(e["target"]))
        fraction = within / len(edges) if edges else 0.0
        ratio = fraction / baseline if baseline else 0.0
        if fraction >= 0.6 or ratio >= 3:
            verdict = "strong"
        elif ratio >= 1.5:
            verdict = "weak"
        else:
            verdict = "none"
            warnings.append(
                f"'{partition_column}' does not match the topology (within-group edge "
                f"share {fraction:.0%} vs random baseline {baseline:.0%}) — coloring by "
                "it would be misleading; compute real communities with "
                "gephi_compute_modularity instead")
        # Spatial separation of the partition in the CURRENT layout: mean
        # intra-group pair distance over mean random pair distance (1.0 =
        # fully mixed, near 0 = tight distinct clusters). This is the
        # objective form of "did the communities separate" — compare it
        # across parameter changes instead of eyeballing exports.
        from .community_layout import separation_score
        # Measured over the main cloud only: a handful of runaway outliers
        # (reported in extent.outliers) would otherwise swamp the pair
        # distances and make the score meaningless.
        positions = {n["key"]: (n["x"], n["y"]) for n in core}
        separation = separation_score(graph, positions, partition_column)
        result["partition"] = {
            "column": partition_column, "groups": len(shares),
            "within_fraction": round(fraction, 3),
            "random_baseline": round(baseline, 3),
            "ratio_vs_random": round(ratio, 2), "verdict": verdict,
            "separation": separation,
        }

    return result


