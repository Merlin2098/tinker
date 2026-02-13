#!/usr/bin/env python3
"""
Kernel guard.

Detects mismatches between:
- the active kernel profile state file (agent/agent_outputs/runtime/active_profile*.json)
- the requested profile in agent/user_task.yaml (mode_profile)

If they differ, it prompts the user to either keep the active profile or switch
the active profile to match the task.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from typing import Optional

try:
    from agent_tools._profile_state import (
        VALID_PROFILES,
        load_state,
        load_yaml,
        normalize_profile,
        project_root,
        resolve_state_path,
    )
except ImportError:
    from _profile_state import (  # type: ignore
        VALID_PROFILES,
        load_state,
        load_yaml,
        normalize_profile,
        project_root,
        resolve_state_path,
    )


def activate_kernel(profile: str, agent_id: Optional[str]) -> int:
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")

    cmd = [sys.executable, str(project_root() / "agent_tools" / "activate_kernel.py"), "--profile", profile]
    if agent_id:
        cmd.extend(["--agent-id", agent_id])
    return subprocess.call(cmd, env=env)


def main() -> int:
    parser = argparse.ArgumentParser(description="Guard against kernel/profile mismatches")
    parser.add_argument("--user-task", default="agent/user_task.yaml", help="User task yaml path")
    parser.add_argument("--agent-id", help="Optional agent identifier (per-agent state file)")
    parser.add_argument(
        "--prefer",
        choices=["active", "task"],
        help="Non-interactive resolution: keep active or switch to task profile",
    )
    args = parser.parse_args()

    user_task_path = project_root() / args.user_task
    user_task = load_yaml(user_task_path)
    task_profile = normalize_profile(user_task.get("mode_profile", ""))
    if task_profile and task_profile not in VALID_PROFILES:
        raise SystemExit(f"Invalid task mode_profile: {task_profile}")

    state_path = resolve_state_path(args.agent_id)
    state = load_state(state_path)
    active_profile = normalize_profile(state.get("profile", ""))
    if active_profile and active_profile not in VALID_PROFILES:
        raise SystemExit(f"Invalid active profile in state file: {active_profile} ({state_path})")

    # Nothing requested by task.
    if not task_profile:
        print("Task mode_profile is empty. No mismatch check required.")
        print(f"Active profile: {active_profile or 'UNKNOWN'}")
        print(f"State file: {state_path}")
        return 0

    # No active profile recorded yet.
    if not active_profile:
        print("No active kernel profile state found.")
        print(f"Task requests: {task_profile}")
        print(f"State file: {state_path}")
        if args.prefer == "active":
            return 0
        if args.prefer == "task":
            rc = activate_kernel(task_profile, args.agent_id)
            if rc != 0:
                raise SystemExit(rc)
            return 0

        print("Choose:")
        print("  1) Keep as-is (no active state)")
        print(f"  2) Activate task profile ({task_profile})")
        print("  3) Abort")
        choice = input("> ").strip()
        if choice == "1":
            return 0
        if choice == "2":
            rc = activate_kernel(task_profile, args.agent_id)
            if rc != 0:
                raise SystemExit(rc)
            return 0
        raise SystemExit("Aborted.")

    # Matching profiles.
    if active_profile == task_profile:
        print(f"Kernel OK: active={active_profile} matches task={task_profile}")
        print(f"State file: {state_path}")
        return 0

    # Mismatch.
    print(f"Kernel mismatch: active={active_profile} task={task_profile}")
    print(f"State file: {state_path}")

    if args.prefer == "active":
        print("Keeping active profile.")
        return 0
    if args.prefer == "task":
        rc = activate_kernel(task_profile, args.agent_id)
        if rc != 0:
            raise SystemExit(rc)
        return 0

    print("Choose:")
    print(f"  1) Keep active ({active_profile})")
    print(f"  2) Switch active to task ({task_profile})")
    print("  3) Abort")
    choice = input("> ").strip()
    if choice == "1":
        return 0
    if choice == "2":
        rc = activate_kernel(task_profile, args.agent_id)
        if rc != 0:
            raise SystemExit(rc)
        return 0
    raise SystemExit("Aborted.")


if __name__ == "__main__":
    raise SystemExit(main())
