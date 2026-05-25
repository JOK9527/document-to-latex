#!/usr/bin/env python3
"""Render a PDF semantic IR into maintainable LaTeX chapter files."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


FRONTMATTER_PATTERNS = [
    r"^\d+\s*月第\d+\s*卷",
    r"^Journal of ",
    r"^February \d{4}",
    r"^Vol\.",
    r"^收稿日期",
    r"^网络出版",
    r"^基金项目",
    r"^引用格式",
    r"^中图分类号",
    r"^文献标志码",
    r"^\S+大学学报",
]
LATEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


@dataclass
class RenderContext:
    project_root: Path
    asset_root: Path
    copied_assets: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def latex_escape(text: str) -> str:
    return "".join(LATEX_SPECIALS.get(char, char) for char in text)


def normalize_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"^(\d+(?:\s*\.\s*\d+)*)\s+", "", title)
    title = title.replace(" .", ".")
    return title or "未命名章节"


def section_level(title: str) -> int:
    match = re.match(r"^(\d+(?:\s*\.\s*\d+)*)\s+", title.strip())
    if not match:
        return 1
    return min(4, re.sub(r"\s+", "", match.group(1)).count(".") + 1)


def section_command(level: int, has_chapters: bool) -> str:
    if not has_chapters:
        return ["section", "subsection", "subsubsection", "paragraph"][max(0, level - 1)]
    return ["chapter", "section", "subsection", "subsubsection"][max(0, level - 1)]


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", value).strip("-")
    return slug or "section"


def is_frontmatter_paragraph(text: str) -> bool:
    clean = text.strip()
    if len(clean) <= 3:
        return True
    if not re.search(r"[\u4e00-\u9fff]", clean) and len(clean) < 80:
        return True
    if any(re.search(pattern, clean) for pattern in FRONTMATTER_PATTERNS):
        return True
    if clean.startswith("航模舵机的动态特性测试与系统辨识") and "摘要" not in clean:
        return True
    if clean.startswith("（1 .") or clean.startswith("(1."):
        return True
    if "摘 要" in clean or "关键词" in clean:
        return True
    return False


def load_ir(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items}


def rel_tex_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def resolve_ir_asset(raw: str | None, ir_path: Path, project_root: Path) -> Path | None:
    if not raw:
        return None
    candidate = Path(raw)
    if candidate.is_absolute() and candidate.exists():
        return candidate
    for base in [project_root, ir_path.parent, Path.cwd()]:
        resolved = (base / raw).resolve()
        if resolved.exists():
            return resolved
    return None


def copy_asset(kind: str, item: dict[str, Any], ir_path: Path, ctx: RenderContext) -> str | None:
    source = resolve_ir_asset(item.get("image_path"), ir_path, ctx.project_root)
    if not source:
        ctx.warnings.append(f"Missing {kind} crop for {item.get('id')}: {item.get('image_path')}")
        return None
    if str(source) in ctx.copied_assets:
        return ctx.copied_assets[str(source)]
    target_dir = ctx.asset_root / kind
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.name
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)
    tex_path = rel_tex_path(target, ctx.project_root)
    ctx.copied_assets[str(source)] = tex_path
    return tex_path


def build_label_maps(ir: dict[str, Any]) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    figure_labels: dict[str, str] = {}
    table_labels: dict[str, str] = {}
    equation_labels: dict[str, str] = {}
    for graphic in ir.get("graphics", []):
        number = graphic.get("source_number")
        label = graphic.get("latex_label")
        if number and label and number not in figure_labels:
            figure_labels[number] = label
    for table in ir.get("tables", []):
        number = table.get("source_number")
        label = table.get("latex_label")
        if number and label and number not in table_labels:
            table_labels[number] = label
    for formula in ir.get("formulas", []):
        match = re.search(r"[\(（]\s*(\d+(?:[-.]\d+)?)\s*[\)）]\s*$", formula.get("text", ""))
        if match:
            equation_labels.setdefault(match.group(1), f"eq:source-{match.group(1)}")
    return figure_labels, table_labels, equation_labels


def replace_refs(text: str, figure_labels: dict[str, str], table_labels: dict[str, str], equation_labels: dict[str, str]) -> str:
    escaped = latex_escape(text)

    def fig_sub(match: re.Match[str]) -> str:
        number = match.group(1)
        label = figure_labels.get(number)
        return f"图~\\ref{{{label}}}" if label else match.group(0)

    def tab_sub(match: re.Match[str]) -> str:
        number = match.group(1)
        label = table_labels.get(number)
        return f"表~\\ref{{{label}}}" if label else match.group(0)

    def eq_sub(match: re.Match[str]) -> str:
        number = match.group(1)
        label = equation_labels.get(number)
        return f"式~\\eqref{{{label}}}" if label else match.group(0)

    escaped = re.sub(r"图\s*([0-9IVXivx]+(?:[-.]\d+)?)", fig_sub, escaped)
    escaped = re.sub(r"表\s*([0-9IVXivx]+(?:[-.]\d+)?)", tab_sub, escaped)
    escaped = re.sub(r"式\s*[\(（]?\s*([0-9]+(?:[-.]\d+)?)\s*[\)）]?", eq_sub, escaped)
    return escaped


def render_paragraph(paragraph: dict[str, Any], figure_labels: dict[str, str], table_labels: dict[str, str], equation_labels: dict[str, str]) -> list[str]:
    text = paragraph.get("text", "").strip()
    if not text or is_frontmatter_paragraph(text):
        return []
    return [replace_refs(text, figure_labels, table_labels, equation_labels), ""]


def render_figure(graphic: dict[str, Any], ir_path: Path, ctx: RenderContext) -> list[str]:
    image_path = copy_asset("figures", graphic, ir_path, ctx)
    caption = graphic.get("caption_text") or f"图像 {graphic.get('id')}"
    label = graphic.get("latex_label") or f"fig:{graphic.get('id')}"
    if not image_path:
        return [
            "% Figure crop missing; review source extraction.",
            f"% {latex_escape(caption)}",
            "",
        ]
    return [
        "\\begin{figure}[htbp]",
        "  \\centering",
        f"  \\includegraphics[width=0.82\\textwidth]{{{image_path}}}",
        f"  \\caption{{{latex_escape(caption)}}}",
        f"  \\label{{{label}}}",
        "\\end{figure}",
        "",
    ]


def render_table(table: dict[str, Any], _ir_path: Path, ctx: RenderContext) -> list[str]:
    caption = table.get("caption_text") or f"表格 {table.get('id')}"
    label = table.get("latex_label") or f"tab:{table.get('id')}"
    ctx.warnings.append(f"Table body not reconstructed for {table.get('id')}; emitted review placeholder.")
    return [
        "\\begin{table}[htbp]",
        "  \\centering",
        f"  \\caption{{{latex_escape(caption)}}}",
        f"  \\label{{{label}}}",
        "  \\begin{tabular}{ll}",
        "    \\hline",
        "    项目 & 内容 \\\\",
        "    \\hline",
        "    表体 & 待根据源文档重建 \\\\",
        "    \\hline",
        "  \\end{tabular}",
        "\\end{table}",
        "",
    ]


def render_formula(formula: dict[str, Any], ir_path: Path, ctx: RenderContext) -> list[str]:
    image_path = copy_asset("formulas", formula, ir_path, ctx)
    match = re.search(r"[\(（]\s*(\d+(?:[-.]\d+)?)\s*[\)）]\s*$", formula.get("text", ""))
    label = f"eq:source-{match.group(1)}" if match else f"eq:{formula.get('id')}"
    ctx.warnings.append(f"Formula {formula.get('id')} needs Math LaTeX reconstruction; emitted image fallback.")
    if not image_path:
        return [
            "% Formula crop missing; source text follows for review.",
            "\\begin{equation*}",
            f"  \\text{{{latex_escape(formula.get('text', ''))}}}",
            "\\end{equation*}",
            "",
        ]
    return [
        "\\begin{equation}",
        "  \\vcenter{\\hbox{%",
        f"    \\includegraphics[width=0.62\\textwidth]{{{image_path}}}%",
        "  }}",
        f"  \\label{{{label}}}",
        "\\end{equation}",
        "",
    ]


def chapter_title_for_plan(section: dict[str, Any], index: int) -> tuple[str, int]:
    if section.get("section_id") is None:
        return "绪论", 1
    title = section.get("title") or f"第{index}章"
    return normalize_title(title), section_level(title)


def render_chapters(ir: dict[str, Any], ir_path: Path, output_dir: Path, ctx: RenderContext) -> dict[str, Any]:
    paragraphs = by_id(ir.get("paragraphs", []))
    graphics = by_id(ir.get("graphics", []))
    tables = by_id(ir.get("tables", []))
    formulas = by_id(ir.get("formulas", []))
    figure_labels, table_labels, equation_labels = build_label_maps(ir)

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    chapter_index = 0
    section_index = 0
    current_lines: list[str] = []
    current_started = False

    def flush_chapter() -> None:
        nonlocal current_lines, current_started
        if not current_lines:
            return
        if not current_started:
            return
        filename = f"chapter{len(written) + 1}.tex"
        (output_dir / filename).write_text("\n".join(current_lines).rstrip() + "\n", encoding="utf-8")
        written.append(filename)
        current_lines = []
        current_started = False

    for plan_index, section in enumerate(ir.get("placement_plan", []), start=1):
        title, level = chapter_title_for_plan(section, plan_index)
        if level == 1:
            flush_chapter()
            chapter_index += 1
            section_index = 0
            current_lines = [
                "% Auto-generated from PDF semantic IR. Review uncertain tables/formulas before final delivery.",
                f"\\chapter{{{latex_escape(title)}}}",
                f"\\label{{chap:semantic-{chapter_index}}}",
                "",
            ]
        elif not current_lines:
            chapter_index += 1
            section_index = 0
            current_lines = [
                "% Auto-generated from PDF semantic IR. Review uncertain tables/formulas before final delivery.",
                f"\\chapter{{{latex_escape(title)}}}",
                f"\\label{{chap:semantic-{chapter_index}}}",
                "",
            ]
        else:
            section_index += 1
            command = section_command(level, has_chapters=True)
            current_lines.extend(
                [
                    f"\\{command}{{{latex_escape(title)}}}",
                    f"\\label{{sec:semantic-{chapter_index}-{section_index}}}",
                    "",
                ]
            )

        blocks = section.get("blocks", [])
        deferred_assets = section.get("deferred_assets", [])
        for block in blocks:
            block_type = block.get("type")
            block_id = block.get("id")
            if block_type == "paragraph" and block_id in paragraphs:
                rendered = render_paragraph(paragraphs[block_id], figure_labels, table_labels, equation_labels)
            elif block_type == "figure" and block_id in graphics:
                rendered = render_figure(graphics[block_id], ir_path, ctx)
            elif block_type == "table" and block_id in tables:
                rendered = render_table(tables[block_id], ir_path, ctx)
            elif block_type == "formula" and block_id in formulas:
                rendered = render_formula(formulas[block_id], ir_path, ctx)
            else:
                rendered = []
            if rendered:
                current_started = True
                current_lines.extend(rendered)

        if deferred_assets:
            current_lines.extend(
                [
                    "% Deferred assets were not explicitly referenced in the extracted prose.",
                    "% Place them manually after semantic review if they are required.",
                    "",
                ]
            )
            for asset in deferred_assets:
                current_lines.append(f"% deferred {asset.get('type')} {asset.get('id')}: {asset.get('label', '')}")
            current_lines.append("")

    flush_chapter()

    chapters_tex = output_dir / "chapters.tex"
    chapters_tex.write_text(
        "% Auto-generated semantic chapter order.\n"
        + "\n".join(f"\\input{{{rel_tex_path(output_dir / filename, ctx.project_root)[:-4]}}}" for filename in written)
        + "\n",
        encoding="utf-8",
    )
    return {"chapters": written, "chapters_entry": str(chapters_tex)}


def write_report(path: Path, summary: dict[str, Any], warnings: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Semantic IR Render Report",
        "",
        f"- Chapters written: {len(summary.get('chapters', []))}",
        f"- Chapter entry: {summary.get('chapters_entry')}",
        "",
        "## Chapters",
        "",
    ]
    lines.extend(f"- {chapter}" for chapter in summary.get("chapters", []))
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in warnings) if warnings else lines.append("- None")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render semantic PDF IR into LaTeX chapters.")
    parser.add_argument("ir", help="PDF semantic IR JSON path")
    parser.add_argument("--project-root", required=True, help="LaTeX project root")
    parser.add_argument("--output-dir", required=True, help="Output chapter directory")
    parser.add_argument("--asset-root", required=True, help="Generated figure/formula asset directory")
    parser.add_argument("--report", help="Optional Markdown render report path")
    args = parser.parse_args()

    ir_path = Path(args.ir).resolve()
    project_root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    ctx = RenderContext(project_root=project_root, asset_root=Path(args.asset_root).resolve())
    ir = load_ir(ir_path)
    summary = render_chapters(ir, ir_path, output_dir, ctx)
    if args.report:
        write_report(Path(args.report), summary, ctx.warnings)
    print(json.dumps({"summary": summary, "warnings": ctx.warnings}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
