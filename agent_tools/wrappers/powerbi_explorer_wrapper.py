#!/usr/bin/env python3
"""
Canonical execution wrapper for the `powerbi_explorer` skill.
"""

from __future__ import annotations

import json
from typing import Any
import zipfile

try:
    from agent_tools.wrappers._explorer_common import file_stats, parse_int, resolve_repo_path
except ImportError:
    from wrappers._explorer_common import file_stats, parse_int, resolve_repo_path


def _safe_json_preview(raw: bytes, max_chars: int) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        return {"available": False, "reason": "decode-failed"}
    preview = text[:max_chars]
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            top_keys = sorted(parsed.keys())[:50]
            return {"available": True, "json_detected": True, "top_level_keys": top_keys, "text_preview": preview}
        if isinstance(parsed, list):
            return {
                "available": True,
                "json_detected": True,
                "item_count": len(parsed),
                "text_preview": preview,
            }
    except Exception:
        pass
    return {"available": True, "json_detected": False, "text_preview": preview}


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    resolved_str, resolved = resolve_repo_path(
        args.get("path"),
        field_name="path",
        allowed_suffixes={".pbix", ".pbit"},
    )
    preview_chars = parse_int(args.get("preview_chars"), field="preview_chars", default=500, minimum=0, maximum=10000)

    with zipfile.ZipFile(resolved) as zf:
        members = sorted(zf.namelist())
        has_data_model = any(name.lower().startswith("datamodel") for name in members)
        layout_candidates = [name for name in members if name.lower().endswith("layout")]
        diagram_candidates = [name for name in members if "diagram" in name.lower()]

        layout_preview = None
        if layout_candidates:
            raw = zf.read(layout_candidates[0])
            layout_preview = _safe_json_preview(raw, max_chars=preview_chars)

    return {
        "status": "ok",
        "skill": "powerbi_explorer",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "member_count": len(members),
        "members_preview": members[:200],
        "has_data_model": has_data_model,
        "layout_files": layout_candidates,
        "diagram_files": diagram_candidates,
        "layout_preview": layout_preview,
        **file_stats(resolved),
    }

