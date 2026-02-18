# Tinker ETL Architecture Notes

## Purpose
This document explains how Tinker modules coordinate an ETL workflow.
It is a practical, module-level map focused on ingest, transform, and export.

## ETL Module Map
Ingestion
- Entry points: `agent/user_task.yaml`, `agent_tools/chat_shortcuts.py`
- Trigger source: `agent/skills/_trigger_engine.yaml`
- File discovery: `agent_tools/wrappers/file_explorer_wrapper.py`
- Input normalization: `agent_tools/wrappers/input_file_handler_wrapper.py`
- Format readers: `agent_tools/wrappers/read_excel_*`, `agent_tools/wrappers/csv_explorer_wrapper.py`, `agent_tools/wrappers/json_explorer_wrapper.py`, `agent_tools/wrappers/yaml_explorer_wrapper.py`

Transform
- Data shaping: `agent_tools/wrappers/excel_to_parquet_wrapper.py`, `agent_tools/wrappers/query_parquet_duckdb_wrapper.py`
- Integrity checks: `agent_tools/wrappers/data_integrity_guardian_wrapper.py`
- Validation gates: `agent_tools/wrappers/input_validation_sanitizer_wrapper.py`, `agent_tools/wrappers/output_validation_checklist_wrapper.py`

Load/Export
- Export outputs: `agent_tools/wrappers/parquet_to_excel_polars_xlsxwriter_wrapper.py`
- Packaging and release aids: `agent_tools/wrappers/devops_packaging_wrapper.py`, `agent_tools/wrappers/log_bundle_folder_management_wrapper.py`

## ETL Flow
1. Initialization
`agent_tools/chat_shortcuts.py` runs `activate_kernel.py`, `compile_registry.py`, `load_static_context.py`, then `mode_selector.py`.

2. Trigger Resolution
`agent/skills/_trigger_engine.yaml` maps extensions, phases, and errors to skills.
Example for ETL
- Extensions: `.csv`, `.xlsx`, `.parquet`
- Phases: `ingest`, `transform`, `export`

3. Skill Activation
Skills are activated or suggested based on the active profile.
Core skills are activated deterministically, non-core are suggested.

4. Wrapper Execution
`agent_tools/run_wrapper.py` executes the selected wrapper(s).
Each wrapper is the canonical implementation for its skill.

5. Outputs
Artifacts are written under `agent/agent_outputs/` by design.

## Where ETL Configuration Lives
- Framework config: `agent_framework_config.yaml`
- Trigger rules: `agent/skills/_trigger_engine.yaml`
- Skill metadata: `agent/skills/**/*.meta.yaml`
- Profiles: `agent/profiles/*.yaml`

## Common ETL Trigger Paths
- `ingest` phase activates `file_explorer` and `input_file_handler`
- `.csv` and `.xlsx` extensions suggest CSV/Excel explorers
- `transform` phase activates `data_integrity_guardian`
- `export` phase suggests parquet export helpers

## Operational Checklist
- Ensure `_trigger_engine.yaml` exists in `agent/skills/`
- Run `agent_tools/compile_registry.py` after adding or editing `.meta.yaml`
- Confirm `agent_tools/load_static_context.py` completes without errors
- Validate the active profile with `agent_tools/mode_selector.py --read-state`

## Notes
- The ETL flow is deterministic. Trigger rules decide which skills run.
- Profiles control activation behavior. LITE is minimal, FULL is most permissive.
