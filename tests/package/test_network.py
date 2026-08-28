"""Networks of coded material: build, analyze, view, export.

The builders turn the coding pipeline's own records into graphs (codes that
co-occur in a chunk, speakers tied to the codes they voice, lenses tied by
agreement), and the analyzer reads them with the same discipline the Gephi
skill teaches. No Gephi, no Java: networkx for structure, the vendored
viewer for the picture.
"""

import json
import os
import tempfile
import unittest

from ai_anthro_toolkit import network

CODED = [
    {"chunk_id": 1, "speaker": "Ana", "All_Codes": "trust, delay"},
    {"chunk_id": 2, "speaker": "Ana", "All_Codes": "trust, cost"},
    {"chunk_id": 3, "speaker": "Ben", "All_Codes": "delay, cost, trust"},
    {"chunk_id": 4, "speaker": "Ben", "All_Codes": "ritual"},
    {"chunk_id": 5, "speaker": "Cy", "All_Codes": ""},
]


class TestBuildNetwork(unittest.TestCase):

    def test_code_cooccurrence_counts_shared_chunks(self):
        g = network.build_network(CODED, kind="code_cooccurrence")
        keys = {n["key"] for n in g["nodes"]}
        self.assertEqual(keys, {"trust", "delay", "cost", "ritual"})
        weights = {frozenset((e["source"], e["target"])): e["size"] for e in g["edges"]}
        self.assertEqual(weights[frozenset(("trust", "delay"))], 2)   # chunks 1 and 3
        self.assertEqual(weights[frozenset(("trust", "cost"))], 2)    # chunks 2 and 3
        self.assertEqual(weights[frozenset(("delay", "cost"))], 1)    # chunk 3
        self.assertNotIn(frozenset(("ritual", "trust")), weights)
        self.assertFalse(g["directed"])
        trust = next(n for n in g["nodes"] if n["key"] == "trust")
        self.assertEqual(trust["attributes"]["frequency"], 3)

    def test_speaker_code_network_is_two_mode(self):
        g = network.build_network(CODED, kind="speaker_code")
        kinds = {n["key"]: n["attributes"]["kind"] for n in g["nodes"]}
        self.assertEqual(kinds["Ana"], "speaker")
        self.assertEqual(kinds["trust"], "code")
        self.assertNotIn("Cy", kinds, "a speaker with no codes has no ties and is left out")
        weights = {(e["source"], e["target"]): e["size"] for e in g["edges"]}
        self.assertEqual(weights[("Ana", "trust")], 2)

    def test_empty_records_give_empty_graph_not_error(self):
        g = network.build_network([], kind="code_cooccurrence")
        self.assertEqual(g["nodes"], [])
        self.assertEqual(g["edges"], [])

    def test_unknown_kind_is_refused(self):
        with self.assertRaises(ValueError):
            network.build_network(CODED, kind="sociogram")


class TestAnalyzeNetwork(unittest.TestCase):

    def test_analysis_lays_out_colors_and_reads_the_graph(self):
        g = network.build_network(CODED, kind="code_cooccurrence")
        out = network.analyze_network(g, seed=7)
        self.assertEqual(out["summary"]["nodes"], 4)
        self.assertEqual(out["summary"]["edges"], 3)
        self.assertEqual(out["summary"]["components"], 2)
        # every node got a position, a size, a color, and a community
        for n in out["graph"]["nodes"]:
            self.assertTrue(all(k in n for k in ("x", "y", "size", "color")))
            self.assertIn("community", n["attributes"])
            self.assertIn("degree", n["attributes"])
        top = out["summary"]["top_degree"][0]
        self.assertEqual(top["key"], "trust")
        self.assertIn("warnings", out["visual"])
        self.assertIn("isolates", out["summary"])

    def test_analysis_is_deterministic_for_a_seed(self):
        g = network.build_network(CODED, kind="code_cooccurrence")
        a = network.analyze_network(g, seed=3)["graph"]["nodes"]
        b = network.analyze_network(g, seed=3)["graph"]["nodes"]
        self.assertEqual([(n["x"], n["y"]) for n in a], [(n["x"], n["y"]) for n in b])

    def test_analysis_never_claims_scale_free(self):
        g = network.build_network(CODED, kind="code_cooccurrence")
        text = json.dumps(network.analyze_network(g, seed=1)).lower()
        self.assertNotIn("scale-free", text)
        self.assertNotIn("power law", text)


