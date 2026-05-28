# DOCX Workflow

Use this workflow for academic papers, theses, reports, and formatting drafts.

## Goal

Convert the editable Word source into a maintainable LaTeX project. Do not simply dump DOCX XML or Pandoc output into `.tex`.

## Preflight

Ask one compact question before conversion unless already answered:

```text
Before I start: do you have a LaTeX template or formatting guide to use? If not, I can choose a default. Should I prioritize strict template compliance or clean maintainable LaTeX?
```

After this, proceed and record assumptions. Avoid stopping repeatedly for issues that can be handled as review notes.

## Extraction

Run:

```bash
python scripts/build_docx_semantic_ir.py source/original.docx \
  --output work/docx_semantic_ir.json \
  --summary work/docx_semantic_ir_summary.md \
  --asset-dir work/docx_assets
```

Then run:

```bash
python scripts/write_docx_authoring_brief.py work/docx_semantic_ir.json \
  --output work/docx_authoring_brief.md
```

Read both files before writing LaTeX.

## What To Inspect

- heading styles and heading-like paragraphs
- abstract, keywords, acknowledgements, appendix, and bibliography sections
- inconsistent numbering or manual heading formatting
- images without nearby captions
- adjacent or grid-aligned images that may form a shared-caption or subfigure group
- captions without nearby images or tables
- tables with empty rows, uneven row widths, or unclear headers
- formulas represented as OMML, images, WMF/EMF fallbacks, OLE objects, or plain text
- citation markers and bibliography candidates

## Authoring Rules

- Use source heading hierarchy when reliable.
- Infer headings only when style, numbering, and context agree.
- Keep small and medium tables near their discussion.
- Rebuild tables as reviewable LaTeX when the structure is clear.
- For academic documents, convert clear data tables to three-line tables by default. Use template-native table commands or `booktabs` (`\toprule`, `\midrule`, `\bottomrule`) instead of preserving Word borders.
- Do not emit Word-style full grid tables with repeated `\hline` unless the template or user explicitly requires bordered tables.
- If the DOCX IR contains table rows and cells, render the table in LaTeX even when the original DOCX has no caption.
- Missing captions should become conservative provisional captions plus `conversion_report.md` assumptions, not `% REVIEW` placeholders that omit the table.
- Mark unclear tables instead of pretending they are clean.
- Preserve figure order and captions when reliable.
- Detect possible figure groups before emitting standalone figures. Choose shared caption, separate captions, subfigure labels, or an in-place review placeholder when the relationship is unclear.
- Generate captions only when the figure role is obvious, and record this.
- Do not use `longtable` as an image-layout workaround. Multi-image content should remain figure semantics.
- Reconstruct formulas as editable LaTeX only when confident.
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
- references pasted as plain text
- mixed Chinese and English punctuation

## Output

Use the template structure or one of the default skeletons. Keep generated content out of `source/`, keep style out of chapter files, and keep review comments close to uncertain conversions.
