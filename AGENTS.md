# AGENTS.md (Tinker Portable Contract)

This repository uses a thin-skill + canonical-wrapper model.

## Core Model
- Skills source of truth:
  - **Source**: `agent/skills/**/*.meta.yaml`
  - **Compiled Index**: `agent/skills/_index.yaml`
  - **Interface**: `agent/skills/**/*.md`
- Execution source of truth:
  - `agent_tools/run_wrapper.py`
  - `agent_tools/wrappers/*.py`

## Skill Loading Protocol
1. **Compile**: `python agent_tools/compile_registry.py` (if needed).
2. Load `agent/skills/_index.yaml` to shortlist.
3. Load `.md` bodies only for invoked skills.
4. Never bulk-load all skill bodies.

## Runtime Bootstrap
1. Read `.clinerules` and `agent/rules/agent_rules.md`.
2. Read `agent_framework_config.yaml`.
3. Generate or refresh static context when needed:
   - `python agent_tools/load_static_context.py`
4. Use `agent/agent_outputs/context.json` as compact index; load heavy files on demand.

## Canonical Tooling
- Registry Compilation (SSOT):
  - `python agent_tools/compile_registry.py`
- Wrapper execution:
  - `python agent_tools/run_wrapper.py --skill <skill> --args-file <json>`
- Schema validation:
  - `python agent_tools/schema_validator.py <file> --type <type>`
  - Supported aliases include `plan` -> `task_plan` and `config` -> `system_config`.
- Full context assembly (optional fast-start context):
  - `python agent_tools/load_full_context.py --task-plan <path> --system-config <path> --summary <path>`
- Kernel profile state:
  - `python agent_tools/activate_kernel.py --profile LITE|STANDARD|FULL`
  - `python agent_tools/mode_selector.py --write-state` (resolve + persist active profile)
  - `python agent_tools/kernel_guard.py --prefer active|task` (non-interactive mismatch handling)

## Optional Plan Docs (Review/Handoff)
- Plan docs are optional helper artifacts for human review or cross-agent handoff.
- They are not required for normal wrapper-first execution.
- Canonical locations:
  - Active: `agent/agent_outputs/plans/plan_active/`
  - Archive: `agent/agent_outputs/plans/archive/`
- Utility:
  - `python agent_tools/plan_doc.py init --id <id> --title <title> --objective <text>`
  - `python agent_tools/plan_doc.py validate --file agent/agent_outputs/plans/plan_active/<id>.yaml`
  - `python agent_tools/plan_doc.py handoff --file <path> --to <target> --notes <text>`

## Context Hygiene
- Keep context minimal and task-scoped.
- Prefer on-demand analysis files:
  - `agent/analysis/treemap.md`
  - `agent/analysis/dependencies_report.md`

## Portability Rules
- Keep framework assets under `agent/`, `agent_tools/`, and `instructions/`.
- Do not move skill markdown/meta files as part of compatibility layering.
- If a host runtime needs per-skill `SKILL.md`, regenerate wrappers via:
  - `python agent_tools/generate_skill_wrappers.py`

## Compatibility
- `agent.md` is a compatibility alias that points to this file.
