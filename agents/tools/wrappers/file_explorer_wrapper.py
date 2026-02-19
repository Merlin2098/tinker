#!/usr/bin/env python3
"""
Canonical execution wrapper for the `file_explorer` facade skill.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

try:
    from agents.tools.wrappers._explorer_common import file_stats, parse_encoding, parse_int, resolve_repo_path
    from agents.tools.wrappers.csv_explorer_wrapper import run as run_csv_explorer
    from agents.tools.wrappers.db_explorer_wrapper import run as run_db_explorer
    from agents.tools.wrappers.docx_explorer_wrapper import run as run_docx_explorer
    from agents.tools.wrappers.excel_explorer_wrapper import run as run_excel_explorer
    from agents.tools.wrappers.html_explorer_wrapper import run as run_html_explorer
    from agents.tools.wrappers.json_explorer_wrapper import run as run_json_explorer
    from agents.tools.wrappers.markdown_explorer_wrapper import run as run_markdown_explorer
    from agents.tools.wrappers.parquet_explorer_wrapper import run as run_parquet_explorer
    from agents.tools.wrappers.pdf_explorer_wrapper import run as run_pdf_explorer
    from agents.tools.wrappers.powerbi_explorer_wrapper import run as run_powerbi_explorer
    from agents.tools.wrappers.pptx_explorer_wrapper import run as run_pptx_explorer
    from agents.tools.wrappers.xml_explorer_wrapper import run as run_xml_explorer
    from agents.tools.wrappers.yaml_explorer_wrapper import run as run_yaml_explorer
except ImportError:
    from wrappers._explorer_common import file_stats, parse_encoding, parse_int, resolve_repo_path
    from wrappers.csv_explorer_wrapper import run as run_csv_explorer
    from wrappers.db_explorer_wrapper import run as run_db_explorer
    from wrappers.docx_explorer_wrapper import run as run_docx_explorer
    from wrappers.excel_explorer_wrapper import run as run_excel_explorer
    from wrappers.html_explorer_wrapper import run as run_html_explorer
    from wrappers.json_explorer_wrapper import run as run_json_explorer
    from wrappers.markdown_explorer_wrapper import run as run_markdown_explorer
    from wrappers.parquet_explorer_wrapper import run as run_parquet_explorer
    from wrappers.pdf_explorer_wrapper import run as run_pdf_explorer
    from wrappers.powerbi_explorer_wrapper import run as run_powerbi_explorer
    from wrappers.pptx_explorer_wrapper import run as run_pptx_explorer
    from wrappers.xml_explorer_wrapper import run as run_xml_explorer
    from wrappers.yaml_explorer_wrapper import run as run_yaml_explorer


WrapperFunc = Callable[[dict[str, Any]], dict[str, Any]]

ROUTING_BY_SUFFIX: dict[str, str] = {
    ".csv": "csv_explorer",
    ".db": "db_explorer",
    ".sqlite": "db_explorer",
    ".sqlite3": "db_explorer",
    ".duckdb": "db_explorer",
    ".docx": "docx_explorer",
    ".xlsx": "excel_explorer",
    ".xlsm": "excel_explorer",
    ".xltx": "excel_explorer",
    ".xltm": "excel_explorer",
    ".htm": "html_explorer",
    ".html": "html_explorer",
    ".json": "json_explorer",
    ".md": "markdown_explorer",
    ".markdown": "markdown_explorer",
    ".parquet": "parquet_explorer",
    ".pdf": "pdf_explorer",
    ".pbix": "powerbi_explorer",
    ".pbit": "powerbi_explorer",
    ".pptx": "pptx_explorer",
    ".xml": "xml_explorer",
    ".yaml": "yaml_explorer",
    ".yml": "yaml_explorer",
}

WRAPPER_BY_SKILL: dict[str, WrapperFunc] = {
    "csv_explorer": run_csv_explorer,
    "db_explorer": run_db_explorer,
    "docx_explorer": run_docx_explorer,
    "excel_explorer": run_excel_explorer,
    "html_explorer": run_html_explorer,
    "json_explorer": run_json_explorer,
    "markdown_explorer": run_markdown_explorer,
    "parquet_explorer": run_parquet_explorer,
    "pdf_explorer": run_pdf_explorer,
    "powerbi_explorer": run_powerbi_explorer,
    "pptx_explorer": run_pptx_explorer,
    "xml_explorer": run_xml_explorer,
    "yaml_explorer": run_yaml_explorer,
}


def _read_generic_text(path: Path, encoding: str, preview_chars: int) -> dict[str, Any]:
    raw_bytes = path.read_bytes()
    if b"\x00" in raw_bytes:
        return {
            "generic_type": "binary",
            "bytes_preview_hex": raw_bytes[: min(preview_chars, 1024)].hex(),
            "truncated": len(raw_bytes) > min(preview_chars, 1024),
        }
    raw = raw_bytes.decode(encoding)
    return {
        "generic_type": "text",
        "encoding": encoding,
        "line_count": raw.count("\n") + 1,
        "text_preview": raw[:preview_chars],
        "truncated": len(raw) > preview_chars,
    }


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    resolved_str, resolved = resolve_repo_path(args.get("path"), field_name="path")
    force_skill = args.get("force_skill")
    if force_skill is not None and (not isinstance(force_skill, str) or not force_skill.strip()):
        raise ValueError("force_skill must be a non-empty string when provided.")
    force_skill = force_skill.strip() if isinstance(force_skill, str) else None

    suffix = resolved.suffix.lower()
    delegated_skill = force_skill or ROUTING_BY_SUFFIX.get(suffix)
    delegate_args = args.get("delegate_args")
    if delegate_args is None:
        delegate_args = {}
    if not isinstance(delegate_args, dict):
        raise ValueError("delegate_args must be a JSON object when provided.")
    delegate_args = dict(delegate_args)
    delegate_args.setdefault("path", args.get("path"))

    if delegated_skill in WRAPPER_BY_SKILL:
        result = WRAPPER_BY_SKILL[delegated_skill](delegate_args)
        return {
            "status": "ok",
            "skill": "file_explorer",
            "path": args.get("path"),
            "resolved_path": resolved_str,
            "detected_extension": suffix,
            "delegated_skill": delegated_skill,
            "delegate_result": result,
            **file_stats(resolved),
        }

    encoding = parse_encoding(args.get("encoding"), default="utf-8-sig")
    preview_chars = parse_int(args.get("preview_chars"), field="preview_chars", default=400, minimum=0, maximum=8000)
    try:
        generic = _read_generic_text(resolved, encoding=encoding, preview_chars=preview_chars)
    except UnicodeDecodeError:
        raw = resolved.read_bytes()
        generic = {
            "generic_type": "binary",
            "bytes_preview_hex": raw[: min(preview_chars, 1024)].hex(),
            "truncated": len(raw) > min(preview_chars, 1024),
        }

    return {
        "status": "ok",
        "skill": "file_explorer",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "detected_extension": suffix,
        "delegated_skill": None,
        "delegate_result": None,
        "generic_result": generic,
        **file_stats(resolved),
    }

