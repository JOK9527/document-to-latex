# LaTeX Maintainability

Generated LaTeX should be easy for a human to maintain.

## Separation

- Keep `main.tex` small.
- Keep original uploads in `source/` for traceability.
- Put global style in template style files.
- Put document metadata in `info.tex` or a template metadata file.
- Put chapter prose in chapter files only.
- Put figures and tables in their own asset directories.
- Avoid repeated raw formatting commands in content files.

## Comments

Add comments where they help future editing:

- generated content entry points
- user-editable regions
- template compatibility choices
- uncertain OCR or formula conversions
- local style exceptions

Avoid comments that restate obvious LaTeX syntax.

## Semantic Macros

Prefer semantic macros when a repeated concept appears. Define them in the template or style layer, not in each chapter.
