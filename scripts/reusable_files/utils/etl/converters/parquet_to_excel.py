from __future__ import annotations

from pathlib import Path

import polars as pl


class ParquetToExcelConverter:
    """Simple parquet-to-excel exporter."""

    @staticmethod
    def write_frame(
        frame: object,
        output_path: str | Path,
        *,
        sheet_name: str = "data",
    ) -> None:
        if not isinstance(frame, pl.DataFrame):
            raise TypeError(
                "ParquetToExcelConverter.write_frame expects a polars.DataFrame "
                f"(received {type(frame)!r})"
            )

        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        frame.write_excel(
            target,
            worksheet=sheet_name[:31],
            autofilter=True,
            autofit=True,
            freeze_panes=(1, 0),
        )

    @staticmethod
    def convert(
        parquet_path: str | Path,
        output_path: str | Path,
        *,
        sheet_name: str = "data",
    ) -> None:
        source = Path(parquet_path)
        if not source.exists():
            raise FileNotFoundError(f"Parquet file not found: {source}")

        frame = pl.read_parquet(source)
        ParquetToExcelConverter.write_frame(frame, output_path, sheet_name=sheet_name)
