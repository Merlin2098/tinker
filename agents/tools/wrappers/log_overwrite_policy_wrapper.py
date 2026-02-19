#!/usr/bin/env python3
"""
Canonical execution wrapper for the `log_overwrite_policy` skill.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from agents.tools.wrappers._explorer_common import parse_bool, parse_encoding
except ImportError:
    from wrappers._explorer_common import parse_bool, parse_encoding


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_log_path(raw_path: Any) -> tuple[str, Path]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("log_file_path is required and must be a non-empty string.")

    root = _project_root()
    candidate = Path(raw_path.strip())
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"log_file_path must resolve inside project root: {resolved}") from exc

    if resolved.exists() and resolved.is_dir():
        raise ValueError(f"log_file_path must be a file path, not a directory: {resolved}")

    return str(resolved), resolved


def _parse_header_lines(raw: Any) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("header_lines must be a list when provided.")

    lines: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            raise ValueError("header_lines items must be strings.")
        lines.append(item)
    return lines


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    resolved_str, resolved = _resolve_log_path(args.get("log_file_path", "logs/execution.log"))
    encoding = parse_encoding(args.get("encoding"), default="utf-8")
    create_parent = parse_bool(args.get("create_parent"), field="create_parent", default=True)
    dry_run = parse_bool(args.get("dry_run"), field="dry_run", default=False)

    header_lines = _parse_header_lines(args.get("header_lines"))
    if not header_lines:
        started = datetime.now(timezone.utc).isoformat()
        header_lines = [
            f"execution_started_utc={started}",
            "log_mode=overwrite",
        ]

    body = "\n".join(header_lines).rstrip() + "\n"

    if create_parent:
        resolved.parent.mkdir(parents=True, exist_ok=True)
    elif not resolved.parent.exists():
        raise FileNotFoundError(f"Parent directory does not exist: {resolved.parent}")

    if dry_run:
        return {
            "status": "ok",
            "skill": "log_overwrite_policy",
            "dry_run": True,
            "log_file_path": args.get("log_file_path", "logs/execution.log"),
            "resolved_path": resolved_str,
            "encoding": encoding,
            "create_parent": create_parent,
            "line_count": len(header_lines),
            "bytes_to_write": len(body.encode(encoding=encoding, errors="replace")),
        }

    resolved.write_text(body, encoding=encoding)
    size = resolved.stat().st_size

    return {
        "status": "ok",
        "skill": "log_overwrite_policy",
        "dry_run": False,
        "log_file_path": args.get("log_file_path", "logs/execution.log"),
        "resolved_path": resolved_str,
        "encoding": encoding,
        "create_parent": create_parent,
        "line_count": len(header_lines),
        "size_bytes": size,
        "overwritten": True,
    }

