# Debugging Limits (Operational)

This file defines bounded debugging depth.
It is operational guidance, not canonical governance.

## Canonical References
- Governance authority: `agent/rules/agent_rules.md`
- Diagnostic classifier: `agent/rules/user_fault_heuristic.md`

## Gates
- Gate 1 (default): classify immediate failure and provide one bounded fix path.
- Gate 2 (opt-in): targeted investigation only on declared scope.
- Gate 3 (explicit confirmation): deep tracing when evidence justifies it.

## Hard Bounds
- No deep debugging in validation-only phase.
- Junior remains Gate 1 only.
- Reconfirm with user after bounded iterations before expanding scope.
