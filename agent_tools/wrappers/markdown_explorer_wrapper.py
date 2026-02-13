#!/usr/bin/env python3
"""
Canonical execution wrapper for the `markdown_explorer` skill.
"""

from __future__ import annotations

import re
from typing import Any

try:
    from agent_tools.wrappers._explorer_common import file_stats, parse_encoding, parse_int, resolve_repo_path
except ImportError:
    from wrappers._explorer_common import file_stats, parse_encoding, parse_int, resolve_repo_path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _count_code_fences(lines: list[str]) -> int:
    count = 0
    in_fence = False
    for line in lines:
        if line.strip().startswith("```"):
            if in_fence:
                count += 1
            in_fence = not in_fence
    return count


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    resolved_str, resolved = resolve_repo_path(
        args.get("path"),
        field_name="path",
        allowed_suffixes={".md", ".markdown"},
    )
    encoding = parse_encoding(args.get("encoding"), default="utf-8-sig")
    preview_chars = parse_int(args.get("preview_chars"), field="preview_chars", default=400, minimum=0, maximum=8000)

    raw = resolved.read_text(encoding=encoding)
    lines = raw.splitlines()

    headings: list[dict[str, Any]] = []
    for line in lines:
        match = HEADING_RE.match(line.strip())
        if match:
            headings.append({"level": len(match.group(1)), "text": match.group(2).strip()})

    links = LINK_RE.findall(raw)

    return {
        "status": "ok",
        "skill": "markdown_explorer",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "encoding": encoding,
        "line_count": len(lines),
        "heading_count": len(headings),
        "headings_preview": headings[:50],
        "link_count": len(links),
        "links_preview": links[:50],
        "code_block_count": _count_code_fences(lines),
        "text_preview": raw[:preview_chars],
        "truncated": len(raw) > preview_chars,
        **file_stats(resolved),
    }

