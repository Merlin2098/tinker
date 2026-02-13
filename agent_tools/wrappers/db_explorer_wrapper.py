#!/usr/bin/env python3
"""
Canonical execution wrapper for the `db_explorer` skill.
"""

from __future__ import annotations

import sqlite3
from typing import Any

try:
    from agent_tools.wrappers._explorer_common import (
        file_stats,
        parse_bool,
        parse_int,
        resolve_repo_path,
        to_jsonable,
    )
except ImportError:
    from wrappers._explorer_common import file_stats, parse_bool, parse_int, resolve_repo_path, to_jsonable


SUPPORTED_SUFFIXES = {".duckdb", ".db", ".sqlite", ".sqlite3"}


def _table_name(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError("table must be a non-empty string when provided.")


def _duckdb_tables(conn: Any) -> list[str]:
    rows = conn.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_name
        """
    ).fetchall()
    return [row[0] for row in rows]


def _duckdb_schema(conn: Any, table: str) -> list[dict[str, Any]]:
    escaped_table = table.replace("'", "''")
    rows = conn.execute(f"PRAGMA table_info('{escaped_table}')").fetchall()
    out = []
    for row in rows:
        out.append(
            {
                "column_id": row[0],
                "name": row[1],
                "type": row[2],
                "not_null": bool(row[3]),
                "default": to_jsonable(row[4]),
                "primary_key": bool(row[5]),
            }
        )
    return out


def _sqlite_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return [row[0] for row in rows]


def _sqlite_schema(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    escaped_table = table.replace("'", "''")
    rows = conn.execute(f"PRAGMA table_info('{escaped_table}')").fetchall()
    out = []
    for row in rows:
        out.append(
            {
                "column_id": row[0],
                "name": row[1],
                "type": row[2],
                "not_null": bool(row[3]),
                "default": to_jsonable(row[4]),
                "primary_key": bool(row[5]),
            }
        )
    return out


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    resolved_str, resolved = resolve_repo_path(
        args.get("path"),
        field_name="path",
        allowed_suffixes=SUPPORTED_SUFFIXES,
    )
    preview_rows = parse_int(args.get("preview_rows"), field="preview_rows", default=20, minimum=0, maximum=500)
    table = _table_name(args.get("table"))
    read_only = parse_bool(args.get("read_only"), field="read_only", default=True)

    suffix = resolved.suffix.lower()
    if suffix == ".duckdb":
        try:
            import duckdb
        except ImportError as exc:
            raise RuntimeError("duckdb is required for .duckdb exploration. Install with: pip install duckdb") from exc

        conn = duckdb.connect(database=str(resolved), read_only=read_only)
        try:
            tables = _duckdb_tables(conn)
            selected = table or (tables[0] if tables else None)
            if selected and selected not in tables:
                raise ValueError(f"Requested table not found: {selected}")
            schema = _duckdb_schema(conn, selected) if selected else []
            rows_preview: list[dict[str, Any]] = []
            if selected and preview_rows > 0:
                rows = conn.execute(f'SELECT * FROM "{selected}" LIMIT {preview_rows}').fetchall()
                cols = [desc[0] for desc in (conn.description or [])]
                rows_preview = [
                    {cols[idx]: to_jsonable(value) for idx, value in enumerate(row)}
                    for row in rows
                ]
        finally:
            conn.close()

        return {
            "status": "ok",
            "skill": "db_explorer",
            "engine": "duckdb",
            "path": args.get("path"),
            "resolved_path": resolved_str,
            "read_only": read_only,
            "table_count": len(tables),
            "tables": tables,
            "selected_table": selected,
            "table_schema": schema,
            "preview_rows": preview_rows,
            "rows_preview": rows_preview,
            **file_stats(resolved),
        }

    conn = sqlite3.connect(f"file:{resolved}?mode=ro", uri=True) if read_only else sqlite3.connect(str(resolved))
    try:
        conn.row_factory = sqlite3.Row
        tables = _sqlite_tables(conn)
        selected = table or (tables[0] if tables else None)
        if selected and selected not in tables:
            raise ValueError(f"Requested table not found: {selected}")
        schema = _sqlite_schema(conn, selected) if selected else []
        rows_preview: list[dict[str, Any]] = []
        if selected and preview_rows > 0:
            rows = conn.execute(f'SELECT * FROM "{selected}" LIMIT {preview_rows}').fetchall()
            rows_preview = [{k: to_jsonable(row[k]) for k in row.keys()} for row in rows]
    finally:
        conn.close()

    return {
        "status": "ok",
        "skill": "db_explorer",
        "engine": "sqlite",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "read_only": read_only,
        "table_count": len(tables),
        "tables": tables,
        "selected_table": selected,
        "table_schema": schema,
        "preview_rows": preview_rows,
        "rows_preview": rows_preview,
        **file_stats(resolved),
    }
