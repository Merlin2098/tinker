#!/usr/bin/env python3
"""
Canonical execution wrapper for the `html_explorer` skill.
"""

from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
from typing import Any

try:
    from agents.tools.wrappers._explorer_common import file_stats, parse_encoding, parse_int, resolve_repo_path
except ImportError:
    from wrappers._explorer_common import file_stats, parse_encoding, parse_int, resolve_repo_path


class _HTMLSummaryParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self._in_title = False
        self._in_script = False
        self._in_style = False
        self.tag_counts: Counter[str] = Counter()
        self.table_count = 0
        self.links: list[str] = []
        self.text_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tag_counts[tag] += 1
        if tag == "title":
            self._in_title = True
        elif tag == "script":
            self._in_script = True
        elif tag == "style":
            self._in_style = True
        elif tag == "table":
            self.table_count += 1

        attrs_map = dict(attrs)
        href = attrs_map.get("href")
        if href:
            self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            self._in_script = False
        elif tag == "style":
            self._in_style = False

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._in_title and self.title is None:
            self.title = text
            return
        if not self._in_script and not self._in_style:
            self.text_chunks.append(text)


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    resolved_str, resolved = resolve_repo_path(
        args.get("path"),
        field_name="path",
        allowed_suffixes={".html", ".htm"},
    )
    encoding = parse_encoding(args.get("encoding"), default="utf-8-sig")
    preview_chars = parse_int(args.get("preview_chars"), field="preview_chars", default=400, minimum=0, maximum=8000)

    raw = resolved.read_text(encoding=encoding)
    parser = _HTMLSummaryParser()
    parser.feed(raw)
    parser.close()

    text_content = " ".join(parser.text_chunks)
    unique_links = list(dict.fromkeys(parser.links))

    return {
        "status": "ok",
        "skill": "html_explorer",
        "path": args.get("path"),
        "resolved_path": resolved_str,
        "encoding": encoding,
        "title": parser.title,
        "tag_count": sum(parser.tag_counts.values()),
        "top_tags": parser.tag_counts.most_common(20),
        "table_count": parser.table_count,
        "link_count": len(unique_links),
        "links_preview": unique_links[:50],
        "text_preview": text_content[:preview_chars],
        "truncated": len(text_content) > preview_chars,
        **file_stats(resolved),
    }


