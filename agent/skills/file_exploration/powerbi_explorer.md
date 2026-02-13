# Skill: powerbi_explorer (Thin Interface)

## Purpose
Inspect `.pbix`/`.pbit` package structure through the canonical execution wrapper.

Business logic lives in:
- `agent_tools/wrappers/powerbi_explorer_wrapper.py`
- `agent_tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.pbix` or `.pbit` path under repository root.
- `preview_chars` (integer, optional, default `500`)

## Execution

```bash
.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill powerbi_explorer --args-json "{\"path\":\"reports/model.pbix\"}"
```

## Output Contract
- `status`, `skill`, `path`, `resolved_path`
- `member_count`, `members_preview`
- `has_data_model`, `layout_files`, `diagram_files`
- `layout_preview`, `size_bytes`
