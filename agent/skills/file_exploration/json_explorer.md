# Skill: json_explorer (Thin Interface)

## Purpose
Inspect JSON structure through the canonical execution wrapper.

Business logic lives in:
- `agent_tools/wrappers/json_explorer_wrapper.py`
- `agent_tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.json` file path under repository root.
- `encoding` (string, optional, default `utf-8-sig`)
- `schema_depth` (integer, optional, default `2`)
- `max_items` (integer, optional, default `20`)

## Execution

```bash
.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill json_explorer --args-json "{\"path\":\"agent/agent_outputs/context.json\"}"
```

## Output Contract
- `status`, `skill`, `path`, `resolved_path`
- `data_type`, `top_level_key_count`, `top_level_keys`, `item_count`
- `schema_preview`, `line_count`, `size_bytes`
