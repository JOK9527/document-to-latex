# document-to-latex

`document-to-latex` is a DOC/DOCX-first Codex skill for turning academic Word drafts into structured, maintainable LaTeX projects.

The skill is not a PDF parser. PDF files may be used as optional visual references, but the active conversion path expects an editable Word source.

The workflow should be used for explicit slash-command requests and for plain-language requests such as converting an academic Word thesis draft to LaTeX. Discussion-only requests should stay in planning mode until the user asks to convert or update files.

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
3. Build and save a DOCX semantic IR with `build_docx_semantic_ir.py`.
4. Generate and save a DOCX authoring brief.
5. Analyze and preprocess any user template as a reusable module output.
6. Rewrite the content into the target LaTeX structure.
7. Preserve uncertain figures, tables, and formulas in place with visible review placeholders instead of silently dropping or moving them.
8. Compile when possible.
9. Run the quality gate and save the report.
10. Report source defects, assumptions, and manual review items.

## Design Position

This skill behaves like an academic editing assistant, not a format dumper. It should:

- understand the Word draft before writing LaTeX
- normalize structure without inventing missing facts
- separate content from style
- rebuild academic tables as semantic three-line LaTeX tables instead of copying Word borders
- render extracted DOCX data tables even when the source forgot the table caption
- use template-native commands when adapting a template
- run conversion as loosely coupled modules with saved intermediate artifacts
- resume from any module when its upstream artifacts already exist and remain valid
- mark uncertain tables, formulas, captions, and references for review
- keep uncertain figures, tables, and formulas near their source position with visible review placeholders
- avoid repeated mid-process questions by doing a short preflight first

## V1.3 Focus

- Treat Word formulas as imperfect content rather than reliable formatting.
- Rebuild equation environments, numbering, labels, and references under LaTeX rules.
- Prefer semantic `\label` plus `\eqref` over manual equation numbers copied from Word.
- Keep ordinary examples and proof steps unnumbered while numbering core formulas and later-referenced formulas.
- Use shared formula macros for repeated math shapes so visual form stays consistent across chapters.
- Make the workflow more modular: source profiling, DOCX extraction, authoring brief, template analysis, LaTeX authoring, compilation, quality gate, and reporting each produce saved outputs and can be rerun independently.

## V1.2 Focus

- Detect adjacent or grid-aligned images as possible figure groups before emitting separate figures.
- Support shared captions, separate captions, subfigure labels, or in-place placeholders for ambiguous multi-image regions.
- Keep uncertain content fixed near its source position with visible review warnings.
- Convert WMF/EMF formula images to supported fallbacks when possible; otherwise keep an in-place placeholder and report the issue.
- Warn when image groups are treated as data tables, especially `longtable` blocks containing `\includegraphics`.
- Use balanced quality checks by default, with strict checks available for final delivery.

## Main Scripts

- `scripts/detect_document.py`: source profile.
- `scripts/build_docx_semantic_ir.py`: DOCX semantic IR and defect report.
- `scripts/write_docx_authoring_brief.py`: AI authoring brief from DOCX IR.
- `scripts/analyze_template.py`: LaTeX template analysis.
- `scripts/extract_format_requirements.py`: formatting requirement extraction.
- `scripts/compile_latex.py`: local LaTeX compile helper.
- `scripts/quality_gate.py`: delivery checks, including optional DOCX IR table coverage.
- `scripts/write_conversion_report.py`: conversion report writer.

## Version

Current development target: `v1.3`.

PDF-only conversion is intentionally deferred until a multimodal or MinerU-level layout pipeline is available.
