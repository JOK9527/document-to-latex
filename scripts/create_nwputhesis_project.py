#!/usr/bin/env python3
"""Create a clean nwputhesis project from the embedded template."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "assets" / "templates" / "nwputhesis"


def copy_template(output: Path, overwrite: bool) -> None:
    if output.exists():
        if not overwrite:
            raise SystemExit(f"Output already exists: {output}. Use --overwrite to replace it.")
        shutil.rmtree(output)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "build", "*.aux", "*.bbl", "*.bcf", "*.blg", "*.log", "*.out")
    shutil.copytree(TEMPLATE, output, ignore=ignore)


def patch_graduate_entry(entry: Path, degree: str, academic: bool) -> None:
    text = entry.read_text(encoding="utf-8")
    text = text.replace("degree = master,", f"degree = {degree},")
    text = text.replace("academic = true,", f"academic = {'true' if academic else 'false'},")
    entry.write_text(text, encoding="utf-8")


def remove_unused_content(output: Path, thesis_type: str) -> None:
    thesis_root = output / "content" / "thesis"
    if thesis_type == "bachelor":
        for path in [output / "graduate.tex", thesis_root / "graduate"]:
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
        (output / "main.tex").write_text("\\input{bachelor}\n", encoding="utf-8")
    else:
        for path in [output / "bachelor.tex", thesis_root / "undergraduate"]:
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
        (output / "main.tex").write_text("\\input{graduate}\n", encoding="utf-8")


def create_project(output: Path, thesis_type: str, academic: bool, overwrite: bool) -> None:
    if not TEMPLATE.exists():
        raise SystemExit(f"Embedded nwputhesis template not found: {TEMPLATE}")
    copy_template(output, overwrite=overwrite)
    if thesis_type in {"master", "phd"}:
        patch_graduate_entry(output / "graduate.tex", thesis_type, academic)
    remove_unused_content(output, thesis_type)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a clean nwputhesis LaTeX project.")
    parser.add_argument("output", help="Output project directory")
    parser.add_argument("--type", choices=["bachelor", "master", "phd"], required=True, help="NWPU thesis type")
    parser.add_argument("--professional", action="store_true", help="Use professional-degree graduate cover/settings")
    parser.add_argument("--overwrite", action="store_true", help="Replace output directory if it already exists")
    args = parser.parse_args()

    create_project(
        Path(args.output).resolve(),
        thesis_type=args.type,
        academic=not args.professional,
        overwrite=args.overwrite,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
