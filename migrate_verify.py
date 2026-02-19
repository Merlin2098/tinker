#!/usr/bin/env python3
"""
Migration verifier for Tinker path consolidation:
  agent/         -> agents/logic/
  agent_tools/   -> agents/tools/
  instructions/  -> agents/instructions/

Usage:
  python migrate_verify.py --write-manifest .migration/move_manifest.json
  python migrate_verify.py --manifest .migration/move_manifest.json
  python migrate_verify.py --manifest .migration/move_manifest.json --strict --fail-on-text-refs
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterator, List

ROOT = Path(".").resolve()
MAPPING = {
    "agent": "agents/logic",
    "agent_tools": "agents/tools",
    "instructions": "agents/instructions",
}

IGNORE_DIRS = {
    ".git",
    ".migration",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
}

IGNORE_FILES = {
    "AGENTS_MIGRATION_PLAN.md",
    "migrate_verify.py",
}

TEXT_EXTS = {
    ".py",
    ".md",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".txt",
    ".cfg",
    ".ps1",
    ".bat",
    ".sh",
    ".rst",
    ".sql",
}

LEGACY_IMPORT_ROOTS = {"agent", "agent_tools"}
LEGACY_PATH_RE = re.compile(
    r"(?:agent_tools/|(?<!agents/)agent/|(?<!agents/)instructions/)"
)


def safe_console_text(value: str) -> str:
    encoding = sys.stdout.encoding or "utf-8"
    return value.encode(encoding, errors="backslashreplace").decode(encoding)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(base: Path) -> Iterator[Path]:
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if set(path.parts) & IGNORE_DIRS:
            continue
        rel = path.relative_to(base).as_posix()
        if rel in IGNORE_FILES:
            continue
        yield path


def write_manifest(path: Path) -> int:
    payload: Dict[str, object] = {
        "mapping": MAPPING,
        "files": {},
    }
    files = payload["files"]
    assert isinstance(files, dict)

    for old_root, new_root in MAPPING.items():
        old_dir = ROOT / old_root
        if not old_dir.exists():
            continue
        for src in old_dir.rglob("*"):
            if not src.is_file():
                continue
            rel = src.relative_to(old_dir).as_posix()
            old_rel = f"{old_root}/{rel}"
            new_rel = f"{new_root}/{rel}"
            files[old_rel] = {
                "target": new_rel,
                "sha256": sha256_file(src),
                "size": src.stat().st_size,
            }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] wrote manifest: {path.relative_to(ROOT).as_posix()}")
    return 0


def verify_structure(strict: bool, errors: List[str], warnings: List[str]) -> None:
    for old_root, new_root in MAPPING.items():
        new_dir = ROOT / new_root
        if not new_dir.exists():
            errors.append(f"missing required directory: {new_root}")

        old_dir = ROOT / old_root
        if old_dir.exists():
            msg = f"legacy path still exists: {old_root}"
            if strict:
                errors.append(msg)
            else:
                warnings.append(msg + " (allowed in compatibility mode)")


def verify_manifest(manifest_path: Path, strict: bool, errors: List[str], warnings: List[str]) -> None:
    if not manifest_path.exists():
        warnings.append(
            f"manifest not found: {manifest_path.relative_to(ROOT).as_posix()} "
            "(skipping pre/post file content verification)"
        )
        return

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"manifest JSON invalid: {exc}")
        return

    files = raw.get("files")
    if not isinstance(files, dict):
        errors.append("manifest format invalid: key 'files' must be an object")
        return

    for old_rel, meta in files.items():
        if not isinstance(meta, dict):
            errors.append(f"manifest entry invalid for {old_rel}")
            continue

        target_rel = meta.get("target")
        expected_hash = meta.get("sha256")
        if not isinstance(target_rel, str):
            errors.append(f"manifest target missing for {old_rel}")
            continue

        target_abs = ROOT / target_rel
        if not target_abs.exists():
            errors.append(f"missing moved file: {target_rel} (from {old_rel})")
            continue

        if isinstance(expected_hash, str):
            got = sha256_file(target_abs)
            if got != expected_hash:
                errors.append(f"hash mismatch: {target_rel}")

        old_abs = ROOT / old_rel
        if strict and old_abs.exists():
            errors.append(f"old file still present in strict mode: {old_rel}")


def scan_python_imports(strict: bool, errors: List[str], warnings: List[str]) -> None:
    for path in iter_files(ROOT):
        if path.suffix.lower() != ".py":
            continue
        rel = path.relative_to(ROOT).as_posix()
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=rel)
        except Exception as exc:
            warnings.append(f"could not parse python file {rel}: {exc}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in LEGACY_IMPORT_ROOTS:
                        msg = f"legacy import namespace: {rel}:{node.lineno} -> import {alias.name}"
                        if strict:
                            errors.append(msg)
                        else:
                            warnings.append(msg)
            elif isinstance(node, ast.ImportFrom):
                if not node.module:
                    continue
                root = node.module.split(".")[0]
                if root in LEGACY_IMPORT_ROOTS:
                    msg = f"legacy import namespace: {rel}:{node.lineno} -> from {node.module}"
                    if strict:
                        errors.append(msg)
                    else:
                        warnings.append(msg)


def scan_text_path_refs(fail_on_text_refs: bool, errors: List[str], warnings: List[str]) -> None:
    for path in iter_files(ROOT):
        if path.suffix.lower() not in TEXT_EXTS:
            continue
        rel = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            warnings.append(f"unable to read {rel}: {exc}")
            continue

        for line_no, line in enumerate(text.splitlines(), start=1):
            if not LEGACY_PATH_RE.search(line):
                continue
            msg = f"legacy path literal: {rel}:{line_no} -> {line.strip()[:180]}"
            if fail_on_text_refs:
                errors.append(msg)
            else:
                warnings.append(msg)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify agents/ migration integrity")
    parser.add_argument(
        "--write-manifest",
        help="Write pre-migration manifest JSON and exit",
    )
    parser.add_argument(
        "--manifest",
        default=".migration/move_manifest.json",
        help="Manifest JSON used for post-migration verification",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when legacy roots/imports still exist",
    )
    parser.add_argument(
        "--fail-on-text-refs",
        action="store_true",
        help="Fail on text/code literals still referencing old path roots",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.write_manifest:
        return write_manifest((ROOT / args.write_manifest).resolve())

    manifest_path = (ROOT / args.manifest).resolve()
    errors: List[str] = []
    warnings: List[str] = []

    verify_structure(args.strict, errors, warnings)
    verify_manifest(manifest_path, args.strict, errors, warnings)
    scan_python_imports(args.strict, errors, warnings)
    scan_text_path_refs(args.fail_on_text_refs, errors, warnings)

    for line in warnings:
        print(safe_console_text(f"[warn] {line}"))
    for line in errors:
        print(safe_console_text(f"[error] {line}"))

    if errors:
        print(f"\nFAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1

    print(f"\nPASSED: 0 error(s), {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

