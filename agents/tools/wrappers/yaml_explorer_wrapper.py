#!/usr/bin/env python3
"""
Canonical execution wrapper for the `yaml_explorer` skill.
"""

from __future__ import annotations

from typing import Any

import yaml

try:
    from agents.tools.wrappers._explorer_common import (
        file_stats,
        parse_encoding,
        parse_int,
        resolve_repo_path,
        to_jsonable,
    )
except ImportError:
    from wrappers._explorer_common import file_stats, parse_encoding, parse_int, resolve_repo_path, to_jsonable


def _type_name(value: Any) -> str:
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    return type(value).__name__


def _schema_preview(value: Any, depth: int, max_depth: int, max_items: int) -> Any:
    if depth >= max_depth:
        return {"type": _type_name(value)}
    if isinstance(value, dict):
        keys = sorted(str(k) for k in value.keys())[:max_items]
        return {
            "type": "object",
            "key_count": len(value),
            "keys": keys,
        }
    if isinstance(value, list):
        sample = value[: max_items]
        return {
            "type": "array",
            "item_count": len(value),
            "sample_item_types": sorted({_type_name(item) for item in sample}),
        }
    return {"type": _type_name(value), "value_preview": to_jsonable(value)}


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    resolved_str, resolved = resolve_repo_path(
        args.get("path"),
        field_name="path",
        allowed_suffixes={".yaml", ".yml"},
    )
    encoding = parse_encoding(args.get("encoding"), default="utf-8-sig")
    schema_depth = parse_int(args.get("schema_depth"), field="schema_depth", default=2, minimum=1, maximum=6)
    max_items = parse_int(args.get("max_items"), field="max_items", default=20, minimum=1, maximum=200)

    raw = resolved.read_text(encoding=encoding)
    data = yaml.safe_load(raw)

    top_level_keys = sorted(str(k) for k in data.keys()) if isinstance(data, dict) else None
    item_count = len(data) if isinstance(data, list) else None

    return {
        "status": "ok",
        "skill": "yaml_explorer",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "encoding": encoding,
        "line_count": raw.count("\n") + 1,
        "data_type": _type_name(data),
        "top_level_key_count": len(top_level_keys) if top_level_keys is not None else None,
        "top_level_keys": top_level_keys[:max_items] if top_level_keys else None,
        "item_count": item_count,
        "schema_preview": _schema_preview(data, depth=0, max_depth=schema_depth, max_items=max_items),
        **file_stats(resolved),
    }


