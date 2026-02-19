# Tinker Framework - VS Code Bootstrap (Model-Agnostic)

Purpose: explicit, repeatable setup in VS Code without vendor lock-in.

## Non-negotiable rules
1. Validate `agents/logic/user_task.yaml` against `agents/logic/agent_protocol/schemas/user_task.schema.yaml`.
2. Do not infer missing required fields.
3. Do not invent data, paths, or outcomes.
4. Keep execution wrapper-first (`agents/tools/run_wrapper.py`, `agents/tools/wrappers/*`).
5. Do not depend on external IDE state for governance/runtime state.

## Explicit bootstrap steps
1. Read governance:
   - `Read .clinerules and agents/logic/rules/agent_rules.md`
2. Activate kernel profile (choose one):
   - `./.venv/Scripts/python.exe agents/tools/activate_kernel.py --profile LITE`
   - `./.venv/Scripts/python.exe agents/tools/activate_kernel.py --profile STANDARD`
   - `./.venv/Scripts/python.exe agents/tools/activate_kernel.py --profile FULL`
3. Load static context:
   - PowerShell: `$env:PYTHONIOENCODING='utf-8'; ./.venv/Scripts/python.exe agents/tools/load_static_context.py`
4. Edit `agents/logic/user_task.yaml`:
   - Required: `mode`, `objective`, `files`, `constraints`
   - Optional: `mode_profile`, `config`, `risk_tolerance`, `phase`, `validation`
5. Trigger:
   - `Run task from agents/logic/user_task.yaml`

## Skill loading protocol
1. `agents/logic/skills/_index.yaml`
2. shortlisted `agents/logic/skills/<category>/<skill>.meta.yaml`
3. invoked `agents/logic/skills/<category>/<skill>.md`

Never bulk-load skill bodies.

