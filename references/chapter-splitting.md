# Chapter Splitting

Split long documents into maintainable files. Use the source document's heading hierarchy when reliable.

## Rules

- Use one `chapterN.tex` per top-level chapter for thesis, report, and book documents.
- Use one `body.tex` for short article-like documents.
- Extract front matter into `abstract.tex`, `acknowledgements.tex`, and `info.tex` when present.
- Extract appendices into `appendix.tex`.
- Generate `chapters.tex` as the ordered chapter aggregator.

## Example

```text
content/thesis/undergraduate/
  info.tex
  abstract.tex
  acknowledgements.tex
  chapters.tex
  chapter1.tex
  chapter2.tex
  chapter3.tex
  conclusion.tex
  appendix.tex
  reference.bib
```

`chapters.tex` should contain only ordered inputs:

```latex
% Auto-generated chapter order.
\input{content/thesis/undergraduate/chapter1}
\input{content/thesis/undergraduate/chapter2}
\input{content/thesis/undergraduate/chapter3}
```

