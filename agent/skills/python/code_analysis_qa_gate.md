# Skill: Code Analysis and QA Gate

## Purpose
Define and run a deterministic code-quality gate before merge or release, combining static analysis signals with clear pass/fail thresholds.

## Use This Skill When
- You need objective QA criteria for changed code.
- A PR/release requires quality evidence.
- Teams need consistent quality checks across agents.

## Inputs
- Target file set or module scope.
- Required quality checks (lint, typing, tests, complexity, security).
- Threshold policy (blockers vs warnings).

## QA Gate Model
1. Structural Checks
- Syntax validity.
- Import and dependency health.
- Basic project conventions.

2. Static Quality Checks
- Lint violations (style and correctness).
- Type consistency checks.
- Complexity and maintainability hotspots.

3. Behavioral Checks
- Critical tests.
- Regression subset.

4. Decision
- PASS: no blocking findings.
- CONDITIONAL: warnings only, with explicit acceptance.
- FAIL: one or more blocking findings.

## Workflow
1. Define gate criteria and severity mapping.
2. Run checks in deterministic order.
3. Normalize findings into a single report.
4. Fail fast on blockers; continue collecting warnings.
5. Emit final gate verdict with remediation list.

## Output Contract
- QA gate report containing:
  - check set executed
  - blockers and warnings
  - affected files
  - final verdict
- Actionable remediation steps for each blocker.

## Guardrails
- Do not merge style and defect severity into one bucket.
- Never pass a gate with unresolved blockers.
- Keep threshold policy explicit and versioned per project.
