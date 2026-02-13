# Skill: markdown_explorer (Thin Interface)

## Purpose
Inspect Markdown structure through the canonical execution wrapper.

Business logic lives in:
- `agent_tools/wrappers/markdown_explorer_wrapper.py`
- `agent_tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.md`/`.markdown` file path under repository root.
- `encoding` (string, optional, default `utf-8-sig`)
- `preview_chars` (integer, optional, default `400`)

## Execution

```bash
.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill markdown_explorer --args-json "{\"path\":\"README.md\"}"
```

## Output Contract
- `status`, `skill`, `path`, `resolved_path`
- `line_count`, `heading_count`, `headings_preview`
- `link_count`, `links_preview`, `code_block_count`
- `text_preview`, `truncated`, `size_bytes`

