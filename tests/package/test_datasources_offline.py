"""Offline parser tests for every data source.

Each test replaces only the network boundary (requests.get, or the scraper
library's fetch call) with a hand-built response in the shape the service
returns, then checks the records the collector builds from it. If a
service's response format changes, these are the tests that should be
updated against a fresh capture; if a parser regresses, these fail without
any network.

    python3.12 -m unittest tests.package.test_datasources_offline -v
"""

import sys
import types
import unittest
from unittest import mock

from ai_anthro_toolkit import datasources
from ai_anthro_toolkit.datasources import (
    citation,
    crossref,
    googlenews,
    ngram,
    openalex,
    patents,
    podcast,
    pubmed,
    scholar,
    trends,
    youtube,
)
from ai_anthro_toolkit.mcp import server


class FakeResponse:
    """The parts of requests.Response the collectors read."""

    def __init__(self, payload=None, status_code=200, text=None, url="https://example.test/"):
        self._payload = payload
        self.status_code = status_code
        self.text = text if text is not None else ""
        self.url = url

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"{self.status_code} error")


def patched_get(module, *responses):
    """Patch module.requests.get to return `responses` in order."""
    return mock.patch.object(module.requests, "get", side_effect=list(responses))


# ── CrossRef ────────────────────────────────────────────────────────────────

CROSSREF_PAYLOAD = {
    "status": "ok",
    "message-type": "work-list",
    "message": {
        "total-results": 2,
        "items": [
            {
                "DOI": "10.1111/amet.12345",
                "type": "journal-article",
                "title": ["Rotating Savings and the Moral Economy of the Market"],
                "author": [{"given": "Ada", "family": "Fennimore", "sequence": "first"},
                           {"family": "Kowalski", "sequence": "additional"},
                           {"name": "Market Research Collective", "sequence": "additional"}],
                "container-title": ["American Ethnologist"],
                "published": {"date-parts": [[2021, 5, 3]]},
                "is-referenced-by-count": 17,
                "publisher": "Wiley",
            },
            {
                "DOI": "10.5555/no-metadata",
                "type": "journal-article",
            },
        ],
    },
}


class TestCrossrefParser(unittest.TestCase):
    def test_records_and_request_parameters(self):
        with patched_get(crossref, FakeResponse(CROSSREF_PAYLOAD)) as get:
            records = crossref.search_crossref(
                "rotating savings", limit=500, year_from=2015, year_to=2024,
                journal="American Ethnologist", mailto="lab@example.org")
        params = get.call_args.kwargs["params"]
        self.assertEqual(params["rows"], 100)  # clamped
        self.assertEqual(params["filter"], "from-pub-date:2015-01-01,"
                         "until-pub-date:2024-12-31,type:journal-article")
        self.assertEqual(params["query.container-title"], "American Ethnologist")
        self.assertEqual(params["mailto"], "lab@example.org")

        first, second = records
        self.assertEqual(first["title"], "Rotating Savings and the Moral Economy of the Market")
        self.assertEqual(first["authors"], ["Ada Fennimore", "Kowalski"])
        self.assertEqual(first["journal"], "American Ethnologist")
        self.assertEqual(first["year"], 2021)
        self.assertEqual(first["doi"], "10.1111/amet.12345")
        self.assertEqual(first["cited_by_count"], 17)
        # Sparse records degrade to None rather than raising.
        self.assertEqual((second["title"], second["journal"], second["year"]),
                         (None, None, None))
        self.assertEqual(second["authors"], [])

    def test_no_filter_when_unrestricted(self):
        with patched_get(crossref, FakeResponse({"message": {"items": []}})) as get:
            self.assertEqual(crossref.search_crossref(
                "x", limit=0, journal_articles_only=False), [])
        params = get.call_args.kwargs["params"]
        self.assertNotIn("filter", params)
        self.assertEqual(params["rows"], 1)

    def test_http_error_raises(self):
        import requests
        with patched_get(crossref, FakeResponse({}, status_code=503)):
            with self.assertRaises(requests.HTTPError):
                crossref.search_crossref("x")

    def test_server_tool_maps_zero_years_to_no_filter(self):
        with patched_get(crossref, FakeResponse({"message": {"items": []}})) as get:
            server.search_crossref("x", year_from=0, year_to=0, journal="")
        self.assertEqual(get.call_args.kwargs["params"]["filter"], "type:journal-article")


