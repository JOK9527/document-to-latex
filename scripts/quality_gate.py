#!/usr/bin/env python3
"""Run delivery checks for generated document-to-latex projects.

This lightweight gate catches issues that are easy to miss in an editing pass:
flat content layouts, mojibake in Chinese LaTeX, unreferenced assets, and
missing delivery reports.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


MOJIBAKE_TOKENS = [
    "锛",
    "鐨",
    "鑸",
    "垫",
    "浠",
    "妯",
    "绯",
    "璇",
    "鎺",
    "鍥",
    "琛",
    "寮",
    "瀛",
    "粨",
    "姘",
    "戣",
    "缂",
]
TEXT_SUFFIXES = {".tex", ".bib", ".md", ".cls", ".sty", ".def"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".pdf"}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def cjk_count(text: str) -> int:
    return sum(1 for char in text if "\u4e00" <= char <= "\u9fff")


def png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", header[16:24])


def tex_files(project: Path) -> list[Path]:
    return sorted(path for path in project.rglob("*") if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES)


def image_files(project: Path) -> list[Path]:
    content = project / "content"
    root = content if content.exists() else project
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)


def check_mojibake(project: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in tex_files(project):
        text = read_text(path)
        token_hits = sum(text.count(token) for token in MOJIBAKE_TOKENS)
        cjk = cjk_count(text)
        suspicious_ratio = token_hits / max(1, cjk)
        if token_hits >= 10 and suspicious_ratio >= 0.015:
            findings.append(
                {
                    "severity": "error",
                    "check": "mojibake",
                    "path": str(path),
                    "message": f"Possible mojibake: {token_hits} suspicious Chinese tokens among {cjk} CJK chars.",
                }
            )
    return findings


def check_structure(project: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not (project / "main.tex").exists():
        findings.append({"severity": "error", "check": "structure", "message": "Missing main.tex."})
    if not (project / "source").exists():
        findings.append({"severity": "warning", "check": "structure", "message": "Missing source/ directory for original materials."})
    if not (project / "conversion_report.md").exists():
        findings.append({"severity": "warning", "check": "structure", "message": "Missing conversion_report.md."})

    content = project / "content"
    if content.exists():
        flat_tex = sorted(path for path in content.glob("*.tex") if path.is_file())
        semantic_dirs = [content / "article", content / "report", content / "thesis"]
        has_semantic_tex = any(directory.exists() and any(directory.rglob("*.tex")) for directory in semantic_dirs)
        if len(flat_tex) > 2 and not has_semantic_tex:
            findings.append(
                {
                    "severity": "warning",
                    "check": "structure",
                    "message": f"Flat content/ layout has {len(flat_tex)} root .tex files; prefer content/article, content/report, or content/thesis/...",
                    "paths": [str(path) for path in flat_tex],
                }
            )
    else:
        findings.append({"severity": "error", "check": "structure", "message": "Missing content/ directory."})
    return findings


def used_graphics(project: Path) -> set[Path]:
    used: set[Path] = set()
    pattern = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
    for path in tex_files(project):
        text = read_text(path)
        for match in pattern.finditer(text):
            raw = match.group(1).strip()
            candidate = (project / raw).resolve()
            if candidate.exists():
                used.add(candidate)
                continue
            if candidate.suffix:
                continue
            for suffix in IMAGE_SUFFIXES:
                with_suffix = candidate.with_suffix(suffix)
                if with_suffix.exists():
                    used.add(with_suffix.resolve())
                    break
    return used


def check_images(project: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    images = image_files(project)
    used = used_graphics(project)
    unreferenced = [path for path in images if path.resolve() not in used]
    if images and len(unreferenced) / len(images) > 0.35:
        findings.append(
            {
                "severity": "warning",
                "check": "images",
                "message": f"{len(unreferenced)} of {len(images)} image assets are not referenced by LaTeX.",
            }
        )

    tiny: list[str] = []
    for path in images:
        dimensions = png_dimensions(path)
        if path.stat().st_size < 1024:
            tiny.append(str(path))
            continue
        if dimensions and (dimensions[0] < 24 or dimensions[1] < 24):
            tiny.append(str(path))
    if len(tiny) >= 5:
        findings.append(
            {
                "severity": "warning",
                "check": "images",
                "message": f"{len(tiny)} image assets look like tiny fragments or legends; review before delivery.",
                "paths": tiny[:20],
            }
        )
    return findings


def table_blocks(text: str) -> list[str]:
    pattern = re.compile(
        r"\\begin\{(?:table|longtable|tabular|tabularx|tblr)\}.*?\\end\{(?:table|longtable|tabular|tabularx|tblr)\}",
        re.S,
    )
    return [match.group(0) for match in pattern.finditer(text)]


def check_table_style(project: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    offenders: list[str] = []
    for path in tex_files(project):
        text = read_text(path)
        for block in table_blocks(text):
            hline_count = len(re.findall(r"\\hline\b", block))
            has_booktabs = any(rule in block for rule in [r"\toprule", r"\midrule", r"\bottomrule"])
            if hline_count >= 2 and not has_booktabs:
                offenders.append(str(path))
                break
    if offenders:
        findings.append(
            {
                "severity": "warning",
                "check": "table_style",
                "message": f"{len(offenders)} file(s) contain Word-style bordered tables using repeated \\hline; prefer academic three-line tables.",
                "paths": offenders,
            }
        )
    return findings


def run_quality_gate(project: Path) -> dict[str, Any]:
    findings = []
    findings.extend(check_structure(project))
    findings.extend(check_mojibake(project))
    findings.extend(check_images(project))
    findings.extend(check_table_style(project))
    return {
        "schema": "document-to-latex.quality-gate.v1",
        "project": str(project),
        "counts": {
            "findings": len(findings),
            "errors": sum(1 for item in findings if item.get("severity") == "error"),
            "warnings": sum(1 for item in findings if item.get("severity") == "warning"),
        },
        "findings": findings,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Quality Gate Report",
        "",
        f"- Project: {result['project']}",
        f"- Findings: {result['counts']['findings']}",
        f"- Errors: {result['counts']['errors']}",
        f"- Warnings: {result['counts']['warnings']}",
        "",
        "## Findings",
        "",
    ]
    if not result["findings"]:
        lines.append("- No quality gate findings.")
    for item in result["findings"]:
        lines.append(f"- [{item['severity']}] {item['check']}: {item['message']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run document-to-latex delivery quality checks.")
    parser.add_argument("project", help="Generated LaTeX project directory")
    parser.add_argument("--output", "-o", help="Optional JSON or Markdown report path")
    parser.add_argument("--fail-on-warning", action="store_true", help="Return non-zero when warnings are present")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    result = run_quality_gate(project)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.suffix.lower() == ".md":
            output.write_text(render_markdown(result), encoding="utf-8")
        else:
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print(render_markdown(result))

    if result["counts"]["errors"] or (args.fail_on_warning and result["counts"]["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
