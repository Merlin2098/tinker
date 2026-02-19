#!/usr/bin/env python3
"""
Canonical execution wrapper for non-execution policy/planning/debugging skills.
"""

from __future__ import annotations

from typing import Any

try:
    from agents.tools.wrappers._explorer_common import parse_int
except ImportError:
    from wrappers._explorer_common import parse_int


POLICY_SKILL_PROFILES: dict[str, dict[str, Any]] = {
    "ambiguity_escalation": {
        "cluster": "governance",
        "focus": "Detect ambiguity early and escalate instead of guessing.",
        "checks": [
            "Identify missing constraints or conflicting requirements.",
            "Summarize uncertainty with explicit decision options.",
            "Block unsafe execution until ambiguity is resolved.",
        ],
    },
    "artifact_persistence_discipline": {
        "cluster": "governance",
        "focus": "Preserve execution artifacts for traceability and reproducibility.",
        "checks": [
            "Store outputs in governed artifact paths.",
            "Avoid destructive cleanup of historical records.",
            "Tag artifacts with context needed for later audit.",
        ],
    },
    "immutable_resource_respect": {
        "cluster": "governance",
        "focus": "Respect immutable/protected resources and contracts.",
        "checks": [
            "Identify protected files/resources before edits.",
            "Reject operations targeting immutable surfaces.",
            "Escalate when requested changes conflict with protections.",
        ],
    },
    "minimal_documentation_policy": {
        "cluster": "governance",
        "focus": "Generate only purposeful documentation with minimal redundancy.",
        "checks": [
            "Confirm documentation is required by task intent.",
            "Prefer concise updates over broad new docs.",
            "Avoid duplicating policy or operational guidance.",
        ],
    },
    "path_traversal_prevention": {
        "cluster": "governance",
        "focus": "Prevent path traversal and out-of-scope filesystem access.",
        "checks": [
            "Resolve and validate paths against allowed root.",
            "Reject traversal segments and escaped absolute targets.",
            "Keep all write/read operations within scoped workspace.",
        ],
    },
    "protected_file_validation": {
        "cluster": "governance",
        "focus": "Enforce protected-file rules before applying changes.",
        "checks": [
            "Cross-check targeted files against blacklist/protected patterns.",
            "Block changes that violate governance restrictions.",
            "Report violation attempts with clear rationale.",
        ],
    },
    "scope_control_discipline": {
        "cluster": "governance",
        "focus": "Maintain strict task scope and avoid opportunistic changes.",
        "checks": [
            "Track requested objective and explicit boundaries.",
            "Separate required changes from optional improvements.",
            "Defer non-scoped work to future steps/checkpoints.",
        ],
    },
    "skill_authority_first": {
        "cluster": "governance",
        "focus": "Prefer authoritative skill paths over ad-hoc reasoning workflows.",
        "checks": [
            "Detect existing skills that cover the requested capability.",
            "Route execution through canonical skill interfaces.",
            "Avoid duplicating logic already defined by active skills.",
        ],
    },
    "verification_before_completion": {
        "cluster": "governance",
        "focus": "Require fresh evidence before declaring completion.",
        "checks": [
            "Run targeted verification aligned to changed behavior.",
            "Capture objective pass/fail signals.",
            "Report residual risk when verification is partial.",
        ],
    },
    "workspace_model_awareness": {
        "cluster": "governance",
        "focus": "Honor repository workspace model and allowed modification zones.",
        "checks": [
            "Differentiate writable framework paths vs protected app code.",
            "Avoid unauthorized edits across workspace boundaries.",
            "Document assumptions when workspace model is uncertain.",
        ],
    },
    "brainstorming_design_explorer": {
        "cluster": "planning",
        "focus": "Explore feasible design options before locking implementation path.",
        "checks": [
            "Generate 2-3 viable approaches.",
            "Evaluate tradeoffs against scope, risk, and cost.",
            "Select minimal viable path with clear rationale.",
        ],
    },
    "context_loading_protocol": {
        "cluster": "planning",
        "focus": "Load context progressively and only as needed.",
        "checks": [
            "Start with compact index/context summaries.",
            "Load deeper files only for active execution paths.",
            "Keep context footprint bounded and relevant.",
        ],
    },
    "decision_process_flow": {
        "cluster": "planning",
        "focus": "Apply deterministic decision flow with explicit assumptions.",
        "checks": [
            "List candidate actions and constraints.",
            "Score/compare options with transparent criteria.",
            "Capture chosen path and rationale.",
        ],
    },
    "llm_inference_optimization": {
        "cluster": "planning",
        "focus": "Control context size and output determinism for reliability.",
        "checks": [
            "Constrain context to decision-relevant inputs.",
            "Favor deterministic settings for execution tasks.",
            "Trim/refresh stale context as task evolves.",
        ],
    },
    "output_validation_checklist": {
        "cluster": "planning",
        "focus": "Validate output completeness and contract compliance before emit.",
        "checks": [
            "Ensure required fields/artifacts are present.",
            "Check output schema/format expectations.",
            "Flag any incomplete or assumed sections explicitly.",
        ],
    },
    "risk_scoring_matrix": {
        "cluster": "planning",
        "focus": "Score risk probability/impact and define handling thresholds.",
        "checks": [
            "Identify top risks by probability and impact.",
            "Assign mitigation or rollback for high-risk items.",
            "Escalate when risk exceeds autonomous threshold.",
        ],
    },
    "execution_flow_orchestration": {
        "cluster": "execution",
        "focus": "Sequence work in stable, auditable execution slices.",
        "checks": [
            "Break work into ordered, testable steps.",
            "Record progress and blockers explicitly.",
            "Gate completion on verification outcomes.",
        ],
    },
    "git_rollback_strategy": {
        "cluster": "execution",
        "focus": "Define safe rollback approach before high-impact edits.",
        "checks": [
            "Identify rollback unit and trigger conditions.",
            "Prefer non-destructive revert-based recovery.",
            "Document rollback command path in checkpoint notes.",
        ],
    },
    "plan_archive_protocol": {
        "cluster": "execution",
        "focus": "Keep plan history durable and auditable across iterations.",
        "checks": [
            "Update active plan status before step transitions.",
            "Preserve prior plans/checkpoints without deletion.",
            "Record completion evidence per iteration.",
        ],
    },
    "debugger_orchestrator": {
        "cluster": "debugging",
        "focus": "Coordinate debugging workflow from symptom to verified fix.",
        "checks": [
            "Capture reproducible failure signal.",
            "Isolate likely root-cause region before code changes.",
            "Confirm fix with targeted regression check.",
        ],
    },
    "root_cause_tracing": {
        "cluster": "debugging",
        "focus": "Trace failure backward to originating trigger condition.",
        "checks": [
            "Map failing behavior to call/data chain.",
            "Locate earliest invariant break point.",
            "Separate trigger cause from downstream symptoms.",
        ],
    },
    "systematic_debugging": {
        "cluster": "debugging",
        "focus": "Apply repeatable debugging phases with hypothesis validation.",
        "checks": [
            "Observe and classify failure mode.",
            "Form and test hypotheses incrementally.",
            "Validate final change against original fault and side effects.",
        ],
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
        raise ValueError("skill_name is required for policy guidance wrapper.")
    skill_name = skill_name.strip()

    profile = POLICY_SKILL_PROFILES.get(skill_name)
    if profile is None:
        known = ", ".join(sorted(POLICY_SKILL_PROFILES.keys()))
        raise ValueError(f"Unknown policy skill '{skill_name}'. Known: {known}")

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
    if output_mode == "actions":
        primary = [f"Action {i + 1}: {item}" for i, item in enumerate(checks)]
    elif output_mode == "plan":
        primary = [f"Step {i + 1}: {item}" for i, item in enumerate(checks)]
    else:
        primary = checks

    return {
        "status": "ok",
        "skill": skill_name,
        "cluster": profile["cluster"],
        "focus": profile["focus"],
        "objective": objective_str or None,
        "target_paths": target_paths,
        "constraints": constraints,
        "output_mode": output_mode,
        "primary_output": primary,
    }

