# Skill: input_file_handler (Thin Interface)

## Purpose
Validate and inspect an input file path through the canonical wrapper.

Business logic lives in:
- `agent_tools/wrappers/input_file_handler_wrapper.py`
- `agent_tools/run_wrapper.py`

## Inputs
- `path` (string, required): File path under repository root.
- `must_exist` (boolean, optional, default `true`)
- `allowed_extensions` (array[string], optional): Example `[".json",".yaml"]`
- `encoding` (string, optional, default `utf-8-sig`)
- `include_preview` (boolean, optional, default `true`)
- `max_preview_lines` (integer, optional, default `5`)
- `preview_chars` (integer, optional, default `1200`)
- `force_text_preview` (boolean, optional, default `false`)

## Execution

```bash
.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill input_file_handler --args-json "{\"path\":\"agent/agent_outputs/context.json\",\"allowed_extensions\":[\".json\"]}"
```

## Output Contract
- `status`, `skill`, `path`, `resolved_path`, `exists`, `extension`
- `size_bytes`, `line_count` (when file exists and text preview is enabled)
- `preview`, `preview_truncated`, `preview_line_count`
