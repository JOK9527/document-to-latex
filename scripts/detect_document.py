#!/usr/bin/env python3
"""Create a lightweight JSON profile for a DOC/DOCX-to-LaTeX source file."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def has_chinese(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


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


def detect(path: Path) -> dict:
    suffix = path.suffix.lower()
    result = {
        "path": str(path),
        "name": path.name,
        "extension": suffix,
        "size_bytes": path.stat().st_size,
        "format": suffix.lstrip(".") or "unknown",
    }

    if suffix == ".docx":
        result.update(profile_docx(path))
    elif suffix == ".doc":
        result["warning"] = "Binary .doc files are not parsed directly. Convert to .docx before running the active workflow."
    elif suffix == ".pdf":
        result["role"] = "reference_only"
        result["warning"] = "PDF is reference-only in this skill version. Provide DOC/DOCX as the primary source."
    else:
        result["warning"] = "Unsupported or unknown format; inspect manually."

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect DOC/DOCX source features for LaTeX conversion.")
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
