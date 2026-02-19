# Skill: file_explorer (Thin Facade Interface)

## Purpose
Detect file type and delegate exploration to canonical format-specific wrappers.

This skill is intentionally thin. Business logic lives in:
- `agents/tools/wrappers/file_explorer_wrapper.py`
- `agents/tools/wrappers/*_explorer_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `path` (string, required): file path under repository root.
- `force_skill` (string, optional): override extension routing.
- `delegate_args` (object, optional): forwarded to delegated wrapper.
- `encoding` (string, optional): used by generic text fallback.
- `preview_chars` (integer, optional): used by generic fallback.

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill file_explorer --args-json "{\"path\":\"agents/logic/user_task.yaml\"}"
```

## Output Contract
Wrapper returns JSON with:
- `status`
- `skill`
- `path`
- `resolved_path`
- `detected_extension`
- `delegated_skill`
- `delegate_result`
- `generic_result` (when no delegate is selected)

## Validation Rules
- `path` must resolve inside repository root.
- `delegate_args` must be an object when provided.
- `force_skill` must match a known explorer wrapper when provided.

## Failure Behavior
- Invalid arguments -> non-zero exit and JSON error payload from runner.
- Delegated wrapper failures propagate as non-zero exit and JSON error payload.

