# User Guidance

Guide the user before converting when the request lacks important context. Ask only for information that changes the output.

## Minimal Questions

When the user simply says "convert this document to LaTeX", ask:

1. Do you have a LaTeX template or existing Overleaf/project folder to use?
2. Do you have formatting requirements, a school/journal guide, or a reference PDF?
3. Should the output prioritize maintainable semantic LaTeX or visual fidelity to the original?

If the user has already provided any of these, do not ask again.

## When to Proceed Without Asking

Proceed with defaults when:

- the user asks for a quick conversion
- no template or guide is available
- the document is simple and the default template is adequate
- the user explicitly says to decide for them

Record assumptions in `conversion_report.md`.

## Suggested Defaults

- Chinese document: `ctexart` or thesis-like template with XeLaTeX
- English short document: `article`
- long report: `report`
- thesis or graduation design: `thesis-lite`
- default goal: maintainable semantic LaTeX

## Useful Follow-up Prompts

Use concise prompts such as:

- "Do you want me to use a specific LaTeX template, or should I choose a default one?"
- "Do you have a formatting guide or reference PDF I should follow?"
- "Should I prioritize matching the original layout, or producing clean LaTeX that is easy to edit?"

Avoid a long intake form unless the user is preparing a thesis, journal submission, or strict institutional format.

