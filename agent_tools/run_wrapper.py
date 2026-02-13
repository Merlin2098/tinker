#!/usr/bin/env python3
"""
Canonical wrapper runner for thin skill interfaces.

Usage:
  .venv/Scripts/python.exe agent_tools/run_wrapper.py --skill connect_duckdb --args-json '{"database_path":"data/example.duckdb"}'
  .venv/Scripts/python.exe agent_tools/run_wrapper.py --skill load_json_files --args-file agent/agent_outputs/plans/load_json.args.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

try:
    from agent_tools.wrappers.connect_duckdb_wrapper import run as run_connect_duckdb
    from agent_tools.wrappers.excel_to_parquet_wrapper import run as run_excel_to_parquet
    from agent_tools.wrappers.load_json_files_wrapper import run as run_load_json_files
    from agent_tools.wrappers.load_sql_queries_wrapper import run as run_load_sql_queries
    from agent_tools.wrappers.load_yaml_files_wrapper import run as run_load_yaml_files
    from agent_tools.wrappers.parquet_to_excel_polars_xlsxwriter_wrapper import run as run_parquet_to_excel_polars_xlsxwriter
    from agent_tools.wrappers.query_parquet_duckdb_wrapper import run as run_query_parquet_duckdb
    from agent_tools.wrappers.read_excel_pandas_wrapper import run as run_read_excel_pandas
    from agent_tools.wrappers.read_excel_polars_openpyxl_wrapper import run as run_read_excel_polars_openpyxl
except ImportError:
    # Allow direct execution as a script from project root.
    from wrappers.connect_duckdb_wrapper import run as run_connect_duckdb
    from wrappers.excel_to_parquet_wrapper import run as run_excel_to_parquet
    from wrappers.load_json_files_wrapper import run as run_load_json_files
    from wrappers.load_sql_queries_wrapper import run as run_load_sql_queries
    from wrappers.load_yaml_files_wrapper import run as run_load_yaml_files
    from wrappers.parquet_to_excel_polars_xlsxwriter_wrapper import run as run_parquet_to_excel_polars_xlsxwriter
    from wrappers.query_parquet_duckdb_wrapper import run as run_query_parquet_duckdb
    from wrappers.read_excel_pandas_wrapper import run as run_read_excel_pandas
    from wrappers.read_excel_polars_openpyxl_wrapper import run as run_read_excel_polars_openpyxl


WrapperFunc = Callable[[dict[str, Any]], dict[str, Any]]

WRAPPER_REGISTRY: dict[str, WrapperFunc] = {
    "connect_duckdb": run_connect_duckdb,
    "excel_to_parquet": run_excel_to_parquet,
    "load_json_files": run_load_json_files,
    "load_sql_queries": run_load_sql_queries,
    "load_yaml_files": run_load_yaml_files,
    "parquet_to_excel_polars_xlsxwriter": run_parquet_to_excel_polars_xlsxwriter,
    "query_parquet_duckdb": run_query_parquet_duckdb,
    "read_excel_pandas": run_read_excel_pandas,
    "read_excel_polars_openpyxl": run_read_excel_polars_openpyxl,
}


def _load_args_json(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid --args-json payload: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("--args-json must decode to a JSON object.")
    return data


def _load_args_file(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise ValueError(f"--args-file not found: {path}")
    try:
        # utf-8-sig tolerates BOM produced by some Windows editors/tools.
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in --args-file ({path}): {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("--args-file must contain a JSON object.")
    return data


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run canonical wrapper by skill name")
    parser.add_argument("--skill", required=True, help="Skill name in wrapper registry")
    parser.add_argument("--args-json", help="JSON object with wrapper args")
    parser.add_argument("--args-file", help="Path to JSON file with wrapper args")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print output JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if bool(args.args_json) == bool(args.args_file):
        print(
            "Error: provide exactly one of --args-json or --args-file.",
            file=sys.stderr,
        )
        return 2

    runner = WRAPPER_REGISTRY.get(args.skill)
    if runner is None:
        known = ", ".join(sorted(WRAPPER_REGISTRY.keys()))
        print(
            f"Error: unknown --skill '{args.skill}'. Known skills: {known}",
            file=sys.stderr,
        )
        return 2

    try:
        payload = _load_args_json(args.args_json) if args.args_json else _load_args_file(args.args_file)
        result = runner(payload)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
