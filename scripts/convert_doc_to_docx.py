#!/usr/bin/env python3
"""Convert legacy .doc files to .docx with a documented fallback chain."""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def local_name(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def validate_docx(path: Path) -> dict[str, Any]:
    result = {"path": str(path), "exists": path.exists(), "valid_docx": False, "has_document_xml": False, "has_body": False}
    if not path.exists():
        result["error"] = "output file not found"
        return result
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            result["has_document_xml"] = "word/document.xml" in names
            if result["has_document_xml"]:
                root = ET.fromstring(archive.read("word/document.xml"))
                result["has_body"] = any(local_name(node.tag) == "body" for node in root.iter())
        result["valid_docx"] = bool(result["has_document_xml"] and result["has_body"])
    except Exception as exc:
        result["error"] = str(exc)
    return result


def word_com_worker(source: str, output: str, queue: mp.Queue) -> None:
    try:
        import pythoncom  # type: ignore
        import win32com.client  # type: ignore

        pythoncom.CoInitialize()
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        document = word.Documents.Open(source, ReadOnly=True, ConfirmConversions=False)
        document.SaveAs2(output, FileFormat=16)
        document.Close(False)
        word.Quit()
        queue.put({"success": True})
    except Exception as exc:
        queue.put({"success": False, "error": str(exc)})


def try_word_com(source: Path, output: Path, timeout: int) -> dict[str, Any]:
    result = {"method": "Word COM", "success": False}
    queue: mp.Queue = mp.Queue()
    process = mp.Process(target=word_com_worker, args=(str(source), str(output), queue))
    process.start()
    process.join(timeout)
    if process.is_alive():
        process.terminate()
        process.join(5)
        result["error"] = f"Word COM timed out after {timeout} seconds."
        return result
    worker_result = queue.get() if not queue.empty() else {"success": False, "error": "Word COM exited without a result."}
    result.update(worker_result)
    if result.get("success"):
        result["validation"] = validate_docx(output)
        result["success"] = bool(result["validation"].get("valid_docx"))
    return result


def find_first(commands: list[str]) -> str | None:
    return next((command for command in commands if shutil.which(command)), None)


def try_libreoffice(source: Path, output: Path, timeout: int) -> dict[str, Any]:
    result = {"method": "LibreOffice headless", "success": False}
    executable = find_first(["soffice", "libreoffice"])
    if not executable:
        result["error"] = "soffice/libreoffice not found on PATH."
        return result
    with tempfile.TemporaryDirectory() as temp_dir:
        command = [executable, "--headless", "--convert-to", "docx", "--outdir", temp_dir, str(source)]
        completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
        result["command"] = command
        result["return_code"] = completed.returncode
        result["output"] = completed.stdout[-2000:]
        candidate = Path(temp_dir) / f"{source.stem}.docx"
        if candidate.exists():
            shutil.copy2(candidate, output)
            result["validation"] = validate_docx(output)
            result["success"] = bool(result["validation"].get("valid_docx"))
        else:
            result["error"] = "LibreOffice did not produce a .docx output file."
    return result


def try_pandoc(source: Path, output: Path, timeout: int) -> dict[str, Any]:
    result = {"method": "Pandoc", "success": False, "fidelity": "low"}
    executable = shutil.which("pandoc")
    if not executable:
        result["error"] = "pandoc not found on PATH."
        return result
    command = [executable, str(source), "-o", str(output)]
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
    result["command"] = command
    result["return_code"] = completed.returncode
    result["output"] = completed.stdout[-2000:]
    result["validation"] = validate_docx(output)
    result["success"] = bool(result["validation"].get("valid_docx"))
    return result


def convert(source: Path, output: Path, timeout: int, skip_word: bool = False) -> dict[str, Any]:
    if source.suffix.lower() != ".doc":
        return {"success": False, "error": "convert_doc_to_docx.py expects a legacy .doc input."}
    output.parent.mkdir(parents=True, exist_ok=True)
    attempts: list[dict[str, Any]] = []
    methods = [] if skip_word else [try_word_com]
    methods.extend([try_libreoffice, try_pandoc])
    for method in methods:
        if output.exists():
            output.unlink()
        try:
            attempt = method(source, output, timeout)
        except subprocess.TimeoutExpired as exc:
            attempt = {"method": method.__name__, "success": False, "error": f"Timed out after {timeout} seconds.", "output": (exc.stdout or "")[-2000:]}
        except Exception as exc:
            attempt = {"method": method.__name__, "success": False, "error": str(exc)}
        attempts.append(attempt)
        if attempt.get("success"):
            return {"success": True, "source": str(source), "output": str(output), "method": attempt.get("method"), "attempts": attempts}
    return {
        "success": False,
        "source": str(source),
        "output": str(output),
        "attempts": attempts,
        "manual_fallback": "Open the .doc in Microsoft Word or LibreOffice and save as .docx, then rerun detect_document.py and build_docx_semantic_ir.py.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a legacy .doc file to .docx with Word COM, LibreOffice, then Pandoc fallback.")
    parser.add_argument("source", help="Legacy .doc source path")
    parser.add_argument("--output", "-o", help="Output .docx path; defaults beside source")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout per conversion method in seconds")
    parser.add_argument("--skip-word-com", action="store_true", help="Skip the Word COM attempt.")
    parser.add_argument("--report", help="Optional JSON conversion report path")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    output = Path(args.output).resolve() if args.output else source.with_suffix(".docx")
    result = convert(source, output, args.timeout, skip_word=args.skip_word_com)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report:
        Path(args.report).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
