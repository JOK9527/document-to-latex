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


def load_quality_gate(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    file_path = Path(path)
    if not file_path.exists():
        return {"warning": f"File not found: {file_path}"}
    raw = file_path.read_text(encoding="utf-8", errors="ignore").strip()
    if not raw:
        return {}
    if file_path.suffix.lower() == ".json":
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            return {"warning": f"Could not parse JSON from {file_path}: {exc}"}
    return {"markdown_path": str(file_path), "markdown_excerpt": raw[:4000]}


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
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            raw = stripped[1:-1]
        return [item.strip() for item in re_split_list(raw) if item.strip()]


def re_split_list(raw: str) -> list[str]:
    import re

    return re.split(r"[;,]", raw)


def merge_lists(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for item in group:
            if item and item not in merged:
                merged.append(item)
    return merged


def compile_status(compile_result: dict[str, Any]) -> tuple[str, list[str]]:
    if not compile_result:
        return "Not run", []
    if compile_result.get("environment_blocker"):
        return "Environment blocker", [str(compile_result.get("error", "LaTeX compiler unavailable."))]
    if compile_result.get("success") is True:
        return "True", []
    if compile_result.get("success") is False:
        return "False", []
    return str(compile_result.get("success", "Not run")), []


def write_report(args: argparse.Namespace) -> str:
    metadata = load_json(args.metadata)
    compile_result = load_json(args.compile_result)
    template_profile = load_json(args.template_profile)
    format_requirements = load_json(args.format_requirements)
    quality_gate = load_quality_gate(args.quality_gate)
    warnings = merge_lists(parse_list(args.warnings), parse_list(args.warnings_json), args.warning or [])
    sources = merge_lists(parse_list(args.sources), parse_list(args.sources_json), args.source or [])
    compile_success, compile_notes = compile_status(compile_result)
    warnings = merge_lists(warnings, compile_notes)

    lines = [
        "# Conversion Report",
        "",
        "## Summary",
        "",
        f"- Source: {metadata.get('path', 'Not recorded')}",
        f"- Format: {metadata.get('format', 'Not recorded')}",
        f"- Template: {args.template or 'Default or not recorded'}",
        f"- Compile status: {compile_success}",
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
            "## Quality Gate",
            "",
            f"- Findings: {quality_gate.get('counts', {}).get('findings', 'Not recorded')}",
            f"- Errors: {quality_gate.get('counts', {}).get('errors', 'Not recorded')}",
            f"- Warnings: {quality_gate.get('counts', {}).get('warnings', 'Not recorded')}",
            f"- Report: {quality_gate.get('markdown_path', args.quality_gate or 'Not recorded')}",
            "",
            "## Build",
            "",
            f"- Command: {compile_result.get('command', 'Not recorded')}",
            f"- Log: {compile_result.get('log_path', 'Not recorded')}",
            f"- Environment blocker: {compile_result.get('environment_blocker', False)}",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Write document-to-LaTeX conversion report.")
    parser.add_argument("--metadata", help="JSON metadata from detect_document.py")
    parser.add_argument("--compile-result", help="JSON result from compile_latex.py")
    parser.add_argument("--template-profile", help="JSON result from analyze_template.py")
    parser.add_argument("--format-requirements", help="JSON result from extract_format_requirements.py")
    parser.add_argument("--quality-gate", help="JSON or Markdown result from quality_gate.py")
    parser.add_argument("--template", help="Template name or path used")
    parser.add_argument("--requirements-summary", help="Short text summary of applied requirements")
    parser.add_argument("--sources", help="Backward-compatible source list: JSON list or semicolon/comma-separated text")
    parser.add_argument("--warnings", help="Backward-compatible warning list: JSON list or semicolon/comma-separated text")
    parser.add_argument("--sources-json", help="JSON list of original source material paths or descriptions")
    parser.add_argument("--warnings-json", help="JSON list of warning strings")
    parser.add_argument("--source", action="append", help="Repeatable source material path or description")
    parser.add_argument("--warning", action="append", help="Repeatable warning/manual review item")
    parser.add_argument("--output", default="conversion_report.md", help="Report path")
    args = parser.parse_args()

    Path(args.output).write_text(write_report(args), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
