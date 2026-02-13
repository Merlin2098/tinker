# Tinker Framework - Chat Bootstrap (Model-Agnostic)

Purpose: explicit setup for chat-based agents.

## Hard constraints
1. Validate `agent/user_task.yaml` against `agent/agent_protocol/schemas/user_task.schema.yaml`.
2. No field inference and no fabricated data.
3. Wrapper-first execution model.

## Trigger phrases
- `Run task from agent/user_task.yaml`
- `Tinker: run`
- `Tinker: validate`

## Kernel commands (chat)
- `Kernel LITE`
- `Kernel STANDARD`
- `Kernel FULL`

## Bootstrap steps
1. Read governance:
   - `Read .clinerules and agent/rules/agent_rules.md`
2. Activate profile via kernel commands.
3. Load context:
   - `$env:PYTHONIOENCODING='utf-8'; ./.venv/Scripts/python.exe agent_tools/load_static_context.py`
4. Prepare `agent/user_task.yaml` when requested:
   - `./.venv/Scripts/python.exe agent_tools/user_task_builder.py ...`
5. Optional review/handoff plan doc (if requested):
   - `./.venv/Scripts/python.exe agent_tools/plan_doc.py init --id <id> --title <title> --objective <text>`
   - `./.venv/Scripts/python.exe agent_tools/plan_doc.py validate --file agent/agent_outputs/plans/plan_active/<id>.yaml`
6. Trigger with one of the trigger phrases.

## Notes
- `mode_profile` in `agent/user_task.yaml` is optional; leave empty unless explicitly needed.
- Optional compatibility fields (`phase`, `validation`) are supported but not required.
- Plan docs under `agent/agent_outputs/plans/` are optional collaboration artifacts, not execution prerequisites.
