# Kernel Profiles (LITE vs STANDARD vs FULL)

This document explains what changes when you activate a kernel profile.

Key idea:
- Kernel is always the same (`agent/kernel/kernel.yaml`).
- The profile changes what gets enabled/disabled (triggers, skill budget, multi-agent, preload set).

## LITE

Use when: daily quick tasks, minimal ceremony, maximum predictability.

Behavior:
- Trigger engine: OFF (no auto-activation or suggestions)
- Lazy loading: OFF
- Multi-agent orchestration: OFF
- Skill budget: small (target 10-15)
- Safety posture: minimal_strict (kernel baseline governance enforced)

Typical outcomes:
- Agent stays narrow and does not fan out into extra skills.
- You must explicitly name additional skills if needed.

## STANDARD

Use when: structured work, planning and validation, conservative automation.

Behavior:
- Trigger engine: ON, but suggest-only (no auto-inject beyond governance)
- Lazy loading: ON (allowlisted-only)
- Multi-agent orchestration: OFF by default (Inspector/Executor opt-in)
- Skill budget: medium (target ~40)
- Safety posture: full governance overlay + kernel baseline

Typical outcomes:
- Agent can propose skills based on file type/phase, but does not auto-activate.
- Good default for non-trivial changes with controlled guidance.

## FULL

Use when: auditing, rollback discipline, advanced debugging, explicit opt-in automation.

Behavior:
- Trigger engine: ON (deterministic activation + cluster fan-out)
- Lazy loading: ON (full allowlist)
- Multi-agent orchestration: ON (explicit opt-in required)
- Skill budget: higher (target ~65)
- Safety posture: strict_audit + rollback/audit workflows

Typical outcomes:
- More automation and more suggested/activated skills.
- Best for complex tasks where guardrails and deeper tooling are worth the overhead.

## How profile is chosen (resolution order)

1. If `mode_profile` is set in `agent/user_task.yaml`, use it.
2. Else, use per-agent state (if you activated with `--agent-id`):
   - `agent/agent_outputs/runtime/active_profile.<agent-id>.json`
3. Else, use default state:
   - `agent/agent_outputs/runtime/active_profile.json`
4. Else, default to LITE.

## Activation commands (PowerShell)

LITE:
- `.\.venv\Scripts\python.exe agent_tools/activate_kernel.py --profile LITE`

STANDARD:
- `.\.venv\Scripts\python.exe agent_tools/activate_kernel.py --profile STANDARD`

FULL:
- `.\.venv\Scripts\python.exe agent_tools/activate_kernel.py --profile FULL`

Per-agent:
- `.\.venv\Scripts\python.exe agent_tools/activate_kernel.py --profile LITE --agent-id agentA`
