# DOCX Workflow

Use this workflow for NWPU academic theses and Word-based formatting drafts.

## Goal

Convert the editable Word source into a maintainable `nwputhesis` project. Do not simply dump DOCX XML or Pandoc output into `.tex`.

## Preflight

For this `doc2latex for nwpuers` branch, use the NWPU-specific preflight from `references/nwpuers-workflow.md`:

```text
璇风‘璁よ鏂囩被鍨嬶細鏈銆佺澹€佸崥澹紵
```

After this, proceed and record assumptions. Avoid stopping repeatedly for issues that can be handled as review notes. Do not ask for a LaTeX template unless the user explicitly wants to override the embedded `nwputhesis` template.

## Extraction

Run source detection first and save the output:

```bash
python scripts/run_module.py \
  --module source_inventory \
  --input source/original.docx \
  --output work/document_profile.json \
  -- python scripts/detect_document.py source/original.docx --output work/document_profile.json
```

Record thesis type as a saved module output:

```text
work/thesis_type_decision.md
```

If the primary source is a legacy `.doc`, convert it before semantic extraction:

```bash
python scripts/run_module.py \
  --module doc_conversion \
  --input source/original.doc \
  --output source/original.docx \
  --output work/doc_conversion_report.json \
  -- python scripts/convert_doc_to_docx.py source/original.doc --output source/original.docx --report work/doc_conversion_report.json
```

Use this fallback order:

1. Word COM: best fidelity for old Word files, Chinese text, embedded images, OLE objects, and formula objects.
2. LibreOffice headless: use when Word COM is unavailable, blocked by sandbox permissions, or times out.
3. Pandoc: low-fidelity diagnostic fallback only; inspect tables, figures, formulas, and headings carefully afterward.
4. Manual save-as: ask the user to open the `.doc` in Word or LibreOffice and save as `.docx` when automated conversion fails or fidelity is questionable.

After any `.doc` conversion, rerun `detect_document.py` against the produced `.docx`. Check `has_body`, `ooxml_flavor`, and any mojibake warnings before building the IR.

Run DOCX semantic extraction:

```bash
python scripts/run_module.py \
  --module docx_semantic_extraction \
  --input source/original.docx \
  --output work/docx_semantic_ir.json \
  --output work/docx_semantic_ir_summary.md \
  --output work/docx_assets \
  -- python scripts/build_docx_semantic_ir.py source/original.docx --output work/docx_semantic_ir.json --summary work/docx_semantic_ir_summary.md --asset-dir work/docx_assets
```

`build_docx_semantic_ir.py` auto-detects Transitional and Strict OOXML namespaces. If `word/document.xml` exists but the body is not found, read the package diagnostic in the error before treating the file as corrupt.

When old `.doc` conversion creates likely UTF-8/GBK mojibake, run extraction once without repair to inspect samples. If the repair candidates are high-confidence phrase-level fixes, rerun with `--repair-mojibake` and record that choice:

```bash
python scripts/build_docx_semantic_ir.py source/original.docx \
  --output work/docx_semantic_ir.json \
  --summary work/docx_semantic_ir_summary.md \
  --asset-dir work/docx_assets \
  --repair-mojibake
```

Do not globally repair single-character symbol-like cases such as `胃` to `theta`; keep them as review items unless formula context makes the intended symbol clear.

Then run:

```bash
python scripts/run_module.py \
  --module authoring_brief \
  --input work/docx_semantic_ir.json \
  --output work/docx_authoring_brief.md \
  -- python scripts/write_docx_authoring_brief.py work/docx_semantic_ir.json --output work/docx_authoring_brief.md
```

Create the NWPU project skeleton:

```bash
python scripts/run_module.py \
  --module nwpu_project_creation \
  --input work/thesis_type_decision.md \
  --input assets/templates/nwputhesis \
  --output project \
  -- python scripts/create_nwputhesis_project.py project --type bachelor --overwrite
```

Use `--type master`, `--type phd`, or `--type master --professional` according to `work/thesis_type_decision.md`.

Then create the authoring plan:

```bash
python scripts/run_module.py \
  --module authoring_plan \
  --input work/docx_authoring_brief.md \
  --input work/docx_semantic_ir.json \
  --input work/thesis_type_decision.md \
  --input project \
  --output work/authoring_plan.md \
  -- python scripts/write_authoring_plan.py \
  --brief work/docx_authoring_brief.md \
  --ir work/docx_semantic_ir.json \
  --output work/authoring_plan.md
```

Read the IR summary, authoring brief, authoring plan, and NWPU workflow before writing LaTeX.

Treat these files as module boundaries. If the DOCX has not changed, reuse the semantic IR. If the IR has not changed, reuse the authoring brief. Resume downstream work from these saved artifacts instead of restarting the whole workflow.

## What To Inspect

- heading styles and heading-like paragraphs
- cover pages, table-of-contents pages, and navigation-only entries that should not become body content
- likely document type: article-like, report-like, thesis-like, experiment report, course design, or template-bound thesis
- abstract, keywords, acknowledgements, appendix, and bibliography sections
- inconsistent numbering or manual heading formatting
- images without nearby captions
- adjacent or grid-aligned images that may form a shared-caption or subfigure group
- captions without nearby images or tables
- tables with empty rows, uneven row widths, or unclear headers
- layout tables used for cover pages or formatting rather than data
- formulas represented as OMML, images, WMF/EMF fallbacks, OLE objects, or plain text
- formulas with manual numbering, unreliable line breaks, stretched delimiters, or Word-only visual spacing
- citation markers and bibliography candidates
- NWPU metadata cues such as title, student number, school, major, supervisor, committee, and degree type

