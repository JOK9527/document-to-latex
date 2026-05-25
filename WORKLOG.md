# Worklog

## v1.0 - 2026-05-26

### Goal

Create a Codex skill that converts common documents into maintainable LaTeX projects, with special attention to templates, formatting requirements, source preservation, figures, tables, equations, citations, and complex PDFs.

### Major Decisions

- Treat the skill as an AI authoring workflow, not a fixed converter.
- Preserve original source documents, templates, and format guides under `source/`.
- Keep content and style separated.
- Preprocess user templates before inserting converted content.
- For PDFs, build semantic IR before writing LaTeX.
- Generate an authoring brief so the AI can understand the document before writing final chapters.
- Use renderer output only as draft scaffold.
- Keep small and medium tables inline in chapter files.
- Prefer `tblr` for converted tables.
- Use `[H]` when figure/table float movement breaks semantic correspondence.

### Test Case

Template:

- `1195343015/nwputhesis`

Source:

- `航模舵机的动态特性测试与系统辨识.pdf`

Result:

- The early mechanical conversion preserved PDF line breaks, confused formulas and citations, and misplaced images.
- Coordinate-aware insertion improved image clustering but still did not understand target layout.
- Semantic IR plus AI-authored rewriting produced a much better thesis-style conversion.
- Final test version used fixed figure/table placement and inline `tblr` tables.

### Issues Found

- Source PDF two-column line breaks cannot be reused in target single-column LaTeX.
- PDF coordinates cannot determine final figure/table placement.
- Citation fragments such as `[1]` and `[2-6]` can be mistaken for formulas if formula detection is too broad.
- Figure captions and body references must be separated.
- LaTeX `[htbp]` can move figures away from the explanatory text even when source code order is correct.
- Splitting small tables into separate files hurts reviewability.

### Fixes Added

- `build_pdf_semantic_ir.py`
- `write_pdf_authoring_brief.py`
- `render_semantic_ir_to_latex.py` as scaffold only
- `references/layout-aware-pdf-extraction.md`
- `references/authoring-lessons.md`
- README and worklog for v1.0 release context

### Remaining Boundaries

- Scanned PDFs need OCR/VLM quality checks.
- Complex formulas may still require manual reconstruction.
- Bibliography extraction can require manual BibTeX cleanup.
- `[H]` improves semantic placement but can create local whitespace; adjust after content correctness is verified.
