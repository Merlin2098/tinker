# Agent Contract (Compatibility Mode)

This role contract is retained for backward compatibility only.

## Status
- Legacy role separation is deprecated for active execution.
- Execution follows the unified workflow under `agent/*/workflow/workflow.md`.

## Compatibility Behavior
- `role` remains accepted in `agent/user_task.yaml` for schema compatibility.
- Capability selection is controlled by kernel profile allowlists.
- No mandatory role handoff is required in this contract.
