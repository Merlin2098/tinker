# Skill: db_explorer (Thin Interface)

## Purpose
Inspect local SQLite/DuckDB files through the canonical execution wrapper.

Business logic lives in:
- `agents/tools/wrappers/db_explorer_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.db`/`.sqlite`/`.duckdb` file path under repository root.
- `read_only` (boolean, optional, default `true`)
- `table` (string, optional)
- `preview_rows` (integer, optional, default `20`, range `0..500`)

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill db_explorer --args-json "{\"path\":\"data/app.duckdb\"}"
```

## Output Contract
- `status`, `skill`, `engine`, `path`, `resolved_path`
- `table_count`, `tables`, `selected_table`
- `table_schema`, `preview_rows`, `rows_preview`
- `size_bytes`

