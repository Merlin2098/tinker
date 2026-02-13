# Workflow - Agent Executor (Regulatory Aligned)

## Step 1: Contract Intake
**Role:** agent_executor
1. Read `agent/user_task.yaml`.
2. Validate against `agent/agent_protocol/schemas/user_task.schema.yaml`.
3. Reject incomplete contracts. No inference allowed.

## Step 1.5: Kernel Profile Resolve
**Role:** agent_executor
1. Ensure a kernel profile is active (use `agent_tools/activate_kernel.py`).
2. Resolve effective profile via `agent_tools/mode_selector.py`.

## Step 2: Execution Gate
**Role:** agent_executor
1. Executor accepts only `phase == B_EXECUTION`.
2. Require `validation.status == PASSED` before any action.
3. If gate fails, stop immediately.

## Step 3: Context and Inputs
**Role:** agent_executor
1. Run `agent_tools/load_static_context.py`.
2. Resolve input artifacts from `config.sources` only.
3. Do not assume default paths for plan/config artifacts.

## Step 4: Controlled Execution
**Role:** agent_executor
1. Execute only approved actions for declared files.
2. Load skills through Layer 1 -> Layer 2 -> Layer 3.
3. Do not create unrequested artifacts or inferred tasks.

## Step 5: Verification and Reports
**Role:** agent_executor
1. Run explicit verification checks.
2. Persist required reports to `agent/agent_outputs/`.
3. Return final status with evidence.
