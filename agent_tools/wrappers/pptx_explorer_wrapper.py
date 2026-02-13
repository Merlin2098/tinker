#!/usr/bin/env python3
"""
Canonical execution wrapper for the `pptx_explorer` skill.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET
import zipfile

try:
    from agent_tools.wrappers._explorer_common import file_stats, parse_int, resolve_repo_path
except ImportError:
    from wrappers._explorer_common import file_stats, parse_int, resolve_repo_path


A_NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
CP_NS = {
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
        allowed_suffixes={".pptx"},
    )
    preview_slides = parse_int(args.get("preview_slides"), field="preview_slides", default=5, minimum=0, maximum=50)

    with zipfile.ZipFile(resolved) as zf:
        members = zf.namelist()
        slide_xmls = sorted(
            [name for name in members if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
        )
        note_xmls = sorted(
            [name for name in members if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml")]
        )

        slide_preview: list[dict[str, Any]] = []
        for idx, name in enumerate(slide_xmls[:preview_slides], start=1):
            root = ET.fromstring(zf.read(name))
            texts = [node.text.strip() for node in root.findall(".//a:t", A_NS) if node.text and node.text.strip()]
            slide_preview.append(
                {
                    "slide_number": idx,
                    "text_fragment_count": len(texts),
                    "text_preview": texts[:20],
                }
            )

        media_count = len([name for name in members if name.startswith("ppt/media/")])
        metadata = _core_props(zf)

    return {
        "status": "ok",
        "skill": "pptx_explorer",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "slide_count": len(slide_xmls),
        "notes_slide_count": len(note_xmls),
        "media_asset_count": media_count,
        "slides_preview": slide_preview,
        "metadata": metadata,
        **file_stats(resolved),
    }

