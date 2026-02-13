#!/usr/bin/env python3
"""
Kernel activation helper.

Writes the active profile state without creating or modifying kernel/profile files.
This is intentionally idempotent and safe for multi-agent usage.
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from agent_tools._profile_state import (
        VALID_PROFILES,
        load_state,
        profile_path,
        resolve_state_path,
        write_state,
    )
except ImportError:
    from _profile_state import (  # type: ignore
        VALID_PROFILES,
        load_state,
        profile_path,
        resolve_state_path,
        write_state,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Activate kernel profile state")
    parser.add_argument("--profile", required=True, help="LITE | STANDARD | FULL")
    parser.add_argument("--agent-id", help="Optional agent identifier for per-agent state")
    parser.add_argument("--state-path", help="Optional explicit state file path")
    args = parser.parse_args()

    profile = args.profile.strip().upper()
    if profile not in VALID_PROFILES:
        raise SystemExit(f"Invalid profile: {profile}")

    p_path = profile_path(profile)
    if not p_path.exists():
        raise SystemExit(f"Profile file not found: {p_path}")

    out_path = resolve_state_path(args.agent_id, args.state_path)

    current = load_state(out_path)
    if current.get("profile") == profile:
        print(f"Kernel profile already active: {profile}")
        print(f"State file: {out_path}")
        return 0

    write_state(out_path, profile, agent_id=args.agent_id, source="activate_kernel")
    print(f"Kernel activated: {profile}")
    print(f"Profile path: {p_path}")
    print(f"State file: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
