#!/usr/bin/env python3
"""
Canonical execution wrapper for UI advisory skills.
"""

from __future__ import annotations

from typing import Any

try:
    from agent_tools.wrappers._explorer_common import parse_int
except ImportError:
    from wrappers._explorer_common import parse_int


UI_SKILL_PROFILES: dict[str, dict[str, Any]] = {
    "ui_framework_selection": {
        "focus": "Select an implementation framework based on delivery stage and constraints.",
        "checks": [
            "MVP/prototype and production scope are explicitly separated.",
            "Framework decision aligns with deployment and team capabilities.",
            "Migration path is defined when starting from MVP stack.",
        ],
        "artifacts": ["framework decision record", "migration triggers"],
    },
    "ui_widget_modularity": {
        "focus": "Design reusable UI components with clear boundaries.",
        "checks": [
            "Widgets have single responsibility and explicit inputs/outputs.",
            "Cross-widget coupling is minimized.",
            "Shared logic is extracted into reusable modules.",
        ],
        "artifacts": ["component boundary map", "reusability checklist"],
    },
    "ui_theme_binding": {
        "focus": "Ensure theme behavior is centralized, reactive, and consistent.",
        "checks": [
            "Theme tokens are centralized and reusable.",
            "Theme switching updates all bound components deterministically.",
            "Fallback/default theme behavior is defined.",
        ],
        "artifacts": ["theme token set", "binding checklist"],
    },
    "ui_layout_proportionality": {
        "focus": "Maintain stable layout behavior across common viewport/device ranges.",
        "checks": [
            "Critical screens have responsive layout rules.",
            "Spacing/sizing scale remains proportional across breakpoints.",
            "Overflow/truncation behaviors are defined.",
        ],
        "artifacts": ["layout breakpoint matrix", "responsive QA checklist"],
    },
    "ui_identity_policy": {
        "focus": "Apply consistent app identity naming/versioning across UI surfaces.",
        "checks": [
            "Single source exists for app name/version metadata.",
            "Identity usage is consistent in splash/title/about/settings.",
            "Branding updates propagate without manual duplication.",
        ],
        "artifacts": ["identity source map", "branding consistency checklist"],
    },
    "ui_splash_and_lazy_loading": {
        "focus": "Manage startup loading UX with clear progress and staged initialization.",
        "checks": [
            "Splash/startup transitions are non-blocking and deterministic.",
            "Heavy resources load lazily with explicit ordering.",
            "Failure and timeout states provide clear user feedback.",
        ],
        "artifacts": ["startup sequence plan", "lazy-load failure handling notes"],
    },
    "ui_application_assets": {
        "focus": "Organize UI assets with predictable lookup and packaging behavior.",
        "checks": [
            "Asset paths are centralized and environment-aware.",
            "Missing asset fallback behavior is explicit.",
            "Packaging/runtime paths are validated for distribution mode.",
        ],
        "artifacts": ["asset manifest policy", "packaging asset checklist"],
    },
}


def _parse_strings(value: Any, *, field: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list of strings when provided.")

    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field} entries must be non-empty strings.")
        out.append(item.strip())
    return out


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    skill_name = args.get("skill_name")
    if not isinstance(skill_name, str) or not skill_name.strip():
        raise ValueError("skill_name is required for ui advisor wrapper.")
    skill_name = skill_name.strip()

    profile = UI_SKILL_PROFILES.get(skill_name)
    if profile is None:
        known = ", ".join(sorted(UI_SKILL_PROFILES.keys()))
        raise ValueError(f"Unknown ui advisory skill '{skill_name}'. Known: {known}")

    objective = args.get("objective")
    if objective is not None and (not isinstance(objective, str) or not objective.strip()):
        raise ValueError("objective must be a non-empty string when provided.")
    objective_str = objective.strip() if isinstance(objective, str) else ""

    output_mode = args.get("output_mode", "checklist")
    if not isinstance(output_mode, str) or not output_mode.strip():
        raise ValueError("output_mode must be a non-empty string when provided.")
    output_mode = output_mode.strip().lower()
    if output_mode not in {"checklist", "plan", "actions"}:
        raise ValueError("output_mode must be one of: checklist, plan, actions.")

    target_paths = _parse_strings(args.get("target_paths"), field="target_paths")
    constraints = _parse_strings(args.get("constraints"), field="constraints")
    max_items = parse_int(args.get("max_items"), field="max_items", default=6, minimum=1, maximum=20)

    checks = profile["checks"][:max_items]
    artifacts = profile["artifacts"][:max_items]

    if output_mode == "actions":
        primary = [f"Action {i + 1}: {item}" for i, item in enumerate(checks)]
    elif output_mode == "plan":
        primary = [f"Step {i + 1}: {item}" for i, item in enumerate(checks)]
    else:
        primary = checks

    return {
        "status": "ok",
        "skill": skill_name,
        "cluster": "ui",
        "focus": profile["focus"],
        "objective": objective_str or None,
        "target_paths": target_paths,
        "constraints": constraints,
        "output_mode": output_mode,
        "primary_output": primary,
        "supporting_artifacts": artifacts,
    }
