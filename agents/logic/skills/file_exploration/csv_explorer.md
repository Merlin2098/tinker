# Skill: csv_explorer (Thin Interface)

## Purpose
Inspect CSV files through the canonical execution wrapper.

Business logic lives in:
- `agents/tools/wrappers/csv_explorer_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.csv` file path under repository root.
- `encoding` (string, optional, default `utf-8-sig`)
- `preview_rows` (integer, optional, default `5`, range `0..200`)

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill csv_explorer --args-json "{\"path\":\"data/example.csv\"}"
```

## Output Contract
- `status`, `skill`, `path`, `resolved_path`
- `encoding`, `delimiter`, `quotechar`
- `row_count`, `column_count`, `columns`
- `rows_preview`, `size_bytes`

