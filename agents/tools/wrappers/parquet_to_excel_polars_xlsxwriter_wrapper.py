#!/usr/bin/env python3
"""
Canonical execution wrapper for the `parquet_to_excel_polars_xlsxwriter` skill.
"""

from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path
from typing import Any


EXCEL_MAX_ROWS = 1_048_576
INVALID_SHEET_CHARS = set("[]:*?/\\")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_input_parquet_path(raw_path: Any) -> tuple[str, Path]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("source_parquet_path is required and must be a non-empty string.")

    project_root = _project_root()
    candidate = Path(raw_path.strip())
    if not candidate.is_absolute():
        candidate = project_root / candidate
    resolved = candidate.resolve()

    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"source_parquet_path must resolve inside project root: {resolved}") from exc

    if resolved.suffix.lower() != ".parquet":
        raise ValueError("source_parquet_path must point to a .parquet file.")
    if not resolved.exists():
        raise FileNotFoundError(f"Source Parquet file not found: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"source_parquet_path must be a file: {resolved}")

    return str(resolved), resolved


def _resolve_output_excel_path(raw_path: Any) -> tuple[str, Path]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("target_excel_path is required and must be a non-empty string.")

    project_root = _project_root()
    candidate = Path(raw_path.strip())
    if not candidate.is_absolute():
        candidate = project_root / candidate
    resolved = candidate.resolve()

    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"target_excel_path must resolve inside project root: {resolved}") from exc

    if resolved.suffix.lower() != ".xlsx":
        raise ValueError("target_excel_path must point to a .xlsx file.")
    if resolved.exists() and not resolved.is_file():
        raise ValueError(f"target_excel_path exists and is not a file: {resolved}")

    return str(resolved), resolved


def _sheet_name(value: Any, default: str = "Sheet1") -> str:
    if value is None:
        candidate = default
    elif isinstance(value, str):
        candidate = value.strip()
    else:
        raise ValueError("sheet_name must be a string when provided.")

    if not candidate:
        raise ValueError("sheet_name cannot be empty.")
    if len(candidate) > 31:
        raise ValueError("sheet_name must be 31 characters or fewer.")
    if any(char in INVALID_SHEET_CHARS for char in candidate):
        raise ValueError("sheet_name contains invalid Excel characters: []:*?/\\")
    return candidate


def _bool(value: Any, default: bool) -> bool:
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


def _max_rows(value: Any, default: int = EXCEL_MAX_ROWS) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and value.strip().isdigit():
        parsed = int(value.strip())
    else:
        raise ValueError("max_rows must be an integer when provided.")
    if parsed <= 0 or parsed > EXCEL_MAX_ROWS:
        raise ValueError(f"max_rows must be between 1 and {EXCEL_MAX_ROWS}.")
    return parsed


def _to_excel_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return str(value)


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    source_raw = args.get("source_parquet_path", args.get("source_path"))
    target_raw = args.get("target_excel_path", args.get("target_path"))
    source_resolved_str, source_resolved = _resolve_input_parquet_path(source_raw)
    target_resolved_str, target_resolved = _resolve_output_excel_path(target_raw)

    sheet_name = _sheet_name(args.get("sheet_name"), default="Sheet1")
    include_header = _bool(args.get("header"), default=True)
    overwrite = _bool(args.get("overwrite"), default=True)
    max_rows = _max_rows(args.get("max_rows"), default=EXCEL_MAX_ROWS)

    if target_resolved.exists() and not overwrite:
        raise ValueError(f"target_excel_path already exists and overwrite=false: {target_resolved}")

    target_resolved.parent.mkdir(parents=True, exist_ok=True)

    try:
        import polars as pl
        import xlsxwriter
    except ImportError as exc:
        raise RuntimeError(
            "polars and xlsxwriter are required for parquet_to_excel_polars_xlsxwriter wrapper. "
            "Install with: pip install polars xlsxwriter"
        ) from exc

    dataframe = pl.read_parquet(source_resolved)
    if dataframe.height == 0:
        raise ValueError("Parquet file is empty.")

    original_row_count = int(dataframe.height)
    truncated = False
    if dataframe.height > max_rows:
        dataframe = dataframe.head(max_rows)
        truncated = True

    workbook = xlsxwriter.Workbook(str(target_resolved))
    try:
        worksheet = workbook.add_worksheet(sheet_name)

        start_row = 0
        if include_header:
            for col_idx, col_name in enumerate(dataframe.columns):
                worksheet.write(0, col_idx, str(col_name))
            start_row = 1

        for row_idx, row in enumerate(dataframe.iter_rows(named=False), start=start_row):
            for col_idx, value in enumerate(row):
                worksheet.write(row_idx, col_idx, _to_excel_value(value))
    finally:
        workbook.close()

    return {
        "status": "ok",
        "skill": "parquet_to_excel_polars_xlsxwriter",
        "source_parquet_path": source_raw,
        "resolved_source_parquet_path": source_resolved_str,
        "target_excel_path": target_raw,
        "resolved_target_excel_path": target_resolved_str,
        "sheet_name": sheet_name,
        "header": include_header,
        "overwrite": overwrite,
        "max_rows": max_rows,
        "source_row_count": original_row_count,
        "row_count_written": int(dataframe.height),
        "column_count": int(dataframe.width),
        "truncated": truncated,
        "source_size_bytes": source_resolved.stat().st_size,
        "target_size_bytes": target_resolved.stat().st_size,
    }

