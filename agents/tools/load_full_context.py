#!/usr/bin/env python3
"""
load_full_context.py

Build a consolidated context JSON from:
- static context (`load_static_context.py`)
- dynamic task artifacts (task plan, system config, summary)
- optional on-demand analysis files (treemap, dependencies_report)
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Optional

try:
    from ._context_common import load_json_file, load_yaml_file, resolve_and_validate
    from .context_loader import enrich_context
    from .load_static_context import load_static_context
except (ImportError, ValueError):
    from _context_common import load_json_file, load_yaml_file, resolve_and_validate  # type: ignore
    from context_loader import enrich_context
    from load_static_context import load_static_context


def load_full_context(
    task_plan_path: str,
    system_config_path: str,
    summary_path: str,
    on_demand: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Load static + dynamic context, optionally enriched with on-demand files."""
    context = load_static_context()
    dynamic_context: Dict[str, Any] = {}

    task_plan_abs = resolve_and_validate(task_plan_path, must_exist=True)
    dynamic_context["task_plan"] = load_json_file(task_plan_abs)

    system_config_abs = resolve_and_validate(system_config_path, must_exist=True)
    dynamic_context["system_config"] = load_yaml_file(system_config_abs)

    summary_abs = resolve_and_validate(summary_path, must_exist=True)
    dynamic_context["summary"] = load_yaml_file(summary_abs)

    full_context = {**context, **dynamic_context}

    if on_demand:
        full_context = enrich_context(full_context, on_demand)

    return full_context


def save_context_as_json(full_context: Dict[str, Any], output_path: str = "agents/logic/agent_outputs/context.json") -> None:
    output_abs = resolve_and_validate(output_path, must_exist=False)
    output_abs.parent.mkdir(parents=True, exist_ok=True)
    with open(output_abs, "w", encoding="utf-8") as f:
        json.dump(full_context, f, indent=2)
    print(f"Full context saved as JSON: {output_abs}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build consolidated static+dynamic context JSON")
    parser.add_argument(
        "--task-plan",
        default="agents/logic/agent_outputs/plans/task_plan.json",
        help="Task plan JSON path",
    )
    parser.add_argument(
        "--system-config",
        default="config/system_config.yaml",
        help="System config YAML path",
    )
    parser.add_argument(
        "--summary",
        default="agents/logic/agent_outputs/summary/summary.yaml",
        help="Summary YAML path",
    )
    parser.add_argument(
        "--on-demand",
        action="append",
        default=[],
        help="Optional on-demand file key (repeatable), e.g. treemap",
    )
    parser.add_argument(
        "--output",
        default="agents/logic/agent_outputs/context.json",
        help="Output context JSON path",
    )
    args = parser.parse_args()

    full_context = load_full_context(
        task_plan_path=args.task_plan,
        system_config_path=args.system_config,
        summary_path=args.summary,
        on_demand=args.on_demand or None,
    )
    save_context_as_json(full_context, output_path=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

