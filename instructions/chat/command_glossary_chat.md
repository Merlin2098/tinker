# Tinker Chat Command Glossary

Purpose: compact reference for chat commands.

## Kernel selection
- `Kernel LITE`
- `Kernel STANDARD`
- `Kernel FULL`

## Task triggers
- `Tinker: validate`
  - Validate task contract and readiness.
- `Tinker: run`
  - Execute task using wrapper-first flow.
- `Run task from agent/user_task.yaml`
  - Explicit trigger for task execution flow.

## Build `user_task.yaml`
- `user_task_builder.py --input <yaml>`
- `user_task_builder.py --from-template <yaml> ...`

## Context refresh
- `load_static_context.py`

## Install Tinker
- `install_tinker.py <dest1> [dest2 ...]`
- `install_tinker.py --pick-dest`
- `install_tinker.py --dry-run <dest>`
- `install_tinker.py --overwrite-framework --backup <dest>`

## Notes
- `mode_profile` is optional.
- `phase` and `validation` are optional compatibility fields, not hard requirements.
