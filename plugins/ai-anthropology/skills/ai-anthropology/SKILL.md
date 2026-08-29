---
name: ai-anthropology
description: Route anthropology and qualitative-research work to the toolkit's specialist skills and MCP tools. Use for research design, ethics, fieldwork, qualitative analysis, scholarly data collection, interpretive claims, academic writing, dissemination, teaching, or career materials when anthropology-specific guidance matters.
---

# AI Anthropology Toolkit



Use the narrowest specialist skill that fits the request. Preserve the researcher's stated epistemic stance and follow the Friction by Design gates in the selected skill; do not decide questions that the skill reserves for the researcher.

## Route the work

- Research questions, literature reviews, methodology, plans, and prospectuses: use the matching research-design skill.
- IRB, consent, fieldwork instruments, sampling, and data management: use the matching ethics or fieldwork skill.
- Codebooks, coding, themes, computational methods, and networks of codes: use `qualitative-analysis` or `digital-computational-methods`.
- Claims, generalization, paper planning, drafting, review, proofs, and abstracts: use the matching analysis or writing skill.
- Conferences, public engagement, applied deliverables, teaching, and career materials: use the matching dissemination or career skill.
- Repeated work and new research instruments: use `repeated-work` or `tool-building`; specification and researcher-ratification gates remain mandatory.

## Computational tools

When MCP tools whose names contain `ai-anthropology` are available, use them for data collection and the qualitative-analysis pipeline. The server enforces codebook ratification before coding. After producing a codebook or coded dataset, run `get_artifact_checks` without waiting to be asked; report fired checks as questions, not verdicts, and distinguish undetermined checks from passes.

For the exact tool surface and boundaries, read [references/tool-reference.md](references/tool-reference.md). For domain procedures, read only the references linked by the selected specialist skill.

If the MCP server is unavailable but code execution is available, follow the repository fallback: run the package doctor before data collection, use reachable sources, and route blocked sources to local execution or the corresponding Colab notebook rather than retrying a network policy failure.
