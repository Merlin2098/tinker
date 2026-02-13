# Invoker Framework - VS Code Bootstrap (Model-Agnostic)

Purpose: Provide explicit, repeatable setup steps in VS Code without vendor lock-in.

## Non-negotiable rules
1. Validate `agent/user_task.yaml` against `agent/agent_protocol/schemas/user_task.schema.yaml`.
2. Do not infer missing required fields.
3. Do not invent data, paths, or validation outcomes.
4. Do not execute if `phase != B_EXECUTION` or `validation.status != PASSED`.
5. Do not depend on external IDE state for governance or runtime state.

## Explicit bootstrap steps
1. Read governance (chat command):
   - `Read .clinerules and agent/rules/agent_rules.md and agent/rules/regulatory_principles_v1.md`
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
3. Load static context (venv only):
   - PowerShell: `$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe agent_tools/load_static_context.py`
   - Bash: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe agent_tools/load_static_context.py`
4. Edit `agent/user_task.yaml`:
   - Set `mode_profile` to LITE, STANDARD, or FULL
   - Fill `role`, `mode`, `objective`, `files`, `config`, `constraints`, `risk_tolerance`, `phase`, `validation`
5. Trigger the agent:
   - `Run task from agent/user_task.yaml`

## Skill loading protocol
1. Layer 1: `agent/skills/_index.yaml`
2. Layer 2: `agent/skills/<category>/<skill>.meta.yaml` (shortlisted only)
3. Layer 3: `agent/skills/<category>/<skill>.md` (invoked only)

Never bulk-load all skill bodies.

## Troubleshooting
- Exit code 127 in bash: use `.venv/Scripts/python.exe` (forward slashes), not Windows backslashes.
- No state file: verify `.venv/Scripts/python.exe` exists and the profile file is present in `agent/profiles/`.
- Silent success: `activate_kernel.py` now prints profile + state path on success.

## Chat-based agents
If you are running in a chat-only environment (no external command hooks),
use `instructions/chat/trigger_chat.md`.
