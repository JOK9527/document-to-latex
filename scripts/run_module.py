#!/usr/bin/env python3
"""Run a pipeline module command and record its artifacts on success."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from pipeline_manifest import fingerprint, load_manifest, utc_now, write_manifest


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


STANDARD_MODULE_IDS = [
    "source_inventory",
    "thesis_type_decision",
    "docx_semantic_extraction",
    "authoring_brief",
    "nwpu_project_creation",
    "authoring_plan",
    "latex_authoring",
    "compilation",
    "quality_gate",
    "conversion_report",
]


def format_command(command: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(command)
    return shlex.join(command)


def record_success(args: argparse.Namespace, command: list[str]) -> dict[str, Any]:
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    entry = {
        "module": args.module,
        "updated_at": utc_now(),
        "command": format_command(command),
        "notes": args.notes,
        "inputs": [fingerprint(Path(item)) for item in args.input],
        "outputs": [fingerprint(Path(item)) for item in args.output],
    }
    manifest["modules"][args.module] = entry
    write_manifest(manifest_path, manifest)
    return entry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one document-to-latex pipeline module and record its successful outputs.",
        epilog="Standard module IDs: " + ", ".join(STANDARD_MODULE_IDS) + ". Scoped IDs may use module:scope.",
    )
    parser.add_argument("--manifest", default="work/pipeline_manifest.json", help="Pipeline manifest path")
    parser.add_argument("--module", required=True, help="Stable module name")
    parser.add_argument("--input", action="append", default=[], help="Input path; repeatable")
    parser.add_argument("--output", action="append", default=[], help="Output path; repeatable")
    parser.add_argument("--notes", help="Short note or assumption")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run after --")
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("provide the module command after --")
    return args


def main() -> int:
    args = parse_args()
    completed = subprocess.run(args.command, check=False)
    if completed.returncode != 0:
        return completed.returncode

    entry = record_success(args, args.command)
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
