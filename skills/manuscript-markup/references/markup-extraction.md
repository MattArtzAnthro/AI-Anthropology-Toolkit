# Getting the Marks Out of the File

A `.docx` is a zip archive of XML parts. Editorial feedback lives in three
of them, and the one that matters most is the one usually lost.

| Part | Holds |
|---|---|
| `word/comments.xml` | Comment text, author, initials, date |
| `word/document.xml` | `commentRangeStart` and `commentRangeEnd`, which mark the exact span each comment is attached to, plus `w:ins` and `w:del` for tracked changes |
| `word/commentsExtended.xml` | Reply threading and resolved state. Absent in older documents, which is absence rather than failure |

The anchored span is the reason to do this properly. A comment reading
"unclear" is unanswerable in the abstract and often obvious once the
sentence it points at is in view. Pasting a manuscript in as plain text
discards every anchor, every author, and every tracked change, which is why
so many researchers believe this feedback cannot be worked with a model at
all.

## Three ways to read it, in order of preference

**1. The MCP tool.** If the toolkit's MCP server is registered, call
`extract_document_markup` with the path. It returns comments, tracked
changes, and a summary. Nothing else is needed.

**2. The Python package.** If the package is installed but the server is
not:

```python
from ai_anthro_toolkit import markup
data = markup.extract_markup("chapter_v6_edited.docx")
```

**3. The standard-library recipe.** If neither is available, this reads the
same parts with nothing but the standard library. It is deliberately short
enough to run inline.

```python
import re, zipfile, xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
local = lambda t: t.rsplit("}", 1)[-1]

def parse(data):
    # No .docx written by Word declares a DTD, and the standard library's
    # parser expands entities. Refusing a DOCTYPE closes that off without
    # adding a dependency.
    if re.search(rb"<!DOCTYPE", data[:4096], re.I):
        raise ValueError("Document declares a DTD; refusing to parse it.")
    return ET.fromstring(data)

def read_markup(path):
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        doc = parse(z.read("word/document.xml"))
        raw = (parse(z.read("word/comments.xml"))
               if "word/comments.xml" in names else None)

    # Comment text, by id.
    texts = {}
    if raw is not None:
        for c in raw:
            if local(c.tag) != "comment":
                continue
            body = " ".join(t.text or "" for t in c.iter()
                            if local(t.tag) == "t")
            texts[c.get(W + "id")] = {
                "author": c.get(W + "author", ""),
                "date": c.get(W + "date", ""),
                "text": re.sub(r"\s+", " ", body).strip(),
            }

    # Anchors: walk the body in order, buffering text while a range is open.
    open_ranges, anchors = {}, {}
    def walk(node):
        for child in node:
            tag = local(child.tag)
            if tag == "commentRangeStart":
                open_ranges[child.get(W + "id")] = []
            elif tag == "commentRangeEnd":
                buf = open_ranges.pop(child.get(W + "id"), [])
                anchors[child.get(W + "id")] = "".join(buf)
            elif tag == "t":
                for buf in open_ranges.values():
                    buf.append(child.text or "")
                walk(child)
            else:
                walk(child)
    walk(doc)

    return [{"id": cid, **meta,
             "anchor": re.sub(r"\s+", " ", anchors.get(cid, "")).strip()}
            for cid, meta in texts.items()]
```

The recipe omits three things the package does: section headings, reply
threading, and the substantive flag on tracked changes. Say so rather than
presenting the two as equivalent.

## What comes back

Per comment: `id`, `author`, `initials`, `date`, `text`, `anchor`,
`paragraph`, `paragraph_index`, `section`, `parent_id`, `resolved`.

Per tracked change: `kind` (insertion or deletion), `author`, `date`,
`text`, `paragraph_index`, `section`, `substantive`.

`substantive` is false for a change carrying no word of three or more
letters. A comma, a space, or a single-letter fix is a correction rather
than a judgment about the manuscript, and reporting three hundred of them
alongside eleven that matter is how a tracked-changes summary becomes
unreadable.

## Formats and their traps

**Google Docs.** Comments and suggestions survive `File > Download >
Microsoft Word (.docx)` intact. Suggestions arrive as tracked changes.
Download rather than working from the share link.

**PDF annotations.** Not read. Ask for the `.docx`, or work from the PDF
comments transcribed by hand. Do not silently fall back to reading the PDF
body text, which loses every anchor and every author.

**A `.doc` file.** Not read. Ask for a `.docx` export.

**Comments with no span.** Word lets a comment attach to an insertion point,
or to a selection containing only a space. The anchor comes back empty and
the enclosing paragraph stands in for it. `summary["unanchored_count"]`
reports how many. This is common and is not an extraction failure.

**Sections are best-effort.** The section is the nearest preceding paragraph
styled as a heading. A document that fakes its headings with bold body text,
or uses a localized or custom style name, will report no section for most
comments. Report the blank rather than guessing which paragraph was meant to
be a heading.

**Resolved comments.** Word hides them in the interface but keeps them in
the file. They surface here. An editor who resolved their own comment
usually withdrew it, so report resolved comments separately rather than
sorting them with the live ones.

**Multiple markers.** Where a volume editor and a copyeditor have both
worked the file, split the inventory by author before sorting. Two people
marking the same paragraph often disagree, and a merged list hides that.

**Anonymized authors.** Blind review through a document strips author names
to "Author" or an initial. The count by author is then a count of nothing;
say so rather than reporting it.
