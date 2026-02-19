#!/usr/bin/env python3
"""
Canonical execution wrapper for the `excel_to_parquet` skill.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_input_excel_path(raw_path: Any) -> tuple[str, Path]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("source_excel_path is required and must be a non-empty string.")

    project_root = _project_root()
    candidate = Path(raw_path.strip())
    if not candidate.is_absolute():
        candidate = project_root / candidate
    resolved = candidate.resolve()

    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"source_excel_path must resolve inside project root: {resolved}") from exc

    if resolved.suffix.lower() not in {".xlsx", ".xls", ".xlsm"}:
        raise ValueError("source_excel_path must point to a .xlsx/.xls/.xlsm file.")
    if not resolved.exists():
        raise FileNotFoundError(f"Source Excel file not found: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"source_excel_path must be a file: {resolved}")

    return str(resolved), resolved


def _resolve_output_parquet_path(raw_path: Any) -> tuple[str, Path]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("target_parquet_path is required and must be a non-empty string.")

    project_root = _project_root()
    candidate = Path(raw_path.strip())
    if not candidate.is_absolute():
        candidate = project_root / candidate
    resolved = candidate.resolve()

    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"target_parquet_path must resolve inside project root: {resolved}") from exc

    if resolved.suffix.lower() != ".parquet":
        raise ValueError("target_parquet_path must point to a .parquet file.")
    if resolved.exists() and not resolved.is_file():
        raise ValueError(f"target_parquet_path exists and is not a file: {resolved}")

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


def _compression(value: Any, default: str = "snappy") -> str:
    if value is None:
        return default
    if not isinstance(value, str) or not value.strip():
        raise ValueError("compression must be a non-empty string when provided.")
    lowered = value.strip().lower()
    alias = {"none": "uncompressed"}
    normalized = alias.get(lowered, lowered)
    allowed = {"snappy", "gzip", "zstd", "lz4", "brotli", "uncompressed"}
    if normalized not in allowed:
        raise ValueError(f"Unsupported compression codec: {value!r}. Allowed: {sorted(allowed)}")
    return normalized


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    source_raw = args.get("source_excel_path", args.get("source_path"))
    target_raw = args.get("target_parquet_path", args.get("target_path"))
    source_resolved_str, source_resolved = _resolve_input_excel_path(source_raw)
    target_resolved_str, target_resolved = _resolve_output_parquet_path(target_raw)

    sheet_name = _sheet_name(args.get("sheet_name"), default=0)
    compression = _compression(args.get("compression"), default="snappy")
    use_polars = _bool(args.get("use_polars"), default=True)
    overwrite = _bool(args.get("overwrite"), default=True)

    if target_resolved.exists() and not overwrite:
        raise ValueError(f"target_parquet_path already exists and overwrite=false: {target_resolved}")

    target_resolved.parent.mkdir(parents=True, exist_ok=True)

    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "pandas is required for excel_to_parquet wrapper. Install with: pip install pandas openpyxl pyarrow"
        ) from exc

    dataframe_pandas = pd.read_excel(source_resolved, sheet_name=sheet_name)
    object_columns = list(dataframe_pandas.select_dtypes(include=["object"]).columns)
    for column in object_columns:
        dataframe_pandas[column] = dataframe_pandas[column].map(
            lambda value: None if pd.isna(value) else str(value)
        )
    row_count = int(len(dataframe_pandas))
    column_count = int(len(dataframe_pandas.columns))
    engine_used = "pandas"
    fallback_reason: str | None = None

    if use_polars:
        try:
            import polars as pl
        except ImportError as exc:
            raise RuntimeError(
                "polars is required when use_polars=true. Install with: pip install polars pyarrow"
            ) from exc
        try:
            dataframe_polars = pl.from_pandas(dataframe_pandas)
            dataframe_polars.write_parquet(target_resolved, compression=compression)
            engine_used = "polars"
        except Exception as exc:
            pandas_compression = None if compression == "uncompressed" else compression
            dataframe_pandas.to_parquet(target_resolved, compression=pandas_compression, index=False)
            engine_used = "pandas_fallback"
            fallback_reason = str(exc)
    else:
        pandas_compression = None if compression == "uncompressed" else compression
        dataframe_pandas.to_parquet(target_resolved, compression=pandas_compression, index=False)
        engine_used = "pandas"

    source_size = source_resolved.stat().st_size
    target_size = target_resolved.stat().st_size
    compression_ratio = 0.0
    if source_size > 0:
        compression_ratio = 1 - (target_size / source_size)

    return {
        "status": "ok",
        "skill": "excel_to_parquet",
        "source_excel_path": source_raw,
        "resolved_source_excel_path": source_resolved_str,
        "target_parquet_path": target_raw,
        "resolved_target_parquet_path": target_resolved_str,
        "sheet_name": sheet_name,
        "compression": compression,
        "use_polars": use_polars,
        "engine_used": engine_used,
        "fallback_reason": fallback_reason,
        "overwrite": overwrite,
        "row_count": row_count,
        "column_count": column_count,
        "source_size_bytes": source_size,
        "target_size_bytes": target_size,
        "compression_ratio": round(compression_ratio, 6),
    }
