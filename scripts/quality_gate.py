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
UNSUPPORTED_GRAPHICS_SUFFIXES = {".wmf", ".emf"}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


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


def graphics_references(project: Path) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    pattern = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
    for path in tex_files(project):
        text = read_text(path)
        for match in pattern.finditer(text):
            raw = match.group(1).strip()
            candidate = (project / raw).resolve()
            resolved: Path | None = None
            if candidate.exists():
                resolved = candidate
            elif not candidate.suffix:
                for suffix in IMAGE_SUFFIXES:
                    with_suffix = candidate.with_suffix(suffix)
                    if with_suffix.exists():
                        resolved = with_suffix.resolve()
                        break
            references.append(
                {
                    "path": path,
                    "raw": raw,
                    "resolved": resolved,
                    "suffix": candidate.suffix.lower(),
                }
            )
    return references


def used_graphics(project: Path) -> set[Path]:
    used: set[Path] = set()
    for reference in graphics_references(project):
        resolved = reference.get("resolved")
        if isinstance(resolved, Path):
            used.add(resolved)
    return used


def check_images(project: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    references = graphics_references(project)
    missing = [f"{item['path']}: {item['raw']}" for item in references if item.get("resolved") is None]
    unsupported = [
        f"{item['path']}: {item['raw']}"
        for item in references
        if (item.get("suffix") or "").lower() in UNSUPPORTED_GRAPHICS_SUFFIXES
    ]
    if missing:
        findings.append(
            {
                "severity": "error",
                "check": "missing_graphics",
                "message": f"{len(missing)} included graphics file(s) cannot be resolved. Use an in-place placeholder instead of silently dropping figures or formula images.",
                "paths": missing[:20],
            }
        )
    if unsupported:
        findings.append(
            {
                "severity": "error",
                "check": "unsupported_graphics",
                "message": f"{len(unsupported)} WMF/EMF graphic reference(s) remain. Convert them to a supported fallback such as PNG/PDF, or keep a visible in-place review placeholder.",
                "paths": unsupported[:20],
            }
        )
    if missing or unsupported:
        findings.extend(check_review_placeholders(project))

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


def environment_blocks(text: str, environments: tuple[str, ...]) -> list[tuple[str, str]]:
    names = "|".join(re.escape(name) for name in environments)
    pattern = re.compile(rf"\\begin\{{({names})\}}.*?\\end\{{\1\}}", re.S)
    return [(match.group(1), match.group(0)) for match in pattern.finditer(text)]


def table_blocks(text: str) -> list[str]:
    return [block for _, block in environment_blocks(text, ("table", "longtable", "tabular", "tabularx", "tblr"))]


def check_review_placeholders(project: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    offenders: list[str] = []
    pattern = re.compile(
        r"(REVIEW|TODO|待复核|待确认|人工复核|placeholder|占位)",
        re.I,
    )
    for path in tex_files(project):
        if pattern.search(read_text(path)):
            offenders.append(str(path))
    if not offenders:
        findings.append(
            {
                "severity": "warning",
                "check": "review_placeholders",
                "message": "No visible review placeholder was found. When content cannot be reliably converted, keep an in-place warning block instead of relying only on the report.",
            }
        )
    return findings


def check_figure_table_semantics(project: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    longtable_graphics: list[str] = []
    table_graphics: list[str] = []
    for path in tex_files(project):
        text = read_text(path)
        for env, block in environment_blocks(text, ("longtable", "table")):
            if r"\includegraphics" not in block:
                continue
            if env == "longtable":
                longtable_graphics.append(str(path))
            elif r"\caption" in block:
                table_graphics.append(str(path))
    if longtable_graphics:
        findings.append(
            {
                "severity": "warning",
                "check": "longtable_graphics",
                "message": "longtable contains graphics. This usually means an image group was treated as a data table; use figure/subfigure/minipage layout or an in-place figure-group placeholder.",
                "paths": sorted(set(longtable_graphics)),
            }
        )
    if table_graphics:
        findings.append(
            {
                "severity": "warning",
                "check": "table_graphics",
                "message": "A table environment contains graphics and a caption. Verify that image content was not mislabeled as a table.",
                "paths": sorted(set(table_graphics)),
            }
        )
    return findings


def rendered_table_count(project: Path) -> int:
    count = 0
    pattern = re.compile(r"\\begin\{(?:table|longtable|sidewaystable)\}")
    for path in tex_files(project):
        count += len(pattern.findall(read_text(path)))
    return count


def check_table_placeholders(project: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    offenders: list[str] = []
    pattern = re.compile(r"%\s*REVIEW:.*(?:table|tabular|caption|表格|表题|表注|三线表)", re.I)
    for path in tex_files(project):
        text = read_text(path)
        if pattern.search(text):
            offenders.append(str(path))
    if offenders:
        findings.append(
            {
                "severity": "warning",
                "check": "table_placeholders",
                "message": "Table-related REVIEW placeholders remain in LaTeX; extracted tables should be rendered, not left as comments.",
                "paths": offenders,
            }
        )
    return findings


def check_table_coverage(project: Path, ir: dict[str, Any] | None) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not ir:
        return findings
    extracted = len(ir.get("tables") or [])
    rendered = rendered_table_count(project)
    if extracted and rendered < extracted:
        findings.append(
            {
                "severity": "warning",
                "check": "table_coverage",
                "message": f"DOCX IR has {extracted} extracted table(s), but LaTeX appears to render only {rendered}. Missing captions are not a reason to omit tables.",
            }
        )
    return findings


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


def run_quality_gate(project: Path, ir: dict[str, Any] | None = None) -> dict[str, Any]:
    findings = []
    findings.extend(check_structure(project))
    findings.extend(check_mojibake(project))
    findings.extend(check_images(project))
    findings.extend(check_figure_table_semantics(project))
    findings.extend(check_table_coverage(project, ir))
    findings.extend(check_table_placeholders(project))
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
    parser.add_argument("--ir", help="Optional DOCX semantic IR JSON path for coverage checks")
    parser.add_argument("--output", "-o", help="Optional JSON or Markdown report path")
    parser.add_argument("--fail-on-warning", action="store_true", help="Return non-zero when warnings are present")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    ir = load_json(Path(args.ir)) if args.ir else None
    result = run_quality_gate(project, ir)
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
