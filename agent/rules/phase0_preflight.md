# Phase 0 Preflight (Operational Checklist)

This file defines a lightweight validation-only checklist.
It is procedural, not canonical policy.

## Canonical References
- Governance: `agent/rules/agent_rules.md`
- Task schema: `agent/agent_protocol/schemas/user_task.schema.yaml`

## Checklist
1. Load `agent/user_task.yaml`.
2. Validate schema with `agent_tools/schema_validator.py --type user_task`.
3. Confirm phase/validation consistency from schema rules.
4. Apply `agent/rules/user_fault_heuristic.md` for classification output.
5. Return a preflight verdict only; do not execute code changes.