# ── PubMed ──────────────────────────────────────────────────────────────────

ESEARCH_PAYLOAD = {"header": {"type": "esearch"},
                   "esearchresult": {"count": "2", "idlist": ["38000001", "38000002"]}}
ESUMMARY_PAYLOAD = {
    "header": {"type": "esummary"},
    "result": {
        "uids": ["38000001", "38000002"],
        "38000001": {
            "uid": "38000001",
            "title": "Care work and household debt among market traders.",
            "authors": [{"name": "Wójcik A", "authtype": "Author"},
                        {"name": "Fennimore A", "authtype": "Author"}],
            "fulljournalname": "Social science & medicine (1982)",
            "pubdate": "2024 Mar",
            "articleids": [{"idtype": "pubmed", "value": "38000001"},
                           {"idtype": "doi", "value": "10.1016/j.socscimed.2024.1"}],
        },
    },
}


class TestPubmedParser(unittest.TestCase):
    def test_two_step_search_and_summary(self):
        with patched_get(pubmed, FakeResponse(ESEARCH_PAYLOAD),
                         FakeResponse(ESUMMARY_PAYLOAD)) as get:
            records = pubmed.search_pubmed("household debt", limit=5, api_key="k",
                                           year_from=2020, journal="Soc Sci Med")
        search_params = get.call_args_list[0].kwargs["params"]
        self.assertEqual(search_params["term"], 'household debt AND "Soc Sci Med"[ta]')
        self.assertEqual(search_params["mindate"], "2020/01/01")
        self.assertEqual(search_params["maxdate"], "2100/12/31")
        self.assertEqual(search_params["api_key"], "k")
        self.assertEqual(get.call_args_list[1].kwargs["params"]["id"], "38000001,38000002")
        # The second id has no summary and is skipped, not padded.
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec["pmid"], "38000001")
        self.assertEqual(rec["authors"], ["Wójcik A", "Fennimore A"])
        self.assertEqual(rec["doi"], "10.1016/j.socscimed.2024.1")

    def test_no_hits_skips_the_summary_call(self):
        empty = {"esearchresult": {"idlist": []}}
        with patched_get(pubmed, FakeResponse(empty)) as get:
            self.assertEqual(pubmed.search_pubmed("nothing"), [])
        self.assertEqual(get.call_count, 1)


# ── OpenAlex ────────────────────────────────────────────────────────────────

OPENALEX_WORKS = {
    "meta": {"count": 1},
    "results": [{
        "id": "https://openalex.org/W100",
        "display_name": "Kinship, Credit, and the Marketplace",
        "publication_year": 2019,
        "doi": "https://doi.org/10.1000/xyz",
        "cited_by_count": 42,
        "open_access": {"is_oa": True},
        "authorships": [{"author": {"display_name": "Ada Fennimore"}},
                        {"institutions": []}],
        "primary_location": {"source": {"display_name": "Economic Anthropology"}},
        "abstract_inverted_index": {"Kinship": [0]},
    }, {
        "id": "https://openalex.org/W200",
        "display_name": "Untitled preprint",
        "primary_location": None,
        "open_access": None,
    }],
}


class TestOpenalexParser(unittest.TestCase):
    def test_venue_resolution_sort_and_records(self):
        sources = {"results": [{"id": "https://openalex.org/S11", "display_name": "EA"},
                               {"id": "https://openalex.org/S12", "display_name": "EA2"}]}
        with patched_get(openalex, FakeResponse(sources), FakeResponse(OPENALEX_WORKS)) as get:
            records = openalex.search_openalex(
                "kinship credit", venue="Economic Anthropology", sort="cited",
                year_from=2010, year_to=2020, open_access_only=True,
                mailto="lab@example.org")
        params = get.call_args_list[1].kwargs["params"]
        self.assertEqual(params["sort"], "cited_by_count:desc")
        self.assertIn("primary_location.source.id:S11|S12", params["filter"])
        self.assertIn("open_access.is_oa:true", params["filter"])
        self.assertEqual(get.call_args_list[0].kwargs["params"]["mailto"], "lab@example.org")

        first, second = records
        self.assertEqual(first["authors"], ["Ada Fennimore"])
        self.assertEqual(first["venue"], "Economic Anthropology")
        self.assertTrue(first["is_open_access"])
        self.assertTrue(first["abstract_available"])
        self.assertIsNone(second["venue"])
        self.assertFalse(second["is_open_access"])
        self.assertEqual(second["cited_by_count"], 0)

    def test_unknown_venue_returns_nothing_without_searching(self):
        with patched_get(openalex, FakeResponse({"results": []})) as get:
            self.assertEqual(openalex.search_openalex("x", venue="No Such Journal"), [])
        self.assertEqual(get.call_count, 1)

    def test_relevance_sort_sends_no_sort_param(self):
        with patched_get(openalex, FakeResponse({"results": []})) as get:
            server.search_openalex("x", sort="relevance")
        self.assertNotIn("sort", get.call_args.kwargs["params"])
        self.assertNotIn("filter", get.call_args.kwargs["params"])


