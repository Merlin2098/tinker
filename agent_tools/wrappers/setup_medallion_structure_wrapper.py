#!/usr/bin/env python3
"""
Canonical execution wrapper for the `setup_medallion_structure` skill.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from agent_tools.wrappers._explorer_common import parse_bool
except ImportError:
    from wrappers._explorer_common import parse_bool


DEFAULT_LAYERS = ["bronze", "silver", "gold"]
VALID_LAYERS = set(DEFAULT_LAYERS)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_root_path(raw: Any) -> tuple[str, Path]:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("base_path is required and must be a non-empty string.")

    root = _project_root()
    candidate = Path(raw.strip())
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"base_path must resolve inside project root: {resolved}") from exc

    return str(resolved), resolved


def _normalize_layers(raw: Any) -> list[str]:
    if raw is None:
        return list(DEFAULT_LAYERS)
    if not isinstance(raw, list) or not raw:
        raise ValueError("layers must be a non-empty list when provided.")

    normalized: list[str] = []
    for entry in raw:
        if not isinstance(entry, str) or not entry.strip():
            raise ValueError("layers entries must be non-empty strings.")
        layer = entry.strip().lower()
        if layer not in VALID_LAYERS:
            allowed = ", ".join(sorted(VALID_LAYERS))
            raise ValueError(f"Invalid layer '{layer}'. Allowed: {allowed}")
        if layer not in normalized:
            normalized.append(layer)
    return normalized


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    base_path_str, base_path = _resolve_root_path(args.get("base_path"))
    layers = _normalize_layers(args.get("layers"))
    create_if_missing = parse_bool(
        args.get("create_if_missing"),
        field="create_if_missing",
        default=True,
    )
    validate_only = parse_bool(args.get("validate_only"), field="validate_only", default=False)

    if validate_only:
        create_if_missing = False

    created_dirs: list[str] = []
    missing_dirs: list[str] = []
    layer_paths: dict[str, str | None] = {
        "bronze_path": None,
        "silver_path": None,
        "gold_path": None,
    }

    for layer in layers:
        path = base_path / layer
        layer_paths[f"{layer}_path"] = str(path)
        if path.exists():
            if not path.is_dir():
                raise ValueError(f"Expected directory for layer '{layer}': {path}")
            continue

        missing_dirs.append(str(path))
        if create_if_missing:
            path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(path))

    structure_valid = len(missing_dirs) == 0 or create_if_missing

    return {
        "status": "ok",
        "skill": "setup_medallion_structure",
        "base_path": base_path_str,
        "layers": layers,
        **layer_paths,
        "structure_valid": structure_valid,
        "created_dirs": created_dirs,
        "missing_dirs": missing_dirs,
        "create_if_missing": create_if_missing,
        "validate_only": validate_only,
    }
