#!/usr/bin/env python3
"""
Mode selector.

Resolves the active profile based on (1) user_task.mode_profile,
(2) per-agent state file, (3) default state file, (4) LITE default.
Outputs the merged kernel+profile bundle as JSON and optionally writes
active profile state.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"PyYAML required: {exc}")


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def resolve_state_path(agent_id: str | None) -> Path:
    runtime_dir = project_root() / "agent" / "agent_outputs" / "runtime"
    if agent_id:
        return runtime_dir / f"active_profile.{agent_id}.json"
    return runtime_dir / "active_profile.json"


def load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def profile_file(profile: str) -> Path:
    return project_root() / "agent" / "profiles" / f"{profile.lower()}.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve active profile bundle")
    parser.add_argument("--user-task", default="agent/user_task.yaml")
    parser.add_argument("--agent-id", help="Optional agent identifier")
    parser.add_argument("--write-state", action="store_true", help="Write active profile state")
    args = parser.parse_args()

    user_task = load_yaml(project_root() / args.user_task)
    requested = str(user_task.get("mode_profile", "")).strip().upper()

    if not requested:
        state = load_state(resolve_state_path(args.agent_id))
        requested = str(state.get("profile", "")).strip().upper()

    if not requested:
        requested = "LITE"

    if requested not in {"LITE", "STANDARD", "FULL"}:
        raise SystemExit(f"Invalid profile: {requested}")

    kernel = load_yaml(project_root() / "agent" / "kernel" / "kernel.yaml")
    profile_path = profile_file(requested)
    if not profile_path.exists():
        raise SystemExit(f"Profile file not found: {profile_path}")
    profile = load_yaml(profile_path)

    bundle = deep_merge(kernel, profile)
    bundle["_resolved_profile"] = requested
    bundle["_resolved_at"] = datetime.now(timezone.utc).isoformat()

    if args.write_state:
        state_path = resolve_state_path(args.agent_id)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_payload = {
            "profile": requested,
            "agent_id": args.agent_id,
            "profile_path": str(profile_path),
            "updated_at": bundle["_resolved_at"],
            "source": "mode_selector",
        }
        state_path.write_text(json.dumps(state_payload, indent=2), encoding="utf-8")

    print(json.dumps(bundle, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
