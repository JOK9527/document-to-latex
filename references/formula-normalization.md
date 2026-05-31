# Formula Normalization

Use this reference when converting equations from imperfect Word documents.

## Goal

Word and PDF output are content references, not trusted formatting sources. Preserve the mathematical meaning first, then rebuild the LaTeX structure, numbering, references, and visual form as a clean academic document.

## Priority

1. Preserve mathematical content exactly.
2. Preserve cross-reference meaning.
3. Rebuild valid LaTeX equation structure.
4. Optimize the ideal academic visual form.
5. Ignore source spacing, line breaks, and manual numbering when they conflict with the rules above.

## Source Policy

- Do not mechanically copy Word equation spacing, line breaks, indentation, or manual numbers.
- Do not treat a PDF screenshot as the formatting authority when it contains stretched delimiters, bad wrapping, or inconsistent numbering.
- Reconstruct editable LaTeX only when the formula is reliable enough to preserve meaning.
- Keep uncertain image-only or low-confidence formulas in place as review placeholders or supported image fallbacks.
- Record source formula defects and reconstruction assumptions in `conversion_report.md`.

## Equation Environments

Use inline math for short formulas embedded in prose:

```latex
\( ... \)
```

Use unnumbered display math for ordinary displays, examples, substitutions, and proof steps:

```latex
\[
...
\]
```

Use one numbered equation only for core formulas in definitions, theorems, lemmas, propositions, or formulas explicitly referenced later:

```latex
\begin{equation}
...
\label{eq:ch3-example}
\end{equation}
```

Use `equation` plus `aligned` when one logical formula needs multiple lines but only one number:

```latex
\begin{equation}
\begin{aligned}
...
\end{aligned}
\label{eq:ch3-example}
\end{equation}
```

Use unnumbered `aligned` for ordinary multi-line derivations:

```latex
\[
\begin{aligned}
...
\end{aligned}
\]
```

Avoid `align` unless every row is an independent equation that must be referenced. Prefer `\[ aligned \]` or `equation + aligned`.

Do not use `$$...$$`.

## Numbering Rules

Number only:

- core formulas in definitions, theorems, lemmas, and propositions
- formulas with explicit later references
- structural summary formulas that the section depends on

Do not number:

- inline formulas
- example calculations
- proof intermediate quantities
- one-step substitutions
- temporary matrix displays
- sent, received, or error vectors shown only as examples
- finite-field arithmetic shown only as a worked calculation

For chapter-based documents, configure numbering in the preamble:

```latex
\numberwithin{equation}{chapter}
\renewcommand{\theequation}{\thechapter-\arabic{equation}}
```

This gives numbers such as `(2-1)` and `(3-1)`. Do not type equation numbers by hand.

## Labels and References

Every numbered equation must have a semantic label:

```latex
\label{eq:ch3-gaussian-binomial}
\label{eq:ch4-singleton-bound}
```

Use `\eqref` for prose references:

```latex
Equation~\eqref{eq:ch4-singleton-bound}
```

For Chinese prose, use the template's language style consistently, for example:

```latex
式~\eqref{eq:ch4-singleton-bound}
```

Replace manual text such as `(2-1)`, `(3.2)`, or `formula (2-1)` when the target equation can be identified.

## Repeated Math Shapes

Define repeated math forms once in the preamble or template layer, not inside each chapter.

Use a compact matrix macro when small matrices look stretched with ordinary `pmatrix`:

```latex
\providecommand{\rankmat}[1]{%
  {\renewcommand{\arraystretch}{0.92}%
  \left(\begin{matrix}#1\end{matrix}\right)}%
}
```

Use a Gaussian binomial macro instead of manually building brackets with `array`:

```latex
\providecommand{\gbinom}[3]{\genfrac{[}{]}{0pt}{}{#1}{#2}_{#3}}
```

Prefer semantic operators:

```latex
\operatorname{rank}
\operatorname{dim}
\operatorname{Tr}
```

## Final Review Checklist

- Inline formulas are unnumbered.
- Numbered equations are core formulas or explicitly referenced.
- Numbered equations have `\label`.
- Prose references use `\eqref`.
- No manual equation numbers remain when the target is known.
- Ordinary derivations do not use numbered `align`.
- Matrices and repeated symbols use template macros when helpful.
- Long formulas do not exceed the page margin.
- Compiled output has centered displays, stable numbering, and no `??` references.
