# document-to-latex Base Project

This is a minimal project folder for using the `document-to-latex` skill in Claude Code, Codex, or another coding assistant that can read project-local instructions.

## Directory Layout

```text
.
|-- .claude/
|   `-- commands/
|       `-- document-to-latex.md
|-- .codex/
|   |-- commands/
|   |   `-- document-to-latex.md
|   `-- skills/
|       `-- doc2latex/
|-- source/
|-- work/
`-- project/
```

## Install The Skill

Copy the released `document-to-latex` skill into:

```text
.codex/skills/doc2latex/
```

After copying, this file should exist:

```text
.codex/skills/doc2latex/SKILL.md
```

Do not put source documents inside `.codex/skills/`. The skill directory is only for the conversion workflow, scripts, references, and templates.

## Use The Project

1. Put the Word source document in `source/`.
2. Put optional templates, formatting guides, or PDF visual references in `source/`.
3. Open this `base-project` folder in the assistant.
4. Run the local command when your assistant supports project commands:

```text
/document-to-latex
```

If slash commands are unavailable, send:

```text
Read .codex/commands/document-to-latex.md or .claude/commands/document-to-latex.md and follow it to convert the document in source/.
```

Generated LaTeX output belongs in `project/`. Intermediate analysis, semantic IR, logs, and reports belong in `work/`.

## Update The Skill

To update the workflow, replace the contents of `.codex/skills/doc2latex/` with a newer release of the skill. Keep `source/`, `work/`, and `project/` as project-specific folders.
