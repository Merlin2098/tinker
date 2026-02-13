# AGENTS.md (Tinker Portable Contract)

This repository uses a thin-skill + canonical-wrapper model.

## Core Model
- Skills source of truth:
  - Layer 1: `agent/skills/_index.yaml`
  - Layer 2: `agent/skills/<category>/<skill>.meta.yaml`
  - Layer 3: `agent/skills/<category>/<skill>.md`
- Execution source of truth:
  - `agent_tools/run_wrapper.py`
  - `agent_tools/wrappers/*.py`

## Skill Loading Protocol
1. Load `agent/skills/_index.yaml` to shortlist.
2. Load only relevant `.meta.yaml` files.
3. Load `.md` bodies only for invoked skills.
4. Never bulk-load all skill bodies.

## Runtime Bootstrap
1. Read `.clinerules` and `agent/rules/agent_rules.md`.
2. Read `agent_framework_config.yaml`.
3. Generate or refresh static context when needed:
   - `python agent_tools/load_static_context.py`
4. Use `agent/agent_outputs/context.json` as compact index; load heavy files on demand.

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
