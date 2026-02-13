#!/usr/bin/env python3
"""
Canonical wrapper runner for thin skill interfaces.

Usage:
  .venv/Scripts/python.exe agent_tools/run_wrapper.py --skill connect_duckdb --args-json '{"database_path":"data/example.duckdb"}'
  .venv/Scripts/python.exe agent_tools/run_wrapper.py --skill load_json_files --args-file agent/agent_outputs/plans/load_json.args.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

try:
    from agent_tools.wrappers.csv_explorer_wrapper import run as run_csv_explorer
    from agent_tools.wrappers.connect_duckdb_wrapper import run as run_connect_duckdb
    from agent_tools.wrappers.db_explorer_wrapper import run as run_db_explorer
    from agent_tools.wrappers.docx_explorer_wrapper import run as run_docx_explorer
    from agent_tools.wrappers.excel_explorer_wrapper import run as run_excel_explorer
    from agent_tools.wrappers.excel_to_parquet_wrapper import run as run_excel_to_parquet
    from agent_tools.wrappers.file_explorer_wrapper import run as run_file_explorer
    from agent_tools.wrappers.generate_exe_pyinstaller_onedir_wrapper import run as run_generate_exe_pyinstaller_onedir
    from agent_tools.wrappers.html_explorer_wrapper import run as run_html_explorer
    from agent_tools.wrappers.json_explorer_wrapper import run as run_json_explorer
    from agent_tools.wrappers.load_json_files_wrapper import run as run_load_json_files
    from agent_tools.wrappers.load_sql_queries_wrapper import run as run_load_sql_queries
    from agent_tools.wrappers.load_yaml_files_wrapper import run as run_load_yaml_files
    from agent_tools.wrappers.markdown_explorer_wrapper import run as run_markdown_explorer
    from agent_tools.wrappers.parquet_explorer_wrapper import run as run_parquet_explorer
    from agent_tools.wrappers.parquet_to_excel_polars_xlsxwriter_wrapper import run as run_parquet_to_excel_polars_xlsxwriter
    from agent_tools.wrappers.pdf_explorer_wrapper import run as run_pdf_explorer
    from agent_tools.wrappers.policy_guidance_wrapper import run as run_policy_guidance
    from agent_tools.wrappers.powerbi_explorer_wrapper import run as run_powerbi_explorer
    from agent_tools.wrappers.pptx_explorer_wrapper import run as run_pptx_explorer
    from agent_tools.wrappers.python_quality_advisor_wrapper import run as run_python_quality_advisor
    from agent_tools.wrappers.query_parquet_duckdb_wrapper import run as run_query_parquet_duckdb
    from agent_tools.wrappers.read_excel_pandas_wrapper import run as run_read_excel_pandas
    from agent_tools.wrappers.read_excel_polars_openpyxl_wrapper import run as run_read_excel_polars_openpyxl
    from agent_tools.wrappers.execution_timer_wrapper import run as run_execution_timer
    from agent_tools.wrappers.input_file_handler_wrapper import run as run_input_file_handler
    from agent_tools.wrappers.input_validation_sanitizer_wrapper import run as run_input_validation_sanitizer
    from agent_tools.wrappers.log_bundle_folder_management_wrapper import run as run_log_bundle_folder_management
    from agent_tools.wrappers.log_overwrite_policy_wrapper import run as run_log_overwrite_policy
    from agent_tools.wrappers.setup_medallion_structure_wrapper import run as run_setup_medallion_structure
    from agent_tools.wrappers.ui_advisor_wrapper import run as run_ui_advisor
    from agent_tools.wrappers.xml_explorer_wrapper import run as run_xml_explorer
    from agent_tools.wrappers.yaml_explorer_wrapper import run as run_yaml_explorer
except ImportError:
    # Allow direct execution as a script from project root.
    from wrappers.csv_explorer_wrapper import run as run_csv_explorer
    from wrappers.connect_duckdb_wrapper import run as run_connect_duckdb
    from wrappers.db_explorer_wrapper import run as run_db_explorer
    from wrappers.docx_explorer_wrapper import run as run_docx_explorer
    from wrappers.excel_explorer_wrapper import run as run_excel_explorer
    from wrappers.excel_to_parquet_wrapper import run as run_excel_to_parquet
    from wrappers.file_explorer_wrapper import run as run_file_explorer
    from wrappers.generate_exe_pyinstaller_onedir_wrapper import run as run_generate_exe_pyinstaller_onedir
    from wrappers.html_explorer_wrapper import run as run_html_explorer
    from wrappers.json_explorer_wrapper import run as run_json_explorer
    from wrappers.load_json_files_wrapper import run as run_load_json_files
    from wrappers.load_sql_queries_wrapper import run as run_load_sql_queries
    from wrappers.load_yaml_files_wrapper import run as run_load_yaml_files
    from wrappers.markdown_explorer_wrapper import run as run_markdown_explorer
    from wrappers.parquet_explorer_wrapper import run as run_parquet_explorer
    from wrappers.parquet_to_excel_polars_xlsxwriter_wrapper import run as run_parquet_to_excel_polars_xlsxwriter
    from wrappers.pdf_explorer_wrapper import run as run_pdf_explorer
    from wrappers.policy_guidance_wrapper import run as run_policy_guidance
    from wrappers.powerbi_explorer_wrapper import run as run_powerbi_explorer
    from wrappers.pptx_explorer_wrapper import run as run_pptx_explorer
    from wrappers.python_quality_advisor_wrapper import run as run_python_quality_advisor
    from wrappers.query_parquet_duckdb_wrapper import run as run_query_parquet_duckdb
    from wrappers.read_excel_pandas_wrapper import run as run_read_excel_pandas
    from wrappers.read_excel_polars_openpyxl_wrapper import run as run_read_excel_polars_openpyxl
    from wrappers.execution_timer_wrapper import run as run_execution_timer
    from wrappers.input_file_handler_wrapper import run as run_input_file_handler
    from wrappers.input_validation_sanitizer_wrapper import run as run_input_validation_sanitizer
    from wrappers.log_bundle_folder_management_wrapper import run as run_log_bundle_folder_management
    from wrappers.log_overwrite_policy_wrapper import run as run_log_overwrite_policy
    from wrappers.setup_medallion_structure_wrapper import run as run_setup_medallion_structure
    from wrappers.ui_advisor_wrapper import run as run_ui_advisor
    from wrappers.xml_explorer_wrapper import run as run_xml_explorer
    from wrappers.yaml_explorer_wrapper import run as run_yaml_explorer


WrapperFunc = Callable[[dict[str, Any]], dict[str, Any]]


def _bind_skill(runner: WrapperFunc, skill_name: str) -> WrapperFunc:
    def _wrapped(args: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(args, dict):
            raise ValueError("Wrapper args must be a JSON object.")
        payload = dict(args)
        payload["skill_name"] = skill_name
        return runner(payload)

    return _wrapped

WRAPPER_REGISTRY: dict[str, WrapperFunc] = {
    "api_client_generator": _bind_skill(run_python_quality_advisor, "api_client_generator"),
    "ambiguity_escalation": _bind_skill(run_policy_guidance, "ambiguity_escalation"),
    "artifact_persistence_discipline": _bind_skill(run_policy_guidance, "artifact_persistence_discipline"),
    "async_concurrency_expert": _bind_skill(run_python_quality_advisor, "async_concurrency_expert"),
    "brainstorming_design_explorer": _bind_skill(run_policy_guidance, "brainstorming_design_explorer"),
    "code_analysis_qa_gate": _bind_skill(run_python_quality_advisor, "code_analysis_qa_gate"),
    "code_structuring_pythonic": _bind_skill(run_python_quality_advisor, "code_structuring_pythonic"),
    "config_env_manager": _bind_skill(run_python_quality_advisor, "config_env_manager"),
    "context_loading_protocol": _bind_skill(run_policy_guidance, "context_loading_protocol"),
    "csv_explorer": run_csv_explorer,
    "data_integrity_guardian": _bind_skill(run_python_quality_advisor, "data_integrity_guardian"),
    "debugger_orchestrator": _bind_skill(run_policy_guidance, "debugger_orchestrator"),
    "decision_process_flow": _bind_skill(run_policy_guidance, "decision_process_flow"),
    "connect_duckdb": run_connect_duckdb,
    "db_explorer": run_db_explorer,
    "dependency_audit": _bind_skill(run_python_quality_advisor, "dependency_audit"),
    "devops_packaging": _bind_skill(run_python_quality_advisor, "devops_packaging"),
    "docx_explorer": run_docx_explorer,
    "execution_timer": run_execution_timer,
    "execution_flow_orchestration": _bind_skill(run_policy_guidance, "execution_flow_orchestration"),
    "excel_explorer": run_excel_explorer,
    "excel_to_parquet": run_excel_to_parquet,
    "externalized_logic_handler": _bind_skill(run_python_quality_advisor, "externalized_logic_handler"),
    "file_explorer": run_file_explorer,
    "generate_exe_pyinstaller_onedir": run_generate_exe_pyinstaller_onedir,
    "git_rollback_strategy": _bind_skill(run_policy_guidance, "git_rollback_strategy"),
    "html_explorer": run_html_explorer,
    "immutable_resource_respect": _bind_skill(run_policy_guidance, "immutable_resource_respect"),
    "input_file_handler": run_input_file_handler,
    "input_validation_sanitizer": run_input_validation_sanitizer,
    "json_explorer": run_json_explorer,
    "llm_inference_optimization": _bind_skill(run_policy_guidance, "llm_inference_optimization"),
    "linter_formatter_guru": _bind_skill(run_python_quality_advisor, "linter_formatter_guru"),
    "log_bundle_folder_management": run_log_bundle_folder_management,
    "log_overwrite_policy": run_log_overwrite_policy,
    "load_json_files": run_load_json_files,
    "load_sql_queries": run_load_sql_queries,
    "load_yaml_files": run_load_yaml_files,
    "markdown_explorer": run_markdown_explorer,
    "minimal_documentation_policy": _bind_skill(run_policy_guidance, "minimal_documentation_policy"),
    "microservices_api_architect": _bind_skill(run_python_quality_advisor, "microservices_api_architect"),
    "naming_control_flow": _bind_skill(run_python_quality_advisor, "naming_control_flow"),
    "output_validation_checklist": _bind_skill(run_policy_guidance, "output_validation_checklist"),
    "parquet_explorer": run_parquet_explorer,
    "parquet_to_excel_polars_xlsxwriter": run_parquet_to_excel_polars_xlsxwriter,
    "path_traversal_prevention": _bind_skill(run_policy_guidance, "path_traversal_prevention"),
    "performance_profiler": _bind_skill(run_python_quality_advisor, "performance_profiler"),
    "pdf_explorer": run_pdf_explorer,
    "plan_archive_protocol": _bind_skill(run_policy_guidance, "plan_archive_protocol"),
    "powerbi_explorer": run_powerbi_explorer,
    "pptx_explorer": run_pptx_explorer,
    "protected_file_validation": _bind_skill(run_policy_guidance, "protected_file_validation"),
    "query_parquet_duckdb": run_query_parquet_duckdb,
    "read_excel_pandas": run_read_excel_pandas,
    "read_excel_polars_openpyxl": run_read_excel_polars_openpyxl,
    "refactoring_assistant": _bind_skill(run_python_quality_advisor, "refactoring_assistant"),
    "regression_test_automation": _bind_skill(run_python_quality_advisor, "regression_test_automation"),
    "risk_scoring_matrix": _bind_skill(run_policy_guidance, "risk_scoring_matrix"),
    "root_cause_tracing": _bind_skill(run_policy_guidance, "root_cause_tracing"),
    "scope_control_discipline": _bind_skill(run_policy_guidance, "scope_control_discipline"),
    "secure_python_practices": _bind_skill(run_python_quality_advisor, "secure_python_practices"),
    "serialization_persistence": _bind_skill(run_python_quality_advisor, "serialization_persistence"),
    "setup_medallion_structure": run_setup_medallion_structure,
    "skill_authority_first": _bind_skill(run_policy_guidance, "skill_authority_first"),
    "systematic_debugging": _bind_skill(run_policy_guidance, "systematic_debugging"),
    "testing_qa_mentor": _bind_skill(run_python_quality_advisor, "testing_qa_mentor"),
    "type_master": _bind_skill(run_python_quality_advisor, "type_master"),
    "ui_application_assets": _bind_skill(run_ui_advisor, "ui_application_assets"),
    "ui_framework_selection": _bind_skill(run_ui_advisor, "ui_framework_selection"),
    "ui_identity_policy": _bind_skill(run_ui_advisor, "ui_identity_policy"),
    "ui_layout_proportionality": _bind_skill(run_ui_advisor, "ui_layout_proportionality"),
    "ui_splash_and_lazy_loading": _bind_skill(run_ui_advisor, "ui_splash_and_lazy_loading"),
    "ui_theme_binding": _bind_skill(run_ui_advisor, "ui_theme_binding"),
    "ui_widget_modularity": _bind_skill(run_ui_advisor, "ui_widget_modularity"),
    "verification_before_completion": _bind_skill(run_policy_guidance, "verification_before_completion"),
    "workspace_model_awareness": _bind_skill(run_policy_guidance, "workspace_model_awareness"),
    "xml_explorer": run_xml_explorer,
    "yaml_explorer": run_yaml_explorer,
}


def _load_args_json(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid --args-json payload: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("--args-json must decode to a JSON object.")
    return data


def _load_args_file(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise ValueError(f"--args-file not found: {path}")
    try:
        # utf-8-sig tolerates BOM produced by some Windows editors/tools.
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in --args-file ({path}): {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("--args-file must contain a JSON object.")
    return data


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run canonical wrapper by skill name")
    parser.add_argument("--skill", required=True, help="Skill name in wrapper registry")
    parser.add_argument("--args-json", help="JSON object with wrapper args")
    parser.add_argument("--args-file", help="Path to JSON file with wrapper args")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print output JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if bool(args.args_json) == bool(args.args_file):
        print(
            "Error: provide exactly one of --args-json or --args-file.",
            file=sys.stderr,
        )
        return 2

    runner = WRAPPER_REGISTRY.get(args.skill)
    if runner is None:
        known = ", ".join(sorted(WRAPPER_REGISTRY.keys()))
        print(
            f"Error: unknown --skill '{args.skill}'. Known skills: {known}",
            file=sys.stderr,
        )
        return 2

    try:
        payload = _load_args_json(args.args_json) if args.args_json else _load_args_file(args.args_file)
        result = runner(payload)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
