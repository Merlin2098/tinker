#!/usr/bin/env python3
"""
Canonical execution wrapper for the `input_file_handler` skill.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from agent_tools.wrappers._explorer_common import (
        file_stats,
        parse_bool,
        parse_encoding,
        parse_int,
        preview_text,
        resolve_repo_path,
    )
except ImportError:
    from wrappers._explorer_common import (
        file_stats,
        parse_bool,
        parse_encoding,
        parse_int,
        preview_text,
        resolve_repo_path,
    )


TEXT_SUFFIXES = {
    ".txt",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".sql",
    ".xml",
    ".html",
    ".htm",
    ".py",
    ".log",
}


def _normalize_extensions(raw: Any) -> set[str] | None:
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise ValueError("allowed_extensions must be a list when provided.")

    normalized: set[str] = set()
    for entry in raw:
        if not isinstance(entry, str) or not entry.strip():
            raise ValueError("allowed_extensions items must be non-empty strings.")
        value = entry.strip().lower()
        if not value.startswith("."):
            value = f".{value}"
        normalized.add(value)

    if not normalized:
        raise ValueError("allowed_extensions cannot be an empty list.")
    return normalized


def _is_text_like(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    must_exist = parse_bool(args.get("must_exist"), field="must_exist", default=True)
    allowed_extensions = _normalize_extensions(args.get("allowed_extensions"))

    resolved_str, resolved = resolve_repo_path(
        args.get("path"),
        field_name="path",
        allowed_suffixes=allowed_extensions,
        must_exist=must_exist,
        file_only=True,
    )

    encoding = parse_encoding(args.get("encoding"), default="utf-8-sig")
    include_preview = parse_bool(args.get("include_preview"), field="include_preview", default=True)
    max_preview_lines = parse_int(
        args.get("max_preview_lines"),
        field="max_preview_lines",
        default=5,
        minimum=0,
        maximum=200,
    )
    preview_chars = parse_int(
        args.get("preview_chars"),
        field="preview_chars",
        default=1200,
        minimum=1,
        maximum=50000,
    )
    force_text_preview = parse_bool(
        args.get("force_text_preview"),
        field="force_text_preview",
        default=False,
    )

    exists = resolved.exists()
    result: dict[str, Any] = {
        "status": "ok",
        "skill": "input_file_handler",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "exists": exists,
        "extension": resolved.suffix.lower(),
        "encoding": encoding,
        "preview": None,
        "preview_truncated": None,
        "preview_line_count": None,
    }

    if not exists:
        result["parent_exists"] = resolved.parent.exists()
        return result

    result.update(file_stats(resolved))

    should_preview = include_preview and (force_text_preview or _is_text_like(resolved))
    if not should_preview or max_preview_lines == 0:
        return result

    raw = resolved.read_text(encoding=encoding)
    lines = raw.splitlines()
    selected = "\n".join(lines[:max_preview_lines])
    preview, char_truncated = preview_text(selected, max_chars=preview_chars)
    line_truncated = len(lines) > max_preview_lines

    result["preview"] = preview
    result["preview_truncated"] = bool(char_truncated or line_truncated)
    result["preview_line_count"] = min(len(lines), max_preview_lines)
    result["line_count"] = len(lines)

    return result
