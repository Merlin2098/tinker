# Skill: parquet_explorer (Thin Interface)

## Purpose
Inspect Parquet schema and preview rows through the canonical execution wrapper.

Business logic lives in:
- `agent_tools/wrappers/parquet_explorer_wrapper.py`
- `agent_tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.parquet` file path under repository root.
- `columns` (array of strings, optional)
- `preview_rows` (integer, optional, default `5`, range `0..200`)

## Execution

```bash
.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill parquet_explorer --args-json "{\"path\":\"data/sample.parquet\"}"
```

## Output Contract
- `status`, `skill`, `path`, `resolved_path`
- `row_count`, `column_count`, `columns`, `schema`
- `selected_columns`, `preview_rows`, `rows_preview`
- `size_bytes`
