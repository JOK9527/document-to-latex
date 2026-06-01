# doc2latex for nwpuers

`doc2latex for nwpuers` is a Northwestern Polytechnical University focused branch of `document-to-latex`.

It converts academic DOCX drafts into LaTeX projects using an embedded, trimmed copy of [`1195343015/nwputhesis`](https://github.com/1195343015/nwputhesis).

The workflow should be used for explicit slash-command requests and for plain-language requests such as converting an academic Word thesis draft to LaTeX. Discussion-only requests should stay in planning mode until the user asks to convert or update files.

## Scope

- Primary input: `.docx`
- Target template: `nwputhesis`
- Target users: NWPU undergraduate, master, and PhD students
- PDF: optional visual reference only

This branch is not a general template selector. It assumes NWPU thesis formatting by default.

## Preflight

Ask only one question before conversion unless already answered:

```text
请确认论文类型：本科、硕士、博士？
```

For graduate theses, default to academic degree. Ask about professional degree only when the user mentions it or the source clearly indicates it.

## Workflow

1. Inspect `source/` for the primary `.docx` or legacy `.doc`.
2. Ask the thesis type question if needed and record the decision under `work/`.
3. Build and save `work/document_profile.json`.
4. Convert legacy `.doc` sources to `.docx` with a recorded fallback chain when needed.
5. Build and save the DOCX semantic IR, summary, and extracted assets.
6. Generate and save `work/docx_authoring_brief.md`.
7. Create the NWPU project skeleton with `scripts/create_nwputhesis_project.py`.
8. Write `work/authoring_plan.md` as the handoff into LaTeX authoring.
9. Fill the appropriate `content/thesis/undergraduate/` or `content/thesis/graduate/` files.
10. Use three-line tables by default; extracted meaningful DOCX data tables must be rendered even when the original table caption is missing.
11. Preserve uncertain figures, tables, and formulas in place with visible review placeholders instead of silently dropping or moving them.
12. Compile when possible and save the compile result.
13. Run the quality gate, preferably with the DOCX semantic IR for table coverage checks.
14. Write a conversion report with source defects, assumptions, quality gate results, and manual review items.

Each stage should save its output under `work/` or `project/` so extraction, planning, project creation, authoring, compilation, quality checks, and reporting can be rerun independently.

## Design Position

This branch behaves like an NWPU thesis editing assistant, not a format dumper. It should:

- understand the Word draft before writing LaTeX
- use scripts as evidence and guardrails, not as substitutes for AI semantic judgment
- normalize structure without inventing missing facts
- separate content from style
- use the embedded `nwputhesis` structure by default
- rebuild academic tables as semantic three-line LaTeX tables instead of copying Word borders
- render meaningful extracted DOCX data tables even when the source forgot the table caption
- run conversion as loosely coupled modules with saved intermediate artifacts
- use stable module IDs for resumable runs
- resume from any module when its upstream artifacts already exist and remain valid
- record module freshness in `work/pipeline_manifest.json`
- mark uncertain tables, formulas, captions, and references for review
- keep uncertain figures, tables, and formulas near their source position with visible review placeholders
- avoid repeated mid-process questions after thesis type is known

## V1.3 Focus

- Treat Word formulas as imperfect content rather than reliable formatting.
- Rebuild equation environments, numbering, labels, and references under LaTeX and `nwputhesis` rules.
- Prefer semantic `\label` plus `\eqref` over manual equation numbers copied from Word.
- Keep ordinary examples and proof steps unnumbered while numbering core formulas and later-referenced formulas.
- Prefer standard matrix environments for ordinary matrices; fix template line-height pollution when compiled matrices stretch.
- Use `\displaystyle` for short inline Gaussian-binomial calculations that must remain attached to list or example text.
- Keep compact matrix macros as fallbacks, while using shared semantic macros for genuinely special repeated math shapes.
- Make the workflow more modular: source profiling, thesis type decision, DOCX extraction, authoring brief, NWPU project creation, LaTeX authoring, compilation, quality gate, and reporting each produce saved outputs and can be rerun independently.

## V1.3.1 Fix

- Corrects the earlier bias toward using compact matrix macros for ordinary matrices.
- Adds a template-layer matrix baseline hook for `nwputhesis` so body line spacing does not stretch matrix internals.
- Adds guidance and quality checks for inline `\gbinom` calculations that need `\displaystyle`.

## V1.3.2 Focus

- Adds `work/pipeline_manifest.json` as the standard module freshness record.
- Adds `work/authoring_plan.md` as the saved handoff into LaTeX authoring.
- Standardizes module output paths under `work/` and `project/`.
- Lets conversion reports include quality gate results.

## V1.3.3 Focus

- Adds a standard `.doc` to `.docx` fallback chain with diagnostics.
- Supports Strict and Transitional OOXML namespace detection during DOCX extraction.
- Records mojibake and risky symbol issues in the DOCX IR, with optional high-confidence repair.
- Adds experiment-report authoring rules for cover tables, TOC entries, data tables, figure groups, and long captions.
- Separates local LaTeX compiler absence as an environment blocker in compile/report output.

## V1.2 Focus

- Detect adjacent or grid-aligned images as possible figure groups before emitting separate figures.
- Support shared captions, separate captions, subfigure labels, or in-place placeholders for ambiguous multi-image regions.
- Keep uncertain content fixed near its source position with visible review warnings.
- Convert WMF/EMF formula images to supported fallbacks when possible; otherwise keep an in-place placeholder and report the issue.
- Warn when image groups are treated as data tables, especially `longtable` blocks containing `\includegraphics`.
- Use balanced quality checks by default, with strict checks available for final delivery.

## Embedded Template

The embedded template lives under:

```text
assets/templates/nwputhesis/
```

The bundle is trimmed. It keeps only the files needed for conversion and compilation:

- `nwputhesis.cls`
- `infra/*.def`
- required cover and logo assets
- graduate authorization statement placeholder PDF
- minimal undergraduate and graduate content skeletons

Removed from the upstream template bundle:

- GitHub workflow files
- VS Code settings
- QQ group image
- demo screenshot
- verbose sample chapters
- font submodule

The upstream template is GPLv3; see `assets/templates/nwputhesis/UPSTREAM_LICENSE_GPLv3`.

## Main Scripts

- `scripts/detect_document.py`: source profile.
- `scripts/convert_doc_to_docx.py`: legacy `.doc` conversion fallback chain and validation.
- `scripts/build_docx_semantic_ir.py`: DOCX semantic IR and defect report.
- `scripts/write_docx_authoring_brief.py`: AI authoring brief from DOCX IR.
- `scripts/create_nwputhesis_project.py`: create a clean NWPU thesis project.
- `scripts/write_authoring_plan.py`: resumable authoring plan from saved artifacts.
- `scripts/run_module.py`: run one pipeline module and record successful inputs/outputs.
- `scripts/pipeline_manifest.py`: record and check module input/output freshness.
- `scripts/compile_latex.py`: local LaTeX compile helper.
- `scripts/quality_gate.py`: delivery checks.
- `scripts/write_conversion_report.py`: conversion report writer.

## Version

Current development target: `v1.3.3`.

PDF-only conversion is intentionally deferred until a multimodal or MinerU-level layout pipeline is available.
