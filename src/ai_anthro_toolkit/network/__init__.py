"""Networks of coded material, without Gephi.

Three builders turn the coding pipeline's own records into graphs, one
analyzer reads them with the discipline the Gephi AI skill teaches, and the
viewer draws them in chat. Structure comes from networkx; the picture from the
vendored sigma.js page shared with Gephi AI. Export to GEXF hands the network
to Gephi, and to Gephi AI, when the full instrument is wanted.

Graph dicts follow the viewer contract: ``nodes`` carry ``key``, ``label``,
``x``, ``y``, ``size``, ``color``, ``attributes``; ``edges`` carry ``source``,
``target``, ``size`` (the weight), ``color``.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from itertools import combinations

import networkx as nx

from ai_anthro_toolkit.network.viewer import analyze_graph, build_app_html

__all__ = ["build_network", "analyze_network", "export_network", "build_app_html", "KINDS"]

KINDS = ("code_cooccurrence", "speaker_code", "lens_agreement")

# The validated palette from the Gephi AI commands: readable on white,
# colorblind-safe. Communities past the eighth are gray.
PALETTE = ["rgb(42,120,214)", "rgb(27,175,122)", "rgb(237,161,0)", "rgb(0,131,0)",
           "rgb(74,58,167)", "rgb(227,73,72)", "rgb(232,123,164)", "rgb(235,104,52)"]
GRAY = "rgb(153,153,153)"

_CODE_FIELDS = ("All_Codes", "codes", "Deductive_Codes", "Inductive_Codes")


def _codes_of(record: dict) -> list[str]:
    """The codes a coded record carries, in the pipeline's own field names.
    ``All_Codes`` wins when present; otherwise deductive and inductive are
    joined. Comma-separated strings and lists are both accepted."""
    if record.get("All_Codes"):
        raw = record["All_Codes"]
    elif record.get("codes"):
        raw = record["codes"]
    else:
        raw = ",".join(str(record.get(f, "") or "") for f in ("Deductive_Codes", "Inductive_Codes"))
    if isinstance(raw, str):
        parts = raw.split(",")
    else:
        parts = list(raw)
    seen: dict[str, None] = {}
    for p in parts:
        p = str(p).strip()
        if p:
            seen.setdefault(p, None)
    return list(seen)


def _node(key: str, **attrs) -> dict:
    return {"key": key, "label": key, "x": 0.0, "y": 0.0, "size": 10.0, "color": GRAY,
            "attributes": attrs, "spells": None}


def _edge(a: str, b: str, weight: float) -> dict:
    return {"source": a, "target": b, "size": float(weight), "color": None, "spells": None}


def build_network(records: list[dict], kind: str = "code_cooccurrence",
                  min_weight: float = 1.0, results_by_lens: dict | None = None) -> dict:
    """Build a graph from coded records.

    kind:
      code_cooccurrence: nodes are codes; an edge joins two codes each time they
        are applied to the same chunk, weighted by the count of such chunks.
      speaker_code: two-mode; a speaker is tied to each code voiced in their
        chunks, weighted by the count. Speakers with no codes are left out.
      lens_agreement: nodes are lenses; an edge weight is the number of chunks
        on which two lenses applied at least one common code. Needs
        ``results_by_lens`` ({lens: coded records}).
    min_weight drops edges below it after counting.
    """
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}, got {kind!r}")
    nodes: dict[str, dict] = {}
    weights: Counter = Counter()
    directed = False
    if kind == "code_cooccurrence":
        freq: Counter = Counter()
        for r in records:
            codes = _codes_of(r)
            freq.update(codes)
            for a, b in combinations(sorted(codes), 2):
                weights[(a, b)] += 1
        for code, n in freq.items():
            nodes[code] = _node(code, kind="code", frequency=n)
    elif kind == "speaker_code":
        for r in records:
            speaker = str(r.get("speaker") or "").strip()
            codes = _codes_of(r)
            if not speaker or not codes:
                continue
            nodes.setdefault(speaker, _node(speaker, kind="speaker", chunks=0))
            nodes[speaker]["attributes"]["chunks"] += 1
            for c in codes:
                nodes.setdefault(c, _node(c, kind="code", frequency=0))
                nodes[c]["attributes"]["frequency"] += 1
                weights[(speaker, c)] += 1
    else:
        if not results_by_lens:
            raise ValueError("lens_agreement needs results_by_lens={lens: coded records}")
        by_lens: dict[str, dict[str, set]] = {}
        for lens, recs in results_by_lens.items():
            by_lens[lens] = {str(r.get("chunk_id")): set(_codes_of(r)) for r in recs}
            nodes[lens] = _node(lens, kind="lens", chunks=len(by_lens[lens]))
        for a, b in combinations(sorted(by_lens), 2):
            shared = sum(1 for cid, codes in by_lens[a].items()
                         if codes and codes & by_lens[b].get(cid, set()))
            if shared:
                weights[(a, b)] += shared
    edges = [_edge(a, b, w) for (a, b), w in sorted(weights.items()) if w >= min_weight]
    return {"nodes": list(nodes.values()), "edges": edges, "directed": directed,
            "node_count_total": len(nodes), "edge_count_total": len(edges),
            "truncated": False, "dynamic": False, "time_min": None, "time_max": None,
            "attr_key": {}, "kind": kind}


def _to_nx(graph: dict) -> nx.Graph:
    G = nx.DiGraph() if graph.get("directed") else nx.Graph()
    for n in graph["nodes"]:
        G.add_node(n["key"], **n.get("attributes", {}))
    for e in graph["edges"]:
        G.add_edge(e["source"], e["target"], weight=float(e.get("size") or 1.0))
    return G


def analyze_network(graph: dict, seed: int = 0, community_resolution: float = 1.0) -> dict:
    """Lay out, size, color, and read a graph built by build_network.

    Returns {"graph": the same graph with positions, sizes (by degree),
    colors (by community), and degree/betweenness/community attributes;
    "summary": counts, density, components, isolates, communities, top nodes;
    "visual": the visual-QA reading (warnings, partition verdict)}. The reading
    describes hub dominance as a property of this network and never as a law.
    """
    G = _to_nx(graph)
    n, m = G.number_of_nodes(), G.number_of_edges()
    out_nodes = [dict(x, attributes=dict(x.get("attributes", {}))) for x in graph["nodes"]]
    by_key = {x["key"]: x for x in out_nodes}
    if n == 0:
        return {"graph": {**graph, "nodes": out_nodes},
                "summary": {"nodes": 0, "edges": 0, "density": 0.0, "components": 0,
                            "isolates": [], "communities": 0, "top_degree": [],
                            "top_betweenness": [], "note": "empty graph"},
                "visual": {"warnings": ["no nodes"]}}
    degree = dict(G.degree())
    weighted = dict(G.degree(weight="weight"))
    betweenness = nx.betweenness_centrality(G, weight=None, seed=seed) if n > 2 else {k: 0.0 for k in G}
    U = G.to_undirected() if G.is_directed() else G
    parts = nx.community.louvain_communities(U, weight="weight", resolution=community_resolution, seed=seed) if m else [{k} for k in U]
    parts = sorted((sorted(p) for p in parts), key=lambda p: (-len(p), p[0]))
    community = {k: i for i, p in enumerate(parts) for k in p}
    pos = nx.spring_layout(U, weight="weight", seed=seed, k=None)
    dmax = max(degree.values()) or 1
    for key, node in by_key.items():
        a = node["attributes"]
        a["degree"] = degree[key]
        a["weighted_degree"] = round(weighted[key], 3)
        a["betweenness"] = round(betweenness[key], 4)
        a["community"] = community[key]
        node["x"] = round(float(pos[key][0]) * 1000, 2)
        node["y"] = round(float(pos[key][1]) * 1000, 2)
        node["size"] = round(8 + 22 * math.sqrt(degree[key] / dmax), 2)
        node["color"] = PALETTE[community[key]] if community[key] < len(PALETTE) else GRAY
    out_graph = {**graph, "nodes": out_nodes,
                 "attr_key": {"community": "community", "degree": "degree", "betweenness": "betweenness"}}
    components = list(nx.connected_components(U))
    isolates = sorted(k for k in U if degree[k] == 0)
    # Ties on a count are broken by weighted degree, then name, so the node
    # that carries the most co-occurrences ranks first among equals.
    top = lambda d: [{"key": k, "value": round(v, 4)} for k, v in
                     sorted(d.items(), key=lambda kv: (-kv[1], -weighted[kv[0]], kv[0]))[:5]]
    summary = {
        "nodes": n, "edges": m, "density": round(nx.density(U), 4),
        "components": len(components), "isolates": isolates,
        "communities": len(parts),
        "community_sizes": [len(p) for p in parts],
        "top_degree": top(degree), "top_betweenness": top(betweenness),
        "reading": _reading(n, m, degree, len(components), isolates, parts),
    }
    return {"graph": out_graph, "summary": summary,
            "visual": analyze_graph(out_graph, partition_column="community")}


def _reading(n, m, degree, ncomp, isolates, parts) -> str:
    """A first sentence a person can read; no claims the numbers do not carry."""
    if m == 0:
        return f"{n} nodes and no ties: nothing co-occurs, so there is no structure to read yet."
    vals = sorted(degree.values(), reverse=True)
    share = vals[0] / sum(vals) if sum(vals) else 0
    hub = "a few nodes concentrate most ties" if share > 0.3 else "ties are spread fairly evenly"
    frag = f"{ncomp} separate components" if ncomp > 1 else "one connected whole"
    iso = f", {len(isolates)} isolated" if isolates else ""
    return f"{n} nodes, {m} ties, {frag}{iso}; {hub}; {len(parts)} communities detected by modularity."


def export_network(graph: dict, path: str, fmt: str = "gexf") -> dict:
    """Write the graph to GEXF (default) or GraphML with positions, sizes, and
    colors, so Gephi, and Gephi AI, can open it as a laid-out map."""
    if fmt not in ("gexf", "graphml"):
        raise ValueError("fmt must be 'gexf' or 'graphml'")
    G = _to_nx(graph)
    for node in graph["nodes"]:
        k = node["key"]
        G.nodes[k]["label"] = node.get("label", k)
        if fmt == "gexf":
            r, g, b = _rgb(node.get("color"))
            G.nodes[k]["viz"] = {"color": {"r": r, "g": g, "b": b, "a": 1.0},
                                 "size": float(node.get("size", 10.0)),
                                 "position": {"x": float(node.get("x", 0.0)), "y": float(node.get("y", 0.0)), "z": 0.0}}
        else:
            G.nodes[k]["x"] = float(node.get("x", 0.0)); G.nodes[k]["y"] = float(node.get("y", 0.0))
            G.nodes[k]["size"] = float(node.get("size", 10.0)); G.nodes[k]["color"] = str(node.get("color") or GRAY)
    if fmt == "gexf":
        nx.write_gexf(G, path)
    else:
        nx.write_graphml(G, path)
    return {"path": path, "format": fmt, "nodes": G.number_of_nodes(), "edges": G.number_of_edges()}


def _rgb(color) -> tuple[int, int, int]:
    if not color:
        return (153, 153, 153)
    if color.startswith("#") and len(color) >= 7:
        return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
    nums = [int(x) for x in "".join(ch if ch.isdigit() or ch == "," else " " for ch in color).replace(",", " ").split()[:3]]
    return tuple(nums) if len(nums) == 3 else (153, 153, 153)  # type: ignore[return-value]
