# Skill: setup_medallion_structure (Thin Interface)

## Purpose
Validate or create a Medallion directory layout (`bronze/silver/gold`) through the canonical wrapper.

Business logic lives in:
- `agents/tools/wrappers/setup_medallion_structure_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `base_path` (string, required): Root directory for the medallion layout (inside repository root).
- `layers` (array[string], optional, default `["bronze","silver","gold"]`)
- `create_if_missing` (boolean, optional, default `true`)
- `validate_only` (boolean, optional, default `false`)

`validate_only=true` forces no directory creation.

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill setup_medallion_structure --args-json "{\"base_path\":\"data/lake\",\"validate_only\":true}"
```

## Output Contract
- `status`, `skill`, `base_path`, `layers`
- `bronze_path`, `silver_path`, `gold_path`
- `structure_valid`, `created_dirs`, `missing_dirs`
- `create_if_missing`, `validate_only`

