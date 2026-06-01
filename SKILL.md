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

Use this skill for explicit slash-command requests and for plain-language requests to convert a Word/DOCX academic draft into LaTeX. If the user is only discussing conversion strategy, do not start the workflow until they ask to convert or update files.

## Core Principles

- Use `nwputhesis` by default.
- Ask only for the thesis type before conversion when it is not already clear.
- Treat the Word source as an imperfect academic draft.
- Preserve original materials under `source/`.
- Generate a complete LaTeX project under `project/`.
- Keep content and style separated.
- Run the workflow as modular, resumable stages with saved intermediate artifacts.
- Keep AI judgment central: scripts provide evidence and guardrails, while the AI makes context-aware NWPU thesis authoring decisions.
- Use NWPU template-native structure and commands.
- Treat Word formulas as imperfect content, not reliable formatting; rebuild equation environments, numbering, labels, and references under LaTeX and `nwputhesis` rules.
- Rebuild academic tables as three-line tables by default.
- Preserve figure, table, and formula positions when conversion confidence is low.
- Record source defects and assumptions in `conversion_report.md`.
- Avoid repeated mid-process questions; continue with review notes when uncertainty is manageable.

## Mandatory Preflight

Before extraction or generation, inspect `source/` and ask only:

```text
璇风‘璁よ鏂囩被鍨嬶細鏈銆佺澹€佸崥澹紵
```

Proceed without asking when the thesis type is already explicit.

For graduate theses, default to academic degree. Ask whether it is professional degree only if the user mentions professional degree, engineering master, 涓撶, 宸ョ▼纭曞＋, or a similar cue.

## Standard Workflow

1. Inspect `source/` for the primary DOCX and optional reference materials.
2. Confirm thesis type: bachelor, master, or PhD, and record `work/thesis_type_decision.md`.
3. Run `scripts/detect_document.py` on the primary Word source and save `work/document_profile.json`.
4. For legacy `.doc`, run the `.doc` conversion fallback chain before extraction and save `work/doc_conversion_report.json`.
5. Run `scripts/build_docx_semantic_ir.py` and save the IR, summary, and extracted assets.
6. If detection or IR shows likely UTF-8/GBK mojibake, inspect repair candidates before authoring; apply only high-confidence repairs and record risky symbol substitutions for review.
7. Run `scripts/write_docx_authoring_brief.py`, save `work/docx_authoring_brief.md`, and read the brief.
8. Create the target project with `scripts/create_nwputhesis_project.py`, using the thesis-type decision as a reusable module input.
9. Write `work/authoring_plan.md` from the saved IR, brief, NWPU project decision, and user constraints.
10. Fill the selected template content directory:
   - bachelor: `content/thesis/undergraduate/`
   - master or PhD: `content/thesis/graduate/`
11. Update metadata in `info.tex`.
12. Write chapters, abstract, references, appendices, acknowledgements, formula-normalized LaTeX, and review notes.
13. Compile if possible and save `project/compile_result.json`.
14. Run `scripts/quality_gate.py` and save `project/quality_gate.json` or Markdown.
15. Write `project/conversion_report.md`.

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

## Source Priority

Use sources in this order:

1. `.docx` as the primary editable source.
2. `.doc` only after conversion to `.docx` using the standard fallback chain: Word COM first, LibreOffice headless second, Pandoc only as a low-fidelity diagnostic fallback, then user-assisted manual save-as when automation fails.
3. PDF as optional visual reference only.
4. Typed user instructions and formatting guides as constraints, not content sources unless explicitly requested.

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

Read `references/docx-workflow.md` and `references/nwpuers-workflow.md` before converting DOCX files.

DOCX extraction must support both Transitional OOXML and Strict OOXML. If `word/document.xml` exists but the body is not found, treat it as a namespace/package diagnostic first, not as a corrupt-file conclusion.

For legacy `.doc`, run `scripts/convert_doc_to_docx.py` or follow the fallback chain in `references/docx-workflow.md`. After conversion, rerun `scripts/detect_document.py` and inspect `ooxml_flavor`, `has_body`, and mojibake warnings before building the IR.

## Authoring Rules

