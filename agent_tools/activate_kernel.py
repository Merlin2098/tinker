#!/usr/bin/env python3
"""
Kernel activation helper.

Writes the active profile state without creating or modifying kernel/profile files.
This is intentionally idempotent and safe for multi-agent usage.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def profile_path(profile: str) -> Path:
    return project_root() / "agent" / "profiles" / f"{profile.lower()}.yaml"


def state_path(agent_id: str | None, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Activate kernel profile state")
    parser.add_argument("--profile", required=True, help="LITE | STANDARD | FULL")
    parser.add_argument("--agent-id", help="Optional agent identifier for per-agent state")
    parser.add_argument("--state-path", help="Optional explicit state file path")
    args = parser.parse_args()

    profile = args.profile.strip().upper()
    if profile not in {"LITE", "STANDARD", "FULL"}:
        raise SystemExit(f"Invalid profile: {profile}")

    p_path = profile_path(profile)
    if not p_path.exists():
        raise SystemExit(f"Profile file not found: {p_path}")

    out_path = state_path(args.agent_id, args.state_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    current = load_state(out_path)
    if current.get("profile") == profile:
        print(f"Kernel profile already active: {profile}")
        print(f"State file: {out_path}")
        return 0

    payload = {
        "profile": profile,
        "agent_id": args.agent_id,
        "profile_path": str(p_path),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "activate_kernel",
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Kernel activated: {profile}")
    print(f"Profile path: {p_path}")
    print(f"State file: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
