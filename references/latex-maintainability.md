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

Common formula macros may include Gaussian binomials, trace/rank operators, or other domain-specific symbols that would otherwise be hand-built repeatedly. Use macros to make the formula shape consistent, but do not hide one-off mathematical content behind opaque commands.

Avoid compact matrix macros as the default representation for ordinary matrices. Prefer standard `matrix`, `pmatrix`, and `bmatrix`; if compiled matrices are visually stretched, diagnose template line-height and matrix hooks first.
