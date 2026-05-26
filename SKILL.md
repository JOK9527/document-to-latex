---
name: doc2latex-for-nwpuers
description: Convert DOCX academic drafts into Northwestern Polytechnical University thesis LaTeX projects using the embedded nwputhesis template. Use when Codex needs to help NWPU undergraduate, master, or PhD students turn imperfect Word drafts into clean, compilable nwputhesis projects with correct structure, metadata, figures, tables, formulas, citations, and review reports.
---

# doc2latex for nwpuers

## Scope

This branch is specialized for Northwestern Polytechnical University students.

- Primary input: `.docx`
- Target template: embedded `nwputhesis`
- Supported thesis types: undergraduate, master, PhD
- PDF: optional visual reference only

Do not ask the user to provide a LaTeX template unless they explicitly want to override the embedded `nwputhesis` template.

## Core Principles

- Use `nwputhesis` by default.
- Ask only for the thesis type before conversion when it is not already clear.
- Treat the Word source as an imperfect academic draft.
- Preserve original materials under `source/`.
- Generate a complete LaTeX project under `project/`.
- Keep content and style separated.
- Use NWPU template-native structure and commands.
- Rebuild academic tables as three-line tables by default.
- Record source defects and assumptions in `conversion_report.md`.
- Avoid repeated mid-process questions; continue with review notes when uncertainty is manageable.

## Mandatory Preflight

Before extraction or generation, inspect `source/` and ask only:

```text
请确认论文类型：本科、硕士、博士？
```

Proceed without asking when the thesis type is already explicit.

For graduate theses, default to academic degree. Ask whether it is professional degree only if the user mentions professional degree, engineering master, 专硕, 工程硕士, or a similar cue.

## Standard Workflow

1. Inspect `source/` for the primary DOCX and optional reference materials.
2. Confirm thesis type: bachelor, master, or PhD.
3. Run `scripts/detect_document.py` on the DOCX source.
4. Run `scripts/build_docx_semantic_ir.py`.
5. Run `scripts/write_docx_authoring_brief.py` and read the brief.
6. Create the target project with `scripts/create_nwputhesis_project.py`.
7. Fill the selected template content directory:
   - bachelor: `content/thesis/undergraduate/`
   - master or PhD: `content/thesis/graduate/`
8. Update metadata in `info.tex`.
9. Write chapters, abstract, references, appendices, acknowledgements, and review notes.
10. Compile if possible.
11. Run `scripts/quality_gate.py`.
12. Write `conversion_report.md`.

## Project Creation

Use:

```bash
python scripts/create_nwputhesis_project.py project --type bachelor --overwrite
python scripts/create_nwputhesis_project.py project --type master --overwrite
python scripts/create_nwputhesis_project.py project --type phd --overwrite
```

For professional-degree graduate theses:

```bash
python scripts/create_nwputhesis_project.py project --type master --professional --overwrite
```

The script deletes unused undergraduate or graduate content from the generated project so the output stays clean.

## Embedded Template Policy

The embedded template is a trimmed copy of `1195343015/nwputhesis`.

Kept:

- `nwputhesis.cls`
- required `infra/*.def`
- required cover, backcover, logo, and school-name assets
- graduate authorization statement placeholder PDF
- minimal undergraduate and graduate content skeletons

Removed:

- GitHub workflow files
- VS Code settings
- QQ group image
- demo screenshot
- verbose sample chapters
- font submodule

Do not reintroduce removed upstream files unless they are needed for compilation or a real NWPU thesis workflow.

## DOCX Handling

Run `scripts/build_docx_semantic_ir.py` to create a semantic IR. It extracts:

- paragraph text, styles, heading candidates, and list hints
- tables, rows, cells, merged-cell warnings, and table quality notes
- images and nearby captions
- OMML/math objects and equation-like paragraphs
- citation-like markers and bibliography candidates
- source defects

Run `scripts/write_docx_authoring_brief.py` and read the brief before writing LaTeX.

## Authoring Rules

- Map Word headings to NWPU chapter and section structure.
- Use template-native abstract, keyword, metadata, bibliography, appendix, acknowledgement, committee, and accomplishment files.
- Convert clear academic tables to three-line tables using `booktabs`.
- Do not preserve Word table border grids unless explicitly required.
- Never omit an extracted Word data table just because it has no caption.
- When a table lacks a caption, infer a conservative provisional caption from nearby text or the table contents, render the table, and record the assumption in `conversion_report.md`.
- Generate missing figure/table captions only when the role is clear, and record that in the report.
- Do not invent missing data, references, formulas, committee members, student numbers, or signatures.
- Keep uncertain formulas and rough tables as review notes when faithful reconstruction is unsafe.
- Put generated figures under `content/figures/`.
- Keep small and medium tables near the related text for reviewability.

## References

- Read `references/nwpuers-workflow.md` first.
- Read `references/docx-workflow.md` for DOCX extraction and authoring.
- Read `references/content-structure.md` for figures and tables.
- Read `references/cross-references.md` for labels and references.
- Read `references/chinese-latex.md` for Chinese text.
- Read `references/troubleshooting.md` when compilation fails.

## Scripts

- `scripts/create_nwputhesis_project.py`: create a clean NWPU thesis project.
- `scripts/detect_document.py`: quick source profile.
- `scripts/build_docx_semantic_ir.py`: DOCX semantic IR and defect report.
- `scripts/write_docx_authoring_brief.py`: authoring brief from DOCX IR.
- `scripts/compile_latex.py`: local compile helper.
- `scripts/quality_gate.py`: delivery checks, including optional DOCX IR table coverage.
- `scripts/write_conversion_report.py`: conversion report writer.
