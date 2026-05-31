# AI Authoring Role

Use this reference to keep the workflow centered on AI understanding rather than turning the skill into a rigid converter.

## Position

This skill is an AI academic authoring workflow with script-backed evidence. Scripts collect facts, preserve artifacts, and run deterministic checks. The AI remains responsible for semantic judgment, local tradeoffs, and context-aware reconstruction.

## Script Responsibilities

Scripts should handle work that is deterministic, repeatable, or easy to verify:

- inspect source files and templates
- extract DOCX structure into reviewable IR
- export assets
- write intermediate artifacts
- record module freshness
- compile LaTeX
- detect obvious delivery issues
- summarize machine-readable reports

Scripts should not become the final authority for semantic decisions that require document context.

## AI Responsibilities

The AI should use script outputs as evidence while making context-aware decisions:

- decide whether a paragraph is a heading, proof, example, caption, or body text
- decide whether a formula should be numbered
- decide whether a manual equation reference can safely become `\eqref`
- decide whether a table is data, layout, or damaged source content
- decide whether adjacent images are a figure group, subfigures, or unrelated assets
- decide whether a formula image is reliable enough to reconstruct as editable LaTeX
- decide when to preserve, reconstruct, or mark a visible review note

## Evidence, Not Shackles

Intermediate artifacts are handoffs, not commands. If the AI finds that the IR, brief, template analysis, or quality gate warning is wrong in context, it may override the artifact and must record the reason in `conversion_report.md`.

Quality gate findings are prompts for judgment unless they are clear delivery blockers such as missing required files, unresolved graphics, compilation failure, or content loss.

## Avoid Over-Automation

Do not replace semantic judgment with broad mechanical rules. Prefer warnings over hard failures for issues that require context, such as inline display style, formula numbering, provisional captions, and uncertain references.

When a script can only detect a pattern, phrase the output as evidence for review. Let the AI decide the repair.
