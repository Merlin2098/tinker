#!/usr/bin/env python3
"""
Shared schema/file loading helpers for agent_tools validators.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, ValidationError

    HAS_JSONSCHEMA = True
except Exception:  # pragma: no cover
    Draft202012Validator = None  # type: ignore[assignment]
    ValidationError = Exception  # type: ignore[assignment]
    HAS_JSONSCHEMA = False

try:
    import yaml

    HAS_YAML = True
except Exception:  # pragma: no cover
    yaml = None  # type: ignore[assignment]
    HAS_YAML = False


SCHEMA_FILES: dict[str, str] = {
    "envelope": "task_envelope.schema.json",
    "task_plan": "task_plan.schema.json",
    "report": "execution_report.schema.json",
    "system_config": "system_config.schema.yaml",
    "user_task": "user_task.schema.yaml",
    "plan_doc": "plan_doc.schema.yaml",
}

SCHEMA_TYPE_ALIASES: dict[str, str] = {
    "plan": "task_plan",
    "config": "system_config",
}


def get_project_root() -> Path:
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "agents").exists() and (current / "agent_framework_config.yaml").exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent.parent


def canonical_schema_type(schema_type: str) -> str:
    normalized = schema_type.strip().lower()
    return SCHEMA_TYPE_ALIASES.get(normalized, normalized)


def get_builtin_schema_path(schema_type: str) -> Path:
    canonical = canonical_schema_type(schema_type)
    if canonical not in SCHEMA_FILES:
        valid = ", ".join(sorted(list(SCHEMA_FILES.keys()) + list(SCHEMA_TYPE_ALIASES.keys())))
        raise ValueError(f"Unknown schema type: {schema_type}. Valid types: {valid}")
    return get_project_root() / "agents" / "logic" / "agent_protocol" / "schemas" / SCHEMA_FILES[canonical]


def load_json_file(path: Path) -> Any:
    # utf-8-sig tolerates BOM from some Windows editors.
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_yaml_file(path: Path) -> Any:
    if not HAS_YAML:
        raise ImportError("PyYAML is required for YAML files. Install with: pip install pyyaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_data_file(path: Path) -> Any:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return load_json_file(path)
    if suffix in (".yaml", ".yml"):
        return load_yaml_file(path)

    # Unknown extension: try JSON, then YAML fallback.
    try:
        return load_json_file(path)
    except json.JSONDecodeError:
        return load_yaml_file(path)


def iter_validation_errors(data: Any, schema: Any) -> list[ValidationError]:
    if not HAS_JSONSCHEMA:
        return []
    validator = Draft202012Validator(schema)
    return list(validator.iter_errors(data))


def detect_schema_type(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    if "envelope" in payload and "payload" in payload:
        return "envelope"
    if "action_plan" in payload and "risk_assessment" in payload:
        return "task_plan"
    if "actions_summary" in payload and "status" in payload:
        return "report"
    if "system_definitions" in payload and "workflow_configuration" in payload:
        return "system_config"
    if "mode" in payload and "objective" in payload and "files" in payload:
        return "user_task"
    return None
