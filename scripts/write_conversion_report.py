#!/usr/bin/env python3
"""Write a Markdown conversion report from JSON metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def load_json(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    file_path = Path(path)
    if not file_path.exists():
        return {"warning": f"File not found: {file_path}"}
    raw = file_path.read_text(encoding="utf-8", errors="ignore").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        return {"warning": f"Could not parse JSON from {file_path}: {exc}"}


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- None recorded"]


def parse_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        return [str(parsed)]
    except json.JSONDecodeError:
        return [item.strip() for item in re_split_list(raw) if item.strip()]


def re_split_list(raw: str) -> list[str]:
    import re

    return re.split(r"[;,]", raw)


def write_report(args: argparse.Namespace) -> str:
    metadata = load_json(args.metadata)
    compile_result = load_json(args.compile_result)
    template_profile = load_json(args.template_profile)
    format_requirements = load_json(args.format_requirements)
    warnings = parse_list(args.warnings)
    sources = parse_list(args.sources)

    lines = [
        "# Conversion Report",
        "",
        "## Summary",
        "",
        f"- Source: {metadata.get('path', 'Not recorded')}",
        f"- Format: {metadata.get('format', 'Not recorded')}",
        f"- Template: {args.template or 'Default or not recorded'}",
        f"- Compile success: {compile_result.get('success', 'Not run')}",
        "",
        "## Source Materials",
        "",
        *bullet_lines(sources),
        "",
        "## Detected Features",
        "",
    ]

    for key in sorted(metadata):
        if key not in {"path", "name", "extension", "format"}:
            lines.append(f"- {key}: {metadata[key]}")

    lines.extend(
        [
            "",
            "## Template Profile",
            "",
            f"- Main file: {template_profile.get('main_file', 'Not recorded')}",
            f"- Document class: {template_profile.get('documentclass', 'Not recorded')}",
            f"- Bibliography system: {template_profile.get('bibliography_system', 'Not recorded')}",
            f"- Needs preprocessing: {template_profile.get('needs_preprocessing', 'Not recorded')}",
            "",
            "## Applied Requirements",
            "",
            args.requirements_summary or "No explicit requirements summary was provided.",
            "",
            "```json",
            json.dumps(format_requirements, ensure_ascii=False, indent=2) if format_requirements else "{}",
            "```",
            "",
            "## Warnings and Manual Review",
            "",
            *bullet_lines(warnings),
            "",
            "## Build",
            "",
            f"- Command: {compile_result.get('command', 'Not recorded')}",
            f"- Log: {compile_result.get('log_path', 'Not recorded')}",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Write document-to-LaTeX conversion report.")
    parser.add_argument("--metadata", help="JSON metadata from detect_document.py")
    parser.add_argument("--compile-result", help="JSON result from compile_latex.py")
    parser.add_argument("--template-profile", help="JSON result from analyze_template.py")
    parser.add_argument("--format-requirements", help="JSON result from extract_format_requirements.py")
    parser.add_argument("--template", help="Template name or path used")
    parser.add_argument("--requirements-summary", help="Short text summary of applied requirements")
    parser.add_argument("--sources", help="JSON list of original source material paths or descriptions")
    parser.add_argument("--warnings", help="JSON list of warning strings")
    parser.add_argument("--output", default="conversion_report.md", help="Report path")
    args = parser.parse_args()

    Path(args.output).write_text(write_report(args), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
