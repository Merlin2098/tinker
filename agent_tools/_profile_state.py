#!/usr/bin/env python3
"""
Shared helpers for kernel/profile state management.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"PyYAML required: {exc}")


VALID_PROFILES = {"LITE", "STANDARD", "FULL"}


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def resolve_state_path(agent_id: str | None, explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    runtime_dir = project_root() / "agent" / "agent_outputs" / "runtime"
    if agent_id:
        return runtime_dir / f"active_profile.{agent_id}.json"
    return runtime_dir / "active_profile.json"


def profile_path(profile: str) -> Path:
    return project_root() / "agent" / "profiles" / f"{profile.lower()}.yaml"


def normalize_profile(value: object) -> str:
    return str(value or "").strip().upper()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_state(path: Path, profile: str, *, agent_id: str | None, source: str) -> dict[str, Any]:
    payload = {
        "profile": profile,
        "agent_id": agent_id,
        "profile_path": str(profile_path(profile)),
        "updated_at": now_iso(),
        "source": source,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
