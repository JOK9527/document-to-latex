#!/usr/bin/env python3
"""Create a lightweight JSON profile for a document-to-LaTeX source file."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path


TEXT_EXTENSIONS = {".md", ".markdown", ".txt", ".tex", ".html", ".htm"}


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def has_chinese(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def read_text_sample(path: Path, limit: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def profile_text(path: Path) -> dict:
    sample = read_text_sample(path)
    return {
        "word_count_estimate": len(re.findall(r"\w+", sample)),
        "has_chinese": has_chinese(sample),
        "has_markdown_tables": bool(re.search(r"^\s*\|.+\|\s*$", sample, re.MULTILINE)),
        "has_latex_math_markers": bool(re.search(r"(\$\$?|\\\[|\\\(|\\begin\{equation\})", sample)),
        "has_html_tags": bool(re.search(r"<(html|body|table|img|p|h[1-6])\b", sample, re.I)),
    }


def profile_docx(path: Path) -> dict:
    result = {
        "has_chinese": False,
        "has_images": False,
        "has_tables": False,
        "has_formulas": False,
        "paragraph_count_estimate": None,
    }
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
            result["has_chinese"] = has_chinese(xml)
            result["has_images"] = any(name.startswith("word/media/") for name in names)
            result["has_tables"] = "<w:tbl" in xml
            result["has_formulas"] = "<m:oMath" in xml or "<m:oMathPara" in xml
            result["paragraph_count_estimate"] = xml.count("<w:p")
    except Exception as exc:  # Keep detection useful even for damaged files.
        result["warning"] = f"Could not inspect DOCX internals: {exc}"
    return result


def profile_pdf(path: Path) -> dict:
    data = path.read_bytes()
    page_count = len(re.findall(rb"/Type\s*/Page\b", data))
    image_count = len(re.findall(rb"/Subtype\s*/Image\b", data))
    text_markers = len(re.findall(rb"\b(BT|ET|Tj|TJ)\b", data[:2_000_000]))
    return {
        "page_count_estimate": page_count or None,
        "image_count_estimate": image_count,
        "may_be_scanned": image_count > 0 and text_markers < max(3, page_count),
        "has_text_markers": text_markers > 0,
    }


def detect(path: Path) -> dict:
    suffix = path.suffix.lower()
    result = {
        "path": str(path),
        "name": path.name,
        "extension": suffix,
        "size_bytes": path.stat().st_size,
        "format": suffix.lstrip(".") or "unknown",
    }

    if suffix in TEXT_EXTENSIONS:
        result.update(profile_text(path))
    elif suffix == ".docx":
        result.update(profile_docx(path))
    elif suffix == ".pdf":
        result.update(profile_pdf(path))
    else:
        result["warning"] = "Unsupported or unknown format; inspect manually."

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect document features for LaTeX conversion.")
    parser.add_argument("source", help="Source document path")
    parser.add_argument("--output", "-o", help="Optional JSON output path")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    if not source.exists():
        print(json.dumps({"error": f"Source not found: {source}"}, indent=2), file=sys.stderr)
        return 1

    result = detect(source)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
