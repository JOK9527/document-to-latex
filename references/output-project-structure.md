# Output Project Structure

Choose a structure that matches the document and preserves maintainability.

## Short Article

```text
converted-latex-project/
  main.tex
  latexmkrc
  conversion_report.md
  format_requirements.yaml
  build.log
  source/
    source-document.ext
    template-or-format-guide.ext
  content/
    figures/
    tables/
    article/
      info.tex
      abstract.tex
      body.tex
      appendix.tex
      reference.bib
  template/
    styles/
```

## Thesis or Long Report

```text
converted-latex-project/
  main.tex
  latexmkrc
  conversion_report.md
  format_requirements.yaml
  build.log
  source/
    source-document.ext
    template-or-format-guide.ext
  content/
    figures/
    tables/
    thesis/
      undergraduate/
        info.tex
        abstract.tex
        acknowledgements.tex
        chapters.tex
        chapter1.tex
        chapter2.tex
        conclusion.tex
        appendix.tex
        reference.bib
  template/
    styles/
```

## User Template

Preserve the original template layout when it is meaningful. Add generated content under `content/` and only bridge into the template where needed.

Do not mix converted chapter content into `.cls`, `.sty`, or `.def` files.

## Source Directory

Use `source/` for original user-provided materials:

```text
source/
  document.docx
  template.zip
  format-guide.pdf
  user-notes.md
```

Rules:

- Keep raw uploads immutable when practical.
- Do not edit source files in place.
- Do not put converted `.tex` chapter files in `source/`.
- Do not put raw uploads inside `content/`.
- Record each source file's role in `conversion_report.md`.
- If a user template is unpacked for use, keep the original archive or path recorded under `source/` and place the working template copy in the active template area.
