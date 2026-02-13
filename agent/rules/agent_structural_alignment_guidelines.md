# Structural Alignment Guidelines for Agents (Phase 1)

Status: Required alignment baseline
Scope: Prompt contracts and execution behavior

## 1. Canonical task contract fields

Every agent prompt must consume and expose the same canonical fields:

- Role
- Mode
- Objective
- Files
- Config
- Constraints
- Risk Tolerance

No prompt may introduce substitute fields that bypass these inputs.

## 2. Validation gate behavior

- Phase A (`A_CONTRACT_VALIDATION`) is mandatory before execution.
- Phase B (`B_EXECUTION`) is blocked unless validation status is PASSED.
- Validation phase produces a verdict only; it must not execute changes.

## 3. Inference and invention bans

- Do not infer missing fields.
- Do not invent config paths, execution plans, or task details.
- Do not infer user intent from unspecified context when required fields are absent.

## 4. Legacy and ambiguity handling

- Remove legacy placeholders not part of the canonical contract.
- Remove objective-based implicit phase detection.
- Reject incomplete or ambiguous contracts with explicit error output.

## 5. Config handling

- Never assume config location (for example, default `task_plan.json` path).
- Use only config entries declared in the task contract.
- If config references are missing, stop and return validation failure.

## 6. Artifact discipline

- Do not create artifacts that are not requested by contract/workflow.
- Do not claim validation success without explicit validation metadata.
- Persist only required outputs for the active role and phase.
