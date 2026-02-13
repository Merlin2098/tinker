# Tinker

## Minimal, Wrapper-First Toolkit for Agentic Workflows

Tinker is a portable toolkit for deterministic AI-assisted execution.

Core principles:
- Wrappers/scripts in `agent_tools/` are the execution source of truth.
- Skills in `agent/skills/` are thin interfaces, not business-logic containers.
- Governance is centralized and minimal (`.clinerules`, `agent/rules/agent_rules.md`).
- Kernel profiles are capability allowlists, not role orchestration.

## Quick Start

1. Activate profile
- `./.venv/Scripts/python.exe agent_tools/activate_kernel.py --profile LITE`

2. Refresh static context
- `./.venv/Scripts/python.exe agent_tools/load_static_context.py`

3. Prepare task contract
- Edit `agent/user_task.yaml`
- Optional helper: `./.venv/Scripts/python.exe agent_tools/user_task_builder.py --help`

4. Execute via wrapper-first flow
- `./.venv/Scripts/python.exe agent_tools/run_wrapper.py --skill <skill> --args-file <args.json>`

## Key Paths

- Skills index: `agent/skills/_index.yaml`
- Trigger engine: `agent/skills/_trigger_engine.yaml`
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

## Current Status (2026-02-13)

Phase 2 rework is active and has delivered these checkpoints:
- Thin-skill + canonical-wrapper migration for completed clusters (`formats/*`, `io/*`, `file_exploration/*`).
- Reduced template surface to:
  - `agent/task_templates/chat/user_task_template.yaml`
  - `agent/task_templates/user_task_dummies_es.yaml`
- Optional plan-doc tooling:
  - `agent_tools/plan_doc.py`
  - `agent/agent_protocol/schemas/plan_doc.schema.yaml`
- `agent_tools` simplification and consolidation:
  - Shared schema helpers: `agent_tools/_schema_utils.py`
  - Shared profile state helpers: `agent_tools/_profile_state.py`
  - Shared context/path helpers: `agent_tools/_context_common.py`
  - Shared repo-root helper: `agent_tools/_repo_root.py`
  - Modernized CLIs:
    - `agent_tools/load_full_context.py`
    - `agent_tools/config_validator.py`
    - `agent_tools/analyze_dependencies.py`
    - `agent_tools/treemap.py`
  - Simplified wrapper registry wiring in `agent_tools/run_wrapper.py`

Validation status:
- Core updated tools compile and run via `.venv` Python.
- Wrapper generation and skill metadata checks pass in dry-run/advisory mode.
