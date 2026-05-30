# Worklog

## v1.3 - 2026-05-31

### Direction

Rebuild formula handling for imperfect Word sources instead of trusting Word or PDF equation formatting.

### Added

- Formula normalization policy covering content fidelity, equation environments, numbering, labels, `\eqref`, and repeated math-shape macros.
- Authoring brief guidance that treats Word equation spacing, line breaks, indentation, and manual numbers as draft signals only.
- Quality-gate warnings for raw `$$`, numbered equations without labels, ordinary numbered `align`, manual equation-number references, and missing chapter equation-numbering configuration.
- Template-level `\rankmat` and `\gbinom` helpers, plus chapter equation numbering in chapter-based skeletons.

### Guardrails

- Do not alter mathematical meaning while fixing formula structure.
- Do not number example calculations or proof intermediate steps unless later prose clearly references them.
- Do not preserve manual equation numbers when semantic labels and `\eqref` can be used.

## v1.2 - 2026-05-28

### Direction

Improve conversion reliability for ambiguous image, table, and formula regions.

### Added

- Figure-group policy for adjacent or grid-aligned images with shared captions, separate captions, subfigure labels, or in-place placeholders.
- In-place placeholder guidance for uncertain figures, tables, and image-only formulas.
- WMF/EMF formula-image handling policy: convert to PNG/PDF fallback when possible and mark uncertain fidelity for review.
- Balanced quality-gate checks for missing graphics, unsupported WMF/EMF references, and likely image-group/table semantic mistakes.

### Guardrails

- Do not use `longtable` to lay out image groups.
- Do not silently drop unsupported graphics or image-only formulas.
- Keep uncertain content near its source paragraph instead of allowing floats to drift away.

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

## nwpuers branch - 2026-05-26

### Direction

Create a Northwestern Polytechnical University focused branch: `doc2latex for nwpuers`.

### Decisions

- Embed a trimmed copy of `1195343015/nwputhesis`.
- Use `nwputhesis` as the default template.
- Reduce preflight to thesis type only: undergraduate, master, or PhD.
- Default graduate output to academic degree unless professional degree is explicitly indicated.
- Add `scripts/create_nwputhesis_project.py` to generate clean bachelor/master/PhD projects.
- Delete unused generated-project content during scaffold creation so undergraduate and graduate trees are not mixed.

### Template Cleanup

Excluded from the embedded bundle:

- GitHub workflow files
- VS Code settings
- QQ group image
- demo screenshot
- verbose sample chapters
- font submodule
