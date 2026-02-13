# Tinker Framework - Generic Bootstrap (Model-Agnostic)

Purpose: explicit, repeatable setup without IDE assumptions.

If you are in chat, prefer `instructions/chat/trigger_chat.md`.

## Hard constraints
1. Validate `agent/user_task.yaml` against `agent/agent_protocol/schemas/user_task.schema.yaml`.
2. No field inference and no fabricated data.
3. Wrapper-first execution model.

## Explicit bootstrap steps
1. Read governance:
   - `Read .clinerules and agent/rules/agent_rules.md`
2. Activate kernel profile:
   - `./.venv/Scripts/python.exe agent_tools/activate_kernel.py --profile LITE|STANDARD|FULL`
3. Load static context:
   - `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe agent_tools/load_static_context.py`
4. Edit `agent/user_task.yaml`:
   - Required: `mode`, `objective`, `files`, `constraints`
   - Optional: `mode_profile`, `config`, `risk_tolerance`, `phase`, `validation`
5. Trigger:
   - `Run task from agent/user_task.yaml`

## Skill loading protocol
1. `_index.yaml`
2. `.meta.yaml` for shortlisted skills
3. `.md` for invoked skills

Do not bulk-load skill bodies.
