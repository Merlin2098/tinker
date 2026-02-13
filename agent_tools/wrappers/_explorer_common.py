#!/usr/bin/env python3
"""
Shared helpers for file_exploration canonical wrappers.
"""

from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path
from typing import Any
import math


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_repo_path(
    raw_path: Any,
    *,
    field_name: str = "path",
    allowed_suffixes: set[str] | None = None,
    must_exist: bool = True,
    file_only: bool = True,
) -> tuple[str, Path]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError(f"{field_name} is required and must be a non-empty string.")

    root = project_root()
    candidate = Path(raw_path.strip())
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{field_name} must resolve inside project root: {resolved}") from exc

    if allowed_suffixes is not None and resolved.suffix.lower() not in allowed_suffixes:
        allowed = ", ".join(sorted(allowed_suffixes))
        raise ValueError(f"{field_name} must use one of extensions: {allowed}")

    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"{field_name} not found: {resolved}")

    if file_only and resolved.exists() and not resolved.is_file():
        raise ValueError(f"{field_name} must be a file: {resolved}")

    return str(resolved), resolved


def parse_encoding(value: Any, default: str = "utf-8-sig") -> str:
    if value is None:
        return default
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError("encoding must be a non-empty string when provided.")


def parse_bool(value: Any, *, field: str, default: bool) -> bool:
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
    raise ValueError(f"{field} must be boolean when provided.")


def parse_int(
    value: Any,
    *,
    field: str,
    default: int,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    if value is None:
        parsed = default
    elif isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and value.strip().isdigit():
        parsed = int(value.strip())
    else:
        raise ValueError(f"{field} must be an integer when provided.")

    if minimum is not None and parsed < minimum:
        raise ValueError(f"{field} must be >= {minimum}.")
    if maximum is not None and parsed > maximum:
        raise ValueError(f"{field} must be <= {maximum}.")
    return parsed


def to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return None
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return str(value)


def file_stats(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {"size_bytes": stat.st_size}


def preview_text(raw: str, *, max_chars: int) -> tuple[str, bool]:
    truncated = len(raw) > max_chars
    return raw[:max_chars], truncated

