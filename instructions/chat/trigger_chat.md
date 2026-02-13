# Tinker Framework - Chat Bootstrap (Model-Agnostic)

Purpose: Provide explicit, repeatable setup steps for chat-based agents (Codex/ChatGPT/etc.).

See `instructions/chat/command_glossary_chat.md` for a compact command reference.

## Hard constraints
1. Validate `agent/user_task.yaml` against `agent/agent_protocol/schemas/user_task.schema.yaml`.
2. No field inference and no data invention.
3. No execution without explicit validation pass.
4. Governance is internal to Tinker; do not depend on external IDE state.

## Chat trigger phrases (explicit)
Any of the following phrases should be treated as a trigger:
- `Run task from agent/user_task.yaml`
- `Tinker: run`
- `Tinker: validate`

## Kernel commands (chat-only)
These commands change the active kernel profile without editing `agent/user_task.yaml`:
- `Kernel LITE`
- `Kernel STANDARD`
- `Kernel FULL`

Rule: In chat flow, `mode_profile` in `agent/user_task.yaml` should be empty unless the user explicitly asks to set it.

## Implicit trigger rule
If the user explicitly asks to “run/execute the task in agent/user_task.yaml”, treat it as a trigger.

## Explicit bootstrap steps
1. Read governance (chat command):
   - `Read .clinerules and agent/rules/agent_rules.md`
2. Activate kernel profile (chat kernel commands):
   - `Kernel LITE` | `Kernel STANDARD` | `Kernel FULL`
3. Load static context (venv only):
   - PowerShell: `$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe agent_tools/load_static_context.py`
   - Bash: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe agent_tools/load_static_context.py`
4. Prepare `agent/user_task.yaml` only when the user explicitly asks for it:
   - Use `agent_tools/user_task_builder.py` and write a draft from explicit user input.
   - PowerShell (example):
     - `$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe agent_tools/user_task_builder.py ...`
   - Alternative inputs:
     - `--input <yaml>` to validate and write a full YAML draft
     - `--from-template <yaml>` to load a template and override with explicit fields
   - Suggested chat template:
      - `agent/task_templates/chat/user_task_template.yaml`
5. Trigger the agent using chat:
   - `Run task from agent/user_task.yaml`
   - or `Tinker: run` / `Tinker: validate`

## Skill loading protocol
1. `_index.yaml`
2. `.meta.yaml` for shortlisted skills
3. `.md` for invoked skills

Do not bulk-load skill bodies.


