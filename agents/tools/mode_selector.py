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
from typing import Any

try:
    from agents.tools._profile_state import (
        VALID_PROFILES,
        load_state,
        load_yaml,
        now_iso,
        profile_path as profile_file,
        project_root,
        resolve_state_path,
        write_state,
    )
except ImportError:
    from _profile_state import (  # type: ignore
        VALID_PROFILES,
        load_state,
        load_yaml,
        now_iso,
        profile_path as profile_file,
        project_root,
        resolve_state_path,
        write_state,
    )


def deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve active profile bundle")
    parser.add_argument("--user-task", default="agents/logic/user_task.yaml")
    parser.add_argument("--agent-id", help="Optional agent identifier")
    parser.add_argument("--write-state", action="store_true", help="Write active profile state")
    parser.add_argument("--read-state", action="store_true", help="Print active profile state and exit")
    args = parser.parse_args()

    if args.read_state:
        state_path = resolve_state_path(args.agent_id)
        state = load_state(state_path)
        if not state:
            print(json.dumps({"state_path": str(state_path), "status": "missing"}, indent=2))
            return 0
        state.setdefault("_state_path", str(state_path))
        print(json.dumps(state, indent=2))
        return 0

    user_task = load_yaml(project_root() / args.user_task)
    requested = str(user_task.get("mode_profile", "")).strip().upper()

    if not requested:
        state = load_state(resolve_state_path(args.agent_id))
        requested = str(state.get("profile", "")).strip().upper()

    if not requested:
        requested = "LITE"

    if requested not in VALID_PROFILES:
        raise SystemExit(f"Invalid profile: {requested}")

    kernel = load_yaml(project_root() / "agents" / "logic" / "kernel" / "kernel.yaml")
    profile_path = profile_file(requested)
    if not profile_path.exists():
        raise SystemExit(f"Profile file not found: {profile_path}")
    profile = load_yaml(profile_path)

    bundle = deep_merge(kernel, profile)
    bundle["_resolved_profile"] = requested
    bundle["_resolved_at"] = now_iso()

    if args.write_state:
        state_path = resolve_state_path(args.agent_id)
        state_payload = write_state(state_path, requested, agent_id=args.agent_id, source="mode_selector")
        state_payload["updated_at"] = bundle["_resolved_at"]
        state_path.write_text(json.dumps(state_payload, indent=2), encoding="utf-8")

    print(json.dumps(bundle, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

