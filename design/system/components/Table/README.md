# Table

Rows of records: the decision log, counts per code, job results.

**Use** a caption that names what the rows are. Mark number columns `numeric` so they right-align with even digits. Put IDs in the `aat-id` style. Wide tables scroll inside their own frame.

**Props** `caption` · `columns`: `[{ key, label, numeric? }]` · `rows`: objects keyed by column (values may be elements).

**Plain HTML** `<div class="aat-table-wrap"><table class="aat-table">…</table></div>`; add `aat-num` to number cells.
