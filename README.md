# document-to-latex

`document-to-latex` is a Codex skill for converting common documents into structured, maintainable LaTeX projects.

The skill is designed for AI-authored conversion, not mechanical PDF rendering. Extraction scripts provide evidence and scaffolding; the AI should read the source, understand the document, and rewrite it for the target LaTeX template.

## What It Handles

- DOCX, Markdown, HTML, TXT, text PDFs, scanned PDFs, and image-based documents
- user-provided LaTeX templates, Overleaf projects, `.cls`, `.sty`, and `.def` files
- typed format requirements and uploaded format guides
- Chinese and English academic writing
- figures, tables, equations, citations, source preservation, and conversion reports

## Core Workflow

1. Ask for missing context: template, formatting guide, reference sample, and output expectations.
2. Preserve original materials in `source/`.
3. Analyze and preprocess any user template.
4. Build a semantic representation of the source document.
5. For complex PDFs, generate a semantic IR and AI authoring brief.
6. Rewrite content for the target template instead of preserving source line breaks.
7. Place figures, tables, and formulas according to semantic context.
8. Compile, repair, and report uncertain conversions.

## Important Lessons from v1.0 Testing

- PDF coordinates are evidence, not final placement rules.
- Renderer output is only a draft scaffold.
- Final chapters should be AI-authored after reading the source and authoring brief.
- For converted reports and theses, content correspondence matters before float aesthetics.
- Use `[H]` when figure/table float movement makes the PDF misleading.
- Keep small and medium tables inline near the related paragraph.
- Prefer `tblr` for converted tables.
- Never classify citation fragments such as `[1]` or `[2-6]` as formulas.

## Main Scripts

- `scripts/detect_document.py`: source profile.
- `scripts/analyze_template.py`: LaTeX template analysis.
- `scripts/build_pdf_semantic_ir.py`: semantic IR for complex PDFs.
- `scripts/write_pdf_authoring_brief.py`: authoring brief for AI rewriting.
- `scripts/render_semantic_ir_to_latex.py`: draft scaffold generator, not final output.
- `scripts/extract_format_requirements.py`: formatting requirement extraction.
- `scripts/compile_latex.py`: local LaTeX compile helper.
- `scripts/write_conversion_report.py`: conversion report writer.

## Version

Current release target: `v1.0`.

This version was validated against an `nwputhesis` template adaptation and a complex Chinese academic PDF with figures, formulas, tables, and two-column source layout.
