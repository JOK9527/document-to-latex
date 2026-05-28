# document-to-latex

Use the project-local skill at `.codex/skills/doc2latex`.

## Preflight

Before starting, verify that this file exists:

```text
.codex/skills/doc2latex/SKILL.md
```

If it is missing, stop and tell the user to copy the `document-to-latex` skill into `.codex/skills/doc2latex/`.

## Read First

Read these files before planning the conversion:

1. `.codex/skills/doc2latex/SKILL.md`
2. `.codex/skills/doc2latex/README.md`

Then read any reference files named by `SKILL.md` for the document type, template, and conversion task.

## Workflow

1. Inspect `source/` for DOC/DOCX files, templates, formatting guides, and optional PDF visual references.
2. Follow the mandatory preflight defined by the local skill.
3. Run the skill's detection, semantic IR, authoring brief, compile, and quality-gate scripts when applicable.
4. Write the generated LaTeX project under `project/`.
5. Keep intermediate analysis and reports under `work/`.
6. Preserve original materials under `source/`.

## Rules

- Do not convert by dumping raw extracted text into LaTeX.
- Treat the Word document as an imperfect academic draft.
- Preserve figures, tables, formulas, citations, and review notes according to the local skill.
- Keep uncertain content in place with visible review placeholders.
- Run the quality gate before final delivery when possible.
