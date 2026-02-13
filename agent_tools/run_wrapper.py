#!/usr/bin/env python3
"""
Canonical wrapper runner for thin skill interfaces.

Usage:
  .venv/Scripts/python.exe agent_tools/run_wrapper.py --skill connect_duckdb --args-json '{"database_path":"data/example.duckdb"}'
  .venv/Scripts/python.exe agent_tools/run_wrapper.py --skill load_json_files --args-file agent/agent_outputs/plans/load_json.args.json
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from functools import lru_cache
from typing import Any, Callable

WrapperFunc = Callable[[dict[str, Any]], dict[str, Any]]


def _bind_skill(runner: WrapperFunc, skill_name: str) -> WrapperFunc:
    def _wrapped(args: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(args, dict):
            raise ValueError("Wrapper args must be a JSON object.")
        payload = dict(args)
        payload["skill_name"] = skill_name
        return runner(payload)

    return _wrapped

DIRECT_WRAPPERS: dict[str, str] = {
    "connect_duckdb": "connect_duckdb",
    "csv_explorer": "csv_explorer",
    "db_explorer": "db_explorer",
    "docx_explorer": "docx_explorer",
    "excel_explorer": "excel_explorer",
    "excel_to_parquet": "excel_to_parquet",
    "execution_timer": "execution_timer",
    "file_explorer": "file_explorer",
    "generate_exe_pyinstaller_onedir": "generate_exe_pyinstaller_onedir",
    "html_explorer": "html_explorer",
    "input_file_handler": "input_file_handler",
    "input_validation_sanitizer": "input_validation_sanitizer",
    "json_explorer": "json_explorer",
    "load_json_files": "load_json_files",
    "load_sql_queries": "load_sql_queries",
    "load_yaml_files": "load_yaml_files",
    "log_bundle_folder_management": "log_bundle_folder_management",
    "log_overwrite_policy": "log_overwrite_policy",
    "markdown_explorer": "markdown_explorer",
    "parquet_explorer": "parquet_explorer",
    "parquet_to_excel_polars_xlsxwriter": "parquet_to_excel_polars_xlsxwriter",
    "pdf_explorer": "pdf_explorer",
    "powerbi_explorer": "powerbi_explorer",
    "pptx_explorer": "pptx_explorer",
    "query_parquet_duckdb": "query_parquet_duckdb",
    "read_excel_pandas": "read_excel_pandas",
    "read_excel_polars_openpyxl": "read_excel_polars_openpyxl",
    "setup_medallion_structure": "setup_medallion_structure",
    "xml_explorer": "xml_explorer",
    "yaml_explorer": "yaml_explorer",
}

ADVISOR_WRAPPER_SKILLS: dict[str, tuple[str, ...]] = {
    "policy_guidance": (
        "ambiguity_escalation",
        "artifact_persistence_discipline",
        "brainstorming_design_explorer",
        "context_loading_protocol",
        "debugger_orchestrator",
        "decision_process_flow",
        "execution_flow_orchestration",
        "git_rollback_strategy",
        "immutable_resource_respect",
        "llm_inference_optimization",
        "minimal_documentation_policy",
        "output_validation_checklist",
        "path_traversal_prevention",
        "plan_archive_protocol",
        "protected_file_validation",
        "risk_scoring_matrix",
        "root_cause_tracing",
        "scope_control_discipline",
        "skill_authority_first",
        "systematic_debugging",
        "verification_before_completion",
        "workspace_model_awareness",
    ),
    "python_quality_advisor": (
        "api_client_generator",
        "async_concurrency_expert",
        "code_analysis_qa_gate",
        "code_structuring_pythonic",
        "config_env_manager",
        "data_integrity_guardian",
        "dependency_audit",
        "devops_packaging",
        "externalized_logic_handler",
        "linter_formatter_guru",
        "microservices_api_architect",
        "naming_control_flow",
        "performance_profiler",
        "refactoring_assistant",
        "regression_test_automation",
        "secure_python_practices",
        "serialization_persistence",
        "testing_qa_mentor",
        "type_master",
    ),
    "ui_advisor": (
        "ui_application_assets",
        "ui_framework_selection",
        "ui_identity_policy",
        "ui_layout_proportionality",
        "ui_splash_and_lazy_loading",
        "ui_theme_binding",
        "ui_widget_modularity",
    ),
}


@lru_cache(maxsize=None)
def _load_wrapper_runner(wrapper_name: str) -> WrapperFunc:
    module_name = f"{wrapper_name}_wrapper"
    try:
        module = importlib.import_module(f"agent_tools.wrappers.{module_name}")
    except ImportError:
        # Allow direct execution from project root:
        # python agent_tools/run_wrapper.py ...
        module = importlib.import_module(f"wrappers.{module_name}")
    runner = getattr(module, "run", None)
    if not callable(runner):
        raise ImportError(f"Wrapper module missing callable run(): {module_name}")
    return runner


def build_wrapper_registry() -> dict[str, WrapperFunc]:
    registry: dict[str, WrapperFunc] = {}

    for skill, wrapper_name in DIRECT_WRAPPERS.items():
        registry[skill] = _load_wrapper_runner(wrapper_name)

    for wrapper_name, skill_names in ADVISOR_WRAPPER_SKILLS.items():
        base_runner = _load_wrapper_runner(wrapper_name)
        for skill in skill_names:
            registry[skill] = _bind_skill(base_runner, skill)

    return registry


WRAPPER_REGISTRY: dict[str, WrapperFunc] = build_wrapper_registry()


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
