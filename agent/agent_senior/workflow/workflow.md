# Workflow - Senior Agent (Regulatory Aligned)

## Step 1: Contract Intake
**Role:** agent_senior
1. Read `agent/user_task.yaml`.
2. Validate it against `agent/agent_protocol/schemas/user_task.schema.yaml`.
3. If schema validation fails, stop and return explicit validation errors.
4. Do not infer missing fields and do not mutate the contract.

## Step 1.5: Kernel Profile Resolve
**Role:** agent_senior
1. Ensure a kernel profile is active (use `agent_tools/activate_kernel.py`).
2. Resolve effective profile via `agent_tools/mode_selector.py`.

## Step 2: Phase Gate
**Role:** agent_senior
1. If `phase == A_CONTRACT_VALIDATION`, perform contract checks only and stop with verdict.
2. If `phase == B_EXECUTION`, continue only when `validation.status == PASSED`.
3. If execution gate fails, stop immediately.

## Step 3: Context and Skill Preparation
**Role:** agent_senior
1. Run `agent_tools/load_static_context.py`.
2. Load `agent/skills/_index.yaml`.
3. Use `_trigger_engine.yaml` for deterministic shortlist.
4. Load `.meta.yaml` and `.md` only for selected skills.

## Step 4: Execution
**Role:** agent_senior
1. Execute only within `objective`, `files`, `config`, and `constraints`.
2. Do not assume config paths; consume only declared config sources.
3. Do not create artifacts that were not requested by role contract/workflow.

## Step 5: Verification and Reporting
**Role:** agent_senior
1. Verify outputs with explicit checks.
2. Confirm governance compliance.
3. Persist required outputs to `agent/agent_outputs/`.
