# Skill: parquet_to_excel_polars_xlsxwriter (Thin Interface)

## Purpose
Convert Parquet to Excel for delivery workflows through the canonical execution wrapper.

This skill is intentionally thin. Business logic lives in:
- `agents/tools/wrappers/parquet_to_excel_polars_xlsxwriter_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `source_parquet_path` (string, required): input `.parquet` path under repository root.
- `target_excel_path` (string, required): output `.xlsx` path under repository root.
- `sheet_name` (string, optional, default `Sheet1`, max 31 chars, Excel-safe chars only)
- `header` (boolean, optional, default `true`)
- `max_rows` (integer, optional, default `1048576`)
- `overwrite` (boolean, optional, default `true`)

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill parquet_to_excel_polars_xlsxwriter --args-json "{\"source_parquet_path\":\"data/data_papa.parquet\",\"target_excel_path\":\"data/data_papa_export.xlsx\"}"
```

Preferred with args file:

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill parquet_to_excel_polars_xlsxwriter --args-file agents/logic/agent_outputs/plans/parquet_to_excel_polars_xlsxwriter.args.json
```

## Output Contract
Wrapper returns JSON with:
- `status`
- `skill`
- `source_parquet_path`
- `resolved_source_parquet_path`
- `target_excel_path`
- `resolved_target_excel_path`
- `sheet_name`
- `header`
- `overwrite`
- `max_rows`
- `source_row_count`
- `row_count_written`
- `column_count`
- `truncated`
- `source_size_bytes`
- `target_size_bytes`

## Validation Rules
- Source and target paths must resolve inside repository root.
- Source must be an existing `.parquet` file.
- Target must have `.xlsx` extension.
- `sheet_name` must satisfy Excel sheet naming rules.
- `max_rows` must be in `1..1048576`.
- Existing target is rejected when `overwrite=false`.

## Failure Behavior
- Invalid arguments -> non-zero exit and JSON error payload from runner.
- Read/write errors -> non-zero exit and JSON error payload from runner.


