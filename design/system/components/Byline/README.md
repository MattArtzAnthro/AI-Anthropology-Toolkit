# Byline

The colophon every toolkit page ends with: the toolkit and its author, linked to the author's website; "· v{version}" naming the version that built the page (left out without a version); and the links to the website, the toolkit on GitHub, its citation DOI, and the author's ORCID.

**Use**
- Every toolkit page ends with a Byline. In a chat panel, the short form; on a full page or an exported record, `full` adds the author's one-sentence description between the credit and the links.
- This is the toolkit's only branding. Inside someone's chat, everything else follows the system.
- Never remove or reword it; it ships with the toolkit's licence and citation.
- Python pages render the same markup with `ai_anthro_toolkit.brand.byline_html(version, full=...)`.

**Props** `version` · `full`.

**Plain HTML** (the short form)
```html
<footer class="aat-byline"><a href="https://www.mattartz.me" target="_blank" rel="noopener"><b>AI Anthropology Toolkit</b> by Matt Artz</a>
  <span class="aat-byline__sep" aria-hidden="true">·</span>
  <span class="aat-id">v3.11.1</span>
  <a href="https://www.mattartz.me" target="_blank" rel="noopener">Website</a>
  <a href="https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit" target="_blank" rel="noopener">Toolkit on GitHub</a>
  <a href="https://doi.org/10.5281/zenodo.16728812" target="_blank" rel="noopener">Cite (DOI)</a>
  <a href="https://orcid.org/0000-0002-3822-1429" target="_blank" rel="noopener">ORCID</a></footer>
```
