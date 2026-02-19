from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Iterator

import duckdb
import polars as pl
import pyarrow as pa


class DuckDBManager:
    """Small helper around DuckDB for parquet-backed SQL transforms."""

    IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(self, database: str = ":memory:") -> None:
        self.database = database
        self.conn = duckdb.connect(database=database)

    @staticmethod
    def adapt_sql_for_duckdb(sql: str) -> str:
        # MySQL-style quoted identifiers and types are common in legacy scripts.
        rewritten = re.sub(r"`([^`]*)`", r'"\1"', sql)
        rewritten = re.sub(r"\bSTRING\b", "VARCHAR", rewritten, flags=re.IGNORECASE)
        rewritten = re.sub(
            r"CAST\(([^)]+?)\s+AS\s+FLOAT\)",
            r"TRY_CAST(\1 AS DOUBLE)",
            rewritten,
            flags=re.IGNORECASE,
        )

        def replace_date_cast(match: re.Match[str]) -> str:
            expr = match.group(1).strip()
            return (
                "COALESCE("
                f"TRY_CAST({expr} AS DATE), "
                f"TRY_STRPTIME({expr}, '%d/%m/%Y')::DATE, "
                f"TRY_STRPTIME({expr}, '%d/%m/%Y %H:%M:%S')::DATE, "
                f"TRY_STRPTIME({expr}, '%Y-%m-%d %H:%M:%S')::DATE"
                ")"
            )

        rewritten = re.sub(
            r"CAST\(([^)]+?)\s+AS\s+DATE\)",
            replace_date_cast,
            rewritten,
            flags=re.IGNORECASE,
        )
        return rewritten

    @classmethod
    def _safe_identifier(cls, alias: str) -> str:
        if not cls.IDENTIFIER_PATTERN.match(alias):
            raise ValueError(f"Invalid SQL identifier: {alias}")
        return alias

    def register_parquet_view(self, alias: str, parquet_path: str | Path) -> None:
        name = self._safe_identifier(alias)
        path = Path(parquet_path)
        if not path.exists():
            raise FileNotFoundError(f"Parquet not found: {path}")
        literal = str(path).replace("'", "''")
        self.conn.execute(
            f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_parquet('{literal}')"
        )

    def register_parquet_views(self, aliases: Iterable[str], parquet_path: str | Path) -> None:
        for alias in aliases:
            self.register_parquet_view(alias, parquet_path)

    def execute_to_arrow(self, sql: str) -> pa.Table:
        return self.conn.execute(sql).fetch_arrow_table()

    def execute_to_polars(self, sql: str) -> pl.DataFrame:
        # For moderate datasets this is convenient; for very large outputs, prefer
        # `execute_stream_arrow_batches` to process data incrementally.
        arrow_table = self.execute_to_arrow(sql)
        return pl.from_arrow(arrow_table)

    def execute_stream_arrow_batches(
        self,
        sql: str,
        *,
        batch_size: int = 100_000,
    ) -> Iterator[pa.RecordBatch]:
        # Streaming option: yields Arrow RecordBatch chunks so callers can write or
        # transform results without loading the full query output in memory.
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")

        reader = self.conn.execute(sql).fetch_record_batch(batch_size)
        while True:
            try:
                batch = reader.read_next_batch()
            except StopIteration:
                break
            if batch.num_rows == 0:
                continue
            yield batch

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "DuckDBManager":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
