# Skill: execution_flow_orchestration (Thin Interface)

## Purpose
Structured execution with atomic actions, progress monitoring, failure handling

Business logic lives in:
- `agent_tools/wrappers/policy_guidance_wrapper.py`
- `agent_tools/run_wrapper.py`

## Inputs
- `objective` (string, optional): Main goal for this advisory skill invocation.
- `target_paths` (array[string], optional): Files/areas to focus on.
- `constraints` (array[string], optional): Guardrails or non-goals to enforce.
- `output_mode` (string, optional, default `checklist`): `checklist|plan|actions`
- `max_items` (integer, optional, default `6`)

## Execution

```bash
.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill execution_flow_orchestration --args-json "{\"objective\":\"<goal>\"}"
```

## Output Contract
- `status`, `skill`, `cluster`, `focus`
- `objective`, `target_paths`, `constraints`, `output_mode`
- `primary_output`

