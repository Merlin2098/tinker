#!/usr/bin/env python3
"""
Canonical execution wrapper for the `csv_explorer` skill.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

try:
    from agents.tools.wrappers._explorer_common import (
        file_stats,
        parse_encoding,
        parse_int,
        resolve_repo_path,
    )
except ImportError:
    from wrappers._explorer_common import file_stats, parse_encoding, parse_int, resolve_repo_path


def _normalize_headers(header_row: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    normalized: list[str] = []
    for idx, raw in enumerate(header_row):
        base = raw.strip() if isinstance(raw, str) else ""
        if not base:
            base = f"column_{idx + 1}"
        count = seen.get(base, 0)
        seen[base] = count + 1
        normalized.append(base if count == 0 else f"{base}_{count + 1}")
    return normalized


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    resolved_str, resolved = resolve_repo_path(
        args.get("path"),
        field_name="path",
        allowed_suffixes={".csv"},
    )
    encoding = parse_encoding(args.get("encoding"), default="utf-8-sig")
    preview_rows = parse_int(args.get("preview_rows"), field="preview_rows", default=5, minimum=0, maximum=200)

    with resolved.open("r", encoding=encoding, newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
            delimiter = dialect.delimiter
            quotechar = dialect.quotechar
        except csv.Error:
            delimiter = ","
            quotechar = '"'

        reader = csv.reader(handle, delimiter=delimiter, quotechar=quotechar)
        all_rows = list(reader)

    if not all_rows:
        return {
            "status": "ok",
            "skill": "csv_explorer",
            "path": args.get("path"),
            "resolved_path": resolved_str,
            "encoding": encoding,
            "delimiter": delimiter,
            "quotechar": quotechar,
            "row_count": 0,
            "column_count": 0,
            "columns": [],
            "rows_preview": [],
            **file_stats(resolved),
        }

    headers = _normalize_headers([str(v) for v in all_rows[0]])
    data_rows = all_rows[1:]

    preview: list[dict[str, Any]] = []
    for row in data_rows[:preview_rows]:
        padded = row + [None] * max(0, len(headers) - len(row))
        preview.append({headers[idx]: padded[idx] for idx in range(len(headers))})

    return {
        "status": "ok",
        "skill": "csv_explorer",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "encoding": encoding,
        "delimiter": delimiter,
        "quotechar": quotechar,
        "row_count": len(data_rows),
        "column_count": len(headers),
        "columns": headers,
        "rows_preview": preview,
        **file_stats(resolved),
    }


