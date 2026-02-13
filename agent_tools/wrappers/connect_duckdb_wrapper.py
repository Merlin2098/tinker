#!/usr/bin/env python3
"""
Canonical execution wrapper for the `connect_duckdb` skill.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb


def _project_root() -> Path:
    # .../agent_tools/wrappers/connect_duckdb_wrapper.py -> project root
    return Path(__file__).resolve().parents[2]


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


def _normalize_config(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("config must be an object/map when provided.")

    normalized: dict[str, Any] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not key:
            raise ValueError("config keys must be non-empty strings.")
        if not isinstance(value, (str, int, float, bool)):
            raise ValueError(
                f"config['{key}'] has unsupported value type: {type(value).__name__}"
            )
        normalized[key] = value
    return normalized


def _resolve_database_path(raw_path: str, read_only: bool) -> tuple[str, str | None, bool]:
    path_value = (raw_path or "").strip()
    if not path_value:
        raise ValueError("database_path is required and cannot be empty.")

    if path_value == ":memory:":
        return ":memory:", None, False

    project_root = _project_root()
    candidate = Path(path_value)
    if not candidate.is_absolute():
        candidate = project_root / candidate
    resolved = candidate.resolve()

    # Guardrails: keep file-based DB paths inside repository root.
    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(
            f"database_path must resolve inside project root: {resolved}"
        ) from exc

    existed_before = resolved.exists()
    if read_only and not existed_before:
        raise FileNotFoundError(f"Read-only database does not exist: {resolved}")

    if not read_only:
        resolved.parent.mkdir(parents=True, exist_ok=True)

    return str(resolved), str(resolved), existed_before


def run(args: dict[str, Any]) -> dict[str, Any]:
    """
    Execute connection validation for DuckDB and return structured metadata.
    """
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    read_only = _bool(args.get("read_only"), default=False)
    config = _normalize_config(args.get("config"))
    db_for_duckdb, resolved_file_path, existed_before = _resolve_database_path(
        str(args.get("database_path", "")),
        read_only=read_only,
    )

    conn: duckdb.DuckDBPyConnection | None = None
    try:
        connect_kwargs: dict[str, Any] = {
            "database": db_for_duckdb,
            "read_only": read_only,
        }
        if config:
            connect_kwargs["config"] = config
        conn = duckdb.connect(**connect_kwargs)
        probe = conn.execute("SELECT 1 AS ok").fetchone()
        query_ok = bool(probe and probe[0] == 1)
    finally:
        if conn is not None:
            conn.close()

    created = False
    if resolved_file_path is not None:
        created = (not existed_before) and Path(resolved_file_path).exists()

    return {
        "status": "ok",
        "skill": "connect_duckdb",
        "database_path": args.get("database_path"),
        "resolved_database_path": resolved_file_path,
        "read_only": read_only,
        "created_database_file": created,
        "config_applied_keys": sorted(config.keys()),
        "probe_query_ok": query_ok,
    }