- Map Word headings to NWPU chapter and section structure.
- Use template-native abstract, keyword, metadata, bibliography, appendix, acknowledgement, committee, and accomplishment files.
- Convert clear academic tables to three-line tables using `booktabs`.
- Avoid preserving Word table border grids unless explicitly required.
- Do not omit an extracted Word data table just because it lacks a caption when rows and cells are meaningful. Render it with a conservative provisional caption and record the assumption in `conversion_report.md`; use an in-place review note for damaged, empty, or layout-only tables.
- Generate missing figure/table captions only when the role is clear, and record that in the report.
- Treat adjacent or grid-aligned images as a possible figure group before emitting independent figures.
- For figure groups, choose one of these policies and record the choice: shared group caption, separate captions, subfigures with labels such as `(a)`, `(b)`, `(c)`, or in-place review placeholder when the relationship is unclear.
- Avoid using `longtable` to lay out image groups. Use a figure/subfigure/minipage layout when confident, or keep an in-place figure-group placeholder.
- Do not invent missing data, references, formulas, committee members, student numbers, or signatures.
- Keep uncertain formulas, rough tables, and ambiguous image groups in their source position as visible review placeholders when faithful reconstruction is unsafe.
- Fix obvious formatting noise when it does not change meaning.
- Treat old `.doc` conversion mojibake as a first-class source defect. Detect likely UTF-8/GBK mojibake before authoring; apply high-confidence phrase-level repairs only when the repaired text is clearly better, and record repaired samples in `conversion_report.md`.
- Do not globally repair single-character symbol-like cases such as `胃` to `theta`; review them only in formula or variable context.
- Infer headings only when numbering, style, and context agree.
- Do not invent missing data, captions, or references.
- Give generated captions only when the image role is clear, and mark them in the report.
- Preserve uncertain formulas as review notes or image fallbacks when editable reconstruction is unsafe.
- For reliable formulas, ignore Word spacing, line breaks, indentation, and manual equation numbers; reconstruct the ideal LaTeX environment.
- Number only core definition/theorem/lemma/proposition formulas or formulas explicitly referenced later.
- Use `equation + label` for numbered formulas, `equation + aligned` for one logical multi-line numbered formula, and `\[ aligned \]` for unnumbered derivations.
- Replace manual equation references with `\eqref` when the target is clear, and record ambiguous references in the report.
- Use standard matrix environments for ordinary matrices. If compiled matrices are stretched while editor previews look normal, diagnose template `\baselineskip`, `\fontsize`, `\arraystretch`, and matrix hooks before changing chapter formulas.
- Keep short inline Gaussian-binomial calculations in place with `\displaystyle`; use local spacing for consecutive tall inline formulas instead of changing global line spacing.
- Define repeated special math shapes such as Gaussian binomials as template-level macros, but keep compact matrix macros as fallbacks rather than the ordinary matrix path.
- When a formula-shape issue is confirmed, search the full chapter or project for the same macro/context instead of fixing only the reported location.
- Preserve WMF/EMF formula images by converting them to a supported fallback such as PNG/PDF when possible. If conversion fidelity is uncertain, include the fallback in place and mark it for manual review.
- Without reliable visual or formula parsing, do not guess LaTeX for image-only formulas. If visual/context confidence is high, reconstruct editable LaTeX and mark it for review; otherwise keep the formula image or a visible placeholder in the original location.
- Put generated figures under `content/figures/`.
- Keep small and medium tables near the related text for reviewability.
- Record unresolved defects in `conversion_report.md`.

## Modular Pipeline

Treat conversion as independent modules with saved outputs. Use the standard NWPU module IDs and contracts in `references/modular-pipeline.md`. Each module must be independently rerunnable from its declared inputs:

- source inventory writes `work/document_profile.json`
- thesis type decision writes `work/thesis_type_decision.md`
- legacy DOC conversion writes `work/doc_conversion_report.json`
- DOCX extraction writes `work/docx_semantic_ir.json`
- authoring brief writes `work/docx_authoring_brief.md`
- NWPU project creation writes the selected `project/` skeleton
- authoring plan writes `work/authoring_plan.md`
- LaTeX authoring writes chapter and asset files under `project/`
- compilation writes `project/compile_result.json` and logs
- quality gate writes `project/quality_gate.md` or JSON
- conversion reporting writes `project/conversion_report.md`

When resuming, reuse existing upstream artifacts if their inputs have not changed. Record and check module freshness with `work/pipeline_manifest.json`. Do not rerun the whole pipeline when a single module can be rerun safely.

## Quality Modes

Default to balanced quality checks.

- `draft`: prioritize content retention and compilation; warnings can remain for review.
- `balanced`: block content loss, missing assets, unsupported graphics, and obvious compilation failures; warn on likely semantic issues.
- `strict`: treat unresolved warnings as delivery blockers for final handoff.

Use `scripts/quality_gate.py --fail-on-warning` only for strict delivery checks. In balanced mode, warnings should be summarized in `conversion_report.md` and fixed when they indicate real semantic drift.

Compilation is a separate check from conversion quality. If `xelatex`, `latexmk`, or the requested engine is unavailable, record an environment blocker in `project/compile_result.json` and `conversion_report.md`; do not call the conversion failed solely because the local compiler is missing. Suggest Overleaf or another LaTeX environment when the project structure is otherwise complete.

## References

- Read `references/nwpuers-workflow.md` first.
- Read `references/docx-workflow.md` for DOCX extraction and authoring.
- Read `references/experiment-report.md` when the source is an experiment report, course report, lab report, or similar chaptered report.
- Read `references/ai-authoring.md` for the AI/script responsibility boundary.
- Read `references/content-structure.md` for figures and tables.
- Read `references/cross-references.md` for labels and references.
- Read `references/formula-normalization.md` before reconstructing formulas from Word or PDF references.
- Read `references/chinese-latex.md` for Chinese text.
- Read `references/modular-pipeline.md` for standard module IDs, saved outputs, and resume rules.
- Read `references/latex-maintainability.md` for maintainable LaTeX.
- Read `references/troubleshooting.md` when compilation fails.

## Scripts

- `scripts/create_nwputhesis_project.py`: create a clean NWPU thesis project.
- `scripts/detect_document.py`: quick source profile.
- `scripts/convert_doc_to_docx.py`: legacy `.doc` to `.docx` conversion with Word COM, LibreOffice, Pandoc, and manual fallback diagnostics.
- `scripts/build_docx_semantic_ir.py`: DOCX semantic IR and defect report.
- `scripts/write_docx_authoring_brief.py`: authoring brief from DOCX IR.
- `scripts/write_authoring_plan.py`: resumable authoring plan from saved artifacts.
- `scripts/run_module.py`: run one pipeline module and record successful inputs/outputs.
- `scripts/pipeline_manifest.py`: record and check module input/output freshness for resumable runs.
- `scripts/compile_latex.py`: local compile helper.
- `scripts/quality_gate.py`: delivery checks, including optional DOCX IR table coverage.
- `scripts/write_conversion_report.py`: conversion report writer.
