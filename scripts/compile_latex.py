#!/usr/bin/env python3
"""Compile a LaTeX project and write a concise JSON result."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def run_command(command: list[str], cwd: Path, timeout: int) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    return completed.returncode, completed.stdout


def compile_project(project: Path, main: str, engine: str, timeout: int) -> dict:
    log_path = project / "build.log"
    if shutil.which("latexmk"):
        command = ["latexmk", f"-{engine}", "-interaction=nonstopmode", "-halt-on-error", main]
    elif shutil.which(engine):
        command = [engine, "-interaction=nonstopmode", "-halt-on-error", main]
    else:
        result = {
            "success": False,
            "environment_blocker": True,
            "command": None,
            "log_path": str(log_path),
            "error": f"No LaTeX compiler found for engine '{engine}'.",
        }
        log_path.write_text(result["error"] + "\n", encoding="utf-8")
        return result

    try:
        code, output = run_command(command, project, timeout)
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        code = 124
        output += f"\nCompilation timed out after {timeout} seconds.\n"

    log_path.write_text(output, encoding="utf-8", errors="ignore")
    return {
        "success": code == 0,
        "environment_blocker": False,
        "return_code": code,
        "command": command,
        "log_path": str(log_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile a generated LaTeX project.")
    parser.add_argument("project", help="Project directory")
    parser.add_argument("--main", default="main.tex", help="Main TeX file")
    parser.add_argument("--engine", default="xelatex", help="Engine for latexmk or direct compile")
    parser.add_argument("--timeout", type=int, default=120, help="Compilation timeout in seconds")
    parser.add_argument("--output", "-o", help="Optional JSON result path")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    result = compile_project(project, args.main, args.engine, args.timeout)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
