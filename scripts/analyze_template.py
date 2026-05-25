#!/usr/bin/env python3
"""Analyze a LaTeX template directory and emit a template profile as JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


AUXILIARY_EXTENSIONS = {
    ".aux",
    ".bbl",
    ".bcf",
    ".blg",
    ".fdb_latexmk",
    ".fls",
    ".log",
    ".out",
    ".run.xml",
    ".synctex.gz",
    ".toc",
}

STYLE_EXTENSIONS = {".cls", ".sty", ".def", ".cfg", ".clo"}
ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".eps", ".svg"}


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def read_text(path: Path, limit: int = 400_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def find_tex_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.tex") if path.is_file())


def score_main_candidate(path: Path, root: Path, text: str) -> int:
    score = 0
    name = path.name.lower()
    if name in {"main.tex", "thesis.tex", "paper.tex", "article.tex", "root.tex"}:
        score += 8
    if name in {"bachelor.tex", "graduate.tex", "master.tex", "phd.tex"}:
        score += 10
    if "\\documentclass" in text:
        score += 25
    if "\\begin{document}" in text:
        score += 10
    if "\\end{document}" in text:
        score += 7
    if "\\input" in text or "\\include" in text:
        score += 2
    # Template body files often contain the document environment but no class.
    # Prefer the driver file with documentclass when both are present.
    if "\\begin{document}" in text and "\\documentclass" not in text:
        score -= 8
    depth = len(path.relative_to(root).parts)
    score -= max(0, depth - 1)
    return score


def parse_commands(text: str) -> dict[str, Any]:
    documentclass = None
    class_match = re.search(r"\\documentclass(?:\[[^\]]*\])?\{([^}]+)\}", text)
    if class_match:
        documentclass = class_match.group(1)

    packages = re.findall(r"\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}", text)
    split_packages = []
    for package_group in packages:
        split_packages.extend(item.strip() for item in package_group.split(",") if item.strip())

    inputs = re.findall(r"\\(?:input|include)\{([^}]+)\}", text)
    bibliographies = re.findall(r"\\(?:bibliography|addbibresource)\{([^}]+)\}", text)
    labels = re.findall(r"\\label\{([^}]+)\}", text)

    return {
        "documentclass": documentclass,
        "packages": sorted(set(split_packages)),
        "inputs": inputs,
        "bibliography_files": bibliographies,
        "label_count": len(labels),
    }


def detect_bibliography_system(text: str, packages: list[str]) -> str | None:
    package_set = set(packages)
    if "biblatex" in package_set or "\\addbibresource" in text or "\\printbibliography" in text:
        return "biblatex/biber"
    if "natbib" in package_set:
        return "natbib/bibtex"
    if "\\bibliography" in text or "\\bibliographystyle" in text:
        return "bibtex"
    return None


def detect_metadata_fields(text: str) -> list[str]:
    fields = []
    patterns = {
        "title": r"\\title\{",
        "author": r"\\author\{",
        "date": r"\\date\{",
        "abstract": r"\\begin\{abstract\}",
        "keywords": r"\\keywords?\{",
        "advisor": r"advisor|supervisor|导师",
        "school": r"school|university|学院|大学",
    }
    for field, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            fields.append(field)
    return fields


def detect_insertion_points(text: str) -> list[str]:
    points = []
    checks = {
        "document_body": r"\\begin\{document\}",
        "abstract": r"\\begin\{abstract\}|abstract",
        "chapters": r"\\(?:input|include)\{[^}]*chapter|\\chapter\{",
        "appendix": r"\\appendix|appendix",
        "bibliography": r"\\bibliography|\\printbibliography|\\addbibresource",
        "figures": r"\\includegraphics",
        "tables": r"\\begin\{(?:table|tabular|longtable|tabularx)\}",
    }
    for point, pattern in checks.items():
        if re.search(pattern, text, re.IGNORECASE):
            points.append(point)
    return points


def analyze(root: Path) -> dict[str, Any]:
    tex_files = find_tex_files(root)
    candidates = []
    aggregate_packages: Counter[str] = Counter()
    aggregate_inputs: list[str] = []
    aggregate_bibliography_files: list[str] = []
    aggregate_text_parts: list[str] = []

    for tex_file in tex_files:
        text = read_text(tex_file)
        parsed = parse_commands(text)
        for package in parsed["packages"]:
            aggregate_packages[package] += 1
        aggregate_inputs.extend(parsed["inputs"])
        aggregate_bibliography_files.extend(parsed["bibliography_files"])
        aggregate_text_parts.append(text[:80_000])
        candidates.append(
            {
                "path": rel(tex_file, root),
                "score": score_main_candidate(tex_file, root, text),
                "documentclass": parsed["documentclass"],
                "has_begin_document": "\\begin{document}" in text,
                "has_end_document": "\\end{document}" in text,
            }
        )

    candidates.sort(key=lambda item: (-item["score"], item["path"]))
    aggregate_text = "\n".join(aggregate_text_parts)
    style_files = sorted(rel(path, root) for path in root.rglob("*") if path.suffix.lower() in STYLE_EXTENSIONS)
    asset_files = sorted(rel(path, root) for path in root.rglob("*") if path.suffix.lower() in ASSET_EXTENSIONS)
    auxiliary_files = sorted(
        rel(path, root)
        for path in root.rglob("*")
        if path.is_file() and any(path.name.lower().endswith(ext) for ext in AUXILIARY_EXTENSIONS)
    )

    main_file = candidates[0]["path"] if candidates else None
    main_text = read_text(root / main_file) if main_file else ""
    main_parsed = parse_commands(main_text)

    warnings = []
    if len([item for item in candidates if item["score"] >= 15]) > 1:
        warnings.append("Multiple likely main TeX files were found.")
    if auxiliary_files:
        warnings.append("Stale auxiliary build files are present.")
    if re.search(r"[A-Za-z]:\\\\|/", aggregate_text) and re.search(r"[A-Za-z]:\\\\", aggregate_text):
        warnings.append("Possible absolute Windows paths found.")
    if not main_file:
        warnings.append("No TeX main file candidate found.")

    return {
        "template_root": str(root),
        "main_file": main_file,
        "main_candidates": candidates[:8],
        "documentclass": main_parsed["documentclass"],
        "style_files": style_files,
        "asset_files_count": len(asset_files),
        "asset_files_sample": asset_files[:20],
        "auxiliary_files": auxiliary_files,
        "packages": sorted(aggregate_packages),
        "duplicate_packages": sorted(package for package, count in aggregate_packages.items() if count > 1),
        "inputs": sorted(set(aggregate_inputs)),
        "bibliography_files": sorted(set(aggregate_bibliography_files)),
        "bibliography_system": detect_bibliography_system(aggregate_text, sorted(aggregate_packages)),
        "metadata_fields": detect_metadata_fields(aggregate_text),
        "insertion_points": detect_insertion_points(aggregate_text),
        "needs_preprocessing": bool(auxiliary_files or warnings),
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a LaTeX template directory.")
    parser.add_argument("template", help="Template directory")
    parser.add_argument("--output", "-o", help="Optional JSON output path")
    args = parser.parse_args()

    root = Path(args.template).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Template directory not found: {root}")

    profile = analyze(root)
    payload = json.dumps(profile, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
