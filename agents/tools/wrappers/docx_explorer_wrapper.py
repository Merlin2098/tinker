#!/usr/bin/env python3
"""
Canonical execution wrapper for the `docx_explorer` skill.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET
import zipfile

try:
    from agents.tools.wrappers._explorer_common import file_stats, parse_int, resolve_repo_path
except ImportError:
    from wrappers._explorer_common import file_stats, parse_int, resolve_repo_path


W_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
CP_NS = {
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
}


def _core_props(zf: zipfile.ZipFile) -> dict[str, str]:
    if "docProps/core.xml" not in zf.namelist():
        return {}
    root = ET.fromstring(zf.read("docProps/core.xml"))
    out: dict[str, str] = {}
    for tag in ["title", "subject", "creator"]:
        node = root.find(f"dc:{tag}", CP_NS)
        if node is not None and node.text:
            out[tag] = node.text.strip()
    for tag in ["created", "modified"]:
        node = root.find(f"dcterms:{tag}", CP_NS)
        if node is not None and node.text:
            out[tag] = node.text.strip()
    return out


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    resolved_str, resolved = resolve_repo_path(
        args.get("path"),
        field_name="path",
        allowed_suffixes={".docx"},
    )
    preview_paragraphs = parse_int(
        args.get("preview_paragraphs"),
        field="preview_paragraphs",
        default=10,
        minimum=0,
        maximum=200,
    )

    with zipfile.ZipFile(resolved) as zf:
        members = zf.namelist()
        if "word/document.xml" not in members:
            raise ValueError("Invalid DOCX file: missing word/document.xml.")
        root = ET.fromstring(zf.read("word/document.xml"))
        paragraphs = []
        for paragraph in root.findall(".//w:p", W_NS):
            texts = [node.text for node in paragraph.findall(".//w:t", W_NS) if node.text]
            joined = "".join(texts).strip()
            if joined:
                paragraphs.append(joined)

        table_count = len(root.findall(".//w:tbl", W_NS))
        header_parts = len([name for name in members if PurePosixPath(name).name.startswith("header")])
        footer_parts = len([name for name in members if PurePosixPath(name).name.startswith("footer")])

        metadata = _core_props(zf)

    return {
        "status": "ok",
        "skill": "docx_explorer",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "paragraph_count": len(paragraphs),
        "table_count": table_count,
        "header_part_count": header_parts,
        "footer_part_count": footer_parts,
        "paragraphs_preview": paragraphs[:preview_paragraphs],
        "metadata": metadata,
        **file_stats(resolved),
    }


