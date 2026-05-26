# document-to-latex

`document-to-latex` is a DOC/DOCX-first Codex skill for turning academic Word drafts into structured, maintainable LaTeX projects.

The skill is not a PDF parser. PDF files may be used as optional visual references, but the active conversion path expects an editable Word source.

## What It Handles

- `.docx` academic papers, theses, graduation projects, and reports
- `.doc` files when a local conversion or inspection tool is available
- user-provided LaTeX templates, Overleaf projects, `.cls`, `.sty`, and `.def` files
- typed formatting requirements and uploaded formatting guides
- imperfect Word drafts with inconsistent headings, rough tables, missing captions, mixed formulas, or incomplete references
- Chinese and English academic writing

## Core Workflow

1. Ask the mandatory preflight question unless the user already answered it.
2. Preserve original materials in `source/`.
3. Build a DOCX semantic IR with `build_docx_semantic_ir.py`.
4. Generate and read a DOCX authoring brief.
5. Analyze and preprocess any user template.
6. Rewrite the content into the target LaTeX structure.
7. Compile when possible.
8. Run the quality gate.
9. Report source defects, assumptions, and manual review items.

## Design Position

This skill behaves like an academic editing assistant, not a format dumper. It should:

- understand the Word draft before writing LaTeX
- normalize structure without inventing missing facts
- separate content from style
- rebuild academic tables as semantic three-line LaTeX tables instead of copying Word borders
- use template-native commands when adapting a template
- mark uncertain tables, formulas, captions, and references for review
- avoid repeated mid-process questions by doing a short preflight first

## Main Scripts

- `scripts/detect_document.py`: source profile.
- `scripts/build_docx_semantic_ir.py`: DOCX semantic IR and defect report.
- `scripts/write_docx_authoring_brief.py`: AI authoring brief from DOCX IR.
- `scripts/analyze_template.py`: LaTeX template analysis.
- `scripts/extract_format_requirements.py`: formatting requirement extraction.
- `scripts/compile_latex.py`: local LaTeX compile helper.
- `scripts/quality_gate.py`: delivery checks.
- `scripts/write_conversion_report.py`: conversion report writer.

## Version

Current development target: `v1.1-docx`.

PDF-only conversion is intentionally deferred until a multimodal or MinerU-level layout pipeline is available.
