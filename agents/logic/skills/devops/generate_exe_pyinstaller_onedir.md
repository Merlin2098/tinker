# Skill: generate_exe_pyinstaller_onedir (Thin Interface)

## Purpose
Build a PyInstaller `--onedir` executable from a Python script through the canonical wrapper.

Business logic lives in:
- `agents/tools/wrappers/generate_exe_pyinstaller_onedir_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `script_path` (string, required): Path to the entry-point `.py` file (repo-relative or absolute).
- `venv_path` (string, optional, default `.venv`): Virtual environment directory.
- `output_dir` (string, optional, default `dist`): Output folder for build artifacts.
- `exe_name` (string, optional): Executable name (defaults to script stem).
- `icon_path` (string, optional): `.ico` file for Windows executable.
- `hidden_imports` (list[string], optional): Extra PyInstaller hidden imports.
- `excludes` (list[string], optional): Modules to exclude.
- `clean` (bool, optional, default `true`): Clean PyInstaller cache.
- `dry_run` (bool, optional, default `false`): Return command without executing.

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill generate_exe_pyinstaller_onedir --args-json "{\"script_path\":\"src/app.py\"}"
```

## Output Contract
- `status`, `skill`, `dry_run`
- `script_path`, `venv_path`, `output_dir`, `exe_name`
- `command`, `dist_folder`, `executable_path`
- `returncode`, `stdout_tail`, `stderr_tail` (when executed)

