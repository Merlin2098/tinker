#!/usr/bin/env python3
"""
Shared context/path helpers for context loader tools.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"PyYAML required: {exc}")


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def resolve_path(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p.resolve()
    return (project_root() / p).resolve()


def is_under_project_root(path: Path) -> bool:
    root = project_root().resolve()
    try:
        path.resolve().relative_to(root)
    except ValueError:
        return False
    return True


def resolve_and_validate(path: str, *, must_exist: bool) -> Path:
    abs_path = resolve_path(path)
    if not is_under_project_root(abs_path):
        raise ValueError(f"Path escapes project_root: {path}")
    if must_exist and not abs_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return abs_path


def load_yaml_file(path: str | Path) -> Any:
    p = resolve_path(str(path)) if isinstance(path, str) else path
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json_file(path: str | Path) -> Any:
    p = resolve_path(str(path)) if isinstance(path, str) else path
    with open(p, "r", encoding="utf-8-sig") as f:
        return json.load(f)
