#!/usr/bin/env python3
"""
Natural-language shortcut router for common chat operations.

Current supported intents:
- commit
- sync
- commit and sync
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from agent_tools._repo_root import find_project_root
except ImportError:
    from _repo_root import find_project_root  # type: ignore


INTENT_ALIASES = {
    "commit": "commit",
    "checkpoint": "commit",
    "sync": "sync",
    "push": "sync",
    "commit and sync": "commit-sync",
    "commit & sync": "commit-sync",
    "checkpoint and sync": "commit-sync",
    "commit-sync": "commit-sync",
}


def now_checkpoint_message() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"checkpoint: chat shortcut {stamp}"


def normalize_intent(raw: str) -> str:
    cleaned = " ".join(raw.strip().lower().replace("_", " ").split())
    return INTENT_ALIASES.get(cleaned, "")


def run_cmd(args: list[str], cwd: Path) -> int:
    proc = subprocess.run(args, cwd=str(cwd))
    return int(proc.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run chat shortcut intents (commit/sync)")
    parser.add_argument(
        "intent",
        help='Shortcut intent text, e.g. "commit", "sync", or "commit and sync"',
    )
    parser.add_argument(
        "--message",
        help="Commit message for commit/commit-and-sync (auto-generated if omitted)",
    )
    parser.add_argument("--remote", default="origin", help="Git remote for sync operations")
    parser.add_argument("--branch", help="Git branch for sync operations (default: current branch)")
    args = parser.parse_args()

    resolved = normalize_intent(args.intent)
    if not resolved:
        valid = ", ".join(sorted(set(INTENT_ALIASES.keys())))
        raise SystemExit(f"Unknown intent: {args.intent!r}. Supported intents: {valid}")

    root = find_project_root(Path(__file__).resolve().parent)
    runner = root / "agent_tools" / "git_checkpoint.py"
    py = Path(sys.executable)

    if resolved == "commit":
        message = args.message or now_checkpoint_message()
        return run_cmd([str(py), str(runner), "commit", "--message", message], root)

    if resolved == "sync":
        cmd = [str(py), str(runner), "sync", "--remote", args.remote]
        if args.branch:
            cmd += ["--branch", args.branch]
        return run_cmd(cmd, root)

    # commit-sync
    message = args.message or now_checkpoint_message()
    cmd = [
        str(py),
        str(runner),
        "commit-sync",
        "--message",
        message,
        "--remote",
        args.remote,
    ]
    if args.branch:
        cmd += ["--branch", args.branch]
    return run_cmd(cmd, root)


if __name__ == "__main__":
    raise SystemExit(main())
