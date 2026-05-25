#!/usr/bin/env python3
"""Build a semantic intermediate representation for complex PDF conversion.

The output is intentionally not LaTeX. It is a structured review artifact used
before generation so figures, tables, formulas, and paragraphs can be placed by
meaning instead of by raw PDF coordinates.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


CAPTION_RE = re.compile(
    r"^\s*(?P<kind>"
    r"(?:\u56fe|Fig\.?|Figure|FIGURE)"
    r"|(?:\u8868|Table|TABLE)"
    r")\s*(?P<number>[0-9IVXivx]+(?:[-.]\d+)?)\s*"
    r"(?P<sep>[\.．:：\-\s])(?P<title>.*)$"
)
SECTION_RE = re.compile(
    r"^\s*(?:"
    r"(?P<num>\d+(?:\s*\.\s*\d+){0,3})\s+"
    r"|(?P<cn>[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341]+)[\u3001\uff0e.]\s*"
    r"|(?P<kw>\u6458\u8981|\u7ed3\u8bba|\u5f15\u8a00|\u53c2\u8003\u6587\u732e)"
    r")(?P<title>.+)?$"
)
FIG_REF_RE = re.compile(r"(?:\u56fe|Fig\.?|Figure)\s*([0-9IVXivx]+(?:[-.]\d+)?)")
TAB_REF_RE = re.compile(r"(?:\u8868|Table)\s*([0-9IVXivx]+(?:[-.]\d+)?)")
EQ_REF_RE = re.compile(r"(?:\u5f0f|Equation|Eq\.?)\s*[\(（]?\s*([0-9]+(?:[-.]\d+)?)\s*[\)）]?")
CITATION_RE = re.compile(r"\[(?:\d+(?:[-,]\s*\d+)*)\]")


@dataclass
class BBox:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return max(0.0, self.x1 - self.x0)

    @property
    def height(self) -> float:
        return max(0.0, self.y1 - self.y0)

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2.0

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2.0

    def horizontal_overlap(self, other: "BBox") -> float:
        overlap = max(0.0, min(self.x1, other.x1) - max(self.x0, other.x0))
        return overlap / max(1.0, min(self.width, other.width))

    def vertical_gap(self, other: "BBox") -> float:
        if self.y1 < other.y0:
            return other.y0 - self.y1
        if other.y1 < self.y0:
            return self.y0 - other.y1
        return 0.0


@dataclass
class Line:
    id: str
    page: int
    text: str
    bbox: BBox
    font_size: float
    block_no: int
    line_no: int
    role: str = "body"


@dataclass
class Paragraph:
    id: str
    section_id: str | None
    page_start: int
    page_end: int
    text: str
    line_ids: list[str]
    references: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class Section:
    id: str
    title: str
    level: int
    page: int
    line_id: str
    paragraph_ids: list[str] = field(default_factory=list)


@dataclass
class Graphic:
    id: str
    page: int
    bbox: BBox
    width: int | None = None
    height: int | None = None
    caption_id: str | None = None
    caption_text: str | None = None
    caption_source: str | None = None
    source_number: str | None = None
    latex_label: str | None = None
    image_path: str | None = None
    referenced_by: list[str] = field(default_factory=list)
    placement_hint: str | None = None


@dataclass
class Caption:
    id: str
    kind: str
    source_number: str
    text: str
    page: int
    bbox: BBox
    line_id: str


@dataclass
class Formula:
    id: str
    page: int
    text: str
    line_ids: list[str]
    referenced_by: list[str] = field(default_factory=list)
    confidence: str = "candidate"
    image_path: str | None = None


@dataclass
class Table:
    id: str
    page: int
    source_number: str
    caption_text: str
    caption_id: str
    bbox: BBox
    latex_label: str
    referenced_by: list[str] = field(default_factory=list)
    placement_hint: str | None = None
    body_status: str = "not_reconstructed"


def bbox_from_raw(raw: Any) -> BBox:
    x0, y0, x1, y1 = raw
    return BBox(round(float(x0), 2), round(float(y0), 2), round(float(x1), 2), round(float(y1), 2))


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compact_for_repetition(text: str) -> str:
    text = normalize_text(text)
    text = re.sub(r"\d+", "#", text)
    return text


def is_caption_text(text: str) -> re.Match[str] | None:
    match = CAPTION_RE.match(text)
    if not match:
        return None
    # "Figure 1 shows ..." at the beginning of a paragraph is usually prose,
    # not a caption. Real captions usually have a punctuation separator and a
    # short title-like continuation.
    title = match.group("title").strip()
    if re.match(r"^(shows|presents|illustrates|gives|depicts)\b", title, re.I):
        return None
    if re.match(r"^(is|are|was|were)\b", title, re.I):
        return None
    if re.match(r"^(\u663e\u793a|\u7ed9\u51fa|\u5bf9\u6bd4|\u4e3a|\u662f|\u8868\u660e|\u53ef\u4ee5|\u6240\u793a)", title):
        return None
    return match


def is_section_heading(line: Line, median_size: float) -> tuple[bool, int]:
    text = normalize_text(line.text)
    if len(text) > 80:
        return False, 0
    if text.endswith(("\u3002", ".", ";", "\uff1b")):
        return False, 0
    if is_formula_line(text):
        return False, 0
    match = SECTION_RE.match(text)
    if not match:
        return False, 0
    if match.group("num"):
        number = re.sub(r"\s+", "", match.group("num"))
        level = number.count(".") + 1
        title = (match.group("title") or "").strip()
        if not title or title.startswith((",", "\uff0c", ".", "\uff0e", ":", "\uff1a", "-", "\uff0d")):
            return False, 0
        cjk_count = len(re.findall(r"[\u4e00-\u9fff]", title))
        alpha_count = len(re.findall(r"[A-Za-z]", title))
        unit_like = bool(re.search(r"\b(?:Hz|PWM|V|N|kg|g|min|s|r)\b|[°℃]", title))
        if cjk_count < 2 and alpha_count < 4:
            return False, 0
        if unit_like and line.font_size < median_size * 1.15:
            return False, 0
    elif match.group("cn"):
        level = 1
    else:
        level = 1
    if line.font_size >= median_size * 1.04 or (match.group("num") and level >= 2 and len(text) < 36):
        return True, min(level, 4)
    return False, 0


def symbol_ratio(text: str) -> float:
    if not text:
        return 0.0
    symbols = sum(1 for char in text if not char.isalnum() and not ("\u4e00" <= char <= "\u9fff") and not char.isspace())
    return symbols / max(1, len(text))


def is_citation_fragment(text: str) -> bool:
    clean = normalize_text(text)
    if not clean:
        return False
    if re.fullmatch(r"\[\s*\d+(?:\s*[-,]\s*\d+)*\s*\][\u3002.、,，;；]?", clean):
        return True
    if re.match(r"^\[\s*\d+(?:\s*[-,]\s*\d+)*\s*\]", clean) and len(clean) <= 40:
        return True
    return False


def ends_like_sentence(text: str) -> bool:
    return bool(re.search(r"[\u3002.!?！？;；：:]$|[。.!?！？][\"'）)]?$", normalize_text(text)))


def starts_like_continuation(text: str) -> bool:
    clean = normalize_text(text)
    if not clean:
        return False
    if is_citation_fragment(clean):
        return True
    if re.match(r"^[，,、;；:：）)]", clean):
        return True
    if re.match(r"^(而|并|且|但|但是|因此|同时|另外|另一方面|式中|其中|由|则|为|与|及)", clean):
        return True
    if re.match(r"^[a-z]", clean):
        return True
    return False


def is_formula_line(text: str) -> bool:
    clean = normalize_text(text)
    if len(clean) < 4 or len(clean) > 180:
        return False
    if re.fullmatch(r"[\(（]\s*\d+(?:[-.]\d+)?\s*[\)）]", clean):
        return False
    if is_citation_fragment(clean):
        return False
    if re.match(r"^\[\s*\d+(?:\s*[-,]\s*\d+)*\s*\]", clean):
        return False
    if is_caption_text(clean):
        return False
    if re.search(r"[\u4e00-\u9fff]{8,}", clean) and symbol_ratio(clean) < 0.18:
        return False
    math_markers = [
        r"[=≈≃≤≥∑∫√∞±×÷]",
        r"\b(?:sin|cos|tan|log|ln|exp|max|min)\b",
        r"[A-Za-z]\s*[_^]\s*[A-Za-z0-9]",
        r"[\(（]\s*\d+(?:[-.]\d+)?\s*[\)）]\s*$",
    ]
    return sum(bool(re.search(pattern, clean)) for pattern in math_markers) >= 1 and symbol_ratio(clean) >= 0.08


def merge_line_text(previous: str, current: str) -> str:
    previous = previous.rstrip()
    current = current.lstrip()
    if not previous:
        return current
    if re.search(r"[-\u2010-\u2015]$", previous) and re.match(r"^[A-Za-z]", current):
        return previous[:-1] + current
    if re.search(r"[\u4e00-\u9fff]$", previous) and re.match(r"^[\u4e00-\u9fff]", current):
        return previous + current
    return previous + " " + current


def extract_pdf_objects(pdf_path: Path) -> tuple[list[Line], list[Graphic], dict[int, tuple[float, float]], list[str]]:
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise SystemExit("PyMuPDF is required for build_pdf_semantic_ir.py. Install package 'pymupdf'.") from exc

    warnings: list[str] = []
    lines: list[Line] = []
    graphics: list[Graphic] = []
    page_sizes: dict[int, tuple[float, float]] = {}

    with fitz.open(str(pdf_path)) as doc:
        for page_index, page in enumerate(doc, start=1):
            page_sizes[page_index] = (float(page.rect.width), float(page.rect.height))
            data = page.get_text("dict")
            for block_no, block in enumerate(data.get("blocks", [])):
                block_type = block.get("type")
                if block_type == 0:
                    for line_no, raw_line in enumerate(block.get("lines", [])):
                        spans = raw_line.get("spans", [])
                        text = normalize_text("".join(span.get("text", "") for span in spans))
                        if not text:
                            continue
                        sizes = [float(span.get("size", 0.0)) for span in spans if span.get("size")]
                        line_id = f"l{len(lines) + 1:05d}"
                        lines.append(
                            Line(
                                id=line_id,
                                page=page_index,
                                text=text,
                                bbox=bbox_from_raw(raw_line.get("bbox")),
                                font_size=round(statistics.median(sizes), 2) if sizes else 0.0,
                                block_no=block_no,
                                line_no=line_no,
                            )
                        )
                elif block_type == 1:
                    graphic_id = f"g{len(graphics) + 1:04d}"
                    graphics.append(
                        Graphic(
                            id=graphic_id,
                            page=page_index,
                            bbox=bbox_from_raw(block.get("bbox")),
                            width=block.get("width"),
                            height=block.get("height"),
                        )
                    )

    if not lines:
        warnings.append("No text lines were extracted; this PDF may require OCR or VLM extraction.")
    if not graphics:
        warnings.append("No embedded image blocks were detected by PyMuPDF.")
    return lines, graphics, page_sizes, warnings


def classify_lines(lines: list[Line], page_sizes: dict[int, tuple[float, float]]) -> tuple[list[Caption], list[Formula], list[Section], list[str]]:
    warnings: list[str] = []
    if not lines:
        return [], [], [], warnings

    body_sizes = [line.font_size for line in lines if line.font_size > 0]
    median_size = statistics.median(body_sizes) if body_sizes else 10.0

    edge_counter: Counter[str] = Counter()
    edge_line_ids: dict[str, list[str]] = defaultdict(list)
    page_count = max(page_sizes) if page_sizes else max(line.page for line in lines)
    for line in lines:
        _, page_height = page_sizes.get(line.page, (0.0, 1.0))
        y_ratio = line.bbox.cy / max(1.0, page_height)
        if y_ratio < 0.08 or y_ratio > 0.92:
            key = compact_for_repetition(line.text)
            if key and len(key) <= 80:
                edge_counter[key] += 1
                edge_line_ids[key].append(line.id)

    repeated_threshold = max(3, math.ceil(page_count * 0.35))
    repeated_edge_ids = {
        line_id
        for key, count in edge_counter.items()
        if count >= repeated_threshold
        for line_id in edge_line_ids[key]
    }

    captions: list[Caption] = []
    formulas: list[Formula] = []
    sections: list[Section] = []

    for line in lines:
        if line.id in repeated_edge_ids:
            line.role = "running_header_footer"
            continue
        caption_match = is_caption_text(line.text)
        if caption_match:
            kind_raw = caption_match.group("kind").lower()
            kind = "table" if kind_raw.startswith("table") or kind_raw == "\u8868" else "figure"
            line.role = f"{kind}_caption"
            captions.append(
                Caption(
                    id=f"{kind[:3]}cap{len(captions) + 1:04d}",
                    kind=kind,
                    source_number=caption_match.group("number"),
                    text=normalize_text(line.text),
                    page=line.page,
                    bbox=line.bbox,
                    line_id=line.id,
                )
            )
            continue
        is_heading, level = is_section_heading(line, median_size)
        if is_heading:
            line.role = "section_heading"
            sections.append(
                Section(
                    id=f"sec{len(sections) + 1:04d}",
                    title=normalize_text(line.text),
                    level=level,
                    page=line.page,
                    line_id=line.id,
                )
            )
            continue
        if is_formula_line(line.text):
            line.role = "formula_candidate"

    current_group: list[Line] = []
    for line in lines:
        if line.role == "formula_candidate":
            if current_group and line.page == current_group[-1].page and abs(line.bbox.y0 - current_group[-1].bbox.y1) < median_size * 1.8:
                current_group.append(line)
            else:
                if current_group:
                    formulas.append(formula_from_lines(current_group, len(formulas) + 1))
                current_group = [line]
        else:
            if current_group:
                formulas.append(formula_from_lines(current_group, len(formulas) + 1))
                current_group = []
    if current_group:
        formulas.append(formula_from_lines(current_group, len(formulas) + 1))

    if len(formulas) > len(lines) * 0.18:
        warnings.append("Many formula candidates were detected; inspect false positives before generation.")
    return captions, formulas, sections, warnings


def formula_from_lines(lines: list[Line], index: int) -> Formula:
    return Formula(
        id=f"eq{index:04d}",
        page=lines[0].page,
        text=" ".join(line.text for line in lines),
        line_ids=[line.id for line in lines],
    )


def assign_sections(lines: list[Line], sections: list[Section]) -> dict[str, str | None]:
    current: Section | None = None
    section_by_line: dict[str, str | None] = {}
    section_by_heading_line = {section.line_id: section for section in sections}
    for line in lines:
        if line.id in section_by_heading_line:
            current = section_by_heading_line[line.id]
        section_by_line[line.id] = current.id if current else None
    return section_by_line


def build_paragraphs(lines: list[Line], sections: list[Section]) -> list[Paragraph]:
    section_by_line = assign_sections(lines, sections)
    content_roles = {"body"}
    paragraphs: list[Paragraph] = []
    group: list[Line] = []

    def flush() -> None:
        nonlocal group
        if not group:
            return
        text = ""
        for item in group:
            text = merge_line_text(text, item.text)
        paragraph = Paragraph(
            id=f"p{len(paragraphs) + 1:05d}",
            section_id=section_by_line.get(group[0].id),
            page_start=group[0].page,
            page_end=group[-1].page,
            text=normalize_text(text),
            line_ids=[item.id for item in group],
        )
        paragraph.references = extract_references(paragraph.text)
        paragraphs.append(paragraph)
        group = []

    for line in lines:
        if line.role not in content_roles:
            flush()
            continue
        if not group:
            group = [line]
            continue

        prev = group[-1]
        same_page = line.page == prev.page
        vertical_gap = line.bbox.y0 - prev.bbox.y1 if same_page else 9999.0
        indent_delta = abs(line.bbox.x0 - prev.bbox.x0)
        starts_new = bool(re.match(r"^(\d+(?:\.\d+)+|[\u4e00-\u9fff]+[\u3001:：])", line.text))

        same_column = indent_delta < 120
        forced_continuation = (
            starts_like_continuation(line.text)
            or not ends_like_sentence(prev.text)
            or is_citation_fragment(line.text)
        )

        close_vertical = vertical_gap < max(22.0, prev.font_size * 2.4)
        continuation_vertical = vertical_gap < max(34.0, prev.font_size * 3.2)

        if same_page and same_column and (close_vertical or (forced_continuation and continuation_vertical)) and not starts_new:
            group.append(line)
        else:
            flush()
            group = [line]
    flush()
    return merge_fragmented_paragraphs(paragraphs)


def merge_fragmented_paragraphs(paragraphs: list[Paragraph]) -> list[Paragraph]:
    merged: list[Paragraph] = []
    for paragraph in paragraphs:
        if not merged:
            merged.append(paragraph)
            continue
        previous = merged[-1]
        same_section = paragraph.section_id == previous.section_id
        close_pages = paragraph.page_start <= previous.page_end + 1
        previous_can_grow = len(previous.text) < 260
        short_or_continuation = (
            is_citation_fragment(paragraph.text)
            or starts_like_continuation(paragraph.text)
            or (previous_can_grow and not ends_like_sentence(previous.text))
            or len(paragraph.text) < 45
        )
        if same_section and close_pages and short_or_continuation and (previous_can_grow or is_citation_fragment(paragraph.text)):
            previous.text = normalize_text(merge_line_text(previous.text, paragraph.text))
            previous.page_end = paragraph.page_end
            previous.line_ids.extend(paragraph.line_ids)
            previous.references = extract_references(previous.text)
        else:
            merged.append(paragraph)

    for index, paragraph in enumerate(merged, start=1):
        paragraph.id = f"p{index:05d}"
    return merged


def extract_references(text: str) -> dict[str, list[str]]:
    refs = {
        "figures": sorted(set(FIG_REF_RE.findall(text))),
        "tables": sorted(set(TAB_REF_RE.findall(text))),
        "equations": sorted(set(EQ_REF_RE.findall(text))),
        "citations": sorted(set(CITATION_RE.findall(text))),
    }
    return {key: value for key, value in refs.items() if value}


def make_latex_label(prefix: str, source_number: str, used: set[str]) -> str:
    stem = re.sub(r"[^0-9A-Za-z.-]+", "-", source_number).strip("-") or "unknown"
    label = f"{prefix}:source-{stem}"
    if label not in used:
        used.add(label)
        return label
    suffix = 2
    while f"{label}-{suffix}" in used:
        suffix += 1
    unique = f"{label}-{suffix}"
    used.add(unique)
    return unique


def safe_filename(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-z._-]+", "-", value).strip("-._")
    return value or "asset"


def attach_paragraphs_to_sections(sections: list[Section], paragraphs: list[Paragraph]) -> None:
    by_id = {section.id: section for section in sections}
    for paragraph in paragraphs:
        if paragraph.section_id and paragraph.section_id in by_id:
            by_id[paragraph.section_id].paragraph_ids.append(paragraph.id)


def pair_figures_with_captions(graphics: list[Graphic], captions: list[Caption]) -> list[str]:
    warnings: list[str] = []
    figure_captions = [caption for caption in captions if caption.kind == "figure"]
    used_graphics: set[str] = set()
    used_labels: set[str] = set()
    for caption in figure_captions:
        candidates = [graphic for graphic in graphics if graphic.page == caption.page and graphic.id not in used_graphics]
        if not candidates:
            warnings.append(f"No image block found near figure caption {caption.source_number} on page {caption.page}.")
            continue
        scored = []
        for graphic in candidates:
            overlap = graphic.bbox.horizontal_overlap(caption.bbox)
            gap = graphic.bbox.vertical_gap(caption.bbox)
            direction_penalty = 0 if graphic.bbox.cy < caption.bbox.cy else 25
            score = gap + direction_penalty - overlap * 40
            scored.append((score, graphic))
        scored.sort(key=lambda item: item[0])
        best = scored[0][1]
        best.caption_id = caption.id
        best.caption_text = caption.text
        best.caption_source = "source_caption"
        best.source_number = caption.source_number
        best.latex_label = make_latex_label("fig", caption.source_number, used_labels)
        used_graphics.add(best.id)
    for graphic in graphics:
        if not graphic.caption_id:
            graphic.caption_source = "uncaptioned"
            graphic.latex_label = f"fig:uncaptioned-{graphic.id}"
            warnings.append(f"Image block {graphic.id} on page {graphic.page} has no paired source caption.")
    return warnings


def build_tables(captions: list[Caption]) -> list[Table]:
    tables: list[Table] = []
    used_labels: set[str] = set()
    for caption in captions:
        if caption.kind != "table":
            continue
        tables.append(
            Table(
                id=f"tab{len(tables) + 1:04d}",
                page=caption.page,
                source_number=caption.source_number,
                caption_text=caption.text,
                caption_id=caption.id,
                bbox=caption.bbox,
                latex_label=make_latex_label("tab", caption.source_number, used_labels),
            )
        )
    return tables


def attach_references(
    paragraphs: list[Paragraph],
    graphics: list[Graphic],
    captions: list[Caption],
    formulas: list[Formula],
    tables: list[Table],
) -> None:
    graphic_by_number: dict[str, Graphic] = {}
    for caption in captions:
        if caption.kind != "figure":
            continue
        for graphic in graphics:
            if graphic.caption_id == caption.id:
                graphic_by_number.setdefault(caption.source_number, graphic)
                break

    formula_by_number: dict[str, Formula] = {}
    for formula in formulas:
        match = re.search(r"[\(（]\s*(\d+(?:[-.]\d+)?)\s*[\)）]\s*$", formula.text)
        if match:
            formula_by_number[match.group(1)] = formula

    table_by_number: dict[str, Table] = {}
    for table in tables:
        table_by_number.setdefault(table.source_number, table)

    for paragraph in paragraphs:
        for number in paragraph.references.get("figures", []):
            graphic = graphic_by_number.get(number)
            if graphic and paragraph.id not in graphic.referenced_by:
                graphic.referenced_by.append(paragraph.id)
        for number in paragraph.references.get("tables", []):
            table = table_by_number.get(number)
            if table and paragraph.id not in table.referenced_by:
                table.referenced_by.append(paragraph.id)
        for number in paragraph.references.get("equations", []):
            formula = formula_by_number.get(number)
            if formula and paragraph.id not in formula.referenced_by:
                formula.referenced_by.append(paragraph.id)

    for graphic in graphics:
        if graphic.referenced_by:
            graphic.placement_hint = f"after first referring paragraph {graphic.referenced_by[0]}"
        elif graphic.caption_text:
            graphic.placement_hint = "near caption section; no explicit body reference found"
        else:
            graphic.placement_hint = "infer semantic caption and place near related paragraph during generation"
    for table in tables:
        if table.referenced_by:
            table.placement_hint = f"after first referring paragraph {table.referenced_by[0]}"
        else:
            table.placement_hint = "near caption section; no explicit body reference found"


def union_bbox(items: list[BBox]) -> BBox:
    return BBox(
        min(item.x0 for item in items),
        min(item.y0 for item in items),
        max(item.x1 for item in items),
        max(item.y1 for item in items),
    )


def render_asset_crops(pdf_path: Path, graphics: list[Graphic], formulas: list[Formula], lines: list[Line], asset_dir: Path) -> list[str]:
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise SystemExit("PyMuPDF is required for asset crop rendering.") from exc

    warnings: list[str] = []
    figures_dir = asset_dir / "figures"
    formulas_dir = asset_dir / "formulas"
    figures_dir.mkdir(parents=True, exist_ok=True)
    formulas_dir.mkdir(parents=True, exist_ok=True)
    line_by_id = {line.id: line for line in lines}

    def clip_rect(bbox: BBox, page_rect: Any) -> Any:
        pad = 3.0
        return fitz.Rect(
            max(page_rect.x0, bbox.x0 - pad),
            max(page_rect.y0, bbox.y0 - pad),
            min(page_rect.x1, bbox.x1 + pad),
            min(page_rect.y1, bbox.y1 + pad),
        )

    with fitz.open(str(pdf_path)) as doc:
        for graphic in graphics:
            page = doc[graphic.page - 1]
            label = graphic.latex_label or graphic.id
            output = figures_dir / f"{safe_filename(label)}.png"
            try:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip_rect(graphic.bbox, page.rect), alpha=False)
                pixmap.save(str(output))
                graphic.image_path = str(output)
            except Exception as exc:  # Keep IR available even when one crop fails.
                warnings.append(f"Could not render crop for {graphic.id}: {exc}")
        for formula in formulas:
            formula_lines = [line_by_id[line_id] for line_id in formula.line_ids if line_id in line_by_id]
            if not formula_lines:
                continue
            page = doc[formula.page - 1]
            bbox = union_bbox([line.bbox for line in formula_lines])
            output = formulas_dir / f"{safe_filename(formula.id)}.png"
            try:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip_rect(bbox, page.rect), alpha=False)
                pixmap.save(str(output))
                formula.image_path = str(output)
            except Exception as exc:
                warnings.append(f"Could not render crop for {formula.id}: {exc}")
    return warnings


def build_quality_notes(paragraphs: list[Paragraph], graphics: list[Graphic], formulas: list[Formula], tables: list[Table]) -> list[str]:
    notes: list[str] = []
    short_paragraphs = sum(1 for paragraph in paragraphs if len(paragraph.text) < 25)
    if paragraphs and short_paragraphs / len(paragraphs) > 0.35:
        notes.append("Paragraph reflow still looks fragmented; review PDF line merging before writing LaTeX.")
    unreferenced_captioned = [graphic.id for graphic in graphics if graphic.caption_text and not graphic.referenced_by]
    if unreferenced_captioned:
        notes.append(f"{len(unreferenced_captioned)} captioned figure(s) have no explicit paragraph reference.")
    if formulas:
        notes.append("Formula candidates require Math LaTeX reconstruction or image fallback before final generation.")
    if tables:
        notes.append("Table captions were detected; table bodies must be reconstructed or inserted as reviewed image fallbacks.")
    return notes


def section_for_page(sections: list[Section], page: int) -> str | None:
    current: str | None = None
    for section in sections:
        if section.page <= page:
            current = section.id
        else:
            break
    return current


def build_placement_plan(
    sections: list[Section],
    paragraphs: list[Paragraph],
    graphics: list[Graphic],
    tables: list[Table],
    formulas: list[Formula],
) -> list[dict[str, Any]]:
    plan_by_section: dict[str | None, dict[str, Any]] = {}

    def get_entry(section_id: str | None) -> dict[str, Any]:
        if section_id not in plan_by_section:
            title = "Front matter"
            if section_id:
                title = next((section.title for section in sections if section.id == section_id), section_id)
            plan_by_section[section_id] = {"section_id": section_id, "title": title, "blocks": [], "deferred_assets": []}
        return plan_by_section[section_id]

    figures_after: dict[str, list[Graphic]] = defaultdict(list)
    tables_after: dict[str, list[Table]] = defaultdict(list)
    formulas_after: dict[str, list[Formula]] = defaultdict(list)
    placed_graphics: set[str] = set()
    placed_tables: set[str] = set()
    placed_formulas: set[str] = set()

    for graphic in graphics:
        if graphic.referenced_by:
            figures_after[graphic.referenced_by[0]].append(graphic)
    for table in tables:
        if table.referenced_by:
            tables_after[table.referenced_by[0]].append(table)
    for formula in formulas:
        if formula.referenced_by:
            formulas_after[formula.referenced_by[0]].append(formula)

    for paragraph in paragraphs:
        entry = get_entry(paragraph.section_id)
        entry["blocks"].append({"type": "paragraph", "id": paragraph.id})
        for graphic in figures_after.get(paragraph.id, []):
            entry["blocks"].append({"type": "figure", "id": graphic.id, "label": graphic.latex_label, "reason": "first_explicit_reference"})
            placed_graphics.add(graphic.id)
        for table in tables_after.get(paragraph.id, []):
            entry["blocks"].append({"type": "table", "id": table.id, "label": table.latex_label, "reason": "first_explicit_reference"})
            placed_tables.add(table.id)
        for formula in formulas_after.get(paragraph.id, []):
            entry["blocks"].append({"type": "formula", "id": formula.id, "reason": "first_explicit_reference"})
            placed_formulas.add(formula.id)

    for graphic in graphics:
        if graphic.id in placed_graphics:
            continue
        section_id = section_for_page(sections, graphic.page)
        get_entry(section_id)["deferred_assets"].append(
            {"type": "figure", "id": graphic.id, "label": graphic.latex_label, "reason": "no_explicit_reference"}
        )
    for table in tables:
        if table.id in placed_tables:
            continue
        section_id = section_for_page(sections, table.page)
        get_entry(section_id)["deferred_assets"].append(
            {"type": "table", "id": table.id, "label": table.latex_label, "reason": "no_explicit_reference"}
        )
    for formula in formulas:
        if formula.id in placed_formulas:
            continue
        section_id = section_for_page(sections, formula.page)
        get_entry(section_id)["deferred_assets"].append(
            {"type": "formula", "id": formula.id, "reason": "formula_candidate_without_reference"}
        )

    ordered_section_ids: list[str | None] = []
    if None in plan_by_section:
        ordered_section_ids.append(None)
    ordered_section_ids.extend(section.id for section in sections if section.id in plan_by_section)
    return [plan_by_section[section_id] for section_id in ordered_section_ids]


def build_ir(pdf_path: Path, asset_dir: Path | None = None) -> dict[str, Any]:
    lines, graphics, page_sizes, warnings = extract_pdf_objects(pdf_path)
    captions, formulas, sections, classify_warnings = classify_lines(lines, page_sizes)
    warnings.extend(classify_warnings)
    paragraphs = build_paragraphs(lines, sections)
    attach_paragraphs_to_sections(sections, paragraphs)
    warnings.extend(pair_figures_with_captions(graphics, captions))
    tables = build_tables(captions)
    attach_references(paragraphs, graphics, captions, formulas, tables)
    if asset_dir:
        warnings.extend(render_asset_crops(pdf_path, graphics, formulas, lines, asset_dir))
    quality_notes = build_quality_notes(paragraphs, graphics, formulas, tables)
    placement_plan = build_placement_plan(sections, paragraphs, graphics, tables, formulas)

    return {
        "schema": "document-to-latex.pdf-semantic-ir.v1",
        "source": str(pdf_path),
        "counts": {
            "pages": len(page_sizes),
            "lines": len(lines),
            "paragraphs": len(paragraphs),
            "sections": len(sections),
            "graphics": len(graphics),
            "tables": len(tables),
            "captions": len(captions),
            "formulas": len(formulas),
            "placement_plan_sections": len(placement_plan),
        },
        "sections": [asdict(section) for section in sections],
        "paragraphs": [asdict(paragraph) for paragraph in paragraphs],
        "graphics": [asdict(graphic) for graphic in graphics],
        "tables": [asdict(table) for table in tables],
        "captions": [asdict(caption) for caption in captions],
        "formulas": [asdict(formula) for formula in formulas],
        "placement_plan": placement_plan,
        "line_roles": Counter(line.role for line in lines),
        "warnings": warnings,
        "quality_notes": quality_notes,
    }


def write_summary(ir: dict[str, Any]) -> str:
    lines = [
        "# PDF Semantic IR Summary",
        "",
        f"- Source: {ir['source']}",
        f"- Schema: {ir['schema']}",
        "",
        "## Counts",
        "",
    ]
    for key, value in ir["counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Sections", ""])
    for section in ir["sections"][:30]:
        lines.append(f"- {section['id']} page {section['page']}: {section['title']}")
    if len(ir["sections"]) > 30:
        lines.append(f"- ... {len(ir['sections']) - 30} more")
    lines.extend(["", "## Figures", ""])
    for graphic in ir["graphics"][:40]:
        caption = graphic.get("caption_text") or "(no source caption)"
        hint = graphic.get("placement_hint") or "(no placement hint)"
        lines.append(f"- {graphic['id']} page {graphic['page']}: {caption}; {hint}")
    if len(ir["graphics"]) > 40:
        lines.append(f"- ... {len(ir['graphics']) - 40} more")
    lines.extend(["", "## Tables", ""])
    for table in ir.get("tables", [])[:30]:
        lines.append(f"- {table['id']} page {table['page']}: {table['caption_text']}; {table['placement_hint']}")
    if len(ir.get("tables", [])) > 30:
        lines.append(f"- ... {len(ir['tables']) - 30} more")
    lines.extend(["", "## Notes", ""])
    for note in ir.get("quality_notes", []):
        lines.append(f"- {note}")
    for warning in ir.get("warnings", [])[:40]:
        lines.append(f"- Warning: {warning}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a semantic IR for PDF-to-LaTeX conversion.")
    parser.add_argument("pdf", help="Source PDF path")
    parser.add_argument("--output", "-o", help="JSON IR output path")
    parser.add_argument("--summary", help="Optional Markdown summary output path")
    parser.add_argument("--asset-dir", help="Optional directory for rendered figure and formula crops")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).resolve()
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    ir = build_ir(pdf_path, Path(args.asset_dir) if args.asset_dir else None)
    payload = json.dumps(ir, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if args.summary:
        Path(args.summary).write_text(write_summary(ir), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
