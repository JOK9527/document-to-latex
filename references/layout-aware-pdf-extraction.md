# Layout-Aware PDF Extraction

For PDFs with figures, tables, formulas, or multi-column text, do not extract plain text and image files independently. Preserve page coordinates, but do not use coordinates alone to decide final LaTeX placement.

The correct model is semantic-first:

1. Build a document IR with sections, paragraphs, references, figures, tables, formulas, and bibliography.
2. Use PDF coordinates to pair assets with captions and to estimate local reading order.
3. Place figures, tables, and formulas in the LaTeX output according to semantic references and section context.
4. Use source coordinates only as a tie-breaker, not as the final placement rule.

Use `scripts/build_pdf_semantic_ir.py` as the first executable pass for complex text PDFs. Treat its JSON output as a conversion planning artifact: inspect section boundaries, paragraph fragmentation, caption pairing, figure reference links, and formula candidates before generating chapter `.tex` files.

Example:

```bash
python scripts/build_pdf_semantic_ir.py source/original.pdf \
  --output work/pdf_semantic_ir.json \
  --summary work/pdf_semantic_ir_summary.md \
  --asset-dir work/pdf_semantic_assets
```

## Required Metadata

For each page, collect:

- text blocks or line groups with bounding boxes
- image blocks with bounding boxes
- figure captions and table captions with bounding boxes
- formula-like blocks with bounding boxes
- page number, column position, and reading-order estimate

## Figures

- Pair each figure caption with the nearest image block by page, vertical distance, and horizontal overlap.
- Use the original caption text in `\caption{...}`.
- Use stable labels such as `fig:source-12`, not generic labels based on chapter or insertion order.
- Insert the figure near the paragraph that refers to it, such as "as shown in Figure 12" or its Chinese equivalent. If no explicit reference exists, insert it near the most relevant section or after the first paragraph that discusses the same concept.
- If a figure has no caption, infer a concise semantic caption from nearby text and mark it as generated in the report.
- Treat body references such as "Figure 13 shows..." or its Chinese equivalent as references, not captions. A real caption usually has a matching English `Fig.13` line nearby in bilingual PDFs.
- If the IR finds a captioned figure but no explicit body reference, place it in the most relevant section after the paragraph that discusses the same subject. Do not append unreferenced figures to the end of the chapter.

## Tables

- Detect table captions separately from table bodies.
- Place tables near paragraphs that reference them, such as "as shown in Table 3" or its Chinese equivalent.
- If table grid reconstruction is not reliable, create a placeholder table with the original caption and a review note instead of pretending the table was converted.
- Preserve source table number labels such as `tab:source-03`.

## Formulas

- Do not merge formula lines into prose.
- If formula recognition is unavailable, prefer a readable formula image crop fallback over broken inline text.
- If using text fallback, group the whole formula block and mark it clearly as needing Math LaTeX reconstruction.
- Prefer later Math OCR/VLM reconstruction for final output.
- Never promote formula fragments to headings or keep them as one-character prose lines.
- When `--asset-dir` is used, formula candidate crops are written into the IR so generation can use them as a readable fallback.

## Paragraph Reflow

PDF line breaks are not paragraph breaks. Reconstruct natural paragraphs before generating LaTeX:

- merge consecutive body lines from the same paragraph
- merge citation-only fragments such as `[1]` and `[2-6]` into the surrounding prose
- remove headers, footers, page numbers, watermarks, and repeated journal metadata
- preserve real section and subsection headings
- keep displayed formulas, figures, and tables as separate block objects
- avoid one-line-per-source-line LaTeX output
- if many paragraphs are shorter than a sentence, stop and repair reflow before generating LaTeX

## AI Authoring Step

The conversion agent must behave like an editor reconstructing the document for the target template. Scripts provide evidence; they do not replace understanding.

Before writing final chapters:

1. Read the source PDF or a rendered page sample.
2. Read `work/pdf_semantic_ir_summary.md`.
3. Generate and read an authoring brief:

```bash
python scripts/write_pdf_authoring_brief.py work/pdf_semantic_ir.json \
  --output work/pdf_authoring_brief.md
```

4. For each section, identify what the section is explaining, which figures/tables support that explanation, and which equations are real displayed formulas.
5. Rewrite paragraphs for the target template's flow. Do not preserve two-column source line breaks.
6. Insert figure/table/equation code only after deciding why the object belongs there.

## Generation Gate

Before writing final LaTeX from a PDF, check the IR:

- Sections should match the source document's real headings.
- Paragraphs should read naturally and should not preserve source line breaks.
- Figure captions should be attached to image blocks or explicitly marked as missing assets.
- Figure, table, and equation references should point to semantic objects when possible.
- The IR `placement_plan` should place referenced figures/tables/formulas after their first referring paragraph.
- Formula candidates should be converted, cropped as fallback images, or marked for review.
- Any inferred captions, unresolved references, and OCR-sensitive material must be listed in `conversion_report.md`.

After review, `scripts/render_semantic_ir_to_latex.py` can generate a draft scaffold. Render into a new directory first, compare with the source, then rewrite the chapter text and asset placement before wiring it into the template entry point. The scaffold is not a final conversion.

Example:

```bash
python scripts/render_semantic_ir_to_latex.py work/pdf_semantic_ir.json \
  --project-root . \
  --output-dir content/thesis/undergraduate_semantic \
  --asset-root content/figures/semantic_assets \
  --report work/semantic_render_report.md
```

## Common Failure Modes

- Figure captions become ordinary body text.
- Images are extracted in file order and appended at the end of a chapter.
- Images are inserted at raw source coordinates even though the target template reflows text differently.
- Captions are replaced with generic generated labels.
- Body references that start with "Figure N" or the localized equivalent are mistaken for captions.
- Formula fragments are mistaken for section headings.
- PDF line breaks are preserved, making prose and formulas unreadable.
