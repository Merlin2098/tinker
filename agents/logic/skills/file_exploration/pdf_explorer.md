# Skill: pdf_explorer (Thin Interface)

## Purpose
Inspect PDF metadata and page text preview through the canonical execution wrapper.

Business logic lives in:
- `agents/tools/wrappers/pdf_explorer_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.pdf` file path under repository root.
- `preview_pages` (integer, optional, default `2`)
- `preview_chars` (integer, optional, default `400`)

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill pdf_explorer --args-json "{\"path\":\"docs/sample.pdf\"}"
```

## Output Contract
- `status`, `skill`, `path`, `resolved_path`
- `parser_available`, `warning` (when parser unavailable)
- `page_count`, `metadata`, `pages_preview`
- `size_bytes`

