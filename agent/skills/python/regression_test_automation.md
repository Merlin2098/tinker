# Skill: Regression Test Automation

## Purpose
Build and maintain automated regression checks so fixes and feature changes do not reintroduce known failures.

## Use This Skill When
- A bug fix is being delivered.
- A high-risk module was modified.
- You need confidence for repeated releases.
- Flaky or unstable tests are impacting trust.

## Inputs
- Change scope (files and behavior affected).
- Existing test suite and execution command.
- Known historical failures or edge cases.

## Workflow
1. Scope Mapping
- Map modified files to impacted behaviors.
- Select minimal critical regression scenarios first.

2. Baseline Definition
- Define expected outputs and invariants.
- Reuse production-like fixtures where possible.

3. Suite Construction
- Add targeted regression tests for fixed defects.
- Add smoke subset for fast validation gates.
- Keep naming explicit: test_<component>_<regression_id>.

4. Execution Strategy
- Run fast subset first, then broader suite.
- Record deterministic command(s) and environment.
- Capture pass/fail counts and failure signatures.

5. Flakiness Control
- Detect non-deterministic tests.
- Isolate flaky cases and require stabilization before gate promotion.

6. Gate Integration
- Wire regression suite into validation phase.
- Fail the gate when critical regression cases fail.

## Output Contract
- Regression test inventory (new/updated tests).
- Execution command list.
- Pass/fail report with failing test identifiers.
- Promotion decision: pass, block, or stabilize-first.

## Guardrails
- Do not add broad low-value tests; prioritize defect-linked coverage.
- Every bug fix must have at least one regression guard.
- Do not hide flaky tests; classify and track them explicitly.
