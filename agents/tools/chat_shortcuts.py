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
    from agents.tools._repo_root import find_project_root
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
    "init": "init",
    "start": "init",
    "bootstrap": "init",
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
    parser.add_argument(
        "--profile",
        default="FULL",
        help="Kernel profile for init (LITE/STANDARD/FULL) [default: FULL]",
    )
    args = parser.parse_args()

    resolved = normalize_intent(args.intent)
    if not resolved:
        valid = ", ".join(sorted(set(INTENT_ALIASES.keys())))
        raise SystemExit(f"Unknown intent: {args.intent!r}. Supported intents: {valid}")

    root = find_project_root(Path(__file__).resolve().parent)
    runner = root / "agents" / "tools" / "git_checkpoint.py"
    py = Path(sys.executable)

    if resolved == "commit":
        message = args.message or now_checkpoint_message()
        return run_cmd([str(py), str(runner), "commit", "--message", message], root)

    if resolved == "sync":
        cmd = [str(py), str(runner), "sync", "--remote", args.remote]
        if args.branch:
            cmd += ["--branch", args.branch]
        return run_cmd(cmd, root)

    if resolved == "init":
        profile = args.profile.upper()
        print(f"🚀 Initializing Tinker Session [Kernel: {profile}]...")
        
        # 1. Activate Kernel
        print(f"  [1/4] Activating Kernel ({profile})...")
        kernel_script = root / "agents" / "tools" / "activate_kernel.py"
        if run_cmd([str(py), str(kernel_script), "--profile", profile], root) != 0:
            return 1
            
        # 2. Compile Registry (SSOT)
        print("  [2/4] Compiling Skill Registry...")
        compiler_script = root / "agents" / "tools" / "compile_registry.py"
        if run_cmd([str(py), str(compiler_script)], root) != 0:
            return 1

        # 3. Load Context
        print("  [3/4] Loading Static Context...")
        context_script = root / "agents" / "tools" / "load_static_context.py"
        if run_cmd([str(py), str(context_script)], root) != 0:
            return 1
            
        # 4. Verify Mode
        print("  [4/4] Verifying Mode State...")
        mode_script = root / "agents" / "tools" / "mode_selector.py"
        run_cmd([str(py), str(mode_script), "--read-state"], root)
        
        print("\n✅ Session Initialized. Ready for task execution.")
        return 0

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
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)

