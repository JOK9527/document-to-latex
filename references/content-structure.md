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

## Local Exceptions

If a figure or table needs local style, add a concise comment explaining why the exception is local.

