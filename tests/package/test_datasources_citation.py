"""Live micro-tests for the DOI citation formatter, plus offline coverage of
DOI normalization and the two refusal paths.

The live tests assert structure rather than exact strings: the formatter
renders whatever metadata the registrar currently holds, and that changes
without notice. What must hold is that a known DOI renders, that the two
error classes stay distinguishable, and that a style name is never silently
accepted when it is wrong.

    python3.12 -m unittest tests.package.test_datasources_citation -v
"""

import unittest

from ai_anthro_toolkit.datasources import (
    UnknownStyleError,
    format_citation,
    format_citation_batch,
    list_citation_styles,
)
from ai_anthro_toolkit.datasources.citation import _clean, normalize_doi

# The toolkit's own Zenodo DOI: a DataCite record, so this also covers the
# non-Crossref registrar path.
TOOLKIT_DOI = "10.5281/zenodo.16728812"
NATURE_DOI = "10.1038/nature14539"
# openRxiv metadata carries the newlines and indentation of the XML it was
# pretty-printed into, straight through the formatter and into the title.
RAGGED_DOI = "10.1101/212779"


class TestNormalizeDoi(unittest.TestCase):
    def test_strips_every_wrapper_form(self):
        for wrapped in ("10.1038/nature14539",
                        "  10.1038/nature14539  ",
                        "doi:10.1038/nature14539",
                        "https://doi.org/10.1038/nature14539",
                        "http://dx.doi.org/10.1038/nature14539",
                        "HTTPS://DOI.ORG/10.1038/nature14539"):
            self.assertEqual(normalize_doi(wrapped).lower(), NATURE_DOI)

    def test_preserves_suffix_case(self):
        self.assertEqual(normalize_doi("https://doi.org/10.5281/ZENODO.123"),
                         "10.5281/ZENODO.123")

    def test_rejects_non_doi_input(self):
        for bad in ("", "   ", "nature14539", "https://example.com/paper"):
            with self.assertRaises(ValueError):
                normalize_doi(bad)


class TestClean(unittest.TestCase):
    def test_decodes_entities_and_collapses_whitespace(self):
        self.assertEqual(_clean("  Science, Technology, &amp;\n   Human Values "),
                         "Science, Technology, & Human Values")

    def test_leaves_ordinary_text_alone(self):
        text = "Harvey, Matthew. 2008. \u201cDrama, Talk, and Emotion.\u201d"
        self.assertEqual(_clean(text), text)


class TestFormatCitationLive(unittest.TestCase):
    def test_renders_a_crossref_doi(self):
        rec = format_citation(NATURE_DOI, style="apa")
        self.assertEqual(rec["doi"], NATURE_DOI)
        self.assertEqual(rec["style"], "apa")
        self.assertEqual(rec["locale"], "en-US")
        self.assertIn("LeCun", rec["citation"])
        self.assertIn("2015", rec["citation"])
        self.assertTrue(rec["source"].startswith("https://citation.doi.org/"))

    def test_renders_a_datacite_doi(self):
        rec = format_citation(f"https://doi.org/{TOOLKIT_DOI}", style="apa")
        self.assertEqual(rec["doi"], TOOLKIT_DOI)
        self.assertIn("Artz", rec["citation"])

    def test_style_actually_changes_the_rendering(self):
        """A style argument that is accepted but ignored would be worse than
        one that errors, because nothing downstream could tell."""
        apa = format_citation(NATURE_DOI, style="apa")["citation"]
        aaa = format_citation(
            NATURE_DOI,
            style="american-anthropological-association")["citation"]
        self.assertNotEqual(apa, aaa)

    def test_citation_is_stripped_of_surrounding_whitespace(self):
        """Several styles, AAA among them, emit a leading newline."""
        rec = format_citation(
            NATURE_DOI, style="american-anthropological-association")
        self.assertEqual(rec["citation"], rec["citation"].strip())
        self.assertTrue(rec["citation"])

    def test_html_entities_are_decoded(self):
        """The formatter HTML-escapes ampersands, so a journal title like
        "Science, Technology, & Human Values" arrives as "&amp;" and would
        otherwise be pasted into a manuscript that way."""
        rec = format_citation("10.1177/0162243907309632", style="apa")
        self.assertIn("Science, Technology, & Human Values", rec["citation"])
        self.assertNotIn("&amp;", rec["citation"])

    def test_bibtex_is_a_style_but_ris_and_csl_are_not(self):
        """Checked against the live formatter rather than assumed: only one
        of the three machine-readable names anyone reaches for is real."""
        self.assertTrue(format_citation(NATURE_DOI, style="bibtex")["citation"]
                        .lstrip().startswith("@article"))
        for absent in ("ris", "csl"):
            with self.assertRaises(ValueError, msg=f"{absent} unexpectedly accepted"):
                format_citation(NATURE_DOI, style=absent)

    def test_unknown_doi_and_unknown_style_raise_distinct_messages(self):
        with self.assertRaises(ValueError) as bad_doi:
            format_citation("10.9999/not-a-real-doi-abc123", style="apa")
        msg = str(bad_doi.exception)
        self.assertIn("not registered", msg)
        self.assertNotIn("list_citation_styles", msg)

        with self.assertRaises(ValueError) as bad_style:
            format_citation(NATURE_DOI, style="chicago-note-bibliography")
        msg = str(bad_style.exception)
        self.assertIn("list_citation_styles", msg)
        self.assertIn("Unknown style", msg)
        self.assertNotIn("not registered", msg)

    def test_unregistered_is_never_reported_as_a_metadata_gap(self):
        """These are different facts about a reference. Calling a registered
        work unregistered tells a researcher a real source is fake, and the
        formatter returns 404 for both, so only the body separates them."""
        with self.assertRaises(ValueError) as e:
            format_citation("10.9999/not-a-real-doi-abc123", style="apa")
        self.assertNotIn("is registered", str(e.exception))


