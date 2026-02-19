# Skill: html_explorer (Thin Interface)

## Purpose
Inspect HTML metadata, links, and text preview through the canonical execution wrapper.

Business logic lives in:
- `agents/tools/wrappers/html_explorer_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.html`/`.htm` file path under repository root.
- `encoding` (string, optional, default `utf-8-sig`)
- `preview_chars` (integer, optional, default `400`)

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill html_explorer --args-json "{\"path\":\"docs/index.html\"}"
```

## Output Contract
- `status`, `skill`, `path`, `resolved_path`
- `title`, `tag_count`, `top_tags`
- `table_count`, `link_count`, `links_preview`
- `text_preview`, `truncated`, `size_bytes`

