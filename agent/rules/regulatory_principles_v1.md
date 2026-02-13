# Invoker Regulatory Principles v1.0

Status: Approved for Phase 1 hardening
Scope: Cognitive and contractual foundation
Effective date: 2026-02-12

## PR-01: Mandatory Contract Validation

Statement:
All task contracts must be validated against the official schema before any execution activity.

Rationale:
Execution without validated inputs introduces non-determinism, hidden assumptions, and unsafe behavior.

Operational implications:
- Contract validation is a mandatory gate.
- Execution is blocked until validation status is explicitly PASSED.
- Validation failures must be returned as explicit errors, not auto-corrected.

Enforcement expectations:
- `phase: A_CONTRACT_VALIDATION` is required before execution.
- `phase: B_EXECUTION` is invalid unless `validation.status == PASSED`.
- Any agent that receives invalid or incomplete contracts must stop.

## PR-02: No Field Inference

Statement:
Agents must not infer missing required fields from context, defaults, prior runs, or repository conventions.

Rationale:
Inference creates contract drift and inconsistent behavior across runtimes.

Operational implications:
- Required fields are mandatory and explicit.
- Missing values are errors.
- Placeholders and prompts must map directly to schema fields.

Enforcement expectations:
- Schema `required` fields are strict.
- Prompt contracts must include: Role, Mode, Objective, Files, Config, Constraints, Risk Tolerance.
- Workflows must reject incomplete task input.

## PR-03: No Data Invention

Statement:
Agents must not fabricate values, paths, constraints, validation outcomes, or execution artifacts.

Rationale:
Invented data breaks traceability and undermines auditability.

Operational implications:
- Config paths and artifacts must be user-provided or contract-defined.
- Validation metadata must reflect actual validation events.
- Missing data must trigger stop-and-report behavior.

Enforcement expectations:
- `additionalProperties: false` in contract schema.
- No fallback to guessed plan/config locations.
- No synthetic "success" status without explicit evidence.

## PR-04: No Reactive Fixing

Statement:
Agents must not silently patch malformed contracts or "repair" user intent during execution.

Rationale:
Reactive fixing hides root input issues and creates inconsistent outcomes.

Operational implications:
- Invalid contracts are rejected, not rewritten.
- Clarification requests are mandatory for ambiguous instructions.
- Phase A returns a deterministic verdict; it does not execute.

Enforcement expectations:
- Validation output must classify failure and stop.
- No execution side effects are allowed during validation-only phase.

## PR-05: Configuration/Data Decoupling

Statement:
Configuration declarations must remain separate from execution payload and operational data.

Rationale:
Coupling config with execution state causes brittle behavior and unsafe implicit defaults.

Operational implications:
- `config` is an explicit contract field.
- `files` identifies target artifacts only; it does not imply configuration.
- Agents must consume declared config references only.

Enforcement expectations:
- No hardcoded config path assumptions.
- Config references must be explicit and validated before use.

## PR-06: Model as Architectural Decision

Statement:
Model selection and runtime behavior are architectural decisions and must be explicit in contract/governance, never implicit.

Rationale:
Different runtimes and models behave differently; hidden model assumptions break portability.

Operational implications:
- Agent mode and role are explicit contract controls.
- Prompts must avoid model-specific hidden logic.
- Cross-runtime behavior must be deterministic from contract + governance.

Enforcement expectations:
- Role/mode must be present in every task contract.
- Workflow entry rules cannot depend on implicit LLM interpretation.

## PR-07: Governance Independent from Tooling

Statement:
Governance must be internal to Invoker and must not depend on external temporary tooling state.

Rationale:
Tooling caches and temporary directories are non-authoritative and non-portable.

Operational implications:
- Invoker must remain operational if external helper files are absent.
- Governance documents are declarative references, not runtime infrastructure.
- Validation and execution gates must live in Invoker contracts/schemas/workflows.

Enforcement expectations:
- No runtime dependency on `.claude/`.
- `claude.md` cannot be required for Invoker execution.