class TestRaggedMetadataLive(unittest.TestCase):
    def test_embedded_newlines_do_not_reach_the_citation(self):
        """The registrar's XML indentation is not part of the title, and a
        citation carrying a line break mid-title is broken where it is
        pasted. The raw response genuinely contains them, so this test is
        worthless unless that stays true — assert it does."""
        import requests
        raw = requests.get("https://citation.doi.org/format",
                           params={"doi": RAGGED_DOI, "style": "apa",
                                   "lang": "en-US"}, timeout=30).text
        self.assertIn("\n", raw.strip(),
                      "source artifact gone; this test no longer proves anything")

        rec = format_citation(RAGGED_DOI, style="apa")
        self.assertNotIn("\n", rec["citation"])
        self.assertNotIn("  ", rec["citation"])
        self.assertIn("Nearly Neutral Evolution Across the Drosophila "
                      "melanogaster Genome", rec["citation"])

    def test_bibtex_ragged_metadata_is_cleaned_too(self):
        rec = format_citation(RAGGED_DOI, style="bibtex")
        self.assertNotIn("\n", rec["citation"])
        self.assertTrue(rec["citation"].startswith("@misc"))


class TestFormatCitationBatchLive(unittest.TestCase):
    def test_formats_every_doi_in_input_order(self):
        result = format_citation_batch([NATURE_DOI, TOOLKIT_DOI], style="apa")
        self.assertEqual(result["requested"], 2)
        self.assertEqual(result["failed"], [])
        self.assertEqual([r["doi"] for r in result["formatted"]],
                         [NATURE_DOI, TOOLKIT_DOI])

    def test_one_bad_doi_does_not_discard_the_good_ones(self):
        result = format_citation_batch(
            [NATURE_DOI, "10.9999/not-a-real-doi-abc123", TOOLKIT_DOI])
        self.assertEqual(len(result["formatted"]), 2)
        self.assertEqual(len(result["failed"]), 1)
        self.assertEqual(result["failed"][0]["doi"], "10.9999/not-a-real-doi-abc123")
        self.assertTrue(result["failed"][0]["reason"])

    def test_malformed_input_is_a_failure_row_not_an_exception(self):
        result = format_citation_batch([NATURE_DOI, "not-a-doi-at-all"])
        self.assertEqual(len(result["formatted"]), 1)
        self.assertEqual(len(result["failed"]), 1)

    def test_accepts_a_delimited_string(self):
        result = format_citation_batch(f"{NATURE_DOI}, {TOOLKIT_DOI}")
        self.assertEqual(result["requested"], 2)
        self.assertEqual(len(result["formatted"]), 2)

    def test_unknown_style_raises_rather_than_failing_every_row(self):
        """A style error is not a fact about any DOI. Recording it once per
        entry would bury one cause under N identical rows."""
        with self.assertRaises(UnknownStyleError):
            format_citation_batch([NATURE_DOI, TOOLKIT_DOI],
                                  style="chicago-note-bibliography")

    def test_style_error_is_typed_not_message_matched(self):
        """The batch used to decide this by searching the exception text,
        which broke silently the moment the wording changed. The type is
        what it keys on now, so assert the type is actually raised."""
        with self.assertRaises(UnknownStyleError):
            format_citation(NATURE_DOI, style="not-a-real-style-xyz")
        self.assertTrue(issubclass(UnknownStyleError, ValueError))


class TestListCitationStylesLive(unittest.TestCase):
    def test_filter_finds_the_anthropology_styles(self):
        result = list_citation_styles("anthropolog", limit=50)
        self.assertGreater(result["total"], 1000)
        self.assertIn("american-anthropological-association", result["styles"])
        self.assertEqual(result["matched"], len(result["styles"]))
        self.assertFalse(result["truncated"])

    def test_truncation_is_reported_not_silent(self):
        result = list_citation_styles("chicago", limit=3)
        self.assertEqual(len(result["styles"]), 3)
        self.assertGreater(result["matched"], 3)
        self.assertTrue(result["truncated"])

    def test_every_returned_name_is_a_usable_style(self):
        """The point of this tool is that format_citation will accept what it
        returns; a name that 400s would make the lookup worthless."""
        name = list_citation_styles("journal-of-the-royal-anthropological",
                                    limit=1)["styles"][0]
        rec = format_citation(NATURE_DOI, style=name)
        self.assertTrue(rec["citation"])


if __name__ == "__main__":
    unittest.main()
