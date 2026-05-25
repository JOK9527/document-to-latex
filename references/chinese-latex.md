# Chinese LaTeX

Use Chinese-aware defaults when the document contains substantial Chinese text.

## Defaults

- Prefer XeLaTeX.
- Prefer `ctexart` for short documents.
- Prefer `ctexrep` or a thesis template for long documents.
- Avoid pdfLaTeX unless the user requires it.

## Fonts

Use template font settings when a user template exists. For default templates, rely on `ctex` defaults first. If compilation fails because fonts are missing, record the issue and use widely available system fonts only when known locally.

## Bibliography

For Chinese academic documents, GB/T 7714 may be appropriate when requested or implied by the formatting guide. Respect the template's bibliography system first.

