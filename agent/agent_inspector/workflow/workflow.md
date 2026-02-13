# Workflow - Agent Inspector (Regulatory Aligned)

## Step 1: Contract Intake
**Role:** agent_inspector
1. Read `agent/user_task.yaml`.
2. Validate against `agent/agent_protocol/schemas/user_task.schema.yaml`.
3. Reject incomplete or ambiguous contracts without inference.

## Step 1.5: Kernel Profile Resolve
**Role:** agent_inspector
1. Ensure a kernel profile is active (use `agent_tools/activate_kernel.py`).
2. Resolve effective profile via `agent_tools/mode_selector.py`.

## Step 2: Phase Gate
**Role:** agent_inspector
1. `A_CONTRACT_VALIDATION`: issue explicit validation verdict and stop.
2. `B_EXECUTION`: allow planning only if `validation.status == PASSED`.
3. If gate fails, stop.

## Step 3: Context and Skill Preparation
**Role:** agent_inspector
1. Run `agent_tools/load_static_context.py`.
2. Load `agent/skills/_index.yaml` and `_trigger_engine.yaml`.
3. Load candidate skill headers before bodies.

## Step 4: Planning
**Role:** agent_inspector
1. Plan only within declared scope (`objective`, `files`, `config`, `constraints`).
2. Do not assume plan/config locations; use explicit config sources.
3. Produce deterministic plan artifacts only when requested.

## Step 5: Validation and Persistence
**Role:** agent_inspector
1. Validate generated artifacts against applicable schemas.
2. Confirm protected-file and scope compliance.
3. Persist outputs under `agent/agent_outputs/`.
