# Skill: read_excel_polars_openpyxl (Thin Interface)

## Purpose
Load Excel files with openpyxl + polars for performance-oriented ingestion through the canonical execution wrapper.

This skill is intentionally thin. Business logic lives in:
- `agent_tools/wrappers/read_excel_polars_openpyxl_wrapper.py`
- `agent_tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.xlsx` or `.xlsm` file under repository root.
- `sheet_name` (string|integer, optional, default `0`)
- `read_only` (boolean, optional, default `true`)
- `data_only` (boolean, optional, default `true`)
- `use_columns` (array of strings, optional)
- `preview_rows` (integer, optional, default `5`, range `0..100`)

## Execution

```bash
.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill read_excel_polars_openpyxl --args-json "{\"path\":\"data/data_papa.xlsx\",\"sheet_name\":0}"
```

Preferred with args file:

```bash
.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill read_excel_polars_openpyxl --args-file agent/agent_outputs/plans/read_excel_polars_openpyxl.args.json
```

## Output Contract
Wrapper returns JSON with:
- `status`
- `skill`
- `path`
- `resolved_path`
- `sheet_name`
- `read_only`
- `data_only`
- `use_columns`
- `preview_rows`
- `row_count`
- `column_count`
- `columns`
- `schema`
- `rows_preview`
- `size_bytes`

## Validation Rules
- `path` must resolve inside repository root.
- `path` must point to an existing `.xlsx` or `.xlsm` file.
- `use_columns` items must be non-empty strings when provided.
- `preview_rows` must be in `0..100`.

## Failure Behavior
- Invalid arguments -> non-zero exit and JSON error payload from runner.
- Read/parse errors -> non-zero exit and JSON error payload from runner.

