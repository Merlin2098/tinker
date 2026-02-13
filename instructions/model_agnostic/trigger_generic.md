# Tinker Framework - Generic Bootstrap (Model-Agnostic)

Purpose: Provide explicit, repeatable setup steps without IDE assumptions.

If you are running in chat, prefer `instructions/chat/trigger_chat.md` and
`instructions/chat/command_glossary_chat.md`.

## Hard constraints
1. Validate `agent/user_task.yaml` against `agent/agent_protocol/schemas/user_task.schema.yaml`.
2. No field inference and no data invention.
3. No execution without explicit validation pass.

## Explicit bootstrap steps
1. Read governance (chat command):
   - `Read .clinerules and agent/rules/agent_rules.md`
2. Activate kernel profile (choose one, OS-specific):
   - PowerShell/CMD:
     - `.\.venv\Scripts\python.exe agent_tools\activate_kernel.py --profile LITE`
     - `.\.venv\Scripts\python.exe agent_tools\activate_kernel.py --profile STANDARD`
     - `.\.venv\Scripts\python.exe agent_tools\activate_kernel.py --profile FULL`
   - Bash (Windows Git Bash):
     - `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe agent_tools/activate_kernel.py --profile LITE`
     - `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe agent_tools/activate_kernel.py --profile STANDARD`
     - `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe agent_tools/activate_kernel.py --profile FULL`
   - Wrapper:
     - `instructions/model_agnostic/activate_kernel.cmd LITE`
     - `./instructions/model_agnostic/activate_kernel.sh LITE`
3. Run static context loader:
   - PowerShell: `$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe agent_tools/load_static_context.py`
   - Bash: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe agent_tools/load_static_context.py`
4. Edit `agent/user_task.yaml`:
   - Set `mode_profile` to LITE, STANDARD, or FULL
   - Fill mode, objective, files, config, constraints, optional compatibility fields
5. Trigger the agent:
   - `Run task from agent/user_task.yaml`

## Skill loading protocol
1. `_index.yaml`
2. `.meta.yaml` for shortlisted skills
3. `.md` for invoked skills

Do not bulk-load skill bodies.

## Troubleshooting
- Exit code 127 in bash: use `.venv/Scripts/python.exe` (forward slashes), not Windows backslashes.
- No state file: verify `.venv/Scripts/python.exe` exists and the profile file is present in `agent/profiles/`.
- Silent success: `activate_kernel.py` now prints profile + state path on success.


