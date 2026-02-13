#!/usr/bin/env python3
"""
Canonical execution wrapper for the `query_parquet_duckdb` skill.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

try:
    from agent_tools.wrappers.connect_duckdb_wrapper import _bool, _normalize_config, _resolve_database_path
except ImportError:
    from wrappers.connect_duckdb_wrapper import _bool, _normalize_config, _resolve_database_path


def _int(value: Any, default: int = 20) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    raise ValueError(f"Invalid integer value: {value!r}")


def _to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def _validate_sql(sql_query: Any, allow_write: bool) -> str:
    if not isinstance(sql_query, str) or not sql_query.strip():
        raise ValueError("sql_query is required and must be a non-empty string.")
    sql = sql_query.strip()
    lowered = sql.lower()
    if not allow_write:
        allowed_prefixes = ("select", "with", "explain", "pragma")
        if not lowered.startswith(allowed_prefixes):
            raise ValueError(
                "Only read/query statements are allowed when allow_write=false."
            )
    return sql


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    read_only = _bool(args.get("read_only"), default=False)
    allow_write = _bool(args.get("allow_write"), default=False)
    preview_rows = _int(args.get("preview_rows"), default=20)
    if preview_rows <= 0 or preview_rows > 1000:
        raise ValueError("preview_rows must be between 1 and 1000.")

    config = _normalize_config(args.get("config"))
    sql_query = _validate_sql(args.get("sql_query"), allow_write=allow_write)

    database_path = str(args.get("database_path", ":memory:"))
    db_for_duckdb, resolved_file_path, _ = _resolve_database_path(
        database_path,
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
        cursor = conn.execute(sql_query)
        columns = [desc[0] for desc in (cursor.description or [])]
        all_rows = cursor.fetchall()
    finally:
        if conn is not None:
            conn.close()

    rows_preview = [
        {columns[idx]: _to_jsonable(value) for idx, value in enumerate(row)}
        for row in all_rows[:preview_rows]
    ]

    return {
        "status": "ok",
        "skill": "query_parquet_duckdb",
        "database_path": database_path,
        "resolved_database_path": resolved_file_path,
        "read_only": read_only,
        "allow_write": allow_write,
        "config_applied_keys": sorted(config.keys()),
        "sql_query": sql_query,
        "row_count": len(all_rows),
        "column_count": len(columns),
        "columns": columns,
        "rows_preview": rows_preview,
        "preview_rows": preview_rows,
        "truncated": len(all_rows) > preview_rows,
    }

