#!/usr/bin/env python3
"""
Canonical execution wrapper for the `read_excel_pandas` skill.
"""

from __future__ import annotations

from datetime import date, datetime, time
import math
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_excel_path(raw_path: Any) -> tuple[str, Path]:
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

    if resolved.suffix.lower() not in {".xlsx", ".xls"}:
        raise ValueError("path must point to a .xlsx or .xls file.")
    if not resolved.exists():
        raise FileNotFoundError(f"Excel file not found: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"path must be a file: {resolved}")

    return str(resolved), resolved


def _sheet_name(value: Any, default: int = 0) -> str | int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ValueError("sheet_name cannot be empty when provided.")
        if stripped.isdigit():
            return int(stripped)
        return stripped
    raise ValueError("sheet_name must be a string or integer when provided.")


def _optional_int(value: Any, *, field: str, minimum: int | None = None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and value.strip().isdigit():
        parsed = int(value.strip())
    else:
        raise ValueError(f"{field} must be an integer when provided.")
    if minimum is not None and parsed < minimum:
        raise ValueError(f"{field} must be >= {minimum}.")
    return parsed


def _header_row(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and value.strip().isdigit():
        parsed = int(value.strip())
    else:
        raise ValueError("header_row must be an integer when provided.")
    if parsed < 0:
        raise ValueError("header_row must be >= 0.")
    return parsed


def _preview_rows(value: Any, default: int = 5) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and value.strip().isdigit():
        parsed = int(value.strip())
    else:
        raise ValueError("preview_rows must be an integer when provided.")
    if parsed < 0 or parsed > 100:
        raise ValueError("preview_rows must be between 0 and 100.")
    return parsed


def _usecols(value: Any) -> str | list[str] | list[int] | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ValueError("usecols cannot be an empty string.")
        return stripped
    if isinstance(value, list):
        if not value:
            raise ValueError("usecols list cannot be empty.")
        normalized: list[str] | list[int] = []
        for item in value:
            if isinstance(item, int):
                normalized.append(item)
            elif isinstance(item, str) and item.strip():
                normalized.append(item.strip())
            else:
                raise ValueError("usecols list items must be non-empty strings or integers.")
        return normalized
    raise ValueError("usecols must be a string or list when provided.")


def _to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return str(value)


def _safe_records(dataframe: Any, preview_rows: int) -> list[dict[str, Any]]:
    if preview_rows == 0:
        return []
    records: list[dict[str, Any]] = []
    preview = dataframe.head(preview_rows)
    for _, row in preview.iterrows():
        records.append({str(column): _to_jsonable(row[column]) for column in dataframe.columns})
    return records


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    resolved_str, resolved = _resolve_excel_path(args.get("path"))
    sheet_name = _sheet_name(args.get("sheet_name"), default=0)
    header_row = _header_row(args.get("header_row"), default=0)
    nrows = _optional_int(args.get("nrows"), field="nrows", minimum=1)
    preview_rows = _preview_rows(args.get("preview_rows"), default=5)
    usecols = _usecols(args.get("usecols"))

    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "pandas is required for read_excel_pandas wrapper. Install with: pip install pandas openpyxl xlrd"
        ) from exc

    df = pd.read_excel(
        resolved,
        sheet_name=sheet_name,
        header=header_row,
        usecols=usecols,
        nrows=nrows,
    )

    columns = [str(column) for column in df.columns]
    dtypes = {str(column): str(dtype) for column, dtype in df.dtypes.items()}

    return {
        "status": "ok",
        "skill": "read_excel_pandas",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "sheet_name": sheet_name,
        "header_row": header_row,
        "nrows": nrows,
        "usecols": usecols,
        "preview_rows": preview_rows,
        "row_count": int(len(df)),
        "column_count": int(len(columns)),
        "columns": columns,
        "dtypes": dtypes,
        "rows_preview": _safe_records(df, preview_rows=preview_rows),
        "size_bytes": resolved.stat().st_size,
    }
