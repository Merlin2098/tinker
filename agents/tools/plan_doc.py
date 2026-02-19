#!/usr/bin/env python3
"""
Optional plan document utility for Tinker.

This tool manages review/handoff plan artifacts under:
  - agents/logic/agent_outputs/plans/plan_active/
  - agents/logic/agent_outputs/plans/archive/

It is intentionally optional and does not enforce execution workflows.
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import ValidationError, validate


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ACTIVE_DIR = ROOT / "agents" / "logic" / "agent_outputs" / "plans" / "plan_active"
DEFAULT_ARCHIVE_DIR = ROOT / "agents" / "logic" / "agent_outputs" / "plans" / "archive"
DEFAULT_SCHEMA = ROOT / "agents" / "logic" / "agent_protocol" / "schemas" / "plan_doc.schema.yaml"

ALLOWED_PLAN_STATUS = {
    "draft",
    "in_review",
    "approved",
    "in_progress",
    "completed",
    "archived",
}
ALLOWED_STEP_STATUS = {"pending", "in_progress", "completed", "blocked", "dropped"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"YAML root must be an object: {path}")
    return data


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def resolve_plan_path(path_arg: str | None, plan_id: str | None = None) -> Path:
    if path_arg:
        candidate = Path(path_arg)
        return candidate if candidate.is_absolute() else ROOT / candidate
    if not plan_id:
        raise SystemExit("Either --file or --id must be provided.")
    return DEFAULT_ACTIVE_DIR / f"{plan_id}.yaml"


def cmd_init(args: argparse.Namespace) -> int:
    path = resolve_plan_path(args.file, args.id)
    if path.exists() and not args.force:
        raise SystemExit(f"Plan already exists: {path}. Use --force to overwrite.")

    payload: dict[str, Any] = {
        "id": args.id,
        "title": args.title,
        "owner": args.owner,
        "created_at": utc_now_iso(),
        "status": args.status,
        "context": {
            "objective": args.objective,
            "scope": args.scope or "",
            "constraints": args.constraint or [],
        },
        "steps": [],
        "handoff": {"to": "", "notes": "", "updated_at": None},
        "approvals": {
            "required": bool(args.approval_required),
            "received": [],
            "approved_by": None,
            "approved_at": None,
        },
    }
    write_yaml(path, payload)
    print(f"Created plan: {path}")
    return 0


def find_step(payload: dict[str, Any], step_id: str) -> dict[str, Any]:
    steps = payload.get("steps")
    if not isinstance(steps, list):
        raise SystemExit("Invalid plan: steps must be a list.")
    for step in steps:
        if isinstance(step, dict) and step.get("id") == step_id:
            return step
    raise SystemExit(f"Step not found: {step_id}")


def cmd_add_step(args: argparse.Namespace) -> int:
    path = resolve_plan_path(args.file)
    payload = read_yaml(path)
    steps = payload.setdefault("steps", [])
    if not isinstance(steps, list):
        raise SystemExit("Invalid plan: steps must be a list.")
    if any(isinstance(s, dict) and s.get("id") == args.step_id for s in steps):
        raise SystemExit(f"Step already exists: {args.step_id}")
    step = {
        "id": args.step_id,
        "description": args.description,
        "status": args.status,
        "acceptance_criteria": args.acceptance or [],
    }
    steps.append(step)
    write_yaml(path, payload)
    print(f"Added step '{args.step_id}' to {path}")
    return 0


def cmd_update_step(args: argparse.Namespace) -> int:
    path = resolve_plan_path(args.file)
    payload = read_yaml(path)
    step = find_step(payload, args.step_id)
    if args.description is not None:
        step["description"] = args.description
    if args.status is not None:
        step["status"] = args.status
    if args.acceptance is not None:
        step["acceptance_criteria"] = args.acceptance
    write_yaml(path, payload)
    print(f"Updated step '{args.step_id}' in {path}")
    return 0


def cmd_set_status(args: argparse.Namespace) -> int:
    path = resolve_plan_path(args.file)
    payload = read_yaml(path)
    payload["status"] = args.status
    write_yaml(path, payload)
    print(f"Set plan status to '{args.status}' in {path}")
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    path = resolve_plan_path(args.file)
    payload = read_yaml(path)
    approvals = payload.setdefault("approvals", {})
    if not isinstance(approvals, dict):
        raise SystemExit("Invalid plan: approvals must be an object.")
    received = approvals.setdefault("received", [])
    if not isinstance(received, list):
        raise SystemExit("Invalid plan: approvals.received must be a list.")
    note = args.note.strip() if args.note else ""
    entry = {"by": args.by, "at": utc_now_iso(), "note": note}
    received.append(entry)
    approvals["approved_by"] = args.by
    approvals["approved_at"] = entry["at"]
    payload["status"] = "approved"
    write_yaml(path, payload)
    print(f"Approved plan {path} by {args.by}")
    return 0


def cmd_handoff(args: argparse.Namespace) -> int:
    path = resolve_plan_path(args.file)
    payload = read_yaml(path)
    handoff = payload.setdefault("handoff", {})
    if not isinstance(handoff, dict):
        raise SystemExit("Invalid plan: handoff must be an object.")
    handoff["to"] = args.to
    handoff["notes"] = args.notes
    handoff["updated_at"] = utc_now_iso()
    write_yaml(path, payload)
    print(f"Updated handoff for {path}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    path = resolve_plan_path(args.file)
    payload = read_yaml(path)
    schema_path = Path(args.schema)
    schema_path = schema_path if schema_path.is_absolute() else ROOT / schema_path
    schema = read_yaml(schema_path)
    try:
        validate(instance=payload, schema=schema)
    except ValidationError as exc:
        raise SystemExit(f"Validation failed for {path}: {exc.message}") from exc
    print(f"Validation passed: {path}")
    return 0


def cmd_archive(args: argparse.Namespace) -> int:
    source = resolve_plan_path(args.file)
    if not source.exists():
        raise SystemExit(f"Plan not found: {source}")
    archive_dir = Path(args.archive_dir)
    archive_dir = archive_dir if archive_dir.is_absolute() else ROOT / archive_dir
    archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = archive_dir / f"{source.stem}.{stamp}.yaml"
    shutil.move(str(source), str(target))
    print(f"Archived plan to: {target}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    active_dir = Path(args.active_dir)
    active_dir = active_dir if active_dir.is_absolute() else ROOT / active_dir
    active_dir.mkdir(parents=True, exist_ok=True)
    paths = sorted(active_dir.glob("*.yaml"))
    if not paths:
        print("No active plan docs.")
        return 0
    for path in paths:
        print(path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Optional Tinker plan document utility.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create a new plan document.")
    p_init.add_argument("--id", required=True, help="Stable plan id (filename stem by default).")
    p_init.add_argument("--title", required=True)
    p_init.add_argument("--objective", required=True)
    p_init.add_argument("--owner", default="manual")
    p_init.add_argument("--scope", default="")
    p_init.add_argument(
        "--status",
        default="draft",
        choices=sorted(ALLOWED_PLAN_STATUS),
        help="Initial plan status.",
    )
    p_init.add_argument("--constraint", action="append", help="Constraint. Repeat as needed.")
    p_init.add_argument("--approval-required", action="store_true")
    p_init.add_argument("--file", help="Output path. Defaults to plan_active/<id>.yaml")
    p_init.add_argument("--force", action="store_true", help="Overwrite if file exists.")
    p_init.set_defaults(func=cmd_init)

    p_add = sub.add_parser("add-step", help="Add a step to an existing plan.")
    p_add.add_argument("--file", required=True, help="Plan file path.")
    p_add.add_argument("--step-id", required=True)
    p_add.add_argument("--description", required=True)
    p_add.add_argument("--status", default="pending", choices=sorted(ALLOWED_STEP_STATUS))
    p_add.add_argument("--acceptance", action="append", help="Acceptance criteria. Repeat as needed.")
    p_add.set_defaults(func=cmd_add_step)

    p_update = sub.add_parser("update-step", help="Update an existing step.")
    p_update.add_argument("--file", required=True, help="Plan file path.")
    p_update.add_argument("--step-id", required=True)
    p_update.add_argument("--description")
    p_update.add_argument("--status", choices=sorted(ALLOWED_STEP_STATUS))
    p_update.add_argument(
        "--acceptance",
        action="append",
        help="Replace acceptance criteria list. Repeat for multiple entries.",
    )
    p_update.set_defaults(func=cmd_update_step)

    p_status = sub.add_parser("set-status", help="Set plan status.")
    p_status.add_argument("--file", required=True, help="Plan file path.")
    p_status.add_argument("--status", required=True, choices=sorted(ALLOWED_PLAN_STATUS))
    p_status.set_defaults(func=cmd_set_status)

    p_approve = sub.add_parser("approve", help="Record approval and mark plan as approved.")
    p_approve.add_argument("--file", required=True, help="Plan file path.")
    p_approve.add_argument("--by", required=True, help="Approver identity.")
    p_approve.add_argument("--note", default="", help="Optional approval note.")
    p_approve.set_defaults(func=cmd_approve)

    p_handoff = sub.add_parser("handoff", help="Record handoff target and notes.")
    p_handoff.add_argument("--file", required=True, help="Plan file path.")
    p_handoff.add_argument("--to", required=True, help="Handoff target.")
    p_handoff.add_argument("--notes", required=True, help="Handoff notes.")
    p_handoff.set_defaults(func=cmd_handoff)

    p_validate = sub.add_parser("validate", help="Validate plan document against schema.")
    p_validate.add_argument("--file", required=True, help="Plan file path.")
    p_validate.add_argument(
        "--schema",
        default=str(DEFAULT_SCHEMA.relative_to(ROOT)),
        help="Schema path (default: agents/logic/agent_protocol/schemas/plan_doc.schema.yaml).",
    )
    p_validate.set_defaults(func=cmd_validate)

    p_archive = sub.add_parser("archive", help="Move plan from active to archive.")
    p_archive.add_argument("--file", required=True, help="Plan file path.")
    p_archive.add_argument(
        "--archive-dir",
        default=str(DEFAULT_ARCHIVE_DIR.relative_to(ROOT)),
        help="Archive directory path.",
    )
    p_archive.set_defaults(func=cmd_archive)

    p_list = sub.add_parser("list", help="List active plan docs.")
    p_list.add_argument(
        "--active-dir",
        default=str(DEFAULT_ACTIVE_DIR.relative_to(ROOT)),
        help="Active plan directory path.",
    )
    p_list.set_defaults(func=cmd_list)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

