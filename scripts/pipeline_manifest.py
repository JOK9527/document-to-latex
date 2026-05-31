#!/usr/bin/env python3
"""Record and check resumable document-to-latex pipeline module state."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


SCHEMA = "document-to-latex.pipeline-manifest.v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_directory(path: Path) -> str:
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        if ".git" in child.parts:
            continue
        relative = child.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(hash_file(child).encode("ascii"))
    return digest.hexdigest()


def fingerprint(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    exists = resolved.exists()
    result: dict[str, Any] = {
        "path": str(path),
        "resolved": str(resolved),
        "exists": exists,
    }
    if not exists:
        return result

    stat = resolved.stat()
    result.update(
        {
            "mtime_ns": stat.st_mtime_ns,
            "size_bytes": stat.st_size if resolved.is_file() else None,
            "kind": "directory" if resolved.is_dir() else "file",
            "sha256": hash_directory(resolved) if resolved.is_dir() else hash_file(resolved),
        }
    )
    return result


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema": SCHEMA, "modules": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("schema", SCHEMA)
    data.setdefault("modules", {})
    return data


def write_manifest(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record_module(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    entry = {
        "module": args.module,
        "updated_at": utc_now(),
        "command": args.command,
        "notes": args.notes,
        "inputs": [fingerprint(Path(item)) for item in args.input],
        "outputs": [fingerprint(Path(item)) for item in args.output],
    }
    manifest["modules"][args.module] = entry
    write_manifest(manifest_path, manifest)
    return entry


def same_fingerprint(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    keys = ["exists", "kind", "sha256"]
    return all(previous.get(key) == current.get(key) for key in keys)


def check_module(args: argparse.Namespace) -> dict[str, Any]:
    manifest = load_manifest(Path(args.manifest))
    entry = manifest.get("modules", {}).get(args.module)
    if not entry:
        return {"fresh": False, "module": args.module, "reason": "module not recorded"}

    input_results = []
    for previous in entry.get("inputs", []):
        current = fingerprint(Path(previous["path"]))
        input_results.append(
            {
                "path": previous["path"],
                "fresh": same_fingerprint(previous, current),
                "previous": previous,
                "current": current,
            }
        )

    output_results = []
    for previous in entry.get("outputs", []):
        current = fingerprint(Path(previous["path"]))
        output_results.append(
            {
                "path": previous["path"],
                "exists": current.get("exists", False),
                "previous": previous,
                "current": current,
            }
        )

    fresh = all(item["fresh"] for item in input_results) and all(item["exists"] for item in output_results)
    return {
        "fresh": fresh,
        "module": args.module,
        "recorded_at": entry.get("updated_at"),
        "inputs": input_results,
        "outputs": output_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Record or check document-to-latex pipeline module freshness.")
    parser.add_argument("--manifest", default="work/pipeline_manifest.json", help="Pipeline manifest path")
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    record = subparsers.add_parser("record", help="Record a module's input/output fingerprints")
    record.add_argument("--module", required=True, help="Stable module name")
    record.add_argument("--input", action="append", default=[], help="Input path; repeatable")
    record.add_argument("--output", action="append", default=[], help="Output path; repeatable")
    record.add_argument("--command", help="Command used to produce the outputs")
    record.add_argument("--notes", help="Short note or assumption")

    check = subparsers.add_parser("check", help="Check whether a recorded module is fresh")
    check.add_argument("--module", required=True, help="Stable module name")

    args = parser.parse_args()
    if args.command_name == "record":
        result = record_module(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    result = check_module(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("fresh") else 1


if __name__ == "__main__":
    raise SystemExit(main())
