# Skill: Skill Merger

## Status
- **Tier**: Core
- **Cluster**: Meta
- **Type**: Action (Maintenance)

## Description
Consolidates multiple existing skills into a single, comprehensive skill. This acts as a "Garbage Collector" that registers a new superior skill and safely deletes the obsolete ones, preventing registry bloat.

## Triggering
- **Natural Language**: "merge these skills into...", "consolidate tools...", "clean up the registry..."
- **System**: When the agent detects redundancy or overlapping functionality in available tools.

## Inputs
| Field | Type | Description |
|---|---|---|
| `new_skill_name` | string | Snake_case name of the new consolidated skill. |
| `cluster` | string | Target cluster for the new skill. |
| `description` | string | Description for the new skill. |
| `doc_md` | string | Markdown content for the new skill interface. |
| `wrapper_code` | string | Python code for the new consolidated wrapper. |
| `metadata` | dict | Metadata for the new skill (triggers, priority, etc.). |
| `skills_to_delete` | list[string] | List of existing skill names to remove after successful creation. |
| `force_core` | boolean | Set to `true` to allow deleting CORE skills (Dangerous). Defaults to `false`. |

## Behavior
1.  **Validation**:
    -   Validates the new skill inputs (same as `skill_builder`).
    -   Checks if `skills_to_delete` exist.
    -   **Guardrail**: Prevents deletion of `Core` tier skills unless `force_core` is True.
2.  **Creation**: Use `skill_builder` logic to write the new skill files.
3.  **Deletion**:
    -   Deletes `.md` and `.meta.yaml` of obsolete skills.
    -   Deletes `_wrapper.py` of obsolete skills.
4.  **Registration**: Runs `compile_registry.py`.
5.  **Output**: Report of created and deleted files.

## Output
- JSON object confirming the merge operation.
