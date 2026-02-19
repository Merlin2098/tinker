# Tinker Architecture

## LLM-Friendly Specification (v3.1.0)

---

## System Overview

Tinker is a deterministic orchestration layer governing AI agent execution.
It transforms any repository into an agent-ready workspace without modifying
application source code.

### Core Capabilities

- **Explicit task contracts** — All work defined via `user_task.yaml`
- **Kernel operational modes** — Inheritance-based capability profiles
- **Self-organizing registry** — Auto-compiled from `.meta.yaml` definitions
- **Self-improvement** — Agent can build and merge skills autonomously
- **Deterministic trigger evaluation** — Extension/phase/error matching
- **Lazy-loaded skills** — Minimal context activation
- **Config-driven structure** — Paths and limits in `agent_framework_config.yaml`
- **Model-family instruction overrides** — Claude, GPT, etc.

---

## Initialization Flow

```
User says: "Initiate Tinker. Kernel FULL"
                    │
                    ▼
        ┌───────────────────────┐
        │  chat_shortcuts.py    │  (Orchestrator)
        │  intent: init         │
        └───────────┬───────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
┌─────────┐  ┌────────────┐  ┌──────────────┐
│ activate │  │ compile    │  │ load_static  │
│ _kernel  │  │ _registry  │  │ _context     │
│   .py    │  │   .py      │  │   .py        │
└────┬─────┘  └─────┬──────┘  └──────┬───────┘
     │              │                │
     ▼              ▼                ▼
  Profile       _index.yaml      context.json
  State         _trigger_engine
                   .yaml
                    │
                    ▼
        ┌───────────────────────┐
        │  mode_selector.py     │  (Verification)
        │  --read-state         │
        └───────────────────────┘
                    │
                    ▼
            ✅ Session Ready
```

---

## Execution Flow

```
user_task.yaml
        │
        ▼
  Kernel Resolution ──→ Profile loaded (LITE/STANDARD/FULL)
        │
        ▼
  Trigger Engine ──────→ Match extensions, phases, errors
        │
        ▼
  Instruction Layer ───→ Model-specific overrides applied
        │
        ▼
  Skill Activation ────→ Lazy-load matched skills
        │
        ▼
  Wrapper Execution ───→ agents/tools/wrappers/*.py
        │
        ▼
  Agent Output ────────→ agents/logic/agent_outputs/
```

---

## Component Map

### Governance Layer

| Component                    | Path                           | Role                              |
| :--------------------------- | :----------------------------- | :-------------------------------- |
| Global Rules                 | `.clinerules`                  | Top-level agent constraints       |
| Agent Rules                  | `agents/logic/rules/agent_rules.md`   | Governance, security, policies    |
| Semantic Triggers            | `agent_rules.md` §10          | Natural language → command mapping|

### Registry Layer (SSOT)

| Component                    | Path                                | Role                          |
| :--------------------------- | :---------------------------------- | :---------------------------- |
| Skill Definitions            | `agents/logic/skills/**/*.meta.yaml`       | Source of truth (human-authored) |
| Compiled Index               | `agents/logic/skills/_index.yaml`          | Auto-generated skill directory |
| Compiled Triggers            | `agents/logic/skills/_trigger_engine.yaml` | Auto-generated trigger rules  |
| Registry Compiler            | `agents/tools/compile_registry.py`   | SSOT compilation engine       |

### Kernel Layer

| Component                    | Path                           | Role                              |
| :--------------------------- | :----------------------------- | :-------------------------------- |
| Base Profile                 | `agents/logic/profiles/_base.yaml`    | Shared defaults (inherited)       |
| LITE Profile                 | `agents/logic/profiles/lite.yaml`     | Minimal capabilities              |
| STANDARD Profile             | `agents/logic/profiles/standard.yaml` | Normal development                |
| FULL Profile                 | `agents/logic/profiles/full.yaml`     | Full access + self-modification   |
| Profile Activator            | `agents/tools/activate_kernel.py` | Writes active profile state     |

### Execution Layer

| Component                    | Path                              | Role                           |
| :--------------------------- | :-------------------------------- | :----------------------------- |
| Wrapper Runner               | `agents/tools/run_wrapper.py`      | Skill execution engine         |
| Canonical Wrappers           | `agents/tools/wrappers/*.py`       | Deterministic skill implementations |
| Chat Router                  | `agents/tools/chat_shortcuts.py`   | Intent routing (init/commit/sync) |

### Context Layer

| Component                    | Path                                    | Role                        |
| :--------------------------- | :-------------------------------------- | :-------------------------- |
| Static Context Generator     | `agents/tools/load_static_context.py`    | Produces context.json       |
| On-Demand Context Loader     | `agents/tools/context_loader.py`         | Lazy-loads gitignored files |
| Central Config               | `agent_framework_config.yaml`           | Paths, limits, profiles     |
| Generated Context            | `agents/logic/agent_outputs/context.json`      | Agent's "working memory"    |

### Self-Improvement Layer

| Component                    | Path                                         | Role                       |
| :--------------------------- | :------------------------------------------- | :------------------------- |
| Skill Builder                | `agents/logic/skills/meta/skill_builder.meta.yaml`  | Create new skills          |
| Skill Merger                 | `agents/logic/skills/meta/skill_merger.meta.yaml`   | Consolidate/clean skills   |
| Builder Wrapper              | `agents/tools/wrappers/skill_builder_wrapper.py` | Builder execution       |
| Merger Wrapper               | `agents/tools/wrappers/skill_merger_wrapper.py`  | Merger execution        |

---

## Profile Inheritance

```
    _base.yaml
        │
        ├── lite.yaml        (inherits: _base)
        │       │
        ├── standard.yaml    (inherits: lite)
        │       │
        └── full.yaml        (inherits: standard)
```

Each profile defines:

- `mode` — Operational mode identifier
- `model_family` — Target LLM family
- `risk_tolerance` — low / medium / high
- `execution_scope` — What directories are writable
- `modification_permissions` — What the agent can change

---

## Config-Driven Architecture

`agent_framework_config.yaml` is the single configuration point:

```yaml
static_context:
  output_path: agents/logic/agent_outputs/context.json
  max_lines: 1000                    # Context budget
  file_tree_max_depth: 2
  excluded_dirs_from_tree: [...]

on_demand_files:
  treemap:
    path: agents/logic/analysis/treemap.md  # ← Change path here if structure changes
  dependencies_report:
    path: agents/logic/analysis/dependencies_report.md
```

If the project structure changes, update `agent_framework_config.yaml`.
All scripts read paths from this config — no hardcoded paths.

---

## Determinism Principles

1. **Minimal context activation** — Only load what's needed
2. **No uncontrolled exploration** — Skills are activated by triggers, not discovery
3. **No redesign without permission** — Core skills are protected
4. **Strict separation of intent and execution** — Task contract → wrapper → output
5. **Budget enforcement** — context.json has a hard line-count limit with deterministic truncation

---

## Security Model

### Protected Files (Global Blacklist)

- `agents/logic/rules/agent_rules.md`
- `agents/logic/skills/_index.yaml` (auto-generated)
- `agents/logic/skills/_trigger_engine.yaml` (auto-generated)
- `.git/**`, `.env`, `credentials.json`, `secrets.*`
- `requirements.txt`, `pyproject.toml`

### Execution Isolation

- All Python execution MUST use `.venv/Scripts/python.exe` (Windows)
- All execution MUST set `PYTHONIOENCODING=utf-8`
- No global interpreter usage permitted

---

**Architecture version:** 3.1.0
**Last Updated:** 2026-02-17

