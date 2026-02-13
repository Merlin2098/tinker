# Skill: connect_duckdb (Thin Interface)

## Purpose
Open and validate a DuckDB connection through the canonical execution wrapper.

This skill is intentionally thin. Business logic lives in:
- `agent_tools/wrappers/connect_duckdb_wrapper.py`
- `agent_tools/run_wrapper.py`

## Inputs
- `database_path` (string, required): `:memory:` or path under repository root.
- `read_only` (boolean, optional, default `false`)
- `config` (object, optional): DuckDB config key/value map.

## Execution
Use the canonical wrapper runner:

```bash
.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill connect_duckdb --args-json "{\"database_path\":\"data/example.duckdb\",\"read_only\":false}"
```

Alternative with args file:

```bash
.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill connect_duckdb --args-file agent/agent_outputs/plans/connect_duckdb.args.json
```

## Output Contract
Wrapper returns JSON with:
- `status` (`ok` or error path from runner)
- `skill`
- `database_path`
- `resolved_database_path` (`null` when `:memory:`)
- `read_only`
- `created_database_file`
- `config_applied_keys`
- `probe_query_ok`

## Validation Rules
- `database_path` must not be empty.
- File-based paths must resolve inside repository root.
- In `read_only=true`, database file must already exist.
- `config` must be a JSON object with primitive values only.

## Failure Behavior
- Invalid arguments -> non-zero exit and JSON error payload from runner.
- DuckDB connection failure -> non-zero exit and JSON error payload from runner.

