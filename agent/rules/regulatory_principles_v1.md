# Regulatory Principles v1 (Historical Rationale)

Status: non-canonical companion note.

## Canonical Governance
- Authoritative policy: `agent/rules/agent_rules.md`
- Contract schema: `agent/agent_protocol/schemas/user_task.schema.yaml`

## Purpose of This File
- Preserve the original rationale behind Phase 1 hardening.
- Explain why deterministic validation and explicit contracts were introduced.

## Principle Summary
1. Validate contracts before execution.
2. Do not infer missing required fields.
3. Do not invent values, paths, or statuses.
4. Keep config references explicit and separate from execution payload.
5. Keep governance independent from optional external tooling artifacts.

For policy enforcement, always defer to `agent_rules.md`.
