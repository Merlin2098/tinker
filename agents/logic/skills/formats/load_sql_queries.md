# Skill: load_sql_queries (Thin Interface)

## Purpose
Load SQL query files through the canonical execution wrapper.

This skill is intentionally thin. Business logic lives in:
- `agents/tools/wrappers/load_sql_queries_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.sql` file path under repository root.
- `encoding` (string, optional, default `utf-8-sig`)
- `strip_comments` (boolean, optional, default `false`)
- `preview_chars` (integer, optional, default `400`, range `1..4000`)

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill load_sql_queries --args-json "{\"path\":\"queries/example.sql\"}"
```

Preferred with args file:

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill load_sql_queries --args-file agents/logic/agent_outputs/plans/load_sql_queries.args.json
```

## Output Contract
Wrapper returns JSON with:
- `status`
- `skill`
- `path`
- `resolved_path`
- `encoding`
- `strip_comments`
- `line_count`
- `size_bytes`
- `statement_count`
- `query_text`
- `query_preview`
- `preview_chars`
- `truncated`

## Validation Rules
- `path` must resolve inside repository root.
- `path` must point to an existing `.sql` file.
- `preview_chars` must be in `1..4000`.
- SQL content must be non-empty after optional preprocessing.

## Failure Behavior
- Invalid arguments -> non-zero exit and JSON error payload from runner.
- Read/validation errors -> non-zero exit and JSON error payload from runner.


