# Skill: Debugger Orchestrator

## Purpose
Provide a deterministic debugging workflow that avoids random fixes and ensures every bug investigation ends with verifiable evidence.

## Use This Skill When
- A failure has unclear origin.
- Multiple symptoms may share the same root cause.
- A fix is needed with regression protection.
- You need to structure debugging work for another agent.

## Do Not Use This Skill When
- The issue is purely cosmetic and already understood.
- A validated fix is already specified in an approved task plan.

## Required Inputs
- Failing symptom (error, traceback, incorrect output, unstable behavior).
- Relevant files, logs, and execution context.
- Expected behavior (acceptance criteria).

## Workflow
1. Triage
- Classify severity and blast radius.
- Identify whether this is a data issue, code issue, config issue, or environment issue.

2. Reproduce
- Create a minimal reproducible scenario.
- Lock inputs and execution path to remove noise.
- Record exact command and observed output.

3. Isolate
- Trace call path and state transitions around the failure.
- Identify first bad state, not just final crash location.
- Build 1-2 hypotheses and test each with evidence.

4. Fix
- Apply the smallest change that resolves the proven root cause.
- Avoid unrelated refactors during incident resolution.

5. Verify
- Re-run the reproduction case.
- Run targeted checks for neighboring behavior.
- Confirm no protected files or out-of-scope components were changed.

6. Regression-proof
- Add or update tests to prevent recurrence.
- Document failure signature and guard condition.

## Output Contract
- Root cause statement with evidence.
- Change summary linked to files touched.
- Verification results (before/after).
- Regression test list added or updated.

## Guardrails
- Never claim success without re-running verification.
- Never mark a hypothesis as root cause without direct evidence.
- Prefer deterministic checks over manual confidence.
