# Authoring Lessons

Use this reference before finalizing conversions from complex PDFs, especially papers, reports, and theses.

## Role of the AI

The AI is not a PDF renderer. It should behave like a careful editor who has read the source document and is rewriting it for the target LaTeX template.

Scripts provide:

- extraction evidence
- section and paragraph candidates
- figure, table, formula, and citation candidates
- draft scaffolds
- quality warnings

Scripts do not decide the final prose, figure placement, formula reconstruction, or table layout.

## PDF to Target Template

Do not preserve PDF line breaks. Multi-column source layout, page breaks, and local coordinates are extraction clues, not target layout requirements.

Before writing final chapter files:

- read the source page or rendered page sample
- read the semantic IR summary
- read the authoring brief
- understand what each section is trying to explain
- decide which figures, tables, and equations support that explanation
- rewrite paragraphs for the target template flow

## Figures

Place figures because the text needs them, not because the PDF coordinate says so.

Preferred behavior:

- Insert a figure after the paragraph that introduces or explains it.
- If LaTeX float movement makes the PDF misleading, use `[H]` with the `float` package.
- Start with content correctness. Relax float placement later only if the user wants prettier pagination.
- Use semantic captions from the source or from AI understanding.
- Do not force unreferenced figures into the chapter; defer them with a review note.

## Tables

For converted documents, source review is often more important than abstract file purity.

Preferred behavior:

- Keep small and medium tables inline in the chapter source near the related paragraph.
- Use `tblr` from `tabularray` for converted tables unless the template forbids it.
- Split table data into separate files only when tables are very large, reused, or generated from external data.
- Never pretend an unreliable table extraction is complete. Rebuild it or mark it for review.

## Formulas

Formula extraction must be conservative.

- Citation fragments such as `[1]` and `[2-6]` are prose/citation markers, not equations.
- Number-only formula labels such as `(12)` are not equations by themselves.
- Rewrite clear formulas as editable LaTeX.
- Use image fallback only when the formula cannot be reconstructed reliably and mark it in the report.
- Do not promote formula fragments to headings or standalone prose.

## Release Gate

Before calling a conversion ready:

- paragraphs read naturally in the target template
- figures and tables are near their explanatory text
- formulas are editable LaTeX or explicitly marked for review
- tables are readable in source and PDF
- source uploads remain under `source/`
- warnings and assumptions are recorded in the conversion report or worklog
