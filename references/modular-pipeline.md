# Modular Pipeline

Use this reference when running or extending the conversion workflow.

## Goal

The skill is a resumable pipeline, not one large conversion pass. Each module has one responsibility, writes its own artifact, and reads upstream artifacts instead of recomputing them.

## Principles

- Keep modules single-purpose and independently rerunnable.
- Keep coupling low: downstream modules read documented files, not hidden runtime state.
- Keep cohesion high: extraction, planning, template creation, authoring, compilation, quality checks, and reporting each own their local logic.
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
  document_profile.json
  docx_semantic_ir.json
  docx_semantic_ir_summary.md
  docx_authoring_brief.md
  thesis_type_decision.md
  authoring_plan.md
project/
  main.tex
  content/
  quality_gate.md
  conversion_report.md
```

## Modules

1. Source inventory
   - Input: `source/`
   - Output: `work/document_profile.json` or an equivalent notes file
   - Rerun when source files change.

2. Thesis type decision
   - Input: user answer, DOCX cues
   - Output: `work/thesis_type_decision.md`
   - Rerun when the target thesis type or professional-degree status changes.

3. DOCX semantic extraction
   - Input: primary DOCX
   - Output: `work/docx_semantic_ir.json`, `work/docx_semantic_ir_summary.md`, exported assets
   - Rerun when the Word source changes.

4. Authoring brief
   - Input: DOCX semantic IR
   - Output: `work/docx_authoring_brief.md`
   - Rerun when extraction or conversion rules change.

5. Project creation
   - Input: embedded `nwputhesis` template and thesis type decision
   - Output: `project/`
   - Rerun when thesis type or template bundle changes.

6. LaTeX authoring
   - Input: authoring brief, semantic IR, generated project, user constraints
   - Output: chapter, metadata, asset, bibliography, and report draft files
   - Rerun at chapter, section, or asset granularity whenever possible.

7. Compilation
   - Input: `project/`
   - Output: PDF, compile logs, local repair notes
   - Rerun after LaTeX changes.

8. Quality gate
   - Input: `project/`, optional DOCX semantic IR
   - Output: `project/quality_gate.md` or JSON
   - Rerun after authoring or asset changes.

9. Conversion report
   - Input: all module outputs and unresolved notes
   - Output: `project/conversion_report.md`
   - Rerun before delivery.

## Resume Rules

- If `work/docx_semantic_ir.json` exists and the source DOCX has not changed, reuse it.
- If `work/docx_authoring_brief.md` exists and the IR has not changed, reuse it.
- If `project/` already matches the thesis type decision, reuse it.
- If only one chapter changes, update that chapter and rerun compile, quality gate, and report.
- If quality gate fails, fix the smallest responsible module output rather than restarting the whole pipeline.
