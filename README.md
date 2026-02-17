# Tinker

## Portable, Wrapper-First Toolkit for Agentic Workflows

Tinker is a deterministic orchestration layer for AI-assisted execution.
It turns any repository into an agent-ready workspace with governance,
skill management, and controlled execution — without modifying your source code.

### Core Principles

- **Wrappers are the execution source of truth** (`agent_tools/`).
- **Skills are thin interfaces**, not business-logic containers (`agent/skills/`).
- **Governance is centralized and minimal** (`.clinerules`, `agent/rules/agent_rules.md`).
- **Kernel profiles are capability allowlists**, not role orchestration.
- **Configuration drives structure** (`agent_framework_config.yaml`).

---

## Quick Start

### One-Command Initialization

Say this in the chat to initialize a full session:

```text
Initiate Tinker. Kernel FULL
```

The agent will automatically execute the full initialization sequence:

1. Read governance rules
2. Activate the Kernel profile (FULL / STANDARD / LITE)
3. Compile the Skill Registry (SSOT)
4. Load static context
5. Verify mode state

To start with a different profile:

```text
Initiate Tinker. Kernel LITE
```

### Typical Workflow

1. **Initialize** — `Initiate Tinker. Kernel FULL`
2. **Define Task** — Edit `agent/user_task.yaml` (your task contract)
3. **Execute** — Say `Tinker: run`
4. **Validate** — Review output files and code changes
5. **Save** — Say `commit` or `sync` or `commit and sync`

---

## Project Structure

```
tinker/
├── agent/                          # Agent workspace (autonomous, writable)
│   ├── skills/                     # Skill definitions (*.meta.yaml + *.md)
│   │   ├── _index.yaml             # Auto-compiled skill index (DO NOT EDIT)
│   │   ├── _trigger_engine.yaml    # Auto-compiled trigger rules (DO NOT EDIT)
│   │   └── <cluster>/              # Skills organized by cluster
│   ├── profiles/                   # Kernel profiles
│   │   ├── _base.yaml              # Base profile (inherited by all)
│   │   ├── lite.yaml               # Minimal capabilities
│   │   ├── standard.yaml           # Standard capabilities
│   │   └── full.yaml               # Full capabilities
│   ├── rules/                      # Governance rules
│   │   └── agent_rules.md          # Global governance document
│   ├── user_task.yaml              # Active task contract
│   ├── agent_protocol/             # Schemas and protocol definitions
│   ├── analysis/                   # Gitignored analysis artifacts
│   │   ├── treemap.md              # File tree (on-demand)
│   │   └── dependencies_report.md  # Dependency graph (on-demand)
│   └── agent_outputs/              # Plans, reports, context.json
│
├── agent_tools/                    # Execution scripts (source of truth)
│   ├── chat_shortcuts.py           # Chat command router (init, commit, sync)
│   ├── compile_registry.py         # SSOT registry compiler
│   ├── load_static_context.py      # Context generator → context.json
│   ├── activate_kernel.py          # Profile activation
│   ├── run_wrapper.py              # Wrapper execution engine
│   ├── wrappers/                   # Canonical skill wrappers
│   └── ...                         # Validators, analyzers, utilities
│
├── instructions/                   # Model-specific instruction layers
│   ├── chat/                       # Chat bootstrap (trigger_chat.md)
│   ├── claude/                     # Claude-specific overrides
│   └── model_agnostic/             # Universal instructions
│
├── agent_framework_config.yaml     # Central configuration (paths, profiles, limits)
├── architecture.md                 # Architecture specification
└── install_tinker.py               # Framework installer for other projects
```

---

## Key Concepts

### Single Source of Truth (SSOT)

Skills are defined in `.meta.yaml` files. The `compile_registry.py` script
scans all `.meta.yaml` files and generates two derived artifacts:

- `_index.yaml` — Master skill index (sorted by priority)
- `_trigger_engine.yaml` — Extension/phase/error trigger rules

**Never edit these generated files manually.**

### Kernel Profiles

Profiles define what capabilities are available during a session:

| Profile    | Use Case                    |
| ---------- | --------------------------- |
| `LITE`     | Minimal, read-only tasks    |
| `STANDARD` | Normal development work     |
| `FULL`     | Full access, self-modification |

Profiles use recursive inheritance: `FULL` → `STANDARD` → `LITE` → `_base`.

### Config-Driven Paths

All structural paths (analysis files, output paths, exclusions) are defined in
`agent_framework_config.yaml`. If the project structure changes, update the
config — not the scripts.

### Self-Improvement

- **`skill_builder`** — Agent can specify and generate new skills
- **`skill_merger`** — Agent can consolidate and clean up skills (garbage collection)

Both are governed by safeguards: core skills are protected from modification.

---

## Chat Commands

| Command                   | Action                                      |
| ------------------------- | ------------------------------------------- |
| `Initiate Tinker`         | Full initialization (default: Kernel FULL)  |
| `Initiate Tinker. Kernel LITE` | Initialize with LITE profile           |
| `Tinker: run`             | Execute task from `user_task.yaml`          |
| `Tinker: validate`        | Validate task contract                      |
| `commit`                  | Git checkpoint                              |
| `sync`                    | Push to remote                              |
| `commit and sync`         | Checkpoint + push                           |

---

## Validation Tools

| Tool                          | Purpose                       |
| ----------------------------- | ----------------------------- |
| `schema_validator.py`         | Generic YAML/JSON validation  |
| `validate_message.py`         | Message format validation     |
| `validate_skill_metadata.py`  | Skill `.meta.yaml` validation |
| `audit_registry.py`           | Registry integrity audit      |
| `verify_profiles.py`          | Profile inheritance checks    |
| `simulate_execution.py`       | Dry-run execution testing     |

---

## Installing Tinker in Other Projects

```bash
python install_tinker.py --target /path/to/project
```

This copies the framework files, merges `.gitignore` and `requirements.txt`,
and skips generated artifacts (they are regenerated in the target project).

---

**Version:** 3.1.0
**Last Updated:** 2026-02-17
**Status:** Phase 1-3 Complete — Self-Improving Architecture
