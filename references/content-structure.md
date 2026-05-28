# Content Structure

Keep content, data, assets, and style separated inside chapters.

## Tables

For important or large tables, store the LaTeX table separately:

```text
content/tables/chapter1/table-1-1.tex
content/tables/chapter1/table-1-1-data.csv
```

Chapter files should reference tables:

```latex
As shown in Table~\ref{tab:chapter1-method-comparison}, the methods differ.

\input{content/tables/chapter1/table-1-1}
```

The table file should include caption and label, but not global style settings. Put global table style in template style files.

For academic DOCX conversions, rebuild clear data tables as three-line tables by default. Prefer template-native table environments when available; otherwise use `booktabs` rules:

```latex
\begin{table}[htbp]
  \centering
  \caption{Experimental parameters}
  \label{tab:experimental-parameters}
  \begin{tabular}{ll}
    \toprule
    Parameter & Value \\
    \midrule
    $K$ & 1.0 \\
    \bottomrule
  \end{tabular}
\end{table}
```

Do not preserve Word's visual border grid as repeated `\hline` commands unless the template or user explicitly requires bordered tables.

## Figures

Store figures by chapter when possible:

```text
content/figures/chapter1/system-architecture.png
```

Use stable labels:

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.82\textwidth]{content/figures/chapter1/system-architecture.png}
  \caption{System architecture}
  \label{fig:chapter1-system-architecture}
\end{figure}
```

Before writing separate figures, inspect adjacent images as possible figure groups. Common cases:

- several images share one caption
- several images each need their own inferred caption
- several images are subfigures labeled `(a)`, `(b)`, `(c)`, and share one caption
- several images have no reliable caption relationship and should remain as an in-place review placeholder

Do not use `longtable` to lay out image groups. Use `figure` with `subfigure`/`subcaption`, a local `minipage` layout, or a visible in-place placeholder when the relationship is uncertain. If a table-like layout is only a visual container for images, keep the semantic object as a figure, not a table.

When captions are missing, infer them only when nearby context makes the role clear. Otherwise preserve the images in their source position and write a visible review note plus a `conversion_report.md` item.

## In-Place Placeholders

When content cannot be converted faithfully, keep a visible marker near the original source position. This applies to unclear figure groups, rough tables, missing graphics, and image-only formulas.

Prefer a non-floating block or a fixed placement such as `[H]` for review placeholders. Do not let uncertain content float away from the paragraph that explains it.

Example placeholder:

```latex
\begin{center}
\fbox{\parbox{0.88\linewidth}{\centering
Manual review required: the source contains a multi-image region here, but the caption relationship is unclear.
}}
\end{center}
```

## Image-Only Formulas

Some DOCX formulas are stored as WMF/EMF/OLE images rather than editable OMML.

- Prefer semantic conversion for native OMML formulas.
- Convert WMF/EMF images to PNG/PDF fallbacks before LaTeX delivery.
- If a converted fallback may not match Word rendering, show it in place and mark it for manual review.
- Without reliable visual recognition, do not invent LaTeX for image-only formulas.

## Local Exceptions

If a figure or table needs local style, add a concise comment explaining why the exception is local.
