# Cross References

Create cross references proactively instead of leaving raw text such as "see the figure below".

## Label Prefixes

- sections: `sec:`
- figures: `fig:`
- tables: `tab:`
- equations: `eq:`
- algorithms: `alg:`
- listings: `lst:`

## Naming

Use stable, semantic labels:

```text
fig:chapter1-system-architecture
tab:chapter2-experiment-results
eq:chapter3-loss-function
sec:chapter1-background
alg:chapter4-training-procedure
lst:chapter5-api-example
```

## Usage

- Use `Figure~\ref{...}` for figures.
- Use `Table~\ref{...}` for tables.
- Use `Equation~\eqref{...}` for equations.
- Use `Section~\ref{...}` for sections.
- Use `\cite{...}` for bibliographic citations.

If a source reference target is ambiguous, create the most likely label, add a TODO-style LaTeX comment, and record it in the conversion report.

