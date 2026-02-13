# Skill: load_json_files (Thin Interface)

## Purpose
Load and parse JSON files through the canonical execution wrapper.

This skill is intentionally thin. Business logic lives in:
- `agent_tools/wrappers/load_json_files_wrapper.py`
- `agent_tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.json` file path under repository root.
- `encoding` (string, optional, default `utf-8-sig`)

## Execution

```bash
.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill load_json_files --args-json "{\"path\":\"agent/agent_outputs/context.json\"}"
```

Preferred with args file:

```bash
.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill load_json_files --args-file agent/agent_outputs/plans/load_json_files.args.json
```

## Output Contract
Wrapper returns JSON with:
- `status`
- `skill`
- `path`
- `resolved_path`
- `encoding`
- `line_count`
- `size_bytes`
- `data_type`
- `top_level_keys` and `top_level_key_count` for object payloads
- `item_count` for array payloads

## Validation Rules
- `path` must resolve inside repository root.
- `path` must point to an existing `.json` file.
- `encoding` must be a non-empty string when provided.

## Failure Behavior
- Invalid arguments -> non-zero exit and JSON error payload from runner.
- Parse/read errors -> non-zero exit and JSON error payload from runner.
