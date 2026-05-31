#!/usr/bin/env python3
"""Write a resumable LaTeX authoring plan from saved pipeline artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def read_text(path: str | None) -> str:
    if not path:
        return ""
    file_path = Path(path)
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8", errors="ignore").strip()


def load_json(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    file_path = Path(path)
    if not file_path.exists():
        return {}
    raw = file_path.read_text(encoding="utf-8", errors="ignore").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"warning": f"Could not parse JSON: {file_path}"}


def bullet(key: str, value: Any) -> str:
    return f"- {key}: {value if value not in [None, '', []] else 'Not recorded'}"


def write_plan(args: argparse.Namespace) -> str:
    brief = read_text(args.brief)
    ir = load_json(args.ir)
    template_profile = load_json(args.template_profile)
    format_requirements = load_json(args.format_requirements)

    counts = ir.get("counts", {})
    lines = [
        "# LaTeX Authoring Plan",
        "",
        "This plan is a resumable handoff artifact between extraction/template analysis and final LaTeX authoring.",
        "",
        "## Inputs",
        "",
        bullet("Authoring brief", args.brief),
        bullet("DOCX semantic IR", args.ir),
        bullet("Template profile", args.template_profile),
        bullet("Format requirements", args.format_requirements),
        "",
        "## Source Summary",
        "",
        bullet("Paragraphs", counts.get("paragraphs")),
        bullet("Headings", counts.get("headings")),
        bullet("Tables", counts.get("tables")),
        bullet("Images", counts.get("images")),
        bullet("Equations", counts.get("equations")),
        bullet("Citation paragraphs", counts.get("citation_paragraphs")),
        "",
        "## Template Summary",
        "",
        bullet("Main file", template_profile.get("main_file")),
        bullet("Document class", template_profile.get("documentclass")),
        bullet("Bibliography system", template_profile.get("bibliography_system")),
        bullet("Needs preprocessing", template_profile.get("needs_preprocessing")),
        "",
        "## Authoring Modules",
        "",
        "1. Metadata and front matter",
        "2. Section/chapter structure",
        "3. Body prose and formulas",
        "4. Tables and captions",
        "5. Figures and figure groups",
        "6. Bibliography and citations",
        "7. Appendices and back matter",
        "8. Local review notes and conversion report items",
        "",
        "## Formula Policy",
        "",
        "- Preserve mathematical meaning before visual reconstruction.",
        "- Use standard matrix environments first; diagnose template line-height pollution before compact matrix fallbacks.",
        "- Use `\\displaystyle` for short inline Gaussian-binomial calculations that must remain inline.",
        "- Number only core formulas or formulas explicitly referenced later.",
        "",
        "## Resume Notes",
        "",
        "- If only one chapter changes, rerun that authoring module, then compile, quality gate, and report.",
        "- If source extraction changes, regenerate the authoring brief and this plan before editing LaTeX.",
        "- If template analysis changes, verify style-layer assumptions before rewriting content files.",
    ]

    if format_requirements:
        lines.extend(["", "## Format Requirement Snapshot", "", "```json", json.dumps(format_requirements, ensure_ascii=False, indent=2), "```"])
    if brief:
        lines.extend(["", "## Brief Excerpt", "", brief[:4000]])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a resumable LaTeX authoring plan.")
    parser.add_argument("--brief", required=True, help="work/docx_authoring_brief.md")
    parser.add_argument("--ir", help="work/docx_semantic_ir.json")
    parser.add_argument("--template-profile", help="work/template_analysis.json")
    parser.add_argument("--format-requirements", help="work/template_requirements.json")
    parser.add_argument("--output", "-o", required=True, help="Plan output path")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(write_plan(args), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
