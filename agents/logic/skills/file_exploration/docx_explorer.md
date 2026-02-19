# Skill: docx_explorer (Thin Interface)

## Purpose
Inspect DOCX structure, metadata, and paragraph preview through the canonical execution wrapper.

Business logic lives in:
- `agents/tools/wrappers/docx_explorer_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.docx` file path under repository root.
- `preview_paragraphs` (integer, optional, default `10`)

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill docx_explorer --args-json "{\"path\":\"docs/spec.docx\"}"
```

## Output Contract
- `status`, `skill`, `path`, `resolved_path`
- `paragraph_count`, `table_count`
- `header_part_count`, `footer_part_count`
- `paragraphs_preview`, `metadata`, `size_bytes`

