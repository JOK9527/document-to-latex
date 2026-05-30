# NWPUers Workflow

Use this workflow for the `doc2latex for nwpuers` branch.

## Preflight

Ask only:

```text
请确认论文类型：本科、硕士、博士？
```

If the user already said 本科, 硕士, 博士, bachelor, master, or PhD, do not ask again.

For graduate theses, default to academic degree. Ask about professional degree only when the user mentions 专硕, 专业学位, 工程硕士, or professional degree.

## Source Rules

- Primary source must be DOCX.
- DOC must be converted to DOCX first.
- PDF is reference only.
- The embedded `nwputhesis` template is the default and should not be replaced unless the user explicitly asks.

## Project Creation

Create the project before authoring final LaTeX:

```bash
python scripts/create_nwputhesis_project.py project --type bachelor --overwrite
python scripts/create_nwputhesis_project.py project --type master --overwrite
python scripts/create_nwputhesis_project.py project --type phd --overwrite
```

For professional-degree graduate theses:

```bash
python scripts/create_nwputhesis_project.py project --type master --professional --overwrite
```

The generated project intentionally contains only the selected undergraduate or graduate content tree.

## Undergraduate Mapping

Use:

```text
project/
  bachelor.tex
  main.tex
  content/thesis/undergraduate/
    info.tex
    abstract.tex
    chapters.tex
    chapter*.tex
    acknowledgements.tex
    designsummary.tex
    appendix.tex
    reference.bib
```

Fill `info.tex` with title, author, year, month, major, and advisor.

Use `designsummary.tex` for undergraduate graduation design summary. If the DOCX has no equivalent section, leave a concise placeholder and record it in `conversion_report.md`.

## Graduate Mapping

Use:

```text
project/
  graduate.tex
  main.tex
  content/thesis/graduate/
    info.tex
    abstract.tex
    chapters.tex
    chapter*.tex
    committee.tex
    appendix.tex
    acknowledgements.tex
    accomplishments.tex
    reference.bib
    accomplishments.bib
```

Fill `info.tex` with Chinese and English title, author, school, major, advisor, year, month, class number, and student number when available.

Do not invent committee members, student numbers, authorization signatures, or accomplishment bibliography entries. Leave placeholders and record review items.

## Authoring Rules

- Use `\chapter`, `\section`, and `\subsection` according to thesis type and source structure.
- Put ordered chapter inputs in `chapters.tex`.
- Use `\begin{abstract}` and `\begin{engabstract}` in `abstract.tex`.
- Use `\keywordslist{...}` and `\engkeywordslist{...}`.
- Use `biblatex` entries in `reference.bib` whenever references can be reconstructed reliably.
- Rebuild academic tables as three-line tables using `booktabs`.
- Render every extracted Word data table when rows and cells are available, even when the DOCX has no table caption.
- If a table caption is missing, infer a conservative provisional caption from nearby text or table contents, then record that assumption in `conversion_report.md`.
- Keep small and medium tables near the paragraph that discusses them.
- Store figures in `content/figures/`.
- Use stable semantic labels such as `fig:system-architecture`, `tab:experiment-parameters`, and `eq:control-law`.
- Treat Word formula layout as an unreliable draft signal: preserve math content, then rebuild equation environments, numbering, labels, references, and visual layout under `references/formula-normalization.md`.
- Use inline math for prose formulas, unnumbered display math for examples and proof steps, and numbered `equation` only for core formulas or formulas explicitly referenced later.
- Use `equation + aligned` for one logical multi-line numbered formula; use `\[ aligned \]` for unnumbered derivations.
- Replace clear manual equation numbers with semantic `eq:` labels and `\eqref`.
- Keep repeated math shapes, such as compact matrices or Gaussian binomials, in the template or preamble layer instead of redefining them inside chapters.

## Template Bundle Rules

Do not copy upstream demo material into generated projects.

The embedded bundle already excludes:

- `.github/`
- `.vscode/`
- QQ group image
- demo screenshot
- verbose sample chapters
- font submodule

Keep this branch focused and clean.

## Quality Gate

Run the quality gate with the DOCX semantic IR when available:

```bash
python scripts/quality_gate.py project --ir work/docx_semantic_ir.json --output project/quality_gate.md
```

The table coverage check should warn when the IR contains extracted tables but the generated LaTeX has fewer rendered table environments. Missing captions are review items, not a reason to leave table data as `% REVIEW` comments.

Formula checks should warn about raw `$$`, numbered equations without labels, ordinary derivations written as numbered `align`, and manual equation-number references that should become `\eqref`.
