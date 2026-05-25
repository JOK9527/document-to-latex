#!/usr/bin/env python3
"""Write an authoring brief for AI-assisted PDF-to-LaTeX reconstruction.

This is deliberately not a renderer. It summarizes what the AI must understand
before writing the final LaTeX by hand: section intent, paragraph flow, assets,
references, and unresolved extraction risks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def shorten(text: str, limit: int = 180) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "…"


def group_by_section(items: list[dict[str, Any]]) -> dict[str | None, list[dict[str, Any]]]:
    grouped: dict[str | None, list[dict[str, Any]]] = {}
    for item in items:
        grouped.setdefault(item.get("section_id"), []).append(item)
    return grouped


def section_assets(ir: dict[str, Any], section_id: str | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    blocks = []
    deferred = []
    for plan in ir.get("placement_plan", []):
        if plan.get("section_id") == section_id:
            blocks.extend(plan.get("blocks", []))
            deferred.extend(plan.get("deferred_assets", []))
    asset_ids = {block.get("id") for block in blocks + deferred}
    graphics = [item for item in ir.get("graphics", []) if item.get("id") in asset_ids]
    tables = [item for item in ir.get("tables", []) if item.get("id") in asset_ids]
    formulas = [item for item in ir.get("formulas", []) if item.get("id") in asset_ids]
    return graphics, tables, formulas


def write_brief(ir: dict[str, Any]) -> str:
    paragraphs_by_section = group_by_section(ir.get("paragraphs", []))
    sections = ir.get("sections", [])
    lines = [
        "# PDF-to-LaTeX Authoring Brief",
        "",
        "This brief is for AI authoring, not mechanical rendering. Read it together with the source PDF and IR before writing final LaTeX.",
        "",
        "## Non-Negotiable Rules",
        "",
        "- Reconstruct target-template prose; never preserve source PDF line breaks.",
        "- Treat citation markers like `[1]` and `[2-6]` as citations/prose, not formulas.",
        "- Insert figures, tables, and formulas because the surrounding text needs them, not because their source coordinates say so.",
        "- If a figure/table has no clear semantic role, leave it deferred with a review note instead of forcing it into the chapter.",
        "- Write final chapters as an editor would: understand the section, then compose maintainable LaTeX.",
        "",
        "## Extraction Counts",
        "",
    ]
    for key, value in ir.get("counts", {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Section Writing Plan", ""])

    pseudo_sections = [{"id": None, "title": "Front matter / introduction before first numbered section", "level": 1, "page": 1}]
    pseudo_sections.extend(sections)
    for section in pseudo_sections:
        section_id = section.get("id")
        paragraphs = paragraphs_by_section.get(section_id, [])
        graphics, tables, formulas = section_assets(ir, section_id)
        if not paragraphs and not graphics and not tables and not formulas:
            continue
        lines.extend(
            [
                f"### {section.get('title')}",
                "",
                f"- Page: {section.get('page')}",
                f"- Paragraph candidates: {len(paragraphs)}",
                f"- Figure candidates: {len(graphics)}",
                f"- Table candidates: {len(tables)}",
                f"- Formula candidates: {len(formulas)}",
                "",
                "Paragraph flow to rewrite:",
            ]
        )
        for paragraph in paragraphs[:8]:
            refs = paragraph.get("references") or {}
            ref_text = f" refs={refs}" if refs else ""
            lines.append(f"- {paragraph.get('id')}: {shorten(paragraph.get('text', ''))}{ref_text}")
        if len(paragraphs) > 8:
            lines.append(f"- ... {len(paragraphs) - 8} more paragraph candidates")
        if graphics:
            lines.extend(["", "Figures to understand before placement:"])
            for graphic in graphics:
                caption = graphic.get("caption_text") or "(no caption)"
                reason = graphic.get("placement_hint") or "review semantic placement"
                lines.append(f"- {graphic.get('id')} {graphic.get('latex_label')}: {caption}; {reason}")
        if tables:
            lines.extend(["", "Tables to reconstruct or mark for review:"])
            for table in tables:
                lines.append(f"- {table.get('id')} {table.get('latex_label')}: {table.get('caption_text')}; {table.get('placement_hint')}")
        if formulas:
            lines.extend(["", "Formula candidates requiring real math understanding:"])
            for formula in formulas[:8]:
                lines.append(f"- {formula.get('id')}: {shorten(formula.get('text', ''), 120)}")
            if len(formulas) > 8:
                lines.append(f"- ... {len(formulas) - 8} more formula candidates")
        lines.append("")

    lines.extend(["## Quality Notes", ""])
    notes = ir.get("quality_notes") or []
    lines.extend(f"- {note}" for note in notes) if notes else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    warnings = ir.get("warnings") or []
    lines.extend(f"- {warning}" for warning in warnings[:80]) if warnings else lines.append("- None")
    if len(warnings) > 80:
        lines.append(f"- ... {len(warnings) - 80} more warnings")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Write an AI authoring brief from PDF semantic IR.")
    parser.add_argument("ir", help="PDF semantic IR JSON path")
    parser.add_argument("--output", "-o", required=True, help="Markdown brief output path")
    args = parser.parse_args()

    ir = load_json(Path(args.ir))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(write_brief(ir), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
