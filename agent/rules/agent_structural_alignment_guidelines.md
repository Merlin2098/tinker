# Structural Alignment Guidelines (Compatibility Note)

This document is non-canonical.

## Authority
- Governance authority: `agent/rules/agent_rules.md`
- Contract authority: `agent/agent_protocol/schemas/user_task.schema.yaml`

## Minimal Alignment Requirements
- Keep task fields aligned with the user task schema.
- Keep prompts/workflows free of inferred defaults.
- Keep execution gated by explicit validation status.

If any statement here differs from canonical governance, follow `agent_rules.md`.
