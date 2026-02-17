# Tinker

## Minimal, Wrapper-First Toolkit for Agentic Workflows

Tinker is a portable toolkit for deterministic AI-assisted execution.

Core principles:
- Wrappers/scripts in `agent_tools/` are the execution source of truth.
- Skills in `agent/skills/` are thin interfaces, not business-logic containers.
- Governance is centralized and minimal (`.clinerules`, `agent/rules/agent_rules.md`).
- Kernel profiles are capability allowlists, not role orchestration.

## Quick Start

1. Initialize Registry (SSOT)
- `./.venv/Scripts/python.exe agent_tools/compile_registry.py`

2. Activate profile
- `./.venv/Scripts/python.exe agent_tools/activate_kernel.py --profile LITE`

3. Refresh static context
- `./.venv/Scripts/python.exe agent_tools/load_static_context.py`

4. Prepare task contract
- Edit `agent/user_task.yaml`
- Optional helper: `./.venv/Scripts/python.exe agent_tools/user_task_builder.py --help`

5. Execute via wrapper-first flow
- `./.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill <skill> --args-file <args.json>`

## Key Paths

- **Source of Truth**: `agent/skills/**/*.meta.yaml`
- **Compiled Index**: `agent/skills/_index.yaml` (DO NOT EDIT)
- **Compiled Triggers**: `agent/skills/_trigger_engine.yaml` (DO NOT EDIT)
- Registry Compiler: `agent_tools/compile_registry.py`
- Canonical wrappers: `agent_tools/wrappers/*.py`
- Wrapper runner: `agent_tools/run_wrapper.py`
- User task schema: `agent/agent_protocol/schemas/user_task.schema.yaml`
- Optional plan-doc schema: `agent/agent_protocol/schemas/plan_doc.schema.yaml`

## Validation and Safety

- Generic schema validator:
  - `./.venv/Scripts/python.exe agent_tools/schema_validator.py <file> --type <type>`
- Message validator:
  - `./.venv/Scripts/python.exe agent_tools/validate_message.py <file> --type <type>`
- Execution simulator (test-oriented):
  - `./.venv/Scripts/python.exe agent_tools/simulate_execution.py <task_plan.json>`

## Optional Collaboration Artifacts

Plan docs are optional review/handoff artifacts:
- Active: `agent/agent_outputs/plans/plan_active/`
- Archive: `agent/agent_outputs/plans/archive/`
- Utility: `./.venv/Scripts/python.exe agent_tools/plan_doc.py --help`

## Current Status (2026-02-16)

**Phase 1, 2, 3 Complete: Self-Improving Architecture**

1.  **Single Source of Truth (SSOT)**:
    -   Skills defined in `.meta.yaml` (self-contained triggers).
    -   `compile_registry.py` automates index generation.
2.  **Profile Inheritance**:
    -   `_base.yaml` + recursive inheritance (`inherits: ...`).
    -   `FULL` -> `STANDARD` -> `LITE`.
3.  **Self-Improvement**:
    -   `skill_builder`: Agent can specify and generate new skills.
    -   `skill_merger`: Agent can consolidate and clean up skills (Garbage Collection).

Validation status:
- Core architecture operational.
- Auto-discovery and compilation active.
- Self-modification safeguards in place (Core skills protected).
