# Agents Migration Plan

## Objective
Consolidate framework directories under a single root directory `agents/` while preserving runtime stability during migration.

Path mapping:
- `agent/` -> `agents/logic/`
- `agent_tools/` -> `agents/tools/`
- `instructions/` -> `agents/instructions/`

## Constraints and design choices
- Keep portability (no new third-party dependencies).
- Use explicit, project-root-relative paths.
- Maintain temporary backward compatibility via aliases during transition.
- Python package naming remains valid (`agents` is import-safe; hidden names like `.agents` are not).

## Phase 0: Baseline and safety
1. Snapshot current status:
```powershell
git status --short
```
2. Write pre-migration file manifest:
```powershell
python migrate_verify.py --write-manifest .migration/move_manifest.json
```
3. Optional inventory scans:
```powershell
rg -n --glob "*.py" "from agent_tools|import agent_tools|from agent\.|import agent\."
rg -n --glob "*.py" "agent/|agent_tools/|instructions/"
```

## Phase 1: File system migration
Run from project root.

```powershell
# 1) Create destination structure
New-Item -ItemType Directory -Force -Path "agents","agents/logic","agents/tools","agents/instructions" | Out-Null

# 2) Move contents (not container directories)
Get-ChildItem "agent" -Force | ForEach-Object { Move-Item $_.FullName "agents/logic/" }
Get-ChildItem "agent_tools" -Force | ForEach-Object { Move-Item $_.FullName "agents/tools/" }
Get-ChildItem "instructions" -Force | ForEach-Object { Move-Item $_.FullName "agents/instructions/" }

# 3) Remove old containers
Remove-Item "agent","agent_tools","instructions" -Force
```

## Phase 2: Backward compatibility bridge (temporary)
Use junctions on Windows so legacy scripts/import paths still resolve.

```powershell
cmd /c mklink /J agent agents\logic
cmd /c mklink /J agent_tools agents\tools
cmd /c mklink /J instructions agents\instructions
```

Compatibility window goal:
- Existing commands like `python agent_tools/run_wrapper.py` still work.
- Existing imports from `agent_tools...` keep working until code refactor is complete.

## Phase 3: Refactor map

### A) Python import namespace refactor
Primary replacements:
- `from agent_tools.` -> `from agents.tools.`
- `import agent_tools.` -> `import agents.tools.`
- `from agent_tools import` -> `from agents.tools import`
- `import agent_tools` -> `import agents.tools as agent_tools` (temporary shim pattern if needed)

High-impact files:
- `agent_tools/activate_kernel.py`
- `agent_tools/kernel_guard.py`
- `agent_tools/mode_selector.py`
- `agent_tools/schema_validator.py`
- `agent_tools/validate_message.py`
- `agent_tools/validate_skill_metadata.py`
- `agent_tools/verify_profiles.py`
- `agent_tools/wrappers/*.py` (multiple imports from `agent_tools.wrappers`)

### B) Hardcoded filesystem path refactor
Primary replacements:
- `agent/` -> `agents/logic/`
- `agent_tools/` -> `agents/tools/`
- `instructions/` -> `agents/instructions/`

High-impact files:
- `agent_framework_config.yaml`
- `.clinerules`
- `.gitignore`
- `.pre-commit-config.yaml`
- `install_tinker.py`
- `README.md`
- `AGENTS.md`
- `architecture.md`
- `agent_tools/load_static_context.py`
- `agent_tools/load_full_context.py`
- `agent_tools/context_loader.py`
- `agent_tools/config_validator.py`
- `agent_tools/compile_registry.py`
- `agent_tools/migrate_triggers.py`
- `agent_tools/plan_doc.py`
- `agent_tools/user_task_builder.py`
- `agent_tools/treemap.py`

### C) Root detection updates
Several helpers currently derive root from old folder assumptions.
Update these first:
- `agent_tools/_context_common.py`
- `agent_tools/_profile_state.py`
- `agent_tools/_schema_utils.py`
- `agent_tools/_repo_root.py`

Recommended sentinel logic:
- Prefer checking for `agents/tools`, `agents/logic`, and `agent_framework_config.yaml`.
- Keep fallback for legacy roots during transition.

## Phase 4: Regex replacement runbook
Use carefully and review each diff.

```powershell
# Imports
rg -l --glob "*.py" "from agent_tools\\." | ForEach-Object {
  (Get-Content $_ -Raw).Replace("from agent_tools.","from agents.tools.") | Set-Content $_
}
rg -l --glob "*.py" "import agent_tools\\." | ForEach-Object {
  (Get-Content $_ -Raw).Replace("import agent_tools.","import agents.tools.") | Set-Content $_
}

# Path literals in py/yaml/md/txt/gitignore
rg -l "agent_tools/" | ForEach-Object {
  (Get-Content $_ -Raw).Replace("agent_tools/","agents/tools/") | Set-Content $_
}
rg -l "instructions/" | ForEach-Object {
  (Get-Content $_ -Raw).Replace("instructions/","agents/instructions/") | Set-Content $_
}
rg -l "agent/" | ForEach-Object {
  (Get-Content $_ -Raw).Replace("agent/","agents/logic/") | Set-Content $_
}
```

Note: run targeted file globs first to avoid accidental replacements in unrelated content.

## Phase 5: Validation
1. Compatibility-mode verification:
```powershell
python migrate_verify.py --manifest .migration/move_manifest.json
```
2. Strict verification after import/path cleanup:
```powershell
python migrate_verify.py --manifest .migration/move_manifest.json --strict --fail-on-text-refs
```
3. Runtime smoke checks:
```powershell
python agents/tools/compile_registry.py
python agents/tools/load_static_context.py
python agents/tools/run_wrapper.py --skill execution_timer --args-json "{}"
```

## Phase 6: Remove compatibility aliases
After strict verification passes and CI is green:

```powershell
Remove-Item agent,agent_tools,instructions -Force
```

Then run strict validation again.

## Rollback
If major regressions occur:
1. Restore from git state.
2. Recreate old directory layout from manifest + move commands in reverse.
3. Re-enable junction aliases.
4. Re-run `python migrate_verify.py --manifest .migration/move_manifest.json`.

## CI/CD and gitignore notes
- If build scripts or packaging pipelines ignore unknown paths, explicitly include `agents/**`.
- Update runtime ignore entries from:
  - `agent/analysis/...` -> `agents/logic/analysis/...`
  - `agent/agent_outputs/...` -> `agents/logic/agent_outputs/...`
  - `agent/agent_logs/...` -> `agents/logic/agent_logs/...`
- Update deployment installer footprint in `agent_framework_config.yaml`:
  - `agent/`, `agent_tools/`, `instructions/` -> `agents/logic/`, `agents/tools/`, `agents/instructions/`.

