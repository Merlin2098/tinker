# User Fault Heuristic

## Version

2.0.0

## Scope

Reusable classification aid for Phase A contract validation.

---

## 1. Purpose

Classify whether a failure is caused by user-provided contract/input issues
or by system/runtime faults.

---

## 2. Classification rules

Evaluate in order and stop at first match.

### Rule 1 - Missing required contract data

| Signal | Classification |
|--------|---------------|
| Missing required field from user task schema | `USER_INPUT_MISMATCH` |
| Empty `objective` or placeholder text | `USER_INPUT_MISMATCH` |
| Empty `files` or empty `config.sources` | `USER_INPUT_MISMATCH` |

### Rule 2 - Contract contradiction

| Signal | Classification |
|--------|---------------|
| `phase: B_EXECUTION` with `validation.status != PASSED` | `USER_INPUT_MISMATCH` |
| `role: executor` or `role: junior` with `phase: A_CONTRACT_VALIDATION` | `USER_INPUT_MISMATCH` |
| Constraints conflict with objective | `AMBIGUOUS` |

### Rule 3 - Input format mismatch

| Signal | Classification |
|--------|---------------|
| Declared config file is unreadable or malformed | `USER_INPUT_MISMATCH` |
| Declared file path does not exist | `USER_INPUT_MISMATCH` |
| Declared data format is incompatible with task objective | `USER_INPUT_MISMATCH` |

### Rule 4 - Runtime/system evidence

| Signal | Classification |
|--------|---------------|
| Traceback points to application implementation defect | `SYSTEM_ISSUE` |
| System dependency or environment fault outside user contract | `SYSTEM_ISSUE` |

### Rule 5 - Default

| Condition | Classification |
|-----------|---------------|
| Contract is complete and coherent | `CLEAR_TASK` |
| Intent cannot be determined from explicit fields | `AMBIGUOUS` |

---

## 3. Outcomes

| Classification | Action |
|---------------|--------|
| `USER_INPUT_MISMATCH` | Stop and return explicit fix request. |
| `AMBIGUOUS` | Stop and request clarification. |
| `SYSTEM_ISSUE` | Continue to system-level handling workflow. |
| `CLEAR_TASK` | Continue according to phase gate. |

---

## 4. Response format

```text
CLASSIFICATION: <USER_INPUT_MISMATCH | AMBIGUOUS | SYSTEM_ISSUE | CLEAR_TASK>
RULE_MATCHED: <rule id>
EVIDENCE: <what was checked>
SUGGESTION: <next action>
```
