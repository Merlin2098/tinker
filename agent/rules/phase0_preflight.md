# Phase A - Contract Validation

## Version

2.0.0

## Scope

Applies to: senior, inspector.
Execution agents (executor, junior) consume only `B_EXECUTION` tasks.

---

## 1. Purpose

Phase A validates task contract completeness and consistency before execution.
It prevents implicit assumptions, inferred fields, and invalid execution starts.

---

## 2. Activation

Phase A activates only when:

| Condition | Example |
|-----------|---------|
| `phase` is `A_CONTRACT_VALIDATION` | `phase: A_CONTRACT_VALIDATION` |

No objective-based implicit activation is allowed.

---

## 3. Phase A steps

### Step A.1 - Contract schema validation

1. Load `agent/user_task.yaml`.
2. Validate against `agent/agent_protocol/schemas/user_task.schema.yaml`.
3. Reject missing required fields and unknown properties.

### Step A.2 - Deterministic consistency checks

1. Verify role/mode/phase compatibility.
2. Verify `config.sources` are explicit and non-empty.
3. Verify referenced files/configs exist when required by task type.
4. Apply `agent/rules/user_fault_heuristic.md` for classification support.

### Step A.3 - Verdict

| Outcome | Action |
|---------|--------|
| `FAILED` | Stop. Return explicit validation errors. |
| `PASSED` | Update validation metadata and allow Phase B. |

Phase A does not execute code changes.

---

## 4. Constraints

- No execution side effects.
- No inferred defaults.
- No artifact generation beyond validation output.
- Minimal context loading.

---

## 5. Output format

```text
PHASE A RESULT: <PASSED | FAILED>
VALIDATION_STATUS: <PENDING | PASSED | FAILED>
EVIDENCE: <checks performed>
DETAILS: <missing/invalid fields or pass confirmation>
NEXT_STEP: <remain in A or proceed to B_EXECUTION>
```
