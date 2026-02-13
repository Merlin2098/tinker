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

## Optional plan docs
- `plan_doc.py init --id <id> --title <title> --objective <text>`
- `plan_doc.py add-step --file <plan.yaml> --step-id <id> --description <text>`
- `plan_doc.py approve --file <plan.yaml> --by <name> [--note <text>]`
- `plan_doc.py handoff --file <plan.yaml> --to <target> --notes <text>`
- `plan_doc.py validate --file <plan.yaml>`
- `plan_doc.py archive --file <plan.yaml>`

## Install Tinker
- `install_tinker.py <dest1> [dest2 ...]`
- `install_tinker.py --pick-dest`
- `install_tinker.py --dry-run <dest>`
- `install_tinker.py --overwrite-framework --backup <dest>`

## Notes
- `mode_profile` is optional.
- `phase` and `validation` are optional compatibility fields, not hard requirements.
- Plan docs are optional collaboration artifacts and are not required to execute `agent/user_task.yaml`.
