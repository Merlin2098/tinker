# Skill: pptx_explorer (Thin Interface)

## Purpose
Inspect PPTX slides, text fragments, and metadata through the canonical execution wrapper.

Business logic lives in:
- `agents/tools/wrappers/pptx_explorer_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `path` (string, required): `.pptx` file path under repository root.
- `preview_slides` (integer, optional, default `5`)

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill pptx_explorer --args-json "{\"path\":\"docs/pitch.pptx\"}"
```

## Output Contract
- `status`, `skill`, `path`, `resolved_path`
- `slide_count`, `notes_slide_count`, `media_asset_count`
- `slides_preview`, `metadata`, `size_bytes`

