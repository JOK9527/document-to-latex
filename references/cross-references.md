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

## Equation References

Do not preserve source text that manually types equation numbers, such as `formula (2-1)` or `(3.2)`, when the target equation can be identified. Convert the target to a numbered `equation` with a semantic `eq:` label, then cite it with `\eqref`.

If the source contains a manual equation number but the formula is only an example calculation or proof step, do not automatically keep the number. Record the ambiguity and number it only when later prose clearly references it.

