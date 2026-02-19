#!/usr/bin/env python3
"""
Canonical execution wrapper for the `xml_explorer` skill.
"""

from __future__ import annotations

from collections import Counter
from typing import Any
from xml.etree import ElementTree as ET

try:
    from agents.tools.wrappers._explorer_common import file_stats, parse_encoding, parse_int, resolve_repo_path
except ImportError:
    from wrappers._explorer_common import file_stats, parse_encoding, parse_int, resolve_repo_path


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    resolved_str, resolved = resolve_repo_path(
        args.get("path"),
        field_name="path",
        allowed_suffixes={".xml"},
    )
    encoding = parse_encoding(args.get("encoding"), default="utf-8-sig")
    preview_chars = parse_int(args.get("preview_chars"), field="preview_chars", default=400, minimum=0, maximum=8000)

    raw = resolved.read_text(encoding=encoding)
    root = ET.fromstring(raw)

    element_count = 0
    attribute_count = 0
    namespaces: set[str] = set()
    child_tag_counter: Counter[str] = Counter()
    for idx, elem in enumerate(root.iter()):
        element_count += 1
        attribute_count += len(elem.attrib)
        if "}" in elem.tag:
            namespaces.add(elem.tag.split("}")[0].lstrip("{"))
        if idx > 0:
            child_tag_counter[_local_name(elem.tag)] += 1

    text_content = " ".join(part.strip() for part in root.itertext() if part and part.strip())

    return {
        "status": "ok",
        "skill": "xml_explorer",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "encoding": encoding,
        "root_tag": _local_name(root.tag),
        "namespace_count": len(namespaces),
        "namespaces": sorted(namespaces),
        "element_count": element_count,
        "attribute_count": attribute_count,
        "top_child_tags": child_tag_counter.most_common(20),
        "text_preview": text_content[:preview_chars],
        "truncated": len(text_content) > preview_chars,
        **file_stats(resolved),
    }


