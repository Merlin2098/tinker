# Skill: excel_to_parquet (Thin Interface)

## Purpose
Convert Excel sheets to Parquet through the canonical execution wrapper.

This skill is intentionally thin. Business logic lives in:
- `agents/tools/wrappers/excel_to_parquet_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `source_excel_path` (string, required): `.xlsx`/`.xls`/`.xlsm` file under repository root.
- `target_parquet_path` (string, required): output `.parquet` path under repository root.
- `sheet_name` (string|integer, optional, default `0`)
- `compression` (string, optional, default `snappy`)
- `use_polars` (boolean, optional, default `true`)
- `overwrite` (boolean, optional, default `true`)

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill excel_to_parquet --args-json "{\"source_excel_path\":\"data/data_papa.xlsx\",\"target_parquet_path\":\"data/data_papa.parquet\"}"
```

Preferred with args file:

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill excel_to_parquet --args-file agents/logic/agent_outputs/plans/excel_to_parquet.args.json
```

## Output Contract
Wrapper returns JSON with:
- `status`
- `skill`
- `source_excel_path`
- `resolved_source_excel_path`
- `target_parquet_path`
- `resolved_target_parquet_path`
- `sheet_name`
- `compression`
- `use_polars`
- `engine_used`
- `fallback_reason`
- `overwrite`
- `row_count`
- `column_count`
- `source_size_bytes`
- `target_size_bytes`
- `compression_ratio`

## Validation Rules
- Source and target paths must resolve inside repository root.
- Source must be an existing Excel file.
- Target must have `.parquet` extension.
- `compression` must be one of `snappy|gzip|zstd|lz4|brotli|uncompressed|none`.
- Existing target is rejected when `overwrite=false`.

## Failure Behavior
- Invalid arguments -> non-zero exit and JSON error payload from runner.
- Read/write errors -> non-zero exit and JSON error payload from runner.

