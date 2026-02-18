# Skill: log_bundle_folder_management (Thin Interface)

## Purpose
Select or create a log folder that lives outside a bundled executable (e.g., PyInstaller).

Business logic lives in:
- `agent_tools/wrappers/log_bundle_folder_management_wrapper.py`
- `agent_tools/run_wrapper.py`

## Inputs
- `app_name` (string, optional, default `tinker`)
- `bundled_mode` (bool, optional, default `false`)
- `create_if_missing` (bool, optional, default `true`)
- `validate_writable` (bool, optional, default `true`)
- `fallback_to_temp` (bool, optional, default `true`)
- `log_folder_path` (string, optional): Explicit log folder.
- `bundle_root` (string, optional): Bundle root override (e.g., `_MEIPASS`).
- `dry_run` (bool, optional, default `false`)

## Execution

```bash
.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill log_bundle_folder_management --args-json "{\"bundled_mode\":true}"
```

## Output Contract
- `status`, `skill`, `dry_run`
- `resolved_log_folder`, `requested_log_folder_path`, `bundle_root`
- `created`, `fallback_used`
