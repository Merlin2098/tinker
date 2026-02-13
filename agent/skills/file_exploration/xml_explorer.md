# Skill: xml_explorer (Thin Interface)

## Purpose
Inspect XML hierarchy and text preview through the canonical execution wrapper.

Business logic lives in:
- `agent_tools/wrappers/xml_explorer_wrapper.py`
- `agent_tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.xml` file path under repository root.
- `encoding` (string, optional, default `utf-8-sig`)
- `preview_chars` (integer, optional, default `400`)

## Execution

```bash
.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill xml_explorer --args-json "{\"path\":\"config/sample.xml\"}"
```

## Output Contract
- `status`, `skill`, `path`, `resolved_path`
- `root_tag`, `namespace_count`, `namespaces`
- `element_count`, `attribute_count`, `top_child_tags`
- `text_preview`, `truncated`, `size_bytes`
