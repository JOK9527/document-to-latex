#!/usr/bin/env python3
"""Write an AI authoring brief from a DOCX semantic IR."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def shorten(text: str | None, limit: int = 180) -> str:
    if not text:
        return ""
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def section_outline(paragraphs: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for paragraph in paragraphs:
        if paragraph.get("role") in {"heading", "heading_candidate"}:
            level = paragraph.get("level") or 1
            marker = "#" * min(6, int(level) + 2)
            role = paragraph.get("role")
            note = " (candidate; verify)" if role == "heading_candidate" else ""
            lines.append(f"{marker} {shorten(paragraph.get('text'), 120)}{note}")
    return lines


def nearby_body(paragraphs: list[dict[str, Any]], paragraph_id: str | None, radius: int = 2) -> list[str]:
    if not paragraph_id:
        return []
    index = next((i for i, paragraph in enumerate(paragraphs) if paragraph.get("id") == paragraph_id), None)
    if index is None:
        return []
    result: list[str] = []
    for paragraph in paragraphs[max(0, index - radius) : min(len(paragraphs), index + radius + 1)]:
        text = shorten(paragraph.get("text"), 160)
        if text:
            result.append(f"- {paragraph.get('id')} ({paragraph.get('role')}): {text}")
    return result


def write_brief(ir: dict[str, Any]) -> str:
    paragraphs = ir.get("paragraphs", [])
    lines = [
        "# DOCX-to-LaTeX Authoring Brief",
        "",
        "This brief is for AI authoring. Use it with the DOCX source, template profile, and format requirements before writing final LaTeX.",
        "",
        "## Non-Negotiable Rules",
        "",
        "- Treat the DOCX as an imperfect academic draft, not a perfect source.",
        "- Preserve meaning and technical claims.",
        "- Fix obvious formatting noise, but do not invent missing data.",
        "- Use template-native commands and keep style out of content files.",
        "- Rebuild clear academic tables as three-line tables; do not preserve Word border grids unless required.",
        "- Render every extracted data table in LaTeX when rows and cells are available, even if the DOCX has no caption.",
        "- For a table without a caption, infer a conservative provisional caption from nearby text or table contents and record it in the report.",
        "- Treat Word/PDF formula layout as untrusted: preserve math content, then rebuild LaTeX environments, numbering, labels, references, and visual form.",
        "- Number only core formulas or formulas explicitly referenced later; use unnumbered display math for examples, substitutions, and proof steps.",
        "- Replace clear manual equation numbers and references with semantic labels and \\eqref.",
        "- Treat each pipeline stage as resumable: read saved upstream artifacts and write downstream artifacts instead of relying on hidden state.",
        "- Mark uncertain tables, captions, formulas, and references in the report.",
        "- Ask no extra questions unless a missing answer materially changes the output.",
        "",
        "## Extraction Counts",
        "",
    ]
    for key, value in ir.get("counts", {}).items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Source Defects To Handle", ""])
    defects = ir.get("defects", [])
    if not defects:
        lines.append("- No source defects detected by the heuristic pass.")
    for defect in defects:
        lines.append(f"- {defect}")

    lines.extend(["", "## Section Outline", ""])
    outline = section_outline(paragraphs)
    if outline:
        lines.extend(outline)
    else:
        lines.append("- No reliable headings detected. Infer structure conservatively from paragraphs and formatting requirements.")

    lines.extend(["", "## Figures", ""])
    images = ir.get("images", [])
    if not images:
        lines.append("- No embedded images detected.")
    for image in images:
        caption = image.get("nearby_caption") or "(no nearby caption)"
        lines.append(f"- {image.get('id')}: {caption}")
        context = nearby_body(paragraphs, image.get("paragraph_id"))
        if context:
            lines.append("  Nearby text:")
            lines.extend(f"  {item}" for item in context)

    lines.extend(["", "## Tables", ""])
    tables = ir.get("tables", [])
    if not tables:
        lines.append("- No Word tables detected.")
    for table in tables:
        caption = table.get("caption") or "(no caption)"
        notes = table.get("quality_notes") or []
        lines.append(f"- {table.get('id')}: {len(table.get('rows') or [])} row(s), caption: {caption}")
        if not table.get("caption"):
            lines.append("  - Required: do not skip this table. Create a provisional semantic caption and list it as an assumption in conversion_report.md.")
        lines.append("  - Authoring: use a three-line table with template-native rules or booktabs.")
        for note in notes:
            lines.append(f"  - Review: {note}")

    lines.extend(["", "## Formulas", ""])
    lines.extend(
        [
            "Formula policy:",
            "- Word/PDF spacing, line breaks, indentation, and manual equation numbers are draft signals, not authoritative formatting.",
            "- Use inline math for prose formulas, `\\[...\\]` for ordinary displays, `\\[ \\begin{aligned}...\\end{aligned} \\]` for unnumbered derivations, and `equation` with `\\label` for core numbered formulas.",
            "- Use `equation + aligned` when one logical formula needs multiple lines but only one number.",
            "- Avoid numbered `align` unless every row is independently referenced.",
            "- Use standard `pmatrix`/`bmatrix`/`matrix` for ordinary matrices. If compiled matrices look stretched while the source looks normal, inspect template line-height hooks before changing body formulas.",
            "- Keep short inline Gaussian binomial calculations in place with `\\displaystyle`; do not detach them into centered display math unless they are genuinely long.",
            "- When one formula-shape issue is confirmed, search the whole chapter or project for the same macro/context before stopping.",
            "- Define repeated special math shapes in the template or preamble, but keep compact matrix macros as fallbacks rather than the ordinary matrix path.",
            "",
        ]
    )
    equations = ir.get("equations", [])
    if not equations:
        lines.append("- No OMML/math objects detected.")
    for equation in equations:
        hint = shorten(equation.get("text_hint"), 120) or "(no text hint)"
        lines.append(f"- {equation.get('id')} near {equation.get('paragraph_id')}: {hint}; reconstruct as editable LaTeX if reliable, otherwise keep an in-place review fallback.")

    lines.extend(["", "## Pipeline Artifacts", ""])
    lines.extend(
        [
            "- Read this brief as the saved planning artifact for downstream LaTeX authoring.",
            "- Reuse `work/docx_semantic_ir.json` and this brief when the DOCX source has not changed.",
            "- Save thesis type decisions, generated LaTeX, quality gate output, and conversion report as separate artifacts so each stage can be rerun independently.",
        ]
    )

    lines.extend(["", "## Authoring Plan", ""])
    lines.extend(
        [
            "1. Choose the target template structure.",
            "2. Map reliable DOCX headings to LaTeX sections or chapters.",
            "3. Rewrite prose into natural academic LaTeX without preserving Word styling noise.",
            "4. Rebuild formula environments and references under the formula normalization rules.",
            "5. Place figures, tables, and formulas near the text that explains them.",
            "6. Keep uncertain conversions as concise LaTeX comments and report items.",
            "7. Compile, run the quality gate, and repair the smallest responsible issues.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Write an AI authoring brief from DOCX semantic IR.")
    parser.add_argument("ir", help="DOCX semantic IR JSON path")
    parser.add_argument("--output", "-o", required=True, help="Markdown brief output path")
    args = parser.parse_args()

    ir = load_json(Path(args.ir))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(write_brief(ir), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
