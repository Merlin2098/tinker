#!/usr/bin/env python3
"""
Canonical execution wrapper for the `pdf_explorer` skill.
"""

from __future__ import annotations

from typing import Any

try:
    from agent_tools.wrappers._explorer_common import file_stats, parse_int, resolve_repo_path
except ImportError:
    from wrappers._explorer_common import file_stats, parse_int, resolve_repo_path


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    resolved_str, resolved = resolve_repo_path(
        args.get("path"),
        field_name="path",
        allowed_suffixes={".pdf"},
    )
    preview_pages = parse_int(args.get("preview_pages"), field="preview_pages", default=2, minimum=0, maximum=20)
    preview_chars = parse_int(args.get("preview_chars"), field="preview_chars", default=400, minimum=0, maximum=8000)

    try:
        from pypdf import PdfReader
    except ImportError:
        return {
            "status": "ok",
            "skill": "pdf_explorer",
            "path": args.get("path"),
            "resolved_path": resolved_str,
            "parser_available": False,
            "warning": "pypdf not installed; only file metadata is available.",
            **file_stats(resolved),
        }

    reader = PdfReader(str(resolved))
    page_count = len(reader.pages)
    metadata = {}
    if reader.metadata:
        metadata = {str(k): str(v) for k, v in reader.metadata.items()}

    page_texts: list[dict[str, Any]] = []
    for idx, page in enumerate(reader.pages[:preview_pages], start=1):
        text = page.extract_text() or ""
        page_texts.append(
            {
                "page": idx,
                "text_preview": text[:preview_chars],
                "truncated": len(text) > preview_chars,
            }
        )

    return {
        "status": "ok",
        "skill": "pdf_explorer",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "parser_available": True,
        "page_count": page_count,
        "metadata": metadata,
        "preview_pages": preview_pages,
        "pages_preview": page_texts,
        **file_stats(resolved),
    }

