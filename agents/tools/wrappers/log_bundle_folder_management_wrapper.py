#!/usr/bin/env python3
"""
Canonical execution wrapper for the `log_bundle_folder_management` skill.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

try:
    from agents.tools.wrappers._explorer_common import parse_bool
except ImportError:
    from wrappers._explorer_common import parse_bool


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _app_name(raw: Any) -> str:
    if raw is None:
        return "tinker"
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("app_name must be a non-empty string when provided.")
    return raw.strip()


def _resolve_custom_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path.resolve()
    return (_project_root() / path).resolve()


def _default_folder(app_name: str, bundled_mode: bool) -> Path:
    if bundled_mode:
        if os.name == "nt":
            appdata = os.getenv("APPDATA")
            if appdata:
                return (Path(appdata) / app_name / "logs").resolve()
        return (Path.home() / f".{app_name}" / "logs").resolve()
    return (_project_root() / "logs").resolve()


def _ensure_not_inside_bundle(path: Path, bundle_root: Path | None) -> None:
    if bundle_root is None:
        return
    try:
        path.relative_to(bundle_root)
    except ValueError:
        return
    raise ValueError(f"log folder must be outside bundle root: {bundle_root}")


def _validate_writable(folder: Path) -> None:
    probe = folder / ".write_test"
    probe.write_text("ok", encoding="utf-8")
    probe.unlink()


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    app_name = _app_name(args.get("app_name"))
    bundled_mode = parse_bool(args.get("bundled_mode"), field="bundled_mode", default=False)
    create_if_missing = parse_bool(
        args.get("create_if_missing"),
        field="create_if_missing",
        default=True,
    )
    validate_writable = parse_bool(
        args.get("validate_writable"),
        field="validate_writable",
        default=True,
    )
    fallback_to_temp = parse_bool(
        args.get("fallback_to_temp"),
        field="fallback_to_temp",
        default=True,
    )
    dry_run = parse_bool(args.get("dry_run"), field="dry_run", default=False)

    custom = args.get("log_folder_path")
    if custom is not None:
        if not isinstance(custom, str) or not custom.strip():
            raise ValueError("log_folder_path must be a non-empty string when provided.")
        target = _resolve_custom_path(custom.strip())
    else:
        target = _default_folder(app_name, bundled_mode=bundled_mode)

    bundle_root = None
    bundle_root_arg = args.get("bundle_root")
    if bundle_root_arg is not None:
        if not isinstance(bundle_root_arg, str) or not bundle_root_arg.strip():
            raise ValueError("bundle_root must be a non-empty string when provided.")
        bundle_root = _resolve_custom_path(bundle_root_arg.strip())
    elif bundled_mode:
        meipass = os.getenv("_MEIPASS")
        if meipass:
            bundle_root = Path(meipass).resolve()

    _ensure_not_inside_bundle(target, bundle_root)

    if dry_run:
        return {
            "status": "ok",
            "skill": "log_bundle_folder_management",
            "dry_run": True,
            "app_name": app_name,
            "bundled_mode": bundled_mode,
            "bundle_root": str(bundle_root) if bundle_root is not None else None,
            "requested_log_folder_path": custom,
            "resolved_log_folder": str(target),
            "created": None,
            "validate_writable": validate_writable,
            "fallback_to_temp": fallback_to_temp,
            "fallback_used": False,
        }

    fallback_used = False
    selected = target

    try:
        if create_if_missing:
            selected.mkdir(parents=True, exist_ok=True)
        elif not selected.exists():
            raise FileNotFoundError(f"log folder does not exist: {selected}")

        if validate_writable:
            _validate_writable(selected)
    except Exception:
        if not fallback_to_temp:
            raise
        fallback_used = True
        selected = (Path(tempfile.gettempdir()) / f"{app_name}_logs").resolve()
        if create_if_missing:
            selected.mkdir(parents=True, exist_ok=True)
        if validate_writable:
            _validate_writable(selected)

    return {
        "status": "ok",
        "skill": "log_bundle_folder_management",
        "dry_run": dry_run,
        "app_name": app_name,
        "bundled_mode": bundled_mode,
        "bundle_root": str(bundle_root) if bundle_root is not None else None,
        "requested_log_folder_path": custom,
        "resolved_log_folder": str(selected),
        "created": bool(selected.exists()) if not dry_run else None,
        "validate_writable": validate_writable,
        "fallback_to_temp": fallback_to_temp,
        "fallback_used": fallback_used,
    }

