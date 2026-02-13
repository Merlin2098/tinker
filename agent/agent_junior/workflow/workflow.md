# Workflow (Role-Compatibility Mode)

Role-specific orchestration is deprecated.
This repository now uses a single practical execution path for all agents.

## Unified Flow
1. Read `agent/user_task.yaml`.
2. Resolve active profile with `agent_tools/mode_selector.py`.
3. Load minimal context (`agent_tools/load_static_context.py`) only when needed.
4. Select skills via `_index.yaml` + `.meta.yaml`, load `.md` bodies on demand.
5. Execute strictly within `objective`, `files`, `config.sources`, and `constraints`.
6. Verify outputs and persist artifacts in `agent/agent_outputs/`.

## Notes
- `role` is treated as compatibility metadata, not a routing requirement.
- Do not enforce role-only execution branches in this workflow layer.
- Governance and protected-file rules still apply.
