---
name: document-to-latex
description: Convert DOC and DOCX academic papers, theses, reports, and formatting drafts into structured, maintainable LaTeX projects. Use when Codex needs to inspect an imperfect Word document, normalize academic structure, adapt a LaTeX template, honor formatting requirements, preserve figures, tables, formulas, citations, and produce a compilable LaTeX project with review notes.
---

# Document to LaTeX

## Scope

This skill is DOC/DOCX-first. It is for academic papers, theses, graduation projects, reports, and Word-based formatting drafts that need to become clean LaTeX projects.

Use PDF only as optional reference material for visual checking. Do not treat PDF as the primary conversion source in this version.

## Core Principles

- Convert from the editable Word structure whenever possible.
- Treat the source as an imperfect draft, not a perfect specification.
- Ask the minimum preflight questions before doing work, then proceed without repeated interruptions.
- Preserve original materials under `source/`.
- Generate a complete LaTeX project, not only a single `.tex` file.
- Keep content and style separated.
- Adapt to user templates without rewriting template internals unless required for compilation.
- Normalize academic structure: title, metadata, abstract, keywords, chapters, sections, figures, tables, equations, citations, bibliography, appendices, and acknowledgements.
- Rebuild academic tables as LaTeX three-line tables by default; do not preserve Word border styling unless the template or user explicitly requires it.
- Detect source defects and record them instead of silently guessing.
- Compile and repair before delivery whenever the local toolchain supports it.

## Mandatory Preflight

Before extraction or generation, inspect `source/` and ask one compact question unless the answer is already explicit:

```text
Before I start: do you have a LaTeX template or formatting guide to use? If not, I can choose a default. Should I prioritize strict template compliance or clean maintainable LaTeX?
```

Proceed without asking only when the user explicitly says to use defaults, decide for them, or do a quick conversion.

Do not ask a long intake form. Record assumptions in `conversion_report.md`.

## Standard Workflow

1. Inspect `source/` for DOC/DOCX files, templates, format guides, and optional PDF references.
2. Complete the mandatory preflight gate.
3. Run `scripts/detect_document.py` on the primary Word source.
4. For DOCX, run `scripts/build_docx_semantic_ir.py`.
5. Run `scripts/write_docx_authoring_brief.py` and read the brief before writing LaTeX.
6. Analyze and preprocess any user-provided LaTeX template.
7. If no template is provided, choose a default skeleton from `assets/templates/`.
8. Write LaTeX as an editor: clean structure, fix obvious formatting noise, preserve meaning, and mark uncertain conversions.
9. Keep figures, small/medium tables, formulas, and local review notes near the relevant text.
10. Compile if possible.
11. Run `scripts/quality_gate.py`.
12. Write `conversion_report.md` with source defects, assumptions, and manual review items.

## Source Priority

Use sources in this order:

1. `.docx` as the primary editable source.
2. `.doc` only after converting or inspecting it with an available local tool.
3. PDF as optional visual reference only.
4. Typed user instructions and formatting guides as constraints, not content sources unless explicitly requested.

If only PDF is available, explain that PDF-only conversion is outside the active scope of this skill version and ask for DOC/DOCX or permission to produce a limited manual-outline project.

## DOCX Handling

Run `scripts/build_docx_semantic_ir.py` to create a reviewable semantic IR. It extracts:

- paragraph text, styles, heading candidates, and list hints
- tables, rows, cells, merged-cell warnings, and table quality notes
- images and their nearby captions
- OMML/math objects and equation-like paragraphs
- citation-like markers and bibliography candidates
- document defects that affect authoring quality

Run `scripts/write_docx_authoring_brief.py` to convert the IR into an authoring brief. The brief tells the AI what to write, what to fix, and what to flag.

Read `references/docx-workflow.md` before converting DOCX files.

## Imperfect Source Policy

Word documents often contain manual formatting, inconsistent headings, missing figure captions, informal table layouts, copied formulas, mixed punctuation, and incomplete references.

Handle these defects as follows:

- Fix obvious formatting noise when it does not change meaning.
- Infer headings only when numbering, style, and context agree.
- Do not invent missing data, captions, or references.
- Give generated captions only when the image role is clear, and mark them in the report.
- Preserve uncertain formulas as review notes or image fallbacks when editable reconstruction is unsafe.
- Normalize table structure only when the result is faithful and reviewable.
- Convert clear academic tables to three-line tables using template-native table commands or `booktabs` (`\toprule`, `\midrule`, `\bottomrule`). Avoid `\hline` grids copied from Word styling.
- Record unresolved defects in `conversion_report.md`.

## Template Handling

When the user provides a template, preserve it. Identify the main `.tex`, class files, style files, bibliography method, metadata commands, and content insertion points.

Treat most templates as requiring preprocessing. Remove or isolate sample content, stale auxiliary files, absolute paths, and hard-coded metadata before inserting converted content.

Read `references/template-preprocessing.md` and `references/template-adaptation.md` before adapting a user template.

## No Template Handling

When no template is provided, choose a default template from `assets/templates/`:

- `article`: short English or language-neutral papers
- `ctexart`: short Chinese papers
- `report`: long reports
- `thesis-lite`: thesis-like drafts and graduation projects

Copy or recreate the chosen skeleton before writing content. Do not place multiple generated `.tex` files directly under the root of `content/` unless the user explicitly asks for a flat project.

## Content Structure

Use a layered layout:

- `main.tex` assembles the document.
- `source/` stores original DOC/DOCX, optional PDFs, templates, and format guides.
- `content/` stores generated content, figures, tables, chapters, and bibliography.
- `template/` or preserved template files store class, style, layout, fonts, metadata, and bibliography configuration.
- Chapter files contain content only.
- Small and medium tables may remain inline near the related paragraph.
- Table content should be semantic data, not Word visual borders. Use three-line tables by default for academic outputs.
- Figures should use semantic filenames when possible.

Read `references/output-project-structure.md`, `references/chapter-splitting.md`, and `references/content-structure.md` before generating files.

## References

- Read `references/docx-workflow.md` for the active source strategy.
- Read `references/user-guidance.md` before asking preflight questions.
- Read `references/format-requirements.md` when requirements are typed or uploaded.
- Read `references/template-preprocessing.md` before adapting most user templates.
- Read `references/template-adaptation.md` when a user provides a LaTeX template.
- Read `references/output-project-structure.md` before creating the output tree.
- Read `references/chapter-splitting.md` for long documents.
- Read `references/content-structure.md` for figures, tables, data, and style separation.
- Read `references/cross-references.md` for labels, refs, citations, and naming rules.
- Read `references/latex-maintainability.md` for maintainable LaTeX.
- Read `references/chinese-latex.md` for Chinese documents.
- Read `references/troubleshooting.md` when compilation fails.

## Scripts

- `scripts/detect_document.py`: quick source profile.
- `scripts/build_docx_semantic_ir.py`: DOCX semantic IR and defect report.
- `scripts/write_docx_authoring_brief.py`: authoring brief from DOCX IR.
- `scripts/analyze_template.py`: LaTeX template analysis.
- `scripts/extract_format_requirements.py`: formatting requirement extraction.
- `scripts/compile_latex.py`: local compile helper.
- `scripts/quality_gate.py`: delivery checks for structure, mojibake, and missing review artifacts.
- `scripts/write_conversion_report.py`: conversion report writer.
