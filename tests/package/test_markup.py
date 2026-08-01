"""Extraction of comments and tracked changes from a marked-up .docx.

Fixtures are built here rather than committed as binaries, so what each
test asserts is visible in the test itself. A .docx is a zip of XML parts;
only the parts the extractor reads are written.

    python3 -m unittest tests.package.test_markup -v
"""

import tempfile
import unittest
import zipfile
from pathlib import Path

from ai_anthro_toolkit import markup

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
W14 = 'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"'
W15 = 'xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml"'


def build_docx(document_body, comments_body="", extended_body=None):
    """Write a minimal .docx to a temp file and return its path."""
    tmp = Path(tempfile.mkdtemp()) / "fixture.docx"
    with zipfile.ZipFile(tmp, "w") as z:
        z.writestr(
            "word/document.xml",
            f'<?xml version="1.0"?><w:document {W} {W14}><w:body>'
            f"{document_body}</w:body></w:document>",
        )
        if comments_body:
            z.writestr(
                "word/comments.xml",
                f'<?xml version="1.0"?><w:comments {W} {W14}>'
                f"{comments_body}</w:comments>",
            )
        if extended_body:
            z.writestr(
                "word/commentsExtended.xml",
                f'<?xml version="1.0"?><w15:commentsEx {W} {W15}>'
                f"{extended_body}</w15:commentsEx>",
            )
    return str(tmp)


def para(text, style=None, para_id=None):
    props = ""
    if style:
        props = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
    attr = f' w14:paraId="{para_id}"' if para_id else ""
    return f"<w:p{attr}>{props}<w:r><w:t>{text}</w:t></w:r></w:p>"


def comment(cid, author, initials, date, text, para_id=None):
    attr = f' w14:paraId="{para_id}"' if para_id else ""
    return (
        f'<w:comment w:id="{cid}" w:author="{author}" '
        f'w:initials="{initials}" w:date="{date}">'
        f"<w:p{attr}><w:r><w:t>{text}</w:t></w:r></w:p></w:comment>"
    )


class TestComments(unittest.TestCase):
    def test_anchor_is_the_spanned_text_not_the_paragraph(self):
        body = (
            para("Chapter One", style="Heading1")
            + "<w:p><w:r><w:t>Before. </w:t></w:r>"
            '<w:commentRangeStart w:id="1"/>'
            "<w:r><w:t>The claim does not hold.</w:t></w:r>"
            '<w:commentRangeEnd w:id="1"/>'
            "<w:r><w:t> After.</w:t></w:r></w:p>"
        )
        path = build_docx(body, comment("1", "L. Eller", "LE",
                                        "2026-07-31T10:00:00Z",
                                        "Which claim?"))
        result = markup.extract_markup(path)
        self.assertEqual(len(result["comments"]), 1)
        c = result["comments"][0]
        self.assertEqual(c["anchor"], "The claim does not hold.")
        self.assertEqual(c["paragraph"], "Before. The claim does not hold. After.")
        self.assertEqual(c["text"], "Which claim?")
        self.assertEqual(c["author"], "L. Eller")
        self.assertEqual(c["initials"], "LE")
        self.assertEqual(c["section"], "Chapter One")

    def test_anchor_spanning_multiple_runs_is_recovered_whole(self):
        body = (
            "<w:p>"
            '<w:commentRangeStart w:id="7"/>'
            "<w:r><w:t>one </w:t></w:r><w:r><w:t>two </w:t></w:r>"
            "<w:r><w:t>three</w:t></w:r>"
            '<w:commentRangeEnd w:id="7"/>'
            "</w:p>"
        )
        path = build_docx(body, comment("7", "Ed", "E", "", "spans runs"))
        c = markup.extract_markup(path)["comments"][0]
        self.assertEqual(c["anchor"], "one two three")

    def test_anchor_spanning_a_paragraph_boundary_is_recovered_whole(self):
        body = (
            "<w:p>"
            '<w:commentRangeStart w:id="3"/>'
            "<w:r><w:t>end of one</w:t></w:r></w:p>"
            "<w:p><w:r><w:t>start of two</w:t></w:r>"
            '<w:commentRangeEnd w:id="3"/></w:p>'
        )
        path = build_docx(body, comment("3", "Ed", "E", "", "crosses"))
        c = markup.extract_markup(path)["comments"][0]
        self.assertEqual(c["anchor"], "end of one start of two")

    def test_whitespace_only_anchor_reports_no_span_but_keeps_the_paragraph(self):
        """Word lets a comment attach to a point or to a selected space.

        Observed in a real reviewed manuscript: the commenter selected one
        space. There is no quotable span, so the paragraph has to stand in
        for it or the comment becomes undiscussable.
        """
        body = (
            "<w:p><w:r><w:t>Bateson, building on Wiener, </w:t></w:r>"
            '<w:commentRangeStart w:id="5"/>'
            '<w:r><w:t xml:space="preserve"> </w:t></w:r>'
            '<w:commentRangeEnd w:id="5"/>'
            "<w:r><w:t>described something else.</w:t></w:r></w:p>"
        )
        result = markup.extract_markup(
            build_docx(body, comment("5", "Ed", "E", "", "the or is wrong")))
        c = result["comments"][0]
        self.assertEqual(c["anchor"], "")
        self.assertEqual(
            c["paragraph"],
            "Bateson, building on Wiener, described something else.")
        self.assertEqual(result["summary"]["unanchored_count"], 1)

    def test_document_with_no_comments_returns_empty_not_an_error(self):
        path = build_docx(para("Plain prose."))
        result = markup.extract_markup(path)
        self.assertEqual(result["comments"], [])
        self.assertEqual(result["tracked_changes"], [])
        self.assertEqual(result["summary"]["comment_count"], 0)

    def test_orphan_comment_with_no_anchor_still_extracted(self):
        """A comment whose range was lost keeps its text and reports no anchor."""
        path = build_docx(para("Prose."),
                          comment("9", "Ed", "E", "", "floating"))
        c = markup.extract_markup(path)["comments"][0]
        self.assertEqual(c["anchor"], "")
        self.assertEqual(c["text"], "floating")

    def test_reply_threads_and_resolved_state(self):
        body = (
            "<w:p>"
            '<w:commentRangeStart w:id="1"/><w:r><w:t>text</w:t></w:r>'
            '<w:commentRangeEnd w:id="1"/>'
            '<w:commentRangeStart w:id="2"/><w:r><w:t>more</w:t></w:r>'
            '<w:commentRangeEnd w:id="2"/></w:p>'
        )
        comments = (comment("1", "Ed", "E", "", "first", para_id="AAA")
                    + comment("2", "Author", "A", "", "reply", para_id="BBB"))
        extended = (
            '<w15:commentEx w15:paraId="AAA" w15:done="1"/>'
            '<w15:commentEx w15:paraId="BBB" w15:paraIdParent="AAA" '
            'w15:done="0"/>'
        )
        result = markup.extract_markup(build_docx(body, comments, extended))
        by_id = {c["id"]: c for c in result["comments"]}
        self.assertTrue(by_id["1"]["resolved"])
        self.assertIsNone(by_id["1"]["parent_id"])
        self.assertEqual(by_id["2"]["parent_id"], "1")
        self.assertFalse(by_id["2"]["resolved"])

    def test_missing_commentsextended_is_absence_not_failure(self):
        body = ('<w:p><w:commentRangeStart w:id="1"/><w:r><w:t>t</w:t></w:r>'
                '<w:commentRangeEnd w:id="1"/></w:p>')
        c = markup.extract_markup(
            build_docx(body, comment("1", "Ed", "E", "", "x")))["comments"][0]
        self.assertFalse(c["resolved"])
        self.assertIsNone(c["parent_id"])


