# Skill: root_cause_tracing (Thin Interface)

## Purpose
5-step backward call stack tracing to find original trigger

Business logic lives in:
- `agents/tools/wrappers/policy_guidance_wrapper.py`
- `agents/tools/run_wrapper.py`

## Inputs
- `objective` (string, optional): Main goal for this advisory skill invocation.
- `target_paths` (array[string], optional): Files/areas to focus on.
- `constraints` (array[string], optional): Guardrails or non-goals to enforce.
- `output_mode` (string, optional, default `checklist`): `checklist|plan|actions`
- `max_items` (integer, optional, default `6`)

## Execution

```bash
.venv/Scripts/python.exe agents/tools/run_wrapper.py --skill root_cause_tracing --args-json "{\"objective\":\"<goal>\"}"
```

## Output Contract
- `status`, `skill`, `cluster`, `focus`
- `objective`, `target_paths`, `constraints`, `output_mode`
- `primary_output`


