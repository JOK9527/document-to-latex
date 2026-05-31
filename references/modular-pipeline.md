# Modular Pipeline

Use this reference when running or extending the NWPU conversion workflow.

## Goal

The skill is a resumable pipeline, not one large conversion pass. Each module has one responsibility, writes its own artifact, and reads upstream artifacts instead of recomputing them.

The pipeline is script-backed, not script-dominated. Saved artifacts provide evidence for the AI authoring pass; they do not replace context-aware judgment.

## Principles

- Keep modules single-purpose and independently rerunnable.
- Keep coupling low: downstream modules read documented files, not hidden runtime state.
- Keep cohesion high: extraction, thesis-type decision, NWPU project creation, planning, authoring, compilation, quality checks, and reporting each own their local logic.
- Save every module output as a file under `work/`, `project/`, or the final LaTeX tree.
- Make every module safe to rerun from its own inputs without rerunning all upstream modules.
- Never overwrite a useful intermediate artifact without making the command and assumption explicit.

## Recommended Artifacts

Use these artifacts as stable handoff points:

```text
source/
  original.docx
  optional-reference.pdf
work/
  pipeline_manifest.json
  document_profile.json
  thesis_type_decision.md
  docx_semantic_ir.json
  docx_semantic_ir_summary.md
  docx_authoring_brief.md
  authoring_plan.md
project/
  main.tex
  content/
  compile_result.json
  quality_gate.md
  conversion_report.md
```

## Module Contracts

Use these module IDs in `scripts/run_module.py --module` and `scripts/pipeline_manifest.py check --module`. Keep IDs stable between reruns.

| Module ID | Responsibility | Required inputs | Saved outputs | Default runner | Rerun when |
| --- | --- | --- | --- | --- | --- |
| `source_inventory` | Identify source files and roles | `source/` or primary Word file | `work/document_profile.json` | `scripts/detect_document.py` | Source files are added, removed, renamed, or replaced |
| `thesis_type_decision` | Record bachelor/master/PhD and professional-degree choice | User answer and DOCX/template cues | `work/thesis_type_decision.md` | AI decision with saved note | Thesis type or degree status changes |
| `docx_semantic_extraction` | Extract DOCX semantic IR, summary, and assets | Primary `.docx` | `work/docx_semantic_ir.json`, `work/docx_semantic_ir_summary.md`, `work/docx_assets/` | `scripts/build_docx_semantic_ir.py` | The Word source changes |
| `authoring_brief` | Summarize IR into AI authoring guidance | `work/docx_semantic_ir.json` | `work/docx_authoring_brief.md` | `scripts/write_docx_authoring_brief.py` | IR or authoring rules change |
| `nwpu_project_creation` | Create the selected `nwputhesis` skeleton | Embedded template and thesis type decision | `project/` | `scripts/create_nwputhesis_project.py` | Thesis type, professional-degree status, or embedded template changes |
| `authoring_plan` | Create a resumable execution index | Brief, IR, thesis type decision, generated project, user constraints | `work/authoring_plan.md` | `scripts/write_authoring_plan.py` | Any planning input changes |
| `latex_authoring` | Write or update NWPU thesis content and assets | Plan, brief, IR, generated project, user constraints | `project/main.tex`, `project/content/`, `project/template/` or embedded template files | AI authoring with local file edits | A chapter, section, table, figure, formula, metadata file, or template bridge changes |
| `compilation` | Compile the project and capture result | `project/` | `project/compile_result.json`, PDF/logs when available | `scripts/compile_latex.py` | LaTeX or assets change |
| `quality_gate` | Check delivery risks and unresolved warnings | `project/`, optional IR | `project/quality_gate.json` or `project/quality_gate.md` | `scripts/quality_gate.py` | Authoring, assets, or quality mode change |
| `conversion_report` | Record assumptions, defects, results, and review items | Profile, thesis decision, compile result, quality gate | `project/conversion_report.md` | `scripts/write_conversion_report.py` | Any upstream result or review item changes |

For scoped reruns, append a stable scope after the top-level ID, such as `latex_authoring:chapter3` or `latex_authoring:table-3-1`. Use scoped IDs only when the output can be rerun independently and the scope is clear.

## Resume Rules

- If `work/docx_semantic_ir.json` exists and the source DOCX has not changed, reuse it.
- If `work/docx_authoring_brief.md` exists and the IR has not changed, reuse it.
- If `project/` already matches `work/thesis_type_decision.md`, reuse it.
- If only one chapter changes, update that chapter and rerun compile, quality gate, and report.
- If quality gate fails, fix the smallest responsible module output rather than restarting the whole pipeline.

## Manifest

Record module state in:

```text
work/pipeline_manifest.json
```

Prefer running modules through `scripts/run_module.py` so successful commands automatically record their inputs and outputs:

```bash
python scripts/run_module.py \
  --module docx_semantic_extraction \
  --input source/original.docx \
  --output work/docx_semantic_ir.json \
  --output work/docx_semantic_ir_summary.md \
  --output work/docx_assets \
  -- python scripts/build_docx_semantic_ir.py source/original.docx --output work/docx_semantic_ir.json --summary work/docx_semantic_ir_summary.md --asset-dir work/docx_assets
```

For modules run manually or edited by hand, record their inputs and outputs afterward:

```bash
python scripts/pipeline_manifest.py record \
  --module thesis_type_decision \
  --input source/original.docx \
  --output work/thesis_type_decision.md \
  --command "AI decision recorded from source cues and user answer"
```

Before rerunning a module, check whether its saved outputs are still fresh:

```bash
python scripts/pipeline_manifest.py check --module docx_semantic_extraction
```

The check exits with code `0` when the module can be reused and non-zero when it should be rerun.