# ── Books Ngram ─────────────────────────────────────────────────────────────

class TestNgramParser(unittest.TestCase):
    def test_long_format_rows(self):
        payload = [{"ngram": "kinship", "parent": "", "type": "NGRAM",
                    "timeseries": [1e-6, 2e-6, 3e-6]},
                   {"ngram": "", "timeseries": [9.0]}]
        with patched_get(ngram, FakeResponse(payload)) as get:
            rows = ngram.get_ngram_frequencies(["kinship", "reciprocity"], 2000, 2002,
                                               corpus="EN-GB", case_insensitive=True)
        params = get.call_args.kwargs["params"]
        self.assertEqual(params["content"], "kinship, reciprocity")
        self.assertEqual(params["corpus"], 29)
        self.assertEqual(params["case_insensitive"], "true")
        self.assertEqual(rows, [{"term": "kinship", "year": 2000, "frequency": 1e-6},
                                {"term": "kinship", "year": 2001, "frequency": 2e-6},
                                {"term": "kinship", "year": 2002, "frequency": 3e-6}])

    def test_unknown_corpus_and_unexpected_shape(self):
        with self.assertRaises(ValueError):
            ngram.get_ngram_frequencies("x", corpus="klingon")
        with patched_get(ngram, FakeResponse({"error": "bad request"})):
            with self.assertRaises(ValueError):
                ngram.get_ngram_frequencies("x")


# ── Google Patents ──────────────────────────────────────────────────────────

def _patent(number, title):
    return {"patent": {"publication_number": number, "title": f"<b>{title}</b>",
                       "inventor": "Ada Fennimore", "assignee": "Example Corp",
                       "filing_date": "2019-01-02", "publication_date": "2020-07-08"}}


class TestPatentsParser(unittest.TestCase):
    def test_pages_until_limit_and_strips_markup(self):
        page0 = {"results": {"cluster": [{"result": [_patent(f"US{i}", f"Method {i}")
                                                     for i in range(10)]}]}}
        page1 = {"results": {"cluster": [{"result": [_patent("US99", "Last")]}]}}
        with patched_get(patents, FakeResponse(page0), FakeResponse(page1)) as get:
            records = patents.search_google_patents("ethnographic sensor", limit=12)
        self.assertEqual(get.call_count, 2)
        self.assertIn("page%3D1", get.call_args_list[1].args[0])
        self.assertEqual(len(records), 11)  # second page ran short
        self.assertEqual(records[0]["title"], "Method 0")
        self.assertEqual(records[0]["url"], "https://patents.google.com/patent/US0")

    def test_limit_stops_mid_page(self):
        page = {"results": {"cluster": [{"result": [_patent("US1", "A"), _patent("", "B")]}]}}
        with patched_get(patents, FakeResponse(page)):
            records = patents.search_google_patents("x", limit=1)
        self.assertEqual(len(records), 1)

    def test_empty_cluster_ends_and_block_raises(self):
        with patched_get(patents, FakeResponse({"results": {"cluster": []}})):
            self.assertEqual(patents.search_google_patents("x"), [])
        for code in (429, 503):
            with patched_get(patents, FakeResponse({}, status_code=code)):
                with self.assertRaises(RuntimeError) as ctx:
                    patents.search_google_patents("x")
                self.assertIn("rate limiting", str(ctx.exception))


# ── Podcast RSS ─────────────────────────────────────────────────────────────

RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
<channel><title>Field Notes Weekly</title>
<item>
  <title>Episode 2 &#8211; Markets</title>
  <pubDate>Tue, 03 Sep 2024 10:00:00 GMT</pubDate>
  <itunes:duration>3725</itunes:duration>
  <enclosure url="https://cdn.example.test/ep2.mp3" type="audio/mpeg" length="1"/>
  <description>&lt;p&gt;Credit &amp;amp; kinship in the market.&lt;/p&gt;</description>
  <link>https://example.test/ep2</link>