class TestTrackedChanges(unittest.TestCase):
    def test_insertions_and_deletions_with_authors(self):
        body = (
            para("Methods", style="Heading2")
            + "<w:p>"
            '<w:ins w:author="Ed" w:date="2026-07-31T10:00:00Z">'
            "<w:r><w:t>a fuller account</w:t></w:r></w:ins>"
            '<w:del w:author="Ed" w:date="2026-07-31T10:01:00Z">'
            "<w:r><w:delText>the vague one</w:delText></w:r></w:del>"
            "</w:p>"
        )
        changes = markup.extract_markup(build_docx(body))["tracked_changes"]
        self.assertEqual(len(changes), 2)
        ins, dele = changes
        self.assertEqual(ins["kind"], "insertion")
        self.assertEqual(ins["text"], "a fuller account")
        self.assertEqual(ins["author"], "Ed")
        self.assertEqual(ins["section"], "Methods")
        self.assertTrue(ins["substantive"])
        self.assertEqual(dele["kind"], "deletion")
        self.assertEqual(dele["text"], "the vague one")

    def test_punctuation_only_change_is_not_substantive(self):
        body = ('<w:p><w:ins w:author="Ed" w:date="">'
                "<w:r><w:t>, </w:t></w:r></w:ins></w:p>")
        change = markup.extract_markup(build_docx(body))["tracked_changes"][0]
        self.assertFalse(change["substantive"])

    def test_deleted_text_is_not_counted_as_anchor_text(self):
        """w:delText is struck-through prose; an anchor quotes what remains."""
        body = (
            "<w:p>"
            '<w:commentRangeStart w:id="1"/>'
            "<w:r><w:t>kept </w:t></w:r>"
            '<w:del w:author="Ed" w:date=""><w:r>'
            "<w:delText>cut</w:delText></w:r></w:del>"
            '<w:commentRangeEnd w:id="1"/></w:p>'
        )
        c = markup.extract_markup(
            build_docx(body, comment("1", "Ed", "E", "", "q")))["comments"][0]
        self.assertEqual(c["anchor"], "kept")


class TestSummary(unittest.TestCase):
    def test_counts_by_author_and_section(self):
        body = (
            para("Introduction", style="Heading1")
            + '<w:p><w:commentRangeStart w:id="1"/><w:r><w:t>x</w:t></w:r>'
            '<w:commentRangeEnd w:id="1"/></w:p>'
            + para("Methods", style="Heading1")
            + '<w:p><w:commentRangeStart w:id="2"/><w:r><w:t>y</w:t></w:r>'
            '<w:commentRangeEnd w:id="2"/>'
            '<w:commentRangeStart w:id="3"/><w:r><w:t>z</w:t></w:r>'
            '<w:commentRangeEnd w:id="3"/></w:p>'
        )
        comments = (comment("1", "Ed", "E", "", "a")
                    + comment("2", "Ed", "E", "", "b")
                    + comment("3", "Copyeditor", "C", "", "c"))
        summary = markup.extract_markup(build_docx(body, comments))["summary"]
        self.assertEqual(summary["comment_count"], 3)
        self.assertEqual(summary["by_author"], {"Ed": 2, "Copyeditor": 1})
        self.assertEqual(summary["by_section"],
                         {"Introduction": 1, "Methods": 2})

    def test_non_docx_path_raises_a_readable_error(self):
        tmp = Path(tempfile.mkdtemp()) / "notes.txt"
        tmp.write_text("plain text", encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            markup.extract_markup(str(tmp))
        self.assertIn("docx", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
