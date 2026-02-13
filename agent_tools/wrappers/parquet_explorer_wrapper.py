#!/usr/bin/env python3
"""
Canonical execution wrapper for the `parquet_explorer` skill.
"""

from __future__ import annotations

from typing import Any

try:
    from agent_tools.wrappers._explorer_common import file_stats, parse_int, resolve_repo_path, to_jsonable
except ImportError:
    from wrappers._explorer_common import file_stats, parse_int, resolve_repo_path, to_jsonable


def _columns(value: Any) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not value:
        raise ValueError("columns must be a non-empty array of strings when provided.")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError("columns entries must be non-empty strings.")
        out.append(item.strip())
    return out


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    resolved_str, resolved = resolve_repo_path(
        args.get("path"),
        field_name="path",
        allowed_suffixes={".parquet"},
    )
    preview_rows = parse_int(args.get("preview_rows"), field="preview_rows", default=5, minimum=0, maximum=200)
    columns = _columns(args.get("columns"))

    try:
        import polars as pl
    except ImportError as exc:
        raise RuntimeError("polars is required. Install with: pip install polars pyarrow") from exc

    lazy = pl.scan_parquet(resolved)
    if columns:
        lazy = lazy.select(columns)

    schema = lazy.collect_schema()
    row_count = int(lazy.select(pl.len().alias("row_count")).collect().item())
    preview_df = lazy.head(preview_rows).collect()
    rows_preview = [{k: to_jsonable(v) for k, v in row.items()} for row in preview_df.to_dicts()]

    return {
        "status": "ok",
        "skill": "parquet_explorer",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "row_count": row_count,
        "column_count": len(schema),
        "columns": list(schema.names()),
        "schema": {name: str(dtype) for name, dtype in schema.items()},
        "selected_columns": columns,
        "preview_rows": preview_rows,
        "rows_preview": rows_preview,
        **file_stats(resolved),
    }

