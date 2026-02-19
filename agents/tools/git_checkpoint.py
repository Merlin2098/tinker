#!/usr/bin/env python3
"""
Lightweight git helper for checkpoint commit/sync workflows.

Usage examples:
  python agents/tools/git_checkpoint.py commit --message "checkpoint: update docs"
  python agents/tools/git_checkpoint.py sync
  python agents/tools/git_checkpoint.py commit-sync --message "checkpoint: complete rework slice"
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    from agents.tools._repo_root import find_project_root
except ImportError:
    from _repo_root import find_project_root  # type: ignore


def run_git(args: list[str], cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def current_branch(cwd: Path) -> str:
    rc, out, err = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if rc != 0:
        raise SystemExit(f"Failed to resolve current branch: {err or out}")
    branch = out.strip()
    if not branch:
        raise SystemExit("Current branch is empty.")
    return branch


def has_pending_changes(cwd: Path) -> bool:
    rc, out, err = run_git(["status", "--porcelain"], cwd)
    if rc != 0:
        raise SystemExit(f"Failed to inspect git status: {err or out}")
    return bool(out.strip())


def commit_changes(cwd: Path, message: str) -> None:
    rc, _, err = run_git(["add", "-A"], cwd)
    if rc != 0:
        raise SystemExit(f"git add failed: {err}")

    rc, out, err = run_git(["commit", "-m", message], cwd)
    if rc != 0:
        if "nothing to commit" in (out + "\n" + err).lower():
            print("No changes to commit.")
            return
        raise SystemExit(f"git commit failed: {err or out}")
    print(out or "Commit created.")


def push_changes(cwd: Path, remote: str, branch: str | None) -> None:
    target_branch = branch or current_branch(cwd)
    rc, out, err = run_git(["push", remote, target_branch], cwd)
    if rc != 0:
        raise SystemExit(f"git push failed: {err or out}")
    print(out or f"Pushed to {remote}/{target_branch}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Checkpoint git helper (commit/sync)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_commit = sub.add_parser("commit", help="Stage all and create commit")
    p_commit.add_argument("--message", "-m", required=True, help="Commit message")

    p_sync = sub.add_parser("sync", help="Push current (or explicit) branch")
    p_sync.add_argument("--remote", default="origin", help="Git remote name (default: origin)")
    p_sync.add_argument("--branch", help="Branch name (default: current branch)")

    p_both = sub.add_parser("commit-sync", help="Commit then push")
    p_both.add_argument("--message", "-m", required=True, help="Commit message")
    p_both.add_argument("--remote", default="origin", help="Git remote name (default: origin)")
    p_both.add_argument("--branch", help="Branch name (default: current branch)")

    args = parser.parse_args()
    root = find_project_root(Path(__file__).resolve().parent)

    if args.command == "commit":
        if not has_pending_changes(root):
            print("No changes to commit.")
            return 0
        commit_changes(root, args.message)
        return 0

    if args.command == "sync":
        push_changes(root, args.remote, args.branch)
        return 0

    if args.command == "commit-sync":
        if has_pending_changes(root):
            commit_changes(root, args.message)
        else:
            print("No changes to commit; continuing to push.")
        push_changes(root, args.remote, args.branch)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

