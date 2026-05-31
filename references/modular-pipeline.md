# Modular Pipeline

Use this reference when running or extending the conversion workflow.

## Goal

The skill is a resumable pipeline, not one large conversion pass. Each module has one responsibility, writes its own artifact, and reads upstream artifacts instead of recomputing them.

## Principles

- Keep modules single-purpose and independently rerunnable.
- Keep coupling low: downstream modules read documented files, not hidden runtime state.
- Keep cohesion high: extraction, planning, template analysis, authoring, compilation, quality checks, and reporting each own their local logic.
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
  template_analysis.json
  template_requirements.md
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

2. DOCX semantic extraction
   - Input: primary DOCX
   - Output: `work/docx_semantic_ir.json`, `work/docx_semantic_ir_summary.md`, exported assets
   - Rerun when the Word source changes.

3. Authoring brief
   - Input: DOCX semantic IR
   - Output: `work/docx_authoring_brief.md`
   - Rerun when extraction or conversion rules change.

4. Template analysis and preprocessing
   - Input: template files and format requirements
   - Output: `work/template_analysis.json`, `work/template_requirements.md`
   - Rerun when the template or requirements change.

5. LaTeX authoring
   - Input: authoring brief, semantic IR, template analysis, user constraints
   - Output: `project/` LaTeX files
   - Rerun at chapter, section, or asset granularity whenever possible.

6. Compilation
   - Input: `project/`
   - Output: PDF, compile logs, local repair notes
   - Rerun after LaTeX changes.

7. Quality gate
   - Input: `project/`, optional DOCX semantic IR
   - Output: `project/quality_gate.md` or JSON
   - Rerun after authoring or asset changes.

8. Conversion report
   - Input: all module outputs and unresolved notes
   - Output: `project/conversion_report.md`
   - Rerun before delivery.

## Resume Rules

- If `work/docx_semantic_ir.json` exists and the source DOCX has not changed, reuse it.
- If `work/docx_authoring_brief.md` exists and the IR has not changed, reuse it.
- If template analysis exists and the template has not changed, reuse it.
- If only one chapter changes, update that chapter and rerun compile, quality gate, and report.
- If quality gate fails, fix the smallest responsible module output rather than restarting the whole pipeline.