## Authoring Rules

- Use source heading hierarchy when reliable.
- Exclude generated table-of-contents entries from body authoring unless the source lacks real section headings and the entries are the only reliable outline.
- Treat cover-page and metadata tables as front matter, not data tables.
- Infer headings only when style, numbering, and context agree.
- Map reliable headings into the selected `nwputhesis` undergraduate or graduate content structure.
- Keep small and medium tables near their discussion.
- Rebuild tables as reviewable LaTeX when the structure is clear.
- For academic documents, convert clear data tables to three-line tables by default. Use template-native table commands or `booktabs` (`\toprule`, `\midrule`, `\bottomrule`) instead of preserving Word borders.
- Do not emit Word-style full grid tables with repeated `\hline` unless the template or user explicitly requires bordered tables.
- If the DOCX IR contains table rows and cells, render the table in LaTeX even when the original DOCX has no caption.
- Missing captions should become conservative provisional captions plus `conversion_report.md` assumptions, not `% REVIEW` placeholders that omit meaningful data tables.
- Mark unclear, damaged, empty, or layout-only tables instead of pretending they are clean.
- Preserve figure order and captions when reliable.
- Detect possible figure groups before emitting standalone figures. Choose shared caption, separate captions, subfigure labels, or an in-place review placeholder when the relationship is unclear.
- If several adjacent images share one nearby caption or one following analysis paragraph, prefer a figure group or subfigures over unrelated standalone figures.
- If a long figure caption contains analysis prose, keep the concise identifying phrase in `\caption{}` and move the explanation into normal body text.
- Generate captions only when the figure role is obvious, and record this.
- Avoid using `longtable` as an image-layout workaround. Multi-image content should remain figure semantics unless the source is genuinely a data table.
- Reconstruct formulas as editable LaTeX only when confident.
- Treat Word/PDF formula layout as a draft signal, not a formatting authority.
- Preserve math content exactly, then rebuild equation environments, labels, references, and visual layout using `references/formula-normalization.md`.
- Use inline math for prose formulas, unnumbered display math for examples and proof steps, and numbered `equation` only for core formulas or explicit later references.
- Use `equation + aligned` for one logical multi-line numbered formula; use `\[ aligned \]` for unnumbered derivations.
- Do not preserve manual equation numbers; create semantic labels and use `\eqref` when the target is clear.
- Use standard matrix environments for ordinary matrices. If compiled matrices look stretched while the source or editor preview looks normal, inspect template line-height and matrix hooks before rewriting formulas.
- Keep short inline Gaussian-binomial calculations inline with `\displaystyle`; add local spacing for repeated tall inline calculations instead of changing global line spacing.
- Keep repeated special math shapes in template-level macros, but do not replace ordinary matrices with compact macros unless there is a documented exception.
- After confirming a formula-shape issue, search the full chapter or project for the same macro/context before stopping.
- Preserve uncertain formulas in place as review notes or image fallbacks.
- Convert WMF/EMF formula images to PNG/PDF fallbacks before delivery when possible. If fidelity is uncertain, keep the fallback in place and mark it for manual review.
- Normalize obvious punctuation and spacing noise, but do not rewrite technical claims.

## Defect Handling

Source defects should not block the conversion unless they change meaning. Put unresolved issues in `conversion_report.md`.

Common defects:

- body text manually styled as headings
- headings typed as plain bold text
- missing figure/table captions
- duplicate or skipped figure/table numbers
- adjacent images with no clear shared or separate captions
- tables used for layout rather than data
- tables with decorative Word borders that should become semantic three-line tables
- copied formulas stored as images, especially WMF/EMF/OLE formula objects
- formula numbering copied as plain text instead of semantic references
- formulas broken by Word spacing, manual line breaks, or stretched brackets
- references pasted as plain text
- mixed Chinese and English punctuation
- mojibake after legacy `.doc` conversion; repair only high-confidence phrases and record risky symbol substitutions separately

## Output

Use the `nwputhesis` structure created by `scripts/create_nwputhesis_project.py`. Keep generated content out of `source/`, keep style out of chapter files, and keep review comments close to uncertain conversions.

Save module outputs under `work/` and final delivery outputs under `project/` so extraction, planning, project creation, authoring, compilation, quality checks, and reporting can be rerun independently. Record module freshness in `work/pipeline_manifest.json`.

Recommended downstream commands:

```bash
python scripts/run_module.py \
  --module compilation \
  --input project \
  --output project/compile_result.json \
  -- python scripts/compile_latex.py project --output project/compile_result.json

python scripts/run_module.py \
  --module quality_gate \
  --input project \
  --input work/docx_semantic_ir.json \
  --output project/quality_gate.json \
  -- python scripts/quality_gate.py project --ir work/docx_semantic_ir.json --output project/quality_gate.json

python scripts/run_module.py \
  --module conversion_report \
  --input work/document_profile.json \
  --input work/thesis_type_decision.md \
  --input project/compile_result.json \
  --input project/quality_gate.json \
  --output project/conversion_report.md \
  -- python scripts/write_conversion_report.py \
  --metadata work/document_profile.json \
  --compile-result project/compile_result.json \
  --quality-gate project/quality_gate.json \
  --source source/original.docx \
  --warning "Record unresolved conversion assumptions here" \
  --output project/conversion_report.md
```
