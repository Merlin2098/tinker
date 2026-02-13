#!/usr/bin/env python3
"""
Canonical execution wrapper for the `input_validation_sanitizer` skill.
"""

from __future__ import annotations

import re
from typing import Any

try:
    from agent_tools.wrappers._explorer_common import parse_bool, parse_int
except ImportError:
    from wrappers._explorer_common import parse_bool, parse_int


def _normalize_expected_type(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("expected_type must be a non-empty string when provided.")

    normalized = value.strip().lower()
    valid = {"string", "integer", "number", "boolean", "list", "object"}
    if normalized not in valid:
        allowed = ", ".join(sorted(valid))
        raise ValueError(f"expected_type must be one of: {allowed}")
    return normalized


def _type_matches(expected_type: str, value: Any) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return (isinstance(value, int) and not isinstance(value, bool)) or isinstance(value, float)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "list":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    return False


def _type_name(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "object"
    if value is None:
        return "null"
    return type(value).__name__


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")
    if "value" not in args:
        raise ValueError("value is required.")

    value = args["value"]
    expected_type = _normalize_expected_type(args.get("expected_type"))
    strip_strings = parse_bool(args.get("strip_strings"), field="strip_strings", default=True)
    allow_empty = parse_bool(args.get("allow_empty"), field="allow_empty", default=False)

    min_length = None
    if args.get("min_length") is not None:
        min_length = parse_int(args.get("min_length"), field="min_length", default=0, minimum=0)

    max_length = None
    if args.get("max_length") is not None:
        max_length = parse_int(args.get("max_length"), field="max_length", default=0, minimum=0)

    min_value = args.get("min_value")
    max_value = args.get("max_value")
    allowed_values = args.get("allowed_values")
    pattern = args.get("pattern")

    if expected_type and not _type_matches(expected_type, value):
        raise ValueError(
            f"value type mismatch: expected {expected_type}, got {_type_name(value)}"
        )

    if isinstance(value, str) and strip_strings:
        value = value.strip()

    if isinstance(value, (str, list, dict)):
        if not allow_empty and len(value) == 0:
            raise ValueError("value cannot be empty.")
        if min_length is not None and len(value) < min_length:
            raise ValueError(f"value length must be >= {min_length}.")
        if max_length is not None and len(value) > max_length:
            raise ValueError(f"value length must be <= {max_length}.")

    is_number = (isinstance(value, int) and not isinstance(value, bool)) or isinstance(value, float)
    if min_value is not None:
        if not is_number:
            raise ValueError("min_value requires numeric value.")
        if value < min_value:
            raise ValueError(f"value must be >= {min_value}.")

    if max_value is not None:
        if not is_number:
            raise ValueError("max_value requires numeric value.")
        if value > max_value:
            raise ValueError(f"value must be <= {max_value}.")

    if allowed_values is not None:
        if not isinstance(allowed_values, list):
            raise ValueError("allowed_values must be a list when provided.")
        if value not in allowed_values:
            raise ValueError("value must be one of allowed_values.")

    if pattern is not None:
        if not isinstance(pattern, str) or not pattern:
            raise ValueError("pattern must be a non-empty string when provided.")
        if not isinstance(value, str):
            raise ValueError("pattern can only be applied to string value.")
        if re.fullmatch(pattern, value) is None:
            raise ValueError("value does not match required pattern.")

    return {
        "status": "ok",
        "skill": "input_validation_sanitizer",
        "value_type": _type_name(value),
        "sanitized_value": value,
        "applied": {
            "expected_type": expected_type,
            "strip_strings": strip_strings,
            "allow_empty": allow_empty,
            "min_length": min_length,
            "max_length": max_length,
            "min_value": min_value,
            "max_value": max_value,
            "allowed_values_count": len(allowed_values) if isinstance(allowed_values, list) else None,
            "pattern": pattern,
        },
    }
