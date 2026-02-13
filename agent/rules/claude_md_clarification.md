# claude.md Clarification (Phase 1)

Status: Declarative governance note
Scope: Origin, purpose, limitations, and non-dependency policy

## Origin

- `claude.md` was generated from the bootstrap guidance in `instructions/claude/trigger_vscode.md`.
- It is a generated governance artifact and not a system runtime component.

## Intended purpose

- Provide declarative guidance for Claude-oriented sessions.
- Document high-level operating constraints and initialization expectations.
- Improve consistency of operator prompts across environments.

## Limitations

- It is not an execution engine.
- It is not a validation gate.
- It does not provide durable structured context.
- It does not replace schema validation, workflow checks, or protected-file enforcement.

## Why it cannot replace internal validation

- Contract validation requires deterministic schema checks, not descriptive guidance.
- Execution gating requires explicit machine-verifiable status (`validation.status == PASSED`).
- Governance must remain enforceable even when external prompt artifacts are unavailable.

## Governance role

`claude.md` is declarative governance only.

Invoker must function correctly even if `claude.md` is absent, stale, or not loaded.
All mandatory controls must live in Invoker-native assets (schemas, prompts, workflows, rules).
