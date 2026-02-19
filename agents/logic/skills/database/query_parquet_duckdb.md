# Skill: query_parquet_duckdb (Thin Interface)

## Purpose
Execute SQL queries (typically over Parquet sources) using the canonical DuckDB query wrapper.

This skill is intentionally thin. Business logic lives in:
- `agents/tools/wrappers/query_parquet_duckdb_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `sql_query` (string, required): SQL statement to execute.
- `database_path` (string, optional, default `:memory:`): DuckDB target.
- `read_only` (boolean, optional, default `false`)
- `allow_write` (boolean, optional, default `false`): must be `true` for non-read SQL.
- `preview_rows` (integer, optional, default `20`, range `1..1000`)
- `config` (object, optional): DuckDB config key/value map.

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill query_parquet_duckdb --args-json "{\"sql_query\":\"SELECT 1 AS ok\"}"
```

Alternative with args file:

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill query_parquet_duckdb --args-file agents/logic/agent_outputs/plans/query_parquet_duckdb.args.json
```

## Output Contract
Wrapper returns JSON with:
- `status`
- `skill`
- `database_path`
- `resolved_database_path`
- `read_only`
- `allow_write`
- `config_applied_keys`
- `sql_query`
- `row_count`
- `column_count`
- `columns`
- `rows_preview`
- `preview_rows`
- `truncated`

## Validation Rules
- `sql_query` must be a non-empty string.
- If `allow_write=false`, SQL must start with `SELECT`, `WITH`, `EXPLAIN`, or `PRAGMA`.
- `database_path` rules match `connect_duckdb` wrapper constraints.
- `preview_rows` must be in `1..1000`.

## Failure Behavior
- Invalid arguments -> non-zero exit and JSON error payload from runner.
- SQL/connection failure -> non-zero exit and JSON error payload from runner.