class TestExportNetwork(unittest.TestCase):

    def test_gexf_round_trips_through_networkx(self):
        import networkx as nx
        g = network.analyze_network(network.build_network(CODED, kind="code_cooccurrence"), seed=1)["graph"]
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "codes.gexf")
            rec = network.export_network(g, path)
            self.assertEqual(rec["nodes"], 4)
            back = nx.read_gexf(path)
            self.assertEqual(set(back.nodes()), {"trust", "delay", "cost", "ritual"})
            self.assertEqual(back.number_of_edges(), 3)
            self.assertIn("viz", back.nodes["trust"])

    def test_export_refuses_unknown_format(self):
        g = network.build_network(CODED, kind="code_cooccurrence")
        with self.assertRaises(ValueError):
            network.export_network(g, "x.graphml", fmt="dot")


class TestViewer(unittest.TestCase):

    def test_app_html_is_self_contained_and_toolkit_flavoured(self):
        html = network.build_app_html()
        self.assertNotIn("__SIGMA_JS__", html)
        self.assertNotIn("__GRAPHOLOGY_JS__", html)
        for method in ("ui/initialize", "ui/notifications/tool-result", "ui/update-model-context",
                       "ui/notifications/size-changed", "tools/call"):
            self.assertIn(method, html, method)
        # the toolkit's copy must call its own tools, not Gephi's
        self.assertIn("view_network", html)
        self.assertNotIn("gephi_view_graph", html)
        self.assertNotIn("gephi_focus_view", html)


if __name__ == "__main__":
    unittest.main()


class TestServerTools(unittest.TestCase):

    def test_view_network_returns_structured_content_for_the_app(self):
        from mcp.types import CallToolResult
        from ai_anthro_toolkit.mcp import server
        graph = server.analyze_network(server.build_network(CODED))["graph"]
        result = server.view_network(graph, title="Codes", caption_names={"0": "Money"})
        self.assertIsInstance(result, CallToolResult)
        self.assertFalse(result.is_error)
        sc = result.structured_content
        self.assertEqual(sc["title"], "Codes")
        self.assertEqual(sc["captions"], {"column": "community", "names": {"0": "Money"}})
        self.assertEqual({n["key"] for n in sc["nodes"]}, {"trust", "delay", "cost", "ritual"})

    def test_view_network_analyzes_a_raw_graph_itself(self):
        from ai_anthro_toolkit.mcp import server
        result = server.view_network(server.build_network(CODED))
        self.assertFalse(result.is_error)
        self.assertTrue(all("community" in n["attributes"] for n in result.structured_content["nodes"]))

    def test_view_network_refuses_an_empty_graph(self):
        from ai_anthro_toolkit.mcp import server
        self.assertTrue(server.view_network({"nodes": [], "edges": []}).is_error)


class TestBranding(unittest.TestCase):
    """Anything the toolkit draws in a chatbot carries the Matt Artz brand:
    monochrome chrome, the brand typefaces, and a credit that links back."""

    def test_app_html_carries_the_brand_and_the_credit(self):
        html = network.build_app_html()
        self.assertIn('id="brand"', html)
        self.assertIn("https://www.mattartz.me", html)
        self.assertIn("AI Anthropology Toolkit", html)
        self.assertIn("Matt Artz", html)
        self.assertIn("Cormorant Garamond", html)
        self.assertIn("Inter", html)
        self.assertIn("ui/open-link", html)
        # Ink, Charcoal, Silver: the chrome is monochrome, no accent color.
        for token in ("#1A1A1A", "#333333", "#E0E0E0"):
            self.assertIn(token, html, token)
        brand_css = html[html.index('id="brand"'):html.index("</style>", html.index('id="brand"'))]
        self.assertIn("--color-text-info", brand_css, "the accent token must be overridden to monochrome")

    def test_view_network_text_credits_the_toolkit(self):
        from ai_anthro_toolkit.mcp import server
        r = server.view_network(server.build_network(CODED))
        self.assertIn("mattartz.me", r.content[0].text)
        self.assertIn("credit", r.content[0].text.lower())
