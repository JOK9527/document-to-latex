#!/usr/bin/env python3
"""Build a semantic IR for DOCX-to-LaTeX academic authoring.

The IR is a review artifact. It captures Word structure, likely academic
sections, tables, images, formulas, references, and source defects so the AI can
rewrite the document deliberately instead of dumping raw converted text.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


TRANSITIONAL_NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}
STRICT_NS = {
    "w": "http://purl.oclc.org/ooxml/wordprocessingml/main",
    "r": "http://purl.oclc.org/ooxml/officeDocument/relationships",
    "a": "http://purl.oclc.org/ooxml/drawingml/main",
    "wp": "http://purl.oclc.org/ooxml/drawingml/wordprocessingDrawing",
    "m": "http://purl.oclc.org/ooxml/officeDocument/math",
}
NS = dict(TRANSITIONAL_NS)

MOJIBAKE_TOKENS = [
    "瀹", "為", "獙", "鍥", "琛", "绗", "涓", "鎽", "瑕", "鍏", "抽敭", "璇",
    "傝", "枃", "鐚", "閿", "閻", "閼", "濡", "鐠", "锛", "鈥",
]
RISKY_SYMBOL_TOKENS = {
    "胃": "possible theta (θ) mojibake; review in math/formula context only",
}

FIGURE_CAPTION_RE = re.compile(r"^\s*(?:图|Fig\.?|Figure)\s*([0-9]+(?:[-.]\d+)?)\s*[:：.\-\s]*(.+)?$", re.I)
TABLE_CAPTION_RE = re.compile(r"^\s*(?:表|Table)\s*([0-9]+(?:[-.]\d+)?)\s*[:：.\-\s]*(.+)?$", re.I)
HEADING_NUMBER_RE = re.compile(r"^\s*(?:第[一二三四五六七八九十百]+[章节]|[0-9]+(?:\.[0-9]+){0,3})\s+")
CITATION_RE = re.compile(r"\[(?:\d+(?:[-,]\s*\d+)*)\]")


@dataclass
class Paragraph:
    id: str
    text: str
    style: str | None = None
    role: str = "body"
    level: int | None = None
    list_hint: bool = False
    image_ids: list[str] = field(default_factory=list)
    equation_ids: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)


@dataclass
class Table:
    id: str
    rows: list[list[str]]
    caption: str | None = None
    caption_paragraph_id: str | None = None
    quality_notes: list[str] = field(default_factory=list)


@dataclass
class Image:
    id: str
    relationship_id: str
    target: str | None = None
    exported_path: str | None = None
    nearby_caption: str | None = None
    paragraph_id: str | None = None
    role: str = "inline_image"


@dataclass
class Equation:
    id: str
    paragraph_id: str
    text_hint: str | None = None
    source: str = "omml"
    status: str = "needs_latex_reconstruction"


@dataclass
class TextIssue:
    id: str
    paragraph_id: str
    issue_type: str
    severity: str
    message: str
    sample: str
    repaired_sample: str | None = None


def qname(name: str) -> str:
    prefix, local = name.split(":", 1)
    return f"{{{NS[prefix]}}}{local}"


def namespace_uri(tag: str) -> str | None:
    if tag.startswith("{") and "}" in tag:
        return tag[1:].split("}", 1)[0]
    return None


def local_name(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def detect_namespaces(document: ET.Element) -> tuple[str, dict[str, str], list[str]]:
    document_ns = namespace_uri(document.tag)
    seen = sorted({namespace_uri(node.tag) for node in document.iter() if namespace_uri(node.tag)})
    if document_ns == STRICT_NS["w"]:
        return "strict", dict(STRICT_NS), seen
    if document_ns == TRANSITIONAL_NS["w"]:
        return "transitional", dict(TRANSITIONAL_NS), seen
    if document_ns:
        custom = dict(TRANSITIONAL_NS)
        custom["w"] = document_ns
        return "unknown", custom, seen
    return "unknown", dict(TRANSITIONAL_NS), seen


def find_child_by_local(parent: ET.Element, child_name: str) -> ET.Element | None:
    return next((child for child in parent if local_name(child.tag) == child_name), None)


def inspect_docx_package(zf: zipfile.ZipFile, document: ET.Element | None) -> dict[str, Any]:
    names = set(zf.namelist())
    package = {
        "has_document_xml": "word/document.xml" in names,
        "has_relationships": "word/_rels/document.xml.rels" in names,
        "ooxml_flavor": "unknown",
        "wordprocessing_namespace": None,
        "namespaces": [],
    }
    if document is not None:
        flavor, namespaces, seen = detect_namespaces(document)
        package["ooxml_flavor"] = flavor
        package["wordprocessing_namespace"] = namespaces.get("w")
        package["namespaces"] = seen
    return package


def read_zip_xml(zf: zipfile.ZipFile, name: str) -> ET.Element | None:
    try:
        return ET.fromstring(zf.read(name))
    except KeyError:
        return None


def paragraph_text(paragraph: ET.Element) -> str:
    parts: list[str] = []
    for node in paragraph.iter():
        if node.tag in {qname("w:t"), qname("m:t")} and node.text:
            parts.append(node.text)
        elif node.tag == qname("w:tab"):
            parts.append("\t")
        elif node.tag == qname("w:br"):
            parts.append("\n")
    return "".join(parts).strip()


def paragraph_style(paragraph: ET.Element) -> str | None:
    style = paragraph.find("./w:pPr/w:pStyle", NS)
    if style is None:
        return None
    return style.attrib.get(qname("w:val"))


def paragraph_has_numbering(paragraph: ET.Element) -> bool:
    return paragraph.find("./w:pPr/w:numPr", NS) is not None


def heading_level_from_style(style: str | None) -> int | None:
    if not style:
        return None
    match = re.search(r"(?:Heading|标题|Title)([1-6])", style, re.I)
    if match:
        return int(match.group(1))
    match = re.search(r"([1-6])$", style)
    if style.lower().startswith("heading") and match:
        return int(match.group(1))
    return None


def infer_role(text: str, style: str | None) -> tuple[str, int | None]:
    level = heading_level_from_style(style)
    if level:
        return "heading", level
    if HEADING_NUMBER_RE.match(text) and len(text) <= 80:
        return "heading_candidate", text.count(".") + 1 if re.match(r"^\s*\d", text) else 1
    if re.match(r"^\s*(摘要|摘\s*要|Abstract)\s*[:：]?", text, re.I):
        return "abstract", None
    if re.match(r"^\s*(关键词|Key words|Keywords)\s*[:：]?", text, re.I):
        return "keywords", None
    if re.match(r"^\s*(参考文献|References)\s*$", text, re.I):
        return "bibliography_heading", None
    if FIGURE_CAPTION_RE.match(text):
        return "figure_caption", None
    if TABLE_CAPTION_RE.match(text):
        return "table_caption", None
    if CITATION_RE.fullmatch(text):
        return "citation_fragment", None
    return "body", None


def rels_map(root: ET.Element | None) -> dict[str, str]:
    if root is None:
        return {}
    result: dict[str, str] = {}
    for rel in root:
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        if rel_id and target:
            result[rel_id] = target
    return result


def image_relationship_ids(paragraph: ET.Element) -> list[str]:
    ids: list[str] = []
    for node in paragraph.iter():
        embed = node.attrib.get(qname("r:embed"))
        if embed:
            ids.append(embed)
    return ids


def has_omml(paragraph: ET.Element) -> bool:
    return paragraph.find(".//m:oMath", NS) is not None or paragraph.find(".//m:oMathPara", NS) is not None


def table_rows(table: ET.Element) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table.findall("./w:tr", NS):
        cells: list[str] = []
        for cell in row.findall("./w:tc", NS):
            texts = [paragraph_text(paragraph) for paragraph in cell.findall("./w:p", NS)]
            cells.append("\n".join(text for text in texts if text).strip())
        rows.append(cells)
    return rows


def table_quality(rows: list[list[str]]) -> list[str]:
    notes: list[str] = []
    if not rows:
        return ["empty table"]
    widths = [len(row) for row in rows]
    if len(set(widths)) > 1:
        notes.append("uneven row cell counts; possible merged cells or malformed table")
    empty_rows = sum(1 for row in rows if not any(cell.strip() for cell in row))
    if empty_rows:
        notes.append(f"{empty_rows} empty row(s)")
    if rows and all(not cell.strip() for cell in rows[0]):
        notes.append("first row is empty; header may be missing")
    if len(rows) <= 1:
        notes.append("table has one or fewer rows")
    return notes


def mojibake_score(text: str) -> int:
    return sum(text.count(token) for token in MOJIBAKE_TOKENS)


def cjk_count(text: str) -> int:
    return sum(1 for char in text if "\u4e00" <= char <= "\u9fff")


def try_repair_mojibake(text: str) -> str | None:
    if not text or mojibake_score(text) == 0:
        return None
    candidates: list[str] = []
    for source_encoding in ("gbk", "gb18030", "cp936"):
        try:
            candidates.append(text.encode(source_encoding).decode("utf-8"))
        except UnicodeError:
            continue
    candidates = [candidate for candidate in dict.fromkeys(candidates) if candidate != text]
    if not candidates:
        return None
    original_score = mojibake_score(text)
    best = min(candidates, key=lambda item: (mojibake_score(item), -cjk_count(item), len(item)))
    if mojibake_score(best) < original_score and cjk_count(best) >= max(1, cjk_count(text) // 2):
        return best
    return None


def inspect_text(text: str, paragraph_id: str, repair: bool) -> tuple[str, list[TextIssue]]:
    issues: list[TextIssue] = []
    repaired = text
    score = mojibake_score(text)
    if score >= 2:
        candidate = try_repair_mojibake(text)
        issue = TextIssue(
            id="",
            paragraph_id=paragraph_id,
            issue_type="mojibake",
            severity="warning",
            message="Possible UTF-8/GBK mojibake detected in extracted DOCX text.",
            sample=text[:160],
            repaired_sample=candidate[:160] if candidate else None,
        )
        issues.append(issue)
        if repair and candidate:
            repaired = candidate
    for token, message in RISKY_SYMBOL_TOKENS.items():
        if token in repaired:
            issues.append(
                TextIssue(
                    id="",
                    paragraph_id=paragraph_id,
                    issue_type="risky_symbol_mojibake",
                    severity="review",
                    message=message,
                    sample=repaired[:160],
                )
            )
    return repaired, issues


def export_images(zf: zipfile.ZipFile, relationships: dict[str, str], images: list[Image], docx_path: Path, asset_dir: Path | None) -> None:
    if asset_dir is None:
        return
    image_dir = asset_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    for image in images:
        target = relationships.get(image.relationship_id)
        image.target = target
        if not target:
            continue
        media_name = target if target.startswith("word/") else f"word/{target}"
        try:
            suffix = Path(media_name).suffix or ".bin"
            output = image_dir / f"{image.id}{suffix}"
            with zf.open(media_name) as source, output.open("wb") as dest:
                shutil.copyfileobj(source, dest)
            image.exported_path = str(output)
        except KeyError:
            continue


def attach_nearby_captions(paragraphs: list[Paragraph], images: list[Image], tables: list[Table]) -> None:
    paragraph_by_id = {paragraph.id: paragraph for paragraph in paragraphs}
    for image in images:
        if not image.paragraph_id:
            continue
        index = next((i for i, paragraph in enumerate(paragraphs) if paragraph.id == image.paragraph_id), None)
        if index is None:
            continue
        candidates = paragraphs[max(0, index - 2) : min(len(paragraphs), index + 3)]
        caption = next((item for item in candidates if item.role == "figure_caption"), None)
        if caption:
            image.nearby_caption = caption.text
    for table in tables:
        caption_id = table.caption_paragraph_id
        if caption_id and caption_id in paragraph_by_id:
            table.caption = paragraph_by_id[caption_id].text


def build_defects(paragraphs: list[Paragraph], tables: list[Table], images: list[Image], equations: list[Equation], text_issues: list[TextIssue], package: dict[str, Any]) -> list[str]:
    defects: list[str] = []
    if package.get("ooxml_flavor") == "strict":
        defects.append("DOCX uses Strict OOXML; namespace-compatible extraction was applied.")
    elif package.get("ooxml_flavor") == "unknown":
        defects.append("DOCX uses an unrecognized WordprocessingML namespace; extraction used local-name fallback and needs review.")
    heading_candidates = [paragraph.id for paragraph in paragraphs if paragraph.role == "heading_candidate"]
    if heading_candidates:
        defects.append(f"{len(heading_candidates)} heading candidate(s) rely on numbering rather than Word heading styles.")
    captionless_images = [image.id for image in images if not image.nearby_caption]
    if captionless_images:
        defects.append(f"{len(captionless_images)} image(s) have no nearby figure caption.")
    table_notes = sum(len(table.quality_notes) for table in tables)
    if table_notes:
        defects.append(f"{table_notes} table quality note(s) require review.")
    if equations:
        defects.append(f"{len(equations)} OMML/math object(s) need LaTeX reconstruction review.")
    mojibake_issues = [issue for issue in text_issues if issue.issue_type == "mojibake"]
    if mojibake_issues:
        repairable = sum(1 for issue in mojibake_issues if issue.repaired_sample)
        defects.append(f"{len(mojibake_issues)} paragraph(s) contain possible mojibake; {repairable} have high-confidence repair candidates.")
    risky_symbols = [issue for issue in text_issues if issue.issue_type == "risky_symbol_mojibake"]
    if risky_symbols:
        defects.append(f"{len(risky_symbols)} paragraph(s) contain risky symbol-like characters that require formula-context review.")
    bibliography_markers = [paragraph for paragraph in paragraphs if paragraph.role == "bibliography_heading"]
    if not bibliography_markers and any(paragraph.citations for paragraph in paragraphs):
        defects.append("Citations were found, but no clear bibliography heading was detected.")
    return defects


def parse_docx(docx_path: Path, asset_dir: Path | None = None, repair_mojibake: bool = False) -> dict[str, Any]:
    if docx_path.suffix.lower() != ".docx":
        raise SystemExit("build_docx_semantic_ir.py expects a .docx file. Convert .doc to .docx first.")
    if not docx_path.exists():
        raise SystemExit(f"DOCX not found: {docx_path}")

    paragraphs: list[Paragraph] = []
    tables: list[Table] = []
    images: list[Image] = []
    equations: list[Equation] = []
    text_issues: list[TextIssue] = []

    with zipfile.ZipFile(docx_path) as zf:
        document = read_zip_xml(zf, "word/document.xml")
        package = inspect_docx_package(zf, document)
        rels = rels_map(read_zip_xml(zf, "word/_rels/document.xml.rels"))
        if document is None:
            raise SystemExit("word/document.xml not found; invalid DOCX.")
        flavor, namespaces, _seen = detect_namespaces(document)
        NS.update(namespaces)
        body = document.find("./w:body", NS)
        if body is None:
            body = find_child_by_local(document, "body")
        if body is None:
            raise SystemExit(
                "DOCX body not found. Package diagnostic: "
                f"OOXML flavor={flavor}, wordprocessing namespace={package.get('wordprocessing_namespace')}, "
                f"namespaces={package.get('namespaces')}. This usually means a namespace mismatch or damaged document.xml."
            )

        last_table_caption_id: str | None = None
        for child in body:
            if child.tag == qname("w:p"):
                paragraph_id = f"p{len(paragraphs) + 1:05d}"
                text, issues = inspect_text(paragraph_text(child), paragraph_id, repair_mojibake)
                for issue in issues:
                    issue.id = f"txt{len(text_issues) + 1:04d}"
                    text_issues.append(issue)
                style = paragraph_style(child)
                role, level = infer_role(text, style)
                paragraph = Paragraph(
                    id=paragraph_id,
                    text=text,
                    style=style,
                    role=role,
                    level=level,
                    list_hint=paragraph_has_numbering(child),
                    citations=CITATION_RE.findall(text),
                )
                for rel_id in image_relationship_ids(child):
                    image = Image(
                        id=f"img{len(images) + 1:04d}",
                        relationship_id=rel_id,
                        paragraph_id=paragraph.id,
                    )
                    images.append(image)
                    paragraph.image_ids.append(image.id)
                if has_omml(child):
                    equation = Equation(id=f"eq{len(equations) + 1:04d}", paragraph_id=paragraph.id, text_hint=text or None)
                    equations.append(equation)
                    paragraph.equation_ids.append(equation.id)
                if role == "table_caption":
                    last_table_caption_id = paragraph.id
                paragraphs.append(paragraph)
            elif child.tag == qname("w:tbl"):
                rows = table_rows(child)
                table = Table(
                    id=f"tab{len(tables) + 1:04d}",
                    rows=rows,
                    caption_paragraph_id=last_table_caption_id,
                    quality_notes=table_quality(rows),
                )
                tables.append(table)
                last_table_caption_id = None

        export_images(zf, rels, images, docx_path, asset_dir)

    attach_nearby_captions(paragraphs, images, tables)
    defects = build_defects(paragraphs, tables, images, equations, text_issues, package)
    return {
        "schema": "document-to-latex.docx-semantic-ir.v1",
        "source": str(docx_path),
        "docx_package": package,
        "preprocessing": {
            "repair_mojibake": repair_mojibake,
            "mojibake_issue_count": sum(1 for issue in text_issues if issue.issue_type == "mojibake"),
            "risky_symbol_issue_count": sum(1 for issue in text_issues if issue.issue_type == "risky_symbol_mojibake"),
        },
        "counts": {
            "paragraphs": len(paragraphs),
            "headings": sum(1 for item in paragraphs if item.role in {"heading", "heading_candidate"}),
            "tables": len(tables),
            "images": len(images),
            "equations": len(equations),
            "citation_paragraphs": sum(1 for item in paragraphs if item.citations),
            "text_issues": len(text_issues),
            "defects": len(defects),
        },
        "paragraphs": [asdict(item) for item in paragraphs],
        "tables": [asdict(item) for item in tables],
        "images": [asdict(item) for item in images],
        "equations": [asdict(item) for item in equations],
        "text_issues": [asdict(item) for item in text_issues],
        "defects": defects,
    }


def write_summary(ir: dict[str, Any]) -> str:
    lines = [
        "# DOCX Semantic IR Summary",
        "",
        f"- Source: {ir['source']}",
        f"- Schema: {ir['schema']}",
        f"- OOXML flavor: {ir.get('docx_package', {}).get('ooxml_flavor', 'unknown')}",
        f"- Mojibake repair applied: {ir.get('preprocessing', {}).get('repair_mojibake', False)}",
        "",
        "## Counts",
        "",
    ]
    for key, value in ir["counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Structure", ""])
    for paragraph in ir["paragraphs"]:
        if paragraph["role"] in {"heading", "heading_candidate", "abstract", "keywords", "bibliography_heading"}:
            level = paragraph.get("level")
            level_text = f" level {level}" if level else ""
            lines.append(f"- {paragraph['id']} {paragraph['role']}{level_text}: {paragraph['text'][:120]}")
    lines.extend(["", "## Tables", ""])
    for table in ir["tables"]:
        caption = table.get("caption") or "(no caption)"
        notes = "; ".join(table.get("quality_notes") or []) or "ok"
        lines.append(f"- {table['id']}: {len(table['rows'])} row(s), {caption}; {notes}")
    lines.extend(["", "## Images", ""])
    for image in ir["images"]:
        caption = image.get("nearby_caption") or "(no nearby caption)"
        lines.append(f"- {image['id']}: {caption}")
    lines.extend(["", "## Text Issues", ""])
    if not ir.get("text_issues"):
        lines.append("- No mojibake or risky symbol issues detected by the heuristic pass.")
    for issue in ir.get("text_issues", []):
        repair = f"; repair candidate: {issue['repaired_sample'][:80]}" if issue.get("repaired_sample") else ""
        lines.append(f"- {issue['id']} {issue['issue_type']} in {issue['paragraph_id']}: {issue['sample'][:100]}{repair}")
    lines.extend(["", "## Defects", ""])
    if not ir["defects"]:
        lines.append("- No source defects detected by the heuristic pass.")
    for defect in ir["defects"]:
        lines.append(f"- {defect}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a semantic IR for DOCX-to-LaTeX conversion.")
    parser.add_argument("docx", help="Source .docx path")
    parser.add_argument("--output", "-o", help="JSON IR output path")
    parser.add_argument("--summary", help="Optional Markdown summary output path")
    parser.add_argument("--asset-dir", help="Optional directory for exported DOCX assets")
    parser.add_argument("--repair-mojibake", action="store_true", help="Apply high-confidence UTF-8/GBK mojibake repairs in extracted paragraph text and record repairs in the IR.")
    args = parser.parse_args()

    asset_dir = Path(args.asset_dir) if args.asset_dir else None
    ir = parse_docx(Path(args.docx).resolve(), asset_dir=asset_dir, repair_mojibake=args.repair_mojibake)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(ir, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print(json.dumps(ir, ensure_ascii=False, indent=2))
    if args.summary:
        summary = Path(args.summary)
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(write_summary(ir), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
