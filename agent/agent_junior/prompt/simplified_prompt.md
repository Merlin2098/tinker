================================================================================
UNIFIED AGENT PROMPT (ROLE-COMPATIBILITY)
================================================================================
Version: 1.0.0
Language: English

Legacy role folders remain for compatibility, but orchestration is unified.

## Input Contract
- Role: compatibility metadata only
- Mode / Mode Profile: execution hints
- Objective / Files / Config / Constraints: authoritative scope

## Required Steps
1. Validate and read `agent/user_task.yaml`.
2. Resolve active profile with `agent_tools/mode_selector.py`.
3. Use skill wrappers as execution source of truth.
4. Execute only within declared scope.
5. Verify outputs with fresh evidence.

## References
- Workflow: `agent/agent_*/workflow/workflow.md`
- Context: `agent/agent_*/context/context.md`
- Skills Index: `agent/skills/_index.yaml`
================================================================================
