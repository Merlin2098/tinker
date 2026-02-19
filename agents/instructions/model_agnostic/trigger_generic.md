# Tinker Framework - Generic Bootstrap (Model-Agnostic)

Purpose: explicit, repeatable setup without IDE assumptions.

If you are in chat, prefer `agents/instructions/chat/trigger_chat.md`.

## Hard constraints
1. Validate `agents/logic/user_task.yaml` against `agents/logic/agent_protocol/schemas/user_task.schema.yaml`.
2. No field inference and no fabricated data.
3. Wrapper-first execution model.

## Explicit bootstrap steps
1. Read governance:
   - `Read .clinerules and agents/logic/rules/agent_rules.md`
2. Activate kernel profile:
   - `./.venv/Scripts/python.exe agents/tools/activate_kernel.py --profile LITE|STANDARD|FULL`
3. Load static context:
   - `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe agents/tools/load_static_context.py`
   - Optional consolidated context:
   - `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe agents/tools/load_full_context.py --task-plan <path> --system-config <path> --summary <path>`
4. Edit `agents/logic/user_task.yaml`:
   - Required: `mode`, `objective`, `files`, `constraints`
   - Optional: `mode_profile`, `config`, `risk_tolerance`, `phase`, `validation`
5. Optional review/handoff plan doc:
   - `.venv/Scripts/python.exe agents/tools/plan_doc.py init --id <id> --title <title> --objective <text>`
   - `.venv/Scripts/python.exe agents/tools/plan_doc.py validate --file agents/logic/agent_outputs/plans/plan_active/<id>.yaml`
6. Trigger:
   - `Run task from agents/logic/user_task.yaml`

## Skill loading protocol
1. `_index.yaml`
2. `.meta.yaml` for shortlisted skills
3. `.md` for invoked skills

Do not bulk-load skill bodies.

Plan docs in `agents/logic/agent_outputs/plans/` are optional collaboration artifacts, not hard workflow gates.

