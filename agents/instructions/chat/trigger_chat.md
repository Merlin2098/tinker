# Tinker Framework - Chat Bootstrap (Model-Agnostic)

Purpose: explicit command-driven setup for chat-based agents.

## Hard constraints
1. Validate `agents/logic/user_task.yaml` against `agents/logic/agent_protocol/schemas/user_task.schema.yaml`.
2. No field inference and no fabricated data.
3. Wrapper-first execution model.

## Chat Commands
Use these exact phrases in chat:
- `Tinker: validate`
- `Tinker: run`
- `Tinker: full context`
- `Run task from agents/logic/user_task.yaml`
- `commit`
- `sync`
- `commit and sync`

## Kernel commands (chat)
- `Kernel LITE`
- `Kernel STANDARD`
- `Kernel FULL`

## 🚀 Session Startup (Copy & Paste)
Copy and paste ONE of these natural language phrases. The Agent will execute the setup for you.

To start with FULL Kernel (Recommended):
```text
Initiate Tinker. Kernel FULL
```

To start with other profiles:
```text
Initiate Tinker. Kernel LITE
```
```text
Initiate Tinker. Kernel STANDARD
```

## 🔄 Typical Workflow (Day in the Life)

After initialization, follow this cycle:

### 1. Define Task (Contract)
- Edit `agents/logic/user_task.yaml` to define **Objective** and **Constraints**.
- *Tip: Keep scope small and verifiable.*

### 2. Execute
- Chat: `Tinker: run`
- The agent will read the task, plan actions, and execute them via wrappers.

### 3. Validate & Iterate
- Check the output files or code changes.
- If changes are needed, update `user_task.yaml` and run `Tinker: run` again.
- *Tip: Don't just chat new instructions; update the contract.*

### 4. Save State
- Chat: `commit` (saves a local git checkpoint)
- Chat: `sync` (pushes to remote)

## Shortcut intent routing
- If the user says `init` or `start`, run:
  - `./.venv/Scripts/python.exe agents/tools/chat_shortcuts.py "init"`
- If the user says `commit`, run:
  - `./.venv/Scripts/python.exe agents/tools/chat_shortcuts.py "commit"`
- If the user says `sync`, run:
  - `./.venv/Scripts/python.exe agents/tools/chat_shortcuts.py "sync"`
- If the user says `commit and sync`, run:
  - `./.venv/Scripts/python.exe agents/tools/chat_shortcuts.py "commit and sync"`
- If the user says `full context` or `refresh full context`, run:
  - `./.venv/Scripts/python.exe agents/tools/chat_shortcuts.py "full context"`
- If the user says `full context with treemap`, run:
  - `./.venv/Scripts/python.exe agents/tools/chat_shortcuts.py "full context" --include-treemap`
- Optional explicit commit message:
  - `./.venv/Scripts/python.exe agents/tools/chat_shortcuts.py "commit" --message "<checkpoint message>"`

## When To Execute Full Context
Use full context only when one of these conditions is true:
- Non-interactive workflow (CI/batch/reproducible handoff snapshot).
- Cross-cutting architecture analysis needs `dependencies_graph` and `architecture_metrics` together.
- A task explicitly asks for consolidated dynamic + static context in one JSON artifact.

Do not run full context for routine chat turns that only need static context and targeted on-demand reads.

## Notes
- `mode_profile` in `agents/logic/user_task.yaml` is optional; leave empty unless explicitly needed.
- Optional compatibility fields (`phase`, `validation`) are supported but not required.
- Plan docs under `agents/logic/agent_outputs/plans/` are optional collaboration artifacts, not execution prerequisites.