</item>
<item>
  <title>Episode 1</title>
  <pubDate>sometime last spring</pubDate>
  <itunes:duration>12:05</itunes:duration>
</item>
</channel></rss>"""


class TestPodcastParser(unittest.TestCase):
    def test_episode_records(self):
        episodes = podcast.get_podcast_episodes(RSS, limit=10)
        first, second = episodes
        self.assertEqual(first["title"], "Episode 2 - Markets")
        self.assertEqual(first["published"], "2024-09-03")
        self.assertEqual(first["duration"], "1:02:05")
        self.assertEqual(first["audio_url"], "https://cdn.example.test/ep2.mp3")
        self.assertEqual(first["description"], "Credit & kinship in the market.")
        self.assertEqual(second["published"], "sometime last spring")
        self.assertEqual(second["duration"], "0:12:05")
        self.assertEqual(second["audio_url"], "")
        self.assertEqual(len(podcast.get_podcast_episodes(RSS, limit=1)), 1)

    def test_duration_forms(self):
        self.assertEqual(podcast._duration(""), "")
        self.assertEqual(podcast._duration("1:02:03"), "1:02:03")
        self.assertEqual(podcast._duration("about an hour"), "about an hour")

    def test_unreadable_feed_raises_instead_of_returning_nothing(self):
        # Before the fix this returned [], which reads as "no episodes".
        with self.assertRaises(RuntimeError) as ctx:
            podcast.get_podcast_episodes("this is not a feed")
        self.assertIn("Could not read a podcast feed", str(ctx.exception))

    def test_http_error_status_raises(self):
        import feedparser
        result = feedparser.FeedParserDict(entries=[], bozo=False, status=404)
        with mock.patch.object(feedparser, "parse", return_value=result):
            with self.assertRaises(RuntimeError) as ctx:
                podcast.get_podcast_episodes("https://example.test/gone.xml")
        self.assertIn("HTTP 404", str(ctx.exception))

    def test_valid_feed_with_no_items_is_an_empty_list(self):
        empty = '<?xml version="1.0"?><rss version="2.0"><channel><title>t</title></channel></rss>'
        self.assertEqual(podcast.get_podcast_episodes(empty), [])


# ── Google Trends (pytrends) ────────────────────────────────────────────────

class TestTrendsParser(unittest.TestCase):
    def _fake_trendreq(self, *, iot=None, ibr=None, related=None, build_error=None,
                       iot_error=None):
        import pandas as pd

        class FakeTrendReq:
            instances = []

            def __init__(self, hl, tz):
                FakeTrendReq.instances.append(self)

            def build_payload(self, kw_list, geo, timeframe, cat):
                self.kw_list, self.geo, self.timeframe = kw_list, geo, timeframe
                if build_error:
                    raise build_error

            def interest_over_time(self):
                if iot_error:
                    raise iot_error
                return iot if iot is not None else pd.DataFrame()

            def interest_by_region(self, **kwargs):
                return ibr if ibr is not None else pd.DataFrame()

            def related_queries(self):
                if related is None:
                    raise KeyError("default")
                return related

        return FakeTrendReq

    def _patch(self, cls):
        return mock.patch("pytrends.request.TrendReq", cls)

    def test_records_drop_partial_flag_and_zero_regions(self):
        import pandas as pd
        iot = pd.DataFrame({"kinship": [40, 55], "isPartial": [False, True]},
                           index=pd.to_datetime(["2024-01-07", "2024-01-14"]).rename("date"))
        ibr = pd.DataFrame({"geoCode": ["PL", "NZ"], "kinship": [100, 0]},
                           index=pd.Index(["Poland", "New Zealand"], name="geoName"))
        related = {"kinship": {"top": pd.DataFrame({"query": ["kinship terms"], "value": [100]}),
                               "rising": None}}
        cls = self._fake_trendreq(iot=iot, ibr=ibr, related=related)
        with self._patch(cls):
            out = trends.get_google_trends("kinship, , reciprocity", geo="PL")
        self.assertEqual(cls.instances[0].kw_list, ["kinship", "reciprocity"])
        self.assertEqual(out["interest_over_time"][0]["kinship"], 40)
        self.assertNotIn("isPartial", out["interest_over_time"][0])
        self.assertTrue(out["interest_over_time"][0]["date"].startswith("2024-01-07"))
        self.assertEqual([r["geoName"] for r in out["interest_by_region"]], ["Poland"])
        self.assertEqual(out["related_queries"]["kinship"]["top"][0]["query"], "kinship terms")
        self.assertEqual(out["related_queries"]["reciprocity"], {"top": [], "rising": []})

    def test_five_term_cap_and_empty_terms(self):
        import pandas as pd
        iot = pd.DataFrame({"a": [1]}, index=pd.Index(["2024-01-01"], name="date"))
        cls = self._fake_trendreq(iot=iot)
        with self._patch(cls):
            trends.get_google_trends(["a", "b", "c", "d", "e", "f"])
        self.assertEqual(len(cls.instances[0].kw_list), 5)
        with self.assertRaises(ValueError):
            trends.get_google_trends(" , ")

    def test_no_data_is_reported_as_a_block_not_an_empty_success(self):
        cls = self._fake_trendreq(iot_error=RuntimeError("429"))
        with self._patch(cls):
            with self.assertRaises(RuntimeError) as ctx:
                trends.get_google_trends("kinship")
        self.assertIn("rate limiting", str(ctx.exception))

    def test_connection_failure_carries_guidance(self):
        cls = self._fake_trendreq(build_error=ConnectionError("refused"))
        with self._patch(cls):
            with self.assertRaises(RuntimeError) as ctx:
                trends.get_google_trends("kinship")
        self.assertIn("ConnectionError", str(ctx.exception))

    def test_a_block_while_creating_the_client_carries_guidance(self):
        # TrendReq() itself contacts Google; before the fix its failure
        # escaped as a bare requests error with no guidance.
        class Refusing:
            def __init__(self, hl, tz):
                raise ConnectionError("Max retries exceeded")

        with self._patch(Refusing):
            with self.assertRaises(RuntimeError) as ctx:
                trends.get_google_trends("kinship")
        self.assertIn("rate-limits", str(ctx.exception))

    def test_missing_library_names_the_extra(self):
        with mock.patch.dict(sys.modules, {"pytrends": None, "pytrends.request": None}):
            with self.assertRaises(RuntimeError) as ctx:
                trends.get_google_trends("kinship")
        self.assertIn("[data]", str(ctx.exception))


# ── Google News (gnews) ─────────────────────────────────────────────────────

class TestGoogleNewsParser(unittest.TestCase):
    def _gnews(self, results=None, error=None):
        created = {}

        class FakeGNews:
            def __init__(self, **kwargs):
                created.update(kwargs)

            def get_news(self, query):
                if error:
                    raise error
                return results

        return FakeGNews, created

    def test_records_normalized(self):
        results = [{"title": "Market traders — “we pool money”",
                    "publisher": {"href": "https://news.example", "title": "The Example Times"},
                    "published date": "Tue, 03 Sep 2024 10:00:00 GMT",
                    "url": "https://news.example/a", "description": "Credit…"},
                   {"title": "Second", "publisher": "Plain Publisher",
                    "published date": "not a date"}]
        cls, created = self._gnews(results)
        with mock.patch("gnews.GNews", cls):
            records = googlenews.search_google_news("credit", limit=500, period="1m")
        self.assertEqual(created["max_results"], 100)
        self.assertEqual(records[0]["title"], 'Market traders - "we pool money"')
        self.assertEqual(records[0]["publisher"], "The Example Times")
        self.assertEqual(records[0]["published"], "2024-09-03T10:00:00+00:00")
        self.assertEqual(records[0]["description"], "Credit...")
        self.assertEqual(records[1]["publisher"], "Plain Publisher")
        self.assertEqual(records[1]["published"], "not a date")

    def test_empty_and_failed_requests_raise_with_guidance(self):
        for cls, _ in (self._gnews([]), self._gnews(error=OSError("reset"))):
            with mock.patch("gnews.GNews", cls):
                with self.assertRaises(RuntimeError) as ctx:
                    googlenews.search_google_news("credit")
                self.assertIn("rate-limiting", str(ctx.exception))
        self.assertEqual(googlenews._normalize_text(None), None)


# ── Google Scholar (scholarly) ──────────────────────────────────────────────

class TestScholarParser(unittest.TestCase):
    def _scholarly(self, items, search_error=None):
        calls = {}

        def search_pubs(query, **kwargs):
            calls.update(kwargs)
            if search_error:
                raise search_error

            def gen():
                for item in items:
                    if isinstance(item, BaseException):
                        raise item
                    yield item
            return gen()

        fake = types.SimpleNamespace(search_pubs=search_pubs)
        return mock.patch("scholarly.scholarly", fake), calls

    PUB = {"bib": {"title": "Credit – and Kin", "author": ["A Fennimore", "B Kowalski"],
                   "pub_year": "2018", "venue": "Econ Anthropol"},
           "num_citations": 12, "pub_url": "https://example.test/p"}

    def test_records_and_year_filters(self):
        second = {"bib": {"title": "T2", "author": "A Fennimore and B Kowalski",
                          "pub_year": "n.d."}, "eprint_url": "https://example.test/e"}
        patcher, calls = self._scholarly([self.PUB, second])
        with patcher:
            records = scholar.search_google_scholar("credit", limit=50,
                                                    year_from=2010, year_to=2020)
        self.assertEqual(calls, {"year_low": 2010, "year_high": 2020})
        self.assertEqual(records[0]["title"], "Credit - and Kin")
        self.assertEqual(records[0]["year"], 2018)
        self.assertEqual(records[1]["authors"], ["A Fennimore", "B Kowalski"])
        self.assertIsNone(records[1]["year"])
        self.assertEqual(records[1]["url"], "https://example.test/e")

    def test_block_midway_raises_but_other_errors_keep_partial_results(self):
        patcher, _ = self._scholarly([self.PUB, Exception("MaxTriesExceededException")])
        with patcher:
            with self.assertRaises(RuntimeError):
                scholar.search_google_scholar("credit", limit=5)
        patcher, _ = self._scholarly([self.PUB, ValueError("odd page")])
        with patcher:
            self.assertEqual(len(scholar.search_google_scholar("credit", limit=5)), 1)

    def test_empty_and_failed_search_raise(self):
        patcher, _ = self._scholarly([])
        with patcher, self.assertRaises(RuntimeError):
            scholar.search_google_scholar("credit")
        patcher, _ = self._scholarly([], search_error=OSError("captcha"))
        with patcher, self.assertRaises(RuntimeError):
            scholar.search_google_scholar("credit")
        patcher, _ = self._scholarly([ValueError("first page failed")])
        with patcher, self.assertRaises(RuntimeError):
            scholar.search_google_scholar("credit")


# ── YouTube (scrapetube, youtube-transcript-api) ────────────────────────────

SEARCH_RENDERER = {
    "videoId": "abcdefghijk",
    "title": {"runs": [{"text": "Fieldwork in the Market"}]},
    "ownerText": {"runs": [{"text": "Example Anthropology Channel"}]},
    "viewCountText": {"simpleText": "1,234 views"},
    "lengthText": {"simpleText": "12:34"},
}


class TestYoutubeSearchParser(unittest.TestCase):
    def test_records(self):
        with mock.patch("scrapetube.get_search", return_value=iter([SEARCH_RENDERER, {}])) as gs:
            records = youtube.search_youtube("fieldwork", limit=0)
        self.assertEqual(gs.call_args.kwargs["limit"], 1)
        self.assertEqual(records[0], {
            "video_id": "abcdefghijk", "title": "Fieldwork in the Market",
            "channel": "Example Anthropology Channel", "views": "1,234 views",
            "duration": "12:34", "url": "https://www.youtube.com/watch?v=abcdefghijk"})
        self.assertEqual(records[1]["url"], "")
        self.assertEqual(records[1]["title"], "")

    def test_empty_and_broken_scrape_raise(self):
        with mock.patch("scrapetube.get_search", return_value=iter([])):
            with self.assertRaises(RuntimeError) as ctx:
                youtube.search_youtube("fieldwork")
            self.assertIn("no results", str(ctx.exception))
        with mock.patch("scrapetube.get_search", side_effect=KeyError("contents")):
            with self.assertRaises(RuntimeError) as ctx:
                youtube.search_youtube("fieldwork")
            self.assertIn("page structure", str(ctx.exception))


class _Transcript:
    def __init__(self, code, generated, snippets=None, error=None):
        self.language_code = code
        self.is_generated = generated
        self._snippets = snippets or []
        self._error = error

    def fetch(self):
        if self._error:
            raise self._error
        return self._snippets


class TestYoutubeTranscriptParser(unittest.TestCase):
    def _api(self, transcripts=None, list_error=None):
        class FakeApi:
            def list(self, vid):
                if list_error:
                    raise list_error
                return transcripts
        return mock.patch("youtube_transcript_api.YouTubeTranscriptApi", FakeApi)

    def test_prefers_human_captions_in_a_requested_language(self):
        snip = types.SimpleNamespace
        human = _Transcript("pl", False, [snip(start=0.0, duration=1.5, text="Dzień\n dobry"),
                                          snip(start=1.5, duration=2.0, text="na targu")])
        auto = _Transcript("pl", True, [snip(start=0, duration=1, text="auto")])
        with self._api([auto, human]):
            out = youtube.get_youtube_transcript("https://youtu.be/abcdefghijk",
                                                 languages=["pl"])
        self.assertEqual(out["video_id"], "abcdefghijk")
        self.assertFalse(out["auto_generated"])
        self.assertEqual(out["text"], "Dzień dobry na targu")
        self.assertEqual(out["segments"][0], {"start": 0.0, "duration": 1.5,
                                              "text": "Dzień dobry"})

    def test_falls_back_to_generated_and_can_skip_joining(self):
        snip = types.SimpleNamespace(start=0, duration=1, text="hello")
        with self._api([_Transcript("en", True, [snip])]):
            out = youtube.get_youtube_transcript("abcdefghijk", join_segments=False)
        self.assertTrue(out["auto_generated"])
        self.assertIsNone(out["text"])

    def test_failures_become_runtime_errors_with_the_cause(self):
        from youtube_transcript_api import (
            CouldNotRetrieveTranscript,
            RequestBlocked,
            TranscriptsDisabled,
        )
        with self._api([]):
            with self.assertRaises(RuntimeError) as ctx:
                youtube.get_youtube_transcript("abcdefghijk")
            self.assertIn("No transcript available", str(ctx.exception))
        cases = [(RequestBlocked("abcdefghijk"), "blocked"),
                 (TranscriptsDisabled("abcdefghijk"), "TranscriptsDisabled"),
                 (CouldNotRetrieveTranscript("abcdefghijk"), "Could not retrieve")]
        for error, expected in cases:
            with self._api(list_error=error):
                with self.assertRaises(RuntimeError) as ctx:
                    youtube.get_youtube_transcript("abcdefghijk")
                self.assertIn(expected, str(ctx.exception))


# ── DOI citation formatter ──────────────────────────────────────────────────

class TestCitationParser(unittest.TestCase):
    def setUp(self):
        citation._styles_cache = None
        citation._locales_cache = None

    def tearDown(self):
        citation._styles_cache = None
        citation._locales_cache = None

    def test_formats_and_cleans_the_rendering(self):
        body = ("Fennimore, A. (2021). Credit &amp; kinship\n   in the market. "
                "<i>Economic Anthropology</i>, 8(1). https://doi.org/10.1000/xyz\n")
        resp = FakeResponse(text=body, url="https://citation.doi.org/format?doi=10.1000/xyz")
        with patched_get(citation, resp) as get:
            out = citation.format_citation("https://doi.org/10.1000/xyz",
                                           style=" american-anthropological-association ")
        self.assertEqual(get.call_args.kwargs["params"],
                         {"doi": "10.1000/xyz", "style": "american-anthropological-association",
                          "lang": "en-US"})
        self.assertIn("Credit & kinship in the market.", out["citation"])
        self.assertTrue(out["citation"].endswith("10.1000/xyz"))
        self.assertEqual(out["source"], resp.url)

    def test_each_refusal_is_reported_as_what_it_is(self):
        cases = [
            (FakeResponse(status_code=404, text="DOI not found"), ValueError, "not registered"),
            (FakeResponse(status_code=400, text="Metadata could not be retrieved"),
             ValueError, "is registered"),
            (FakeResponse(status_code=400, text="Unknown style ris"),
             citation.UnknownStyleError, "list_citation_styles"),
            (FakeResponse(status_code=400, text="something new"), ValueError, "refused DOI"),
            (FakeResponse(status_code=503, text=""), RuntimeError, "rate-limiting"),
        ]
        for resp, exc, words in cases:
            with patched_get(citation, resp):
                with self.assertRaises(exc) as ctx:
                    citation.format_citation("10.1000/xyz")
                self.assertIn(words, str(ctx.exception))

    def test_unexpected_status_falls_through_to_http_error(self):
        import requests
        with patched_get(citation, FakeResponse(status_code=418, text="teapot")):
            with self.assertRaises(requests.HTTPError):
                citation.format_citation("10.1000/xyz")

    def test_batch_keeps_good_entries_and_stops_on_a_bad_style(self):
        ok = FakeResponse(text="Rendered.")
        missing = FakeResponse(status_code=404, text="DOI not found")
        with patched_get(citation, ok, missing):
            out = citation.format_citation_batch("10.1/a,\n10.1/b, not-a-doi")
        self.assertEqual(out["requested"], 3)
        self.assertEqual([r["doi"] for r in out["formatted"]], ["10.1/a"])
        self.assertEqual([f["doi"] for f in out["failed"]], ["10.1/b", "not-a-doi"])
        bad_style = FakeResponse(status_code=400, text="Unknown style chicago")
        with patched_get(citation, bad_style):
            with self.assertRaises(citation.UnknownStyleError):
                citation.format_citation_batch(["10.1/a", "10.1/b"], style="chicago")

    def test_style_and_locale_lists_are_fetched_once(self):
        styles = FakeResponse(["apa", "american-anthropological-association",
                               "journal-of-the-royal-anthropological-institute"])
        with patched_get(citation, styles) as get:
            first = citation.list_citation_styles("ANTHROPOLOG", limit=1)
            second = citation.list_citation_styles("apa")
        self.assertEqual(get.call_count, 1)
        self.assertEqual(first["matched"], 2)
        self.assertTrue(first["truncated"])
        self.assertEqual(first["styles"], ["american-anthropological-association"])
        self.assertEqual(second["total"], 3)
        with patched_get(citation, FakeResponse(["en-US", "de-DE"])) as get:
            self.assertEqual(datasources.list_citation_locales(), ["de-DE", "en-US"])
            self.assertEqual(citation.list_citation_locales(), ["de-DE", "en-US"])
        self.assertEqual(get.call_count, 1)


# ── The MCP tool wrappers pass their arguments through ──────────────────────

class TestServerDataToolWrappers(unittest.TestCase):
    def test_wrappers_forward_to_the_collectors(self):
        targets = {
            "get_google_trends": (("kinship",), {"timeframe": "today 5-y", "geo": "PL"}),
            "search_google_news": (("credit",), {"limit": 3, "period": "1d",
                                                 "country": "PL", "language": "pl"}),
            "search_google_scholar": (("credit",), {"limit": 2, "year_from": 0,
                                                    "year_to": 2020}),
            "search_google_patents": (("sensor",), {"limit": 4}),
            "get_ngram_frequencies": (("kinship",), {"year_from": 1950, "year_to": 2000,
                                                     "corpus": "en", "case_insensitive": True}),
            "search_youtube": (("fieldwork",), {"limit": 2}),
            "get_youtube_transcript": (("abcdefghijk",), {"languages": ["pl"]}),
            "get_podcast_episodes": (("https://example.test/feed.xml",), {"limit": 5}),
        }
        for name, (args, kwargs) in targets.items():
            with mock.patch.object(server._data, name, return_value=["sentinel"]) as fn:
                self.assertEqual(getattr(server, name)(*args, **kwargs), ["sentinel"])
            self.assertTrue(fn.called, name)
        with mock.patch.object(server._data, "search_google_scholar", return_value=[]) as fn:
            server.search_google_scholar("credit", year_from=0, year_to=0)
        self.assertEqual(fn.call_args.kwargs, {"limit": 5, "year_from": None, "year_to": None})

    def test_pubmed_and_citation_wrappers(self):
        with patched_get(pubmed, FakeResponse({"esearchresult": {"idlist": []}})) as get:
            self.assertEqual(server.search_pubmed("x", year_from=0, journal=""), [])
        self.assertNotIn("mindate", get.call_args.kwargs["params"])
        with patched_get(citation, FakeResponse(text="Rendered.")):
            self.assertEqual(server.format_citation("10.1/a")["citation"], "Rendered.")
        with patched_get(citation, FakeResponse(text="Rendered.")):
            self.assertEqual(server.format_citation_batch(["10.1/a"])["requested"], 1)
        citation._styles_cache = ["apa"]
        try:
            self.assertEqual(server.list_citation_styles("ap")["styles"], ["apa"])
        finally:
            citation._styles_cache = None


if __name__ == "__main__":
    unittest.main()
