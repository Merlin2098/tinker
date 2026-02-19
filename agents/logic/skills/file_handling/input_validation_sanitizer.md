# Skill: input_validation_sanitizer (Thin Interface)

## Purpose
Validate and sanitize a single input payload through the canonical wrapper.

Business logic lives in:
- `agents/tools/wrappers/input_validation_sanitizer_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `value` (any, required): Payload to validate.
- `expected_type` (string, optional): `string|integer|number|boolean|list|object`
- `strip_strings` (boolean, optional, default `true`)
- `allow_empty` (boolean, optional, default `false`)
- `min_length`, `max_length` (integer, optional)
- `min_value`, `max_value` (number, optional)
- `allowed_values` (array, optional)
- `pattern` (string regex, optional, string values only)

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill input_validation_sanitizer --args-json "{\"value\":\"  abc  \",\"expected_type\":\"string\",\"min_length\":3}"
```

## Output Contract
- `status`, `skill`, `value_type`, `sanitized_value`
- `applied.expected_type`, `applied.strip_strings`, `applied.allow_empty`
- `applied.min_length`, `applied.max_length`, `applied.min_value`, `applied.max_value`
- `applied.allowed_values_count`, `applied.pattern`

