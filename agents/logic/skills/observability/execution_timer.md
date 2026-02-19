# Skill: execution_timer (Thin Interface)

## Purpose
Format execution duration for general tasks or SQL-style timings through the canonical wrapper.

Business logic lives in:
- `agents/tools/wrappers/execution_timer_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `task_type` (string, optional, default `general`): `general|sql_query`
- `elapsed_seconds` (number, optional): Direct elapsed duration.
- `started_at` (number, optional): Start timestamp/counter value.
- `ended_at` (number, optional): End timestamp/counter value (defaults to current `perf_counter` when omitted and `started_at` is provided).

Use either:
- `elapsed_seconds`, or
- `started_at` with optional `ended_at`.

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill execution_timer --args-json "{\"task_type\":\"sql_query\",\"elapsed_seconds\":0.23456}"
```

## Output Contract
- `status`, `skill`, `task_type`, `source`
- `execution_time`
- `execution_time_seconds`
- `execution_time_milliseconds`

