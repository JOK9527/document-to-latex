# Worklog

## v1.1-docx - 2026-05-26

### Direction

Reposition the skill as a DOC/DOCX-first academic Word to LaTeX authoring workflow.

### Decisions

- Use DOCX as the primary editable source.
- Treat DOC files as requiring conversion to DOCX before active processing.
- Treat PDF as optional reference material only.
- Keep preflight short and mandatory so the assistant can continue without repeated interruptions.
- Focus on imperfect academic drafts: inconsistent headings, rough tables, missing captions, mixed formulas, and incomplete references.
- Keep the public interface small: DOCX IR, DOCX authoring brief, template analysis, format extraction, compile, quality gate, and conversion report.

### Added

- `references/docx-workflow.md`
- `scripts/build_docx_semantic_ir.py`
- `scripts/write_docx_authoring_brief.py`

### Cleaned

- Removed active PDF conversion scripts and PDF-specific references from the skill interface.
- Rewrote `SKILL.md` and `README.md` around the DOC/DOCX academic workflow.
- Updated user guidance to reduce mid-process pauses.

### Remaining Boundaries

- `.doc` binary files need a local conversion path before semantic extraction.
- OMML formulas are detected but still require LaTeX reconstruction by the authoring model.
- Complex table normalization remains review-driven.
- PDF-only conversion is deferred until a multimodal or layout-analysis pipeline is available.
