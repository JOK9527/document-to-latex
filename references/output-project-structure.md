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

## No-Template Default Structure

When no user template is provided, use one of the default template layouts from `assets/templates/` as the project skeleton. The chosen skeleton is part of the output contract, not only a style suggestion.

Rules:

- Keep generated `.tex` content inside a semantic subdirectory such as `content/article/`, `content/report/`, or `content/thesis/undergraduate/`.
- Keep `content/figures/` and `content/tables/` for assets and supporting table data.
- Keep metadata in `info.tex` or the template's metadata file.
- Keep ordered chapter or section inputs in an aggregator such as `body.tex` or `chapters.tex`.
- Do not create a flat `content/` root with many peer `.tex` files unless the user explicitly requests a compact single-folder project.
- If the converted document naturally has many sections but is still an article, prefer `content/article/body.tex` with clear sectioning over a flat pile of numbered files.

Acceptable no-template article layout:

```text
converted-latex-project/
  main.tex
  latexmkrc
  conversion_report.md
  source/
  content/
    figures/
    tables/
    article/
      info.tex
      abstract-cn.tex
      abstract-en.tex
      body.tex
      appendix.tex
      reference.bib
```

Acceptable no-template thesis/report layout should follow the examples above with a nested `content/report/` or `content/thesis/undergraduate/` directory.

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
