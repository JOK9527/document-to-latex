# Experiment Report Conversion

Use this reference for Chinese experiment reports, lab reports, course reports, course designs, and similar report-like drafts.

## Template Choice

- Short Chinese paper or essay: use `ctexart`.
- Experiment report with cover page, table of contents, chapters, appendices, data processing, or code: use a report-like skeleton (`report` with Chinese support or equivalent `ctexrep` style).
- School thesis or explicit institutional template: use the provided template before defaults.

Preserve cover, directory, appendix, code listing, and data attachment structure when the source clearly has them. If the source only has section headings and no front/back matter, keep the output compact.

## Body Boundaries

- Cover tables are front matter metadata, not data tables.
- Table-of-contents pages are navigation, not body prose. Use them only to cross-check the real heading hierarchy.
- Headers, footers, page numbers, and repeated document titles should not become body content.
- Duplicate paragraphs should be kept only when context shows they are intentional repeated instructions, captions, or results; otherwise preserve one occurrence and record the duplicate removal.

## Table Classification

- Cover/layout table: contains fields such as student, class, date, instructor, score, title, or empty cells for handwriting. Convert to front matter or omit as template metadata with a report note.
- Data table: has measured values, parameters, calculations, comparison rows, or result columns. Convert to semantic LaTeX, usually a three-line table.
- Form-like table: contains checklists, rubrics, signatures, or grading fields. Preserve only if the user needs a printable report form; otherwise record as source layout.
- Damaged table: empty rows, inconsistent cells, or unclear headers. Keep a visible review note near the source position.

## Figures

- Consecutive screenshots, plots, or circuit diagrams with one nearby title usually form a figure group.
- If each image has a clear independent caption, keep separate figures.
- If images are variants of one result, use subfigures or minipages with labels such as `(a)`, `(b)`, `(c)`.
- Long figure captions should be split: concise identifier in `\caption{}`, analysis and interpretation in body text.
- Do not use `longtable` for image layout unless the source is genuinely a table containing images as data.

## Formulas And Symbols

- Treat equation screenshots or OLE formula objects as review-sensitive. Reconstruct editable LaTeX only when the context is clear.
- Manual equation numbers should become semantic labels and `\eqref` references.
- Single-character mojibake repairs, such as a Chinese character that might be a Greek symbol, require formula context before changing.

## Authoring Checklist

Before writing LaTeX, make these decisions and record uncertain ones in `conversion_report.md`:

- Which pages are front matter?
- Which table-of-contents entries are only navigation?
- Which tables are data tables versus layout/form tables?
- Which adjacent images are figure groups?
- Which repeated paragraphs are intentional?
- Which captions contain body analysis that should be moved out of `\caption{}`?
- Which formulas are editable, image fallback, or manual review?
