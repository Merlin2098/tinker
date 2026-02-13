# Workflow - Junior Agent (Regulatory Aligned)

## Step 1: Contract Intake
**Role:** agent_junior
1. Read `agent/user_task.yaml`.
2. Validate against `agent/agent_protocol/schemas/user_task.schema.yaml`.
3. Ensure `role == junior` and `mode == IMPLEMENT_ONLY`.
4. Reject incomplete contracts. No inference allowed.

## Step 1.5: Kernel Profile Resolve
**Role:** agent_junior
1. Ensure a kernel profile is active (use `agent_tools/activate_kernel.py`).
2. Resolve effective profile via `agent_tools/mode_selector.py`.

## Step 2: Execution Gate
**Role:** agent_junior
1. Junior accepts only `phase == B_EXECUTION`.
2. Require `validation.status == PASSED`.
3. If validation is not passed, stop and escalate.

## Step 3: Scoped Execution
**Role:** agent_junior
1. Operate only on declared `files`.
2. Consume only declared `config.sources`.
3. Do not create extra artifacts or perform deep analysis.

## Step 4: Verification and Report
**Role:** agent_junior
1. Verify objective completion inside declared scope.
2. Confirm governance compliance.
3. Report files changed and checks performed.
