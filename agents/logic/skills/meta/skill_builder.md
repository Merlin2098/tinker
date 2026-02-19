# Skill: Skill Builder

## Status
- **Tier**: Core
- **Cluster**: Meta
- **Type**: Action (Creative)

## Description
A meta-skill that allows the agent to create NEW skills for itself. It generates the necessary Thin Skill files (.md, .meta.yaml) and the Canonical Python Wrapper, then registers them into the system.

## Triggering
- **Natural Language**: "create a skill to...", "build a tool for...", "generate a wrapper for..."
- **System**: When a plan requires a capability that doesn't exist, but can be written in Python.

## Inputs
| Field | Type | Description |
|---|---|---|
| `skill_name` | string | Snake_case name of the new skill (e.g., `parse_pdf_tables`). |
| `cluster` | string | Target cluster folder (e.g., `file_handling`, `data_processing`). Defaults to `misc`. |
| `description` | string | One-line description for the registry. |
| `doc_md` | string | Full Markdown content for the skill documentation interface. |
| `wrapper_code` | string | Complete Python code for `agents/tools/wrappers/<name>_wrapper.py`. |
| `metadata` | dict | Dictionary containing `triggers` (extensions, phases, errors) and other meta fields. |

## Behavior
1.  **Validation**: Checks if `skill_name` already exists. Validates python syntax of `wrapper_code`.
2.  **Generation**:
    -   Writes `agents/logic/skills/<cluster>/<skill_name>.md`
    -   Writes `agents/logic/skills/<cluster>/<skill_name>.meta.yaml`
    -   Writes `agents/tools/wrappers/<skill_name>_wrapper.py`
3.  **Registration**: Runs `compile_registry.py` to rebuild `_index.yaml` and `_trigger_engine.yaml`.
4.  **Confirmation**: Returns the paths of created files and the result of the compilation.

## output
- JSON object confirming success or failure.
- If success: Includes list of created files and compiler output.

