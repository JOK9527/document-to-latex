# Conversion Workflow

Use DOCX as the primary editable source. The goal is academic authoring and normalization, not visual scraping.

## Source Strategy

- DOCX: active path. Build semantic IR, write an authoring brief, then author LaTeX for the target template.
- DOC: convert to DOCX with an available local tool before using this skill. If conversion is unavailable, ask the user for DOCX.
- PDF: reference only. Use it to check appearance or numbering when the user provides it with DOCX. Do not use PDF as the main conversion source in this version.
- Formatting guides: extract constraints and apply them after explicit user instructions and template rules.
- LaTeX templates: preprocess before content insertion.

## Risk Areas

- Word headings may be manual formatting instead of real heading styles.
- Tables may have merged cells, empty rows, layout-only columns, or unclear headers.
- Figure and table captions may be missing, duplicated, or separated from the object.
- Formulas may be OMML, images, plain text, or mixed fragments.
- Bibliographies may be plain text rather than structured references.
- Chinese and English punctuation, spacing, and terminology may be inconsistent.

## Output Contract

Always produce a project that can be inspected and edited:

- `source/` with original DOC/DOCX, optional PDF reference, templates, and guides
- main entry point
- content files
- figures and tables directories
- bibliography file when references exist
- format requirements summary when requirements exist
- conversion report
- quality gate report when practical

Before delivery, run `scripts/quality_gate.py` when possible. Treat errors as blockers and warnings as review items to record in `conversion_report.md`.
