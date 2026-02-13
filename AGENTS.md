# AGENTS.md (Template for portable skill-based repos)

This repository uses a skill framework under `agent/skills/` and role workflows under `agent/`.

## Skills

A skill is an instruction artifact stored as:
- Layer 1 index: `agent/skills/_index.yaml`
- Layer 2 metadata: `agent/skills/<category>/<skill_name>.meta.yaml`
- Layer 3 body: `agent/skills/<category>/<skill_name>.md`

### Skill source of truth
- Use `agent/skills/_index.yaml` as the canonical skill catalog.
- Use `agent/skills/_trigger_engine.yaml` for deterministic trigger rules.
- Use `agent/skills/skills_registry.yaml` when additional registry fields are needed.

### How to activate skills
- Explicit trigger: if the user names a skill, load it.
- Intent trigger: if user intent matches trigger rules in `_trigger_engine.yaml`, activate candidate skills.
- Governance overlay: governance skills are always active when defined by your trigger engine/rules.

### Skill loading protocol (must follow)
1. Load Layer 1 (`_index.yaml`) to shortlist.
2. Load only relevant Layer 2 headers (`.meta.yaml`) for shortlisted skills.
3. Load Layer 3 body (`.md`) only for skills being executed.
4. Do not bulk-load all skill bodies.

### Missing or blocked skill files
- If a requested skill file is missing or unreadable, state it briefly and continue with best-effort fallback.

## Roles

Role contracts and workflows live under:
- `agent/agent_senior/`
- `agent/agent_executor/`
- `agent/agent_inspector/`
- `agent/agent_junior/`

Task routing input is defined in `agent/user_task.yaml` (role, mode, objective, files, constraints, phase, hints).

## Runtime bootstrap

Before substantial work:
1. Read governance rules from `.clinerules` and `agent/rules/agent_rules.md`.
2. Read `agent_framework_config.yaml`.
3. If terminal access exists, run `python agent_tools/load_static_context.py` and use `agent/agent_outputs/context.json`.
4. If terminal access does not exist, read required files directly on demand.

## Context hygiene

- Keep context minimal: load only files required for current task.
- Prefer on-demand project analysis files:
  - `agent/analysis/treemap.md`
  - `agent/analysis/dependencies_report.md`
- Never create ad-hoc parallel instruction systems outside this framework.

## Portability rules

- Keep framework files under `agent/` and `agent_tools/`.
- Do not move existing skill markdown/meta files just to satisfy another format.
- If a host environment expects `SKILL.md` per skill, add wrappers in parallel (non-breaking), but keep current files as source of truth.
