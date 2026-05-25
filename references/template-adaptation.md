# Template Adaptation

When the user provides a LaTeX template, preserve it and adapt content into it.

## Inspect First

Identify:

- main `.tex` entry file
- `\documentclass`
- `.cls`, `.sty`, and `.def` files
- bibliography system: BibTeX, biber, natbib, biblatex, or template-specific
- title, metadata, abstract, keywords, appendix, and bibliography insertion points
- existing `\input` or `\include` structure

## Adaptation Rules

- Do not rewrite template internals unless required for compilation.
- Do not duplicate packages already loaded by the template.
- Prefer template-defined commands for title, metadata, abstract, keywords, appendix, and bibliography.
- Generate content files under `content/` unless the template requires a specific directory.
- Keep a short comment where generated content is inserted.
- Record every template file that was changed.

## Insertion Pattern

Prefer a small bridge file when the template has a clear body slot:

```latex
% Auto-generated content entry point.
% Edit chapter files under content/.
\input{content/thesis/undergraduate/chapters}
```

If the template uses an existing file such as `thesis-body.tex`, fill that file with `\input{...}` statements rather than pasting all content into it.

## Format Guide plus Template

When both exist:

- Use the template for structure and supported commands.
- Use the guide for missing requirements.
- If they conflict, follow the user's current request first, then the template.

