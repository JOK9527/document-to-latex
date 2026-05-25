#!/usr/bin/env python3
"""Extract likely formatting requirements from text or lightweight guide files."""

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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def detect_language(text: str) -> str | None:
    chinese = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    latin = sum(1 for char in text if "a" <= char.lower() <= "z")
    if chinese > 20 and chinese >= latin / 3:
        return "zh"
    if latin > 20:
        return "en"
    return None


def find_first(patterns: list[str], text: str, flags: int = re.IGNORECASE) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return normalize_space(match.group(1) if match.groups() else match.group(0))
    return None


def find_all(patterns: list[str], text: str, flags: int = re.IGNORECASE) -> list[str]:
    found = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags):
            value = match.group(1) if match.groups() else match.group(0)
            value = normalize_space(value)
            if value not in found:
                found.append(value)
    return found


def extract(text: str) -> dict[str, Any]:
    compact = normalize_space(text)
    requirements: dict[str, Any] = {
        "language": detect_language(text),
        "page": {},
        "fonts": {},
        "headings": {},
        "bibliography": {},
        "figures": {},
        "tables": {},
        "compiler": None,
        "document_type": None,
        "layout": {},
        "raw_matches": {},
    }

    requirements["page"]["size"] = find_first(
        [r"\b(A4|A3|Letter|Legal)\b", r"(A4纸|A3纸)"],
        compact,
    )
    requirements["page"]["margin"] = find_first(
        [
            r"(?:margin|margins|页边距)[^\d]{0,12}([\d.]+\s*(?:cm|mm|in|inch|英寸|厘米|毫米))",
            r"(?:上下左右|左右|上、下、左、右)[^\d]{0,12}([\d.]+\s*(?:cm|mm|厘米|毫米))",
        ],
        compact,
    )
    requirements["layout"]["columns"] = find_first(
        [r"(two-column|double-column|single-column)", r"(双栏|单栏)"],
        compact,
    )
    requirements["fonts"]["main"] = find_first(
        [
            r"(?:font|字体)[：:\s]*(Times New Roman|Arial|Calibri|宋体|黑体|仿宋|楷体)",
            r"(Times New Roman|Arial|Calibri|宋体|黑体|仿宋|楷体)",
        ],
        compact,
    )
    requirements["fonts"]["size"] = find_first(
        [r"(\d+\s*pt)", r"(小四|四号|五号|三号|二号)"],
        compact,
    )
    requirements["layout"]["line_spacing"] = find_first(
        [r"(\d+(?:\.\d+)?\s*(?:倍行距|line spacing))", r"(single spacing|double spacing|1\.5 spacing)"],
        compact,
    )
    requirements["bibliography"]["style"] = find_first(
        [r"(GB/T\s*7714|gb7714|IEEE|APA|MLA|Chicago|ACM|numeric|author-year)", r"(顺序编码制|著者-出版年制)"],
        compact,
    )
    requirements["compiler"] = find_first(
        [r"(?<![A-Za-z])(xelatex|lualatex|pdflatex|latexmk|bibtex|biber)(?![A-Za-z])"],
        compact,
    )
    requirements["document_type"] = find_first(
        [r"(thesis|dissertation|report|article|paper|book)", r"(本科论文|毕业设计|学位论文|报告|论文|期刊|会议)"],
        compact,
    )
    requirements["figures"]["caption_position"] = find_first(
        [r"(?:figure captions?|图(?:题|注)?)[^，,。.;]{0,20}(above|below|top|bottom|上方|下方)"],
        compact,
    )
    requirements["tables"]["caption_position"] = find_first(
        [r"(?:table captions?|表(?:题|注)?)[^，,。.;]{0,20}(above|below|top|bottom|上方|下方)"],
        compact,
    )
    requirements["headings"]["numbering"] = find_first(
        [r"(numbered headings|unnumbered headings|章节编号|标题编号|不编号)"],
        compact,
    )
    requirements["raw_matches"]["margins"] = find_all(
        [r"(?:left|right|top|bottom|左|右|上|下)[^\d]{0,8}[\d.]+\s*(?:cm|mm|in|厘米|毫米|英寸)"],
        compact,
    )
    requirements["raw_matches"]["font_mentions"] = find_all(
        [r"(Times New Roman|Arial|Calibri|宋体|黑体|仿宋|楷体|小四|四号|五号|三号|二号)"],
        compact,
    )
    requirements["raw_matches"]["bibliography_mentions"] = find_all(
        [r"(GB/T\s*7714|gb7714|IEEE|APA|MLA|Chicago|BibTeX|biblatex|natbib|biber|参考文献[^。.;]{0,30})"],
        compact,
    )

    warnings = []
    if not any(requirements["page"].values()):
        warnings.append("No explicit page size or margin requirements found.")
    if not requirements["bibliography"]["style"]:
        warnings.append("No explicit bibliography style found.")
    if not requirements["compiler"]:
        warnings.append("No explicit compiler requirement found.")
    requirements["warnings"] = warnings
    return requirements


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract likely LaTeX format requirements.")
    parser.add_argument("input", nargs="?", help="Text file containing typed notes or extracted guide text")
    parser.add_argument("--text", help="Requirements text passed directly")
    parser.add_argument("--output", "-o", help="Optional JSON output path")
    args = parser.parse_args()

    if args.text is not None:
        text = args.text
    elif args.input:
        text = read_text(Path(args.input).resolve())
    else:
        raise SystemExit("Provide an input text file or --text.")

    result = extract(text)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
