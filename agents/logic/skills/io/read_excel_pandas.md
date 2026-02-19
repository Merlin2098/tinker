# Skill: read_excel_pandas (Thin Interface)

## Purpose
Load Excel files for exploratory analysis through the canonical execution wrapper.

This skill is intentionally thin. Business logic lives in:
- `agents/tools/wrappers/read_excel_pandas_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.xlsx` or `.xls` file under repository root.
- `sheet_name` (string|integer, optional, default `0`)
- `header_row` (integer, optional, default `0`)
- `usecols` (string|array, optional)
- `nrows` (integer, optional)
- `preview_rows` (integer, optional, default `5`, range `0..100`)

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill read_excel_pandas --args-json "{\"path\":\"data/data_papa.xlsx\"}"
```

Preferred with args file:

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill read_excel_pandas --args-file agents/logic/agent_outputs/plans/read_excel_pandas.args.json
```

## Output Contract
Wrapper returns JSON with:
- `status`
- `skill`
- `path`
- `resolved_path`
- `sheet_name`
- `header_row`
- `nrows`
- `usecols`
- `preview_rows`
- `row_count`
- `column_count`
- `columns`
- `dtypes`
- `rows_preview`
- `size_bytes`

## Validation Rules
- `path` must resolve inside repository root.
- `path` must point to an existing `.xlsx` or `.xls` file.
- `header_row` must be `>= 0` when provided.
- `nrows` must be `>= 1` when provided.
- `preview_rows` must be in `0..100`.

## Failure Behavior
- Invalid arguments -> non-zero exit and JSON error payload from runner.
- Read/parse errors -> non-zero exit and JSON error payload from runner.


