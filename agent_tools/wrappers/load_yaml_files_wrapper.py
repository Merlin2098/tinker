#!/usr/bin/env python3
"""
Canonical execution wrapper for the `load_yaml_files` skill.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


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

    if resolved.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError("path must point to a .yaml or .yml file.")
    if not resolved.exists():
        raise FileNotFoundError(f"YAML file not found: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"path must be a file: {resolved}")

    return str(resolved), resolved


def _encoding(value: Any, default: str = "utf-8-sig") -> str:
    if value is None:
        return default
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError("encoding must be a non-empty string when provided.")


def _type_name(data: Any) -> str:
    if isinstance(data, dict):
        return "object"
    if isinstance(data, list):
        return "array"
    if data is None:
        return "null"
    if isinstance(data, bool):
        return "boolean"
    if isinstance(data, (int, float)):
        return "number"
    if isinstance(data, str):
        return "string"
    return type(data).__name__


def _summary(data: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {"data_type": _type_name(data)}
    if isinstance(data, dict):
        keys = sorted(data.keys())
        summary["top_level_keys"] = keys
        summary["top_level_key_count"] = len(keys)
    elif isinstance(data, list):
        summary["item_count"] = len(data)
    return summary


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    encoding = _encoding(args.get("encoding"))
    resolved_str, resolved = _resolve_input_path(args.get("path"))

    raw = resolved.read_text(encoding=encoding)
    data = yaml.safe_load(raw)

    line_count = raw.count("\n") + 1
    size_bytes = resolved.stat().st_size

    return {
        "status": "ok",
        "skill": "load_yaml_files",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "encoding": encoding,
        "line_count": line_count,
        "size_bytes": size_bytes,
        **_summary(data),
    }

