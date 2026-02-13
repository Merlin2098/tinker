# Tinker Chat Command Glossary

Purpose: single-page reference for chat commands and when to use them.

## Kernel selection (chat)
- `Kernel LITE`
  - Use when you want the lightest guardrails and quickest iteration.
- `Kernel STANDARD`
  - Use for normal work that needs more checks than LITE.
- `Kernel FULL`
  - Use for high-risk changes or when you want maximum governance checks.

## Task triggers (chat)
- `Tinker: validate`
  - Use after preparing `agent/user_task.yaml` to run Phase A validation only.
- `Tinker: run`
  - Use only after validation passes to run Phase B execution.
- `Run task from agent/user_task.yaml`
  - Full explicit trigger. Equivalent to `Tinker: run` or `Tinker: validate` depending on `phase`.

## Build user_task.yaml
- `user_task_builder.py --input <yaml>`
  - Use when you manually edited a YAML template and want it validated and written to `agent/user_task.yaml`.
- `user_task_builder.py --from-template <yaml> ...`
  - Use when you want the agent to assemble `agent/user_task.yaml` from explicit inputs.

## Context refresh
- `load_static_context.py`
  - Use after large project changes or when you want a fresh project snapshot for the agent.

## Install Tinker (portable deploy)
- `install_tinker.py <dest1> [dest2 ...]`
  - Use to copy the Tinker footprint into other project roots and merge `requirements.txt` and `.gitignore` (differences only).
- `install_tinker.py --pick-dest`
  - Use to select the destination project root via a folder picker (GUI). If unavailable, it prompts for a path.
- `install_tinker.py --dry-run <dest>`
  - Use to preview changes.
- `install_tinker.py --overwrite-framework --backup <dest>`
  - Use when the destination already has Tinker/legacy files and you want a clean overwrite with backups.

## Kernel mismatch guard
- `kernel_guard.py`
  - Use when you switch between Claude Code and chat and want to detect if active kernel differs from `agent/user_task.yaml`'s `mode_profile`.
- `kernel_guard.py --prefer active|task`
  - Use for non-interactive resolution (keep active or switch to task).

## Notes
- In chat flow, `mode_profile` in `agent/user_task.yaml` should be empty unless you explicitly want to override the kernel state.
- For Claude Code or IDE hooks, use their respective trigger docs instead of these chat commands.

