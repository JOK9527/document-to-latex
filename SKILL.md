---
name: document-to-latex
description: Convert common documents into structured, compilable LaTeX projects. Use when Codex needs to convert DOCX, Markdown, HTML, TXT, PDF, scanned documents, images, reports, theses, papers, or lecture notes into LaTeX; adapt user-provided LaTeX templates; honor typed format requirements or uploaded formatting guides; preserve structure, figures, tables, formulas, citations, and produce compilation reports.
---

# Document to LaTeX

## Core Principles

- Preserve semantic structure before visual layout unless the user explicitly asks for layout replication.
- Prefer explicit user instructions over templates, uploaded format guides, and skill defaults.
- Generate a complete LaTeX project, not only a single `.tex` file.
- Keep content and style separated at both project and chapter level.
- Add concise comments at generated boundaries, template adaptation points, and uncertain conversions.
- Proactively create labels and references for figures, tables, equations, sections, algorithms, listings, and citations.
- For PDFs, build semantic structure first; use layout coordinates to support extraction, not to blindly copy source placement.
- Treat script output as evidence and draft scaffolding. The final PDF conversion must be authored by the AI like an editor who has read and understood the document, not mechanically emitted from extractor output.
- For converted reports, papers, and theses, prioritize content correspondence over float aesthetics: place figures and tables near the text that explains them, use `[H]` when needed to prevent misleading float movement, and only relax float placement after semantic correctness is verified.
- Keep small and medium tables in the chapter source near the paragraph that discusses them. Prefer `tblr` for maintainable converted tables unless the target template already prescribes another table system.
- Compile and repair before delivery whenever the local toolchain supports it.
- Report uncertain OCR, formula, table, reference, and layout conversions.

## Standard Workflow

1. Identify the source document type and complexity.
2. Guide the user to provide missing conversion context when it is not already clear.
3. Collect external constraints:
   - typed formatting requirements in the user request
   - uploaded formatting guides
   - user-provided LaTeX templates
4. Preprocess any user-provided template unless it is already clean, complete, and compilable.
5. Merge constraints by priority.
6. Choose the conversion strategy for the source format.
7. For complex PDFs, build and review a semantic IR before writing LaTeX.
8. Write an authoring brief that explains section intent, paragraph flow, figure/table/formula roles, and unresolved risks.
9. Choose or preserve the output project structure.
10. Convert content into semantic LaTeX by rewriting for the target template, not by preserving source line breaks.
11. Split long content into chapters and sections. Keep local tables inline unless they are too large to review comfortably.
12. Adapt content to the preprocessed user template, or apply a default template.
13. Compile the project and repair common failures.
14. Write a conversion report with risks and manual review items.

## User Guidance

Before converting, ask only for missing information that materially affects the output. Prefer short, practical questions over long questionnaires.

Ask whether the user has:

- a LaTeX template, Overleaf zip, `.cls`, `.sty`, `.def`, or existing project
- a formatting guide, school or journal specification, PDF sample, or reference document
- typed format requirements such as page size, margins, bibliography style, language, compiler, and chapter structure
- a preference for faithful layout replication versus maintainable semantic LaTeX

If the user wants a quick default conversion, proceed with defaults and record assumptions in `conversion_report.md`.

Read `references/user-guidance.md` when the request lacks template, format, or output-structure context.

## Constraint Priority

Apply constraints in this order:

1. Explicit user instruction in the current request
2. User-provided LaTeX template
3. Uploaded formatting guide or specification document
4. Skill defaults

When constraints conflict, follow the highest-priority constraint and record the conflict in `conversion_report.md`.

## Template Handling

When the user provides a template, preserve its structure. Identify the main `.tex`, class files, style files, bibliography method, and content insertion points. Insert converted content into template-compatible files rather than rewriting template internals.

