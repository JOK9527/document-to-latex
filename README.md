# doc2latex for nwpuers

`doc2latex for nwpuers` is a Northwestern Polytechnical University focused branch of `document-to-latex`.

It converts academic DOCX drafts into LaTeX projects using an embedded, trimmed copy of [`1195343015/nwputhesis`](https://github.com/1195343015/nwputhesis).

## Scope

- Primary input: `.docx`
- Target template: `nwputhesis`
- Target users: NWPU undergraduate, master, and PhD students
- PDF: optional visual reference only

This branch is not a general template selector. It assumes NWPU thesis formatting by default.

## Preflight

Ask only one question before conversion unless already answered:

```text
请确认论文类型：本科、硕士、博士？
```

For graduate theses, default to academic degree. Ask about professional degree only when the user mentions it or the source clearly indicates it.

## Workflow

1. Inspect `source/` for the primary `.docx`.
2. Ask the thesis type question if needed.
3. Build DOCX semantic IR.
4. Generate the DOCX authoring brief.
5. Create the project with `scripts/create_nwputhesis_project.py`.
6. Fill the appropriate `content/thesis/undergraduate/` or `content/thesis/graduate/` files.
7. Use three-line tables by default.
8. Compile when possible.
9. Run the quality gate.
10. Write a conversion report.

## Embedded Template

The embedded template lives under:

```text
assets/templates/nwputhesis/
```

The bundle is trimmed. It keeps only the files needed for conversion and compilation:

- `nwputhesis.cls`
- `infra/*.def`
- required cover and logo assets
- graduate authorization statement placeholder PDF
- minimal undergraduate and graduate content skeletons

Removed from the upstream template bundle:

- GitHub workflow files
- VS Code settings
- QQ group image
- demo screenshot
- verbose sample chapters
- font submodule

The upstream template is GPLv3; see `assets/templates/nwputhesis/UPSTREAM_LICENSE_GPLv3`.

## Main Scripts

- `scripts/detect_document.py`: source profile.
- `scripts/build_docx_semantic_ir.py`: DOCX semantic IR and defect report.
- `scripts/write_docx_authoring_brief.py`: AI authoring brief from DOCX IR.
- `scripts/create_nwputhesis_project.py`: create a clean NWPU thesis project.
- `scripts/compile_latex.py`: local LaTeX compile helper.
- `scripts/quality_gate.py`: delivery checks.
- `scripts/write_conversion_report.py`: conversion report writer.

