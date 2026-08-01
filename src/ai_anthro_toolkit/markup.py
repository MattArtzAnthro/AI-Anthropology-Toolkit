"""Read comments and tracked changes out of a marked-up .docx.

A .docx is a zip of XML parts. Editorial feedback lives in three of them:
`word/comments.xml` holds the comment text, `word/document.xml` holds the
`commentRangeStart`/`commentRangeEnd` markers that say which span each
comment is attached to, and `word/commentsExtended.xml` holds reply
threading and resolved state. The anchor is the part that matters and the
part most often lost: it is what lets a comment be discussed against the
sentence it points at rather than against a summary of the document.

Standard library only, so this works wherever Python does and adds no
dependency to the package.
"""

from __future__ import annotations

import re
import zipfile
from collections import Counter

import xml.etree.ElementTree as ET

_MAIN = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
_W15 = "http://schemas.microsoft.com/office/word/2012/wordml"

_ID = f"{{{_MAIN}}}id"
_VAL = f"{{{_MAIN}}}val"
_AUTHOR = f"{{{_MAIN}}}author"
_INITIALS = f"{{{_MAIN}}}initials"
_DATE = f"{{{_MAIN}}}date"
_PARA_ID = f"{{{_W14}}}paraId"
_EX_PARA_ID = f"{{{_W15}}}paraId"
_EX_PARENT = f"{{{_W15}}}paraIdParent"
_EX_DONE = f"{{{_W15}}}done"

# A change carrying no word of three or more characters is punctuation,
# spacing, or a single-letter fix. Those are corrections; they are not
# judgments about the manuscript, and grouping them with the ones that are
# is what makes a tracked-changes summary unreadable.
_SUBSTANTIVE = re.compile(r"[^\W\d_]{3,}", re.UNICODE)


_DOCTYPE = re.compile(rb"<!DOCTYPE", re.IGNORECASE)


def _parse_xml(data: bytes):
    """Parse an OOXML part, refusing any document that declares a DTD.

    The standard library's parser expands internal entities, which is the
    billion-laughs exposure, and a DTD is also the route to external
    entity references. Word emits no DOCTYPE in any part of a .docx, so a
    document that carries one is either not from Word or has been built to
    be parsed rather than read. `defusedxml` would close this too, at the
    cost of a dependency this module exists to avoid.
    """
    if _DOCTYPE.search(data[:4096]):
        raise ValueError(
            "This document declares a DTD, which no .docx written by Word "
            "does. Refusing to parse it.")
    return ET.fromstring(data)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _paragraph_style(node) -> str:
    for child in node:
        if _local(child.tag) == "pPr":
            for prop in child:
                if _local(prop.tag) == "pStyle":
                    return prop.get(_VAL, "")
    return ""


def _is_heading(style: str) -> bool:
    return style.lower().startswith(("heading", "title", "subtitle"))


class _Reader:
    """Walks the document body once, in order, accumulating three things.

    The paragraph buffer, one open buffer per comment range currently
    open, and one buffer per tracked change currently being read. Deleted
    text feeds only the change buffer: struck-through prose is not part of
    the paragraph a reader sees, and quoting it back as an anchor would
    quote text that is on its way out of the manuscript.
    """

    def __init__(self):
        self.section = ""
        self.paragraph_index = 0
        self._paragraph = []
        self._paragraph_style = ""
        self._open = {}
        self._change_stack = []
        self.anchors = {}
        self.changes = []

    def walk(self, node) -> None:
        for child in node:
            tag = _local(child.tag)
            if tag == "p":
                self._start_paragraph(child)
                self.walk(child)
                self._end_paragraph()
            elif tag == "commentRangeStart":
                self._open_range(child.get(_ID, ""))
            elif tag == "commentRangeEnd":
                self._close_range(child.get(_ID, ""))
            elif tag in ("ins", "del"):
                kind = "insertion" if tag == "ins" else "deletion"
                self._change_stack.append({
                    "kind": kind,
                    "author": child.get(_AUTHOR, ""),
                    "date": child.get(_DATE, ""),
                    "parts": [],
                    "paragraph_index": max(self.paragraph_index, 1),
                    "section": self.section,
                })
                self.walk(child)
                self._end_change()
            elif tag == "t":
                self._text(child.text or "", deleted=False)
            elif tag == "delText":
                self._text(child.text or "", deleted=True)
            else:
                self.walk(child)

    def _start_paragraph(self, node) -> None:
        self.paragraph_index += 1
        self._paragraph = []
        self._paragraph_style = _paragraph_style(node)

    def _end_paragraph(self) -> None:
        text = _clean("".join(self._paragraph))
        for record in self.anchors.values():
            if record["paragraph_index"] == self.paragraph_index:
                record["paragraph"] = text
        # A range left open across a paragraph break needs the break to
        # survive as a space, or the last word of one paragraph fuses to
        # the first word of the next.
        for buffer in self._open.values():
            buffer.append(" ")
        if _is_heading(self._paragraph_style) and text:
            self.section = text

    def _open_range(self, cid: str) -> None:
        if not cid or cid in self.anchors:
            return
        self._open[cid] = []
        self.anchors[cid] = {
            "paragraph_index": max(self.paragraph_index, 1),
            "section": self.section,
            "paragraph": "",
            "anchor": "",
        }

    def _close_range(self, cid: str) -> None:
        buffer = self._open.pop(cid, None)
        if buffer is not None:
            self.anchors[cid]["anchor"] = _clean("".join(buffer))

    def _text(self, text: str, deleted: bool) -> None:
        if self._change_stack:
            self._change_stack[-1]["parts"].append(text)
        if deleted:
            return
        self._paragraph.append(text)
        for buffer in self._open.values():
            buffer.append(text)

    def _end_change(self) -> None:
        record = self._change_stack.pop()
        text = _clean("".join(record.pop("parts")))
        record["text"] = text
        record["substantive"] = bool(_SUBSTANTIVE.search(text))
        self.changes.append(record)


