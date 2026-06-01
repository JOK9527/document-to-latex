#!/usr/bin/env python3
"""Create a lightweight JSON profile for a DOC/DOCX-to-LaTeX source file."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def has_chinese(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def namespace_uri(tag: str) -> str | None:
    if tag.startswith("{") and "}" in tag:
        return tag[1:].split("}", 1)[0]
    return None


def local_name(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def body_exists(xml: str) -> bool:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return False
    return any(local_name(node.tag) == "body" for node in root.iter())


def ooxml_flavor(xml: str) -> str:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return "invalid_xml"
    namespace = namespace_uri(root.tag)
    if namespace == "http://schemas.openxmlformats.org/wordprocessingml/2006/main":
        return "transitional"
    if namespace == "http://purl.oclc.org/ooxml/wordprocessingml/main":
        return "strict"
    return "unknown"


def count_local(xml: str, name: str) -> int:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return 0
    return sum(1 for node in root.iter() if local_name(node.tag) == name)


def doc_conversion_plan() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "method": "Word COM",
            "when": "Windows with Microsoft Word available; highest fidelity for legacy .doc, Chinese text, images, and formula objects.",
        },
        {
            "priority": "2",
            "method": "LibreOffice headless",
            "when": "Use soffice/libreoffice when Word COM is unavailable, denied by sandbox, or times out.",
        },
        {
            "priority": "3",
            "method": "Pandoc",
            "when": "Use only as a low-fidelity fallback or diagnostic path; inspect structure carefully afterward.",
        },
        {
            "priority": "4",
            "method": "Manual Word save-as",
            "when": "Ask the user to manually save as .docx when automated conversion fails or fidelity is questionable.",
        },
    ]


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
            flavor = ooxml_flavor(xml)
            result["has_chinese"] = has_chinese(xml)
            result["has_images"] = any(name.startswith("word/media/") for name in names)
            result["has_tables"] = count_local(xml, "tbl") > 0
            result["has_formulas"] = count_local(xml, "oMath") > 0 or count_local(xml, "oMathPara") > 0
            result["paragraph_count_estimate"] = count_local(xml, "p")
            result["ooxml_flavor"] = flavor
            result["has_body"] = body_exists(xml)
            if flavor in {"strict", "unknown"}:
                result["warning"] = f"DOCX uses {flavor} OOXML namespace; extraction must use namespace auto-detection."
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
        result["conversion_required"] = True
        result["conversion_plan"] = doc_conversion_plan()
        result["recommended_command"] = f"python scripts/convert_doc_to_docx.py {path} --output {path.with_suffix('.docx')}"
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
