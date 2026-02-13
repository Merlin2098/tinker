# Debugging Fan-Out Limits

## Version

2.0.0

## Scope

Applies to all agents during `B_EXECUTION`.

---

## 1. Policy

- Debugging cluster activation is never automatic.
- Debugging depth must be explicit and bounded.
- No debugging is allowed during `A_CONTRACT_VALIDATION`.

---

## 2. Gates

### Gate 1 - Initial response (default)

- Inspect the immediate failure signal.
- Apply `user_fault_heuristic.md`.
- Return one bounded fix proposal.

### Gate 2 - Targeted investigation

Requires explicit user request for deeper debugging.

- Load `systematic_debugging`.
- Limit scope to declared files and direct dependencies.

### Gate 3 - Deep investigation

Requires explicit user confirmation after Gate 2.

- Load `root_cause_tracing` (after `systematic_debugging`).
- Expand only when evidence justifies scope extension.

---

## 3. Hard limits

- Maximum debug iterations before reconfirmation: 2.
- Junior agent remains Gate 1 only.
- No deep debugging for contracts with `risk_tolerance: LOW` unless user overrides explicitly.

---

## 4. Enforcement

- Respect skill metadata dependencies and bindings.
- Respect phase gate (`A` blocks debugging execution paths).
- Stop and escalate when limits are reached.