def _read_comments(xml_bytes: bytes) -> list[dict]:
    root = _parse_xml(xml_bytes)
    comments = []
    for node in root:
        if _local(node.tag) != "comment":
            continue
        paragraphs = [p for p in node.iter() if _local(p.tag) == "p"]
        text = _clean(" ".join(
            t.text or "" for t in node.iter() if _local(t.tag) == "t"))
        para_id = ""
        for p in paragraphs:
            para_id = p.get(_PARA_ID, "") or para_id
        comments.append({
            "id": node.get(_ID, ""),
            "author": node.get(_AUTHOR, ""),
            "initials": node.get(_INITIALS, ""),
            "date": node.get(_DATE, ""),
            "text": text,
            "_para_id": para_id,
        })
    return comments


def _read_extended(xml_bytes: bytes) -> dict[str, dict]:
    root = _parse_xml(xml_bytes)
    entries = {}
    for node in root:
        if _local(node.tag) != "commentEx":
            continue
        para_id = node.get(_EX_PARA_ID, "")
        if para_id:
            entries[para_id] = {
                "parent": node.get(_EX_PARENT, ""),
                "done": node.get(_EX_DONE, "0") in ("1", "true", "True"),
            }
    return entries


def extract_markup(path: str) -> dict:
    """Extract comments, anchors, and tracked changes from a .docx.

    Returns `{"comments": [...], "tracked_changes": [...], "summary": {...}}`.
    Each comment carries the span it is anchored to, the paragraph and
    section containing that span, its reply parent, and whether it has been
    marked resolved. Documents with no comments return empty lists rather
    than raising, and a missing `commentsExtended.xml` is read as absence
    of threading rather than as a failure.
    """
    if not zipfile.is_zipfile(path):
        raise ValueError(
            f"{path} is not a .docx file (a .docx is a zip archive). "
            "Export from Google Docs or Word as .docx first; PDF "
            "annotations are not read by this extractor.")

    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        if "word/document.xml" not in names:
            raise ValueError(
                f"{path} is a zip archive but not a .docx: no "
                "word/document.xml inside it.")
        document = archive.read("word/document.xml")
        comments_xml = (archive.read("word/comments.xml")
                        if "word/comments.xml" in names else b"")
        extended_xml = (archive.read("word/commentsExtended.xml")
                        if "word/commentsExtended.xml" in names else b"")

    reader = _Reader()
    reader.walk(_parse_xml(document))

    raw = _read_comments(comments_xml) if comments_xml else []
    extended = _read_extended(extended_xml) if extended_xml else {}
    by_para_id = {c["_para_id"]: c["id"] for c in raw if c["_para_id"]}

    comments = []
    for record in raw:
        anchor = reader.anchors.get(record["id"], {})
        thread = extended.get(record.pop("_para_id"), {})
        parent = by_para_id.get(thread.get("parent", ""))
        comments.append({
            **record,
            "anchor": anchor.get("anchor", ""),
            "paragraph": anchor.get("paragraph", ""),
            "paragraph_index": anchor.get("paragraph_index", 0),
            "section": anchor.get("section", ""),
            "parent_id": parent if parent != record["id"] else None,
            "resolved": thread.get("done", False),
        })

    substantive = [c for c in reader.changes if c["substantive"]]
    summary = {
        "comment_count": len(comments),
        "tracked_change_count": len(reader.changes),
        "substantive_change_count": len(substantive),
        "by_author": dict(Counter(c["author"] for c in comments)),
        "by_section": dict(Counter(c["section"] for c in comments if c["section"])),
        "change_authors": dict(Counter(c["author"] for c in reader.changes)),
        "unresolved_count": sum(1 for c in comments if not c["resolved"]),
        # Word lets a comment attach to an insertion point, or to a
        # selection that is only whitespace. Those carry no quotable span,
        # and the enclosing paragraph is what stands in for it.
        "unanchored_count": sum(1 for c in comments if not c["anchor"]),
    }
    return {"comments": comments,
            "tracked_changes": reader.changes,
            "summary": summary}