Treat most templates as requiring preprocessing. Templates from schools, journals, Overleaf, GitHub, or prior projects may contain sample content, absolute paths, hard-coded metadata, stale auxiliary files, missing assets, duplicate package loading, or unclear entry points. Normalize these issues before inserting converted content.

Preprocessing is layered: always extract the template profile, usually perform non-destructive cleanup, and only minimally restructure when the template cannot otherwise receive converted content or compile reliably.

Skip preprocessing only when the template is already minimal, complete, clearly structured, and successfully compiles in the target environment.

Read `references/template-preprocessing.md` before adapting a user template.
Read `references/template-adaptation.md` before modifying or adapting a user template.

## No Template Handling

When no template is provided, choose a default template from `assets/templates/`:

- `article`: short English or language-neutral documents
- `ctexart`: Chinese short documents
- `report`: long reports with chapters
- `thesis-lite`: thesis-like documents, graduation projects, and long academic drafts

Keep default templates small and maintainable. Put global style in template files and content in `content/`.

## Content Structure

Use a layered project layout:

- `main.tex` assembles the document.
- `source/` stores original uploaded source documents, templates, and format guides for traceability.
- `content/` stores user content, figures, tables, chapters, and bibliography.
- `template/` or the preserved user template stores class, style, layout, fonts, metadata, and bibliography configuration.
- Chapter files contain content only. Do not scatter global style commands inside chapters.
- Large or important tables should live in `content/tables/<chapter>/` and may keep source data next to generated LaTeX.
- Small and medium tables may remain inline in chapter files to preserve review context. Prefer `tblr` for converted tables because column widths, wrapping, and alignment are easier to adjust.
- Figures should live in `content/figures/<chapter>/` with semantic filenames when possible.

Do not mix original uploads into `content/` or template directories. Copy or record original materials under `source/`; generate editable LaTeX outputs under `content/`.

Read `references/output-project-structure.md`, `references/chapter-splitting.md`, and `references/content-structure.md` when generating project files.

## References

- Read `references/conversion-workflow.md` for source-specific conversion strategy.
- Read `references/layout-aware-pdf-extraction.md` before converting PDFs with figures, tables, formulas, or multi-column layout.
- Read `references/user-guidance.md` when user intent, template availability, or format requirements are incomplete.
- Read `references/format-requirements.md` when requirements are typed or uploaded.
- Read `references/template-preprocessing.md` before adapting most user-provided templates.
- Read `references/template-adaptation.md` when a user provides a LaTeX template.
- Read `references/output-project-structure.md` before creating the output tree.
- Read `references/chapter-splitting.md` for long documents.
- Read `references/content-structure.md` for chapter-level figures, tables, data, and style separation.
- Read `references/cross-references.md` for labels, refs, citations, and naming rules.
- Read `references/latex-maintainability.md` for comments and maintainable LaTeX structure.
- Read `references/authoring-lessons.md` before finalizing AI-authored conversions from complex PDFs.
- Read `references/chinese-latex.md` for Chinese documents.
- Read `references/troubleshooting.md` when compilation fails.

## Scripts

- Use `scripts/detect_document.py` to produce a quick JSON profile of source documents.
- Use `scripts/analyze_template.py` to inspect user-provided LaTeX templates before adaptation.
- Use `scripts/build_pdf_semantic_ir.py` before converting complex PDFs with figures, tables, formulas, or multi-column layout.
- Use `scripts/write_pdf_authoring_brief.py` to create the brief the AI reads before authoring final LaTeX.
- Use `scripts/render_semantic_ir_to_latex.py` only to create a draft scaffold from reviewed PDF semantic IR. Do not treat renderer output as final without AI rewriting and source comparison.
- Use `scripts/extract_format_requirements.py` to extract likely formatting requirements from typed notes or guide text.
- Use `scripts/compile_latex.py` to compile generated projects and capture logs.
- Use `scripts/write_conversion_report.py` to create `conversion_report.md` from conversion metadata and warnings.
