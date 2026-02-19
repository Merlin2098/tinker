# Skill: load_yaml_files (Thin Interface)

## Purpose
Load and parse YAML files through the canonical execution wrapper.

This skill is intentionally thin. Business logic lives in:
- `agents/tools/wrappers/load_yaml_files_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.yaml` or `.yml` file path under repository root.
- `encoding` (string, optional, default `utf-8-sig`)

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill load_yaml_files --args-json "{\"path\":\"agents/logic/user_task.yaml\"}"
```

Preferred with args file:

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill load_yaml_files --args-file agents/logic/agent_outputs/plans/load_yaml_files.args.json
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
- `path` must point to an existing `.yaml`/`.yml` file.
- `encoding` must be a non-empty string when provided.

## Failure Behavior
- Invalid arguments -> non-zero exit and JSON error payload from runner.
- Parse/read errors -> non-zero exit and JSON error payload from runner.


