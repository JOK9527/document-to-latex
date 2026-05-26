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

## Local Exceptions

If a figure or table needs local style, add a concise comment explaining why the exception is local.
