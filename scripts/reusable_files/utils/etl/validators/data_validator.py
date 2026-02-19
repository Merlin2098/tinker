from __future__ import annotations

from datetime import datetime
from typing import Any


class DataValidator:
    """Generic data quality helpers."""

    @staticmethod
    def validate_required_columns(
        data_columns: list[str],
        required_columns: list[str],
    ) -> tuple[bool, list[str]]:
        missing = [column for column in required_columns if column not in data_columns]
        return len(missing) == 0, missing

    @staticmethod
    def validate_date_format(
        rows: list[dict[str, Any]],
        date_columns: list[str],
        fmt: str = "%Y-%m-%d",
    ) -> tuple[bool, list[dict[str, Any]]]:
        invalid: list[dict[str, Any]] = []
        for column in date_columns:
            for idx, row in enumerate(rows, start=2):
                value = row.get(column)
                if value in (None, ""):
                    continue
                try:
                    datetime.strptime(str(value), fmt)
                except ValueError:
                    invalid.append({"row": idx, "column": column, "value": value})
        return len(invalid) == 0, invalid

    @staticmethod
    def validate_no_nulls(
        rows: list[dict[str, Any]],
        required_columns: list[str],
    ) -> tuple[bool, list[dict[str, Any]]]:
        null_rows: list[dict[str, Any]] = []
        for idx, row in enumerate(rows, start=2):
            null_columns = [column for column in required_columns if str(row.get(column, "")).strip() == ""]
            if null_columns:
                null_rows.append({"row": idx, "columns": null_columns})
        return len(null_rows) == 0, null_rows
