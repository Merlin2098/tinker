# Skill: excel_explorer (Thin Interface)

## Purpose
Inspect workbook structure and sample rows through the canonical execution wrapper.

Business logic lives in:
- `agents/tools/wrappers/excel_explorer_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.xlsx`/`.xlsm`/template workbook path under repository root.
- `sheet_name` (string|integer, optional)
- `read_only` (boolean, optional, default `true`)
- `data_only` (boolean, optional, default `true`)
- `preview_rows` (integer, optional, default `5`, range `0..100`)

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill excel_explorer --args-json "{\"path\":\"data/data_papa.xlsx\"}"
```

## Output Contract
- `status`, `skill`, `path`, `resolved_path`
- `sheet_count`, `sheet_summaries`, `selected_sheet`
- `columns`, `column_count`, `rows_preview`
- `read_only`, `data_only`, `size_bytes`

