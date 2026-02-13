#!/usr/bin/env python3
"""
Canonical execution wrapper for the `load_sql_queries` skill.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_input_path(raw_path: Any) -> tuple[str, Path]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("path is required and must be a non-empty string.")

    project_root = _project_root()
    candidate = Path(raw_path.strip())
    if not candidate.is_absolute():
        candidate = project_root / candidate
    resolved = candidate.resolve()

    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"path must resolve inside project root: {resolved}") from exc

    if resolved.suffix.lower() != ".sql":
        raise ValueError("path must point to a .sql file.")
    if not resolved.exists():
        raise FileNotFoundError(f"SQL file not found: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"path must be a file: {resolved}")

    return str(resolved), resolved


def _encoding(value: Any, default: str = "utf-8-sig") -> str:
    if value is None:
        return default
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError("encoding must be a non-empty string when provided.")


def _int(value: Any, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    raise ValueError(f"Invalid integer value: {value!r}")


def _bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def _strip_sql_comments(sql_text: str) -> str:
    lines: list[str] = []
    for line in sql_text.splitlines():
        if line.strip().startswith("--"):
            continue
        lines.append(line)
    return "\n".join(lines)


def _statement_count(sql_text: str) -> int:
    parts = [part.strip() for part in sql_text.split(";")]
    return sum(1 for part in parts if part)


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    encoding = _encoding(args.get("encoding"))
    preview_chars = _int(args.get("preview_chars"), default=400)
    if preview_chars <= 0 or preview_chars > 4000:
        raise ValueError("preview_chars must be between 1 and 4000.")
    strip_comments = _bool(args.get("strip_comments"), default=False)

    resolved_str, resolved = _resolve_input_path(args.get("path"))
    raw = resolved.read_text(encoding=encoding)
    query_text = _strip_sql_comments(raw) if strip_comments else raw

    if not query_text.strip():
        raise ValueError("SQL file is empty after preprocessing.")

    line_count = query_text.count("\n") + 1
    size_bytes = resolved.stat().st_size
    truncated = len(query_text) > preview_chars

    return {
        "status": "ok",
        "skill": "load_sql_queries",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "encoding": encoding,
        "strip_comments": strip_comments,
        "line_count": line_count,
        "size_bytes": size_bytes,
        "statement_count": _statement_count(query_text),
        "query_text": query_text,
        "query_preview": query_text[:preview_chars],
        "preview_chars": preview_chars,
        "truncated": truncated,
    }

