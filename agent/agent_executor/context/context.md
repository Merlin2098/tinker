# Context (Role-Compatibility Mode)

This context file is intentionally minimal.

## Operating Model
- Single execution model across all legacy role folders.
- Profile allowlists (`agent/profiles/*.yaml`) decide capabilities.
- Skill wrappers are the canonical execution layer.

## Invariants
- Respect governance and protected files.
- Stay within declared task scope.
- Keep plans and reports under `agent/agent_outputs/`.
- Verify before claiming completion.
