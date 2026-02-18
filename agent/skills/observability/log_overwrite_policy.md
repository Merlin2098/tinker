# Skill: log_overwrite_policy (Thin Interface)

## Purpose
Create or overwrite a log file at each execution with standard header lines.

Business logic lives in:
- `agent_tools/wrappers/log_overwrite_policy_wrapper.py`
- `agent_tools/run_wrapper.py`

## Inputs
- `log_file_path` (string, optional, default `logs/execution.log`)
- `encoding` (string, optional, default `utf-8`)
- `create_parent` (bool, optional, default `true`)
- `header_lines` (list[string], optional): Custom header lines.
- `dry_run` (bool, optional, default `false`)

## Execution

```bash
.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill log_overwrite_policy --args-json "{\"log_file_path\":\"logs/execution.log\"}"
```

## Output Contract
- `status`, `skill`, `dry_run`
- `resolved_path`, `encoding`, `line_count`
- `size_bytes` (when executed)
