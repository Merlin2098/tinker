#!/usr/bin/env python3
"""
Canonical execution wrapper for Python quality advisory skills.
"""

from __future__ import annotations

from typing import Any

try:
    from agent_tools.wrappers._explorer_common import parse_int
except ImportError:
    from wrappers._explorer_common import parse_int


PYTHON_SKILL_PROFILES: dict[str, dict[str, Any]] = {
    "code_structuring_pythonic": {
        "focus": "Structure code with cohesive modules and clear separation of concerns.",
        "checks": [
            "Functions/classes follow single responsibility.",
            "Modules expose clear public API boundaries.",
            "Control flow remains readable and shallow where possible.",
        ],
        "artifacts": ["module layout sketch", "refactor checklist"],
    },
    "data_integrity_guardian": {
        "focus": "Protect correctness with validation, constraints, and integrity checks.",
        "checks": [
            "Input contracts are validated at boundaries.",
            "State transitions preserve invariants.",
            "Failure paths avoid partial/invalid persisted state.",
        ],
        "artifacts": ["integrity checklist", "guard clauses list"],
    },
    "secure_python_practices": {
        "focus": "Apply secure defaults and reduce attack surface in Python code.",
        "checks": [
            "Untrusted inputs are validated and sanitized.",
            "Secrets are not hardcoded or logged.",
            "External execution and deserialization are restricted/safe.",
        ],
        "artifacts": ["security hardening checklist", "risk notes"],
    },
    "type_master": {
        "focus": "Improve static guarantees with accurate type hints and contracts.",
        "checks": [
            "Public functions/classes expose explicit types.",
            "Optional/None semantics are explicit.",
            "Generic/container types are precise where useful.",
        ],
        "artifacts": ["typing plan", "type coverage targets"],
    },
    "async_concurrency_expert": {
        "focus": "Design safe async/concurrent flows with clear cancellation and backpressure behavior.",
        "checks": [
            "Blocking work is isolated from async event loop.",
            "Cancellation and timeout behavior is explicit.",
            "Shared state access is synchronized or avoided.",
        ],
        "artifacts": ["concurrency design notes", "failure mode checklist"],
    },
    "microservices_api_architect": {
        "focus": "Shape service boundaries and API contracts for reliability and evolution.",
        "checks": [
            "Endpoints have explicit request/response contracts.",
            "Versioning/backward compatibility is defined.",
            "Service responsibilities avoid overlap.",
        ],
        "artifacts": ["API contract checklist", "service boundary notes"],
    },
    "code_analysis_qa_gate": {
        "focus": "Define deterministic quality gates before integration/release.",
        "checks": [
            "Static checks have clear pass/fail thresholds.",
            "Critical warnings are treated as build blockers.",
            "Gate order is deterministic and documented.",
        ],
        "artifacts": ["QA gate matrix", "failure triage policy"],
    },
    "testing_qa_mentor": {
        "focus": "Design robust, maintainable test strategy with meaningful coverage.",
        "checks": [
            "Critical paths include automated tests.",
            "Fixtures are minimal and deterministic.",
            "Assertions validate behavior, not implementation details.",
        ],
        "artifacts": ["test plan", "coverage focus list"],
    },
    "regression_test_automation": {
        "focus": "Prevent behavior drift with stable regression automation.",
        "checks": [
            "Baseline cases cover high-risk behavior.",
            "Regression suite is reproducible and isolated.",
            "Flaky tests are quarantined and tracked.",
        ],
        "artifacts": ["regression suite outline", "stability checklist"],
    },
    "naming_control_flow": {
        "focus": "Increase readability through naming consistency and straightforward control flow.",
        "checks": [
            "Identifiers reveal intent and unit/domain meaning.",
            "Branching complexity is bounded and understandable.",
            "Magic values are replaced by named constants/config.",
        ],
        "artifacts": ["naming conventions list", "complexity hotspots"],
    },
    "performance_profiler": {
        "focus": "Target measurable bottlenecks with evidence-driven optimization.",
        "checks": [
            "Hot paths are identified before optimization.",
            "Memory/CPU bottlenecks are measured and compared.",
            "Performance changes are validated against baseline.",
        ],
        "artifacts": ["profiling plan", "baseline vs optimized report"],
    },
    "dependency_audit": {
        "focus": "Audit dependency risk across security, compatibility, and maintenance.",
        "checks": [
            "Critical vulnerabilities are identified and prioritized.",
            "Version constraints are explicit and coherent.",
            "Unused/high-risk dependencies are flagged.",
        ],
        "artifacts": ["dependency audit summary", "remediation queue"],
    },
    "linter_formatter_guru": {
        "focus": "Standardize style/quality tooling to reduce noise and drift.",
        "checks": [
            "Formatter and linter rules do not conflict.",
            "Rules are deterministic across local/CI runs.",
            "Pre-commit hooks enforce baseline automatically.",
        ],
        "artifacts": ["toolchain config checklist", "CI quality gate notes"],
    },
    "refactoring_assistant": {
        "focus": "Plan low-risk refactors that improve maintainability.",
        "checks": [
            "Behavior-preserving steps are sequenced incrementally.",
            "High-risk edits include rollback strategy.",
            "Tests guard critical behavior before/after changes.",
        ],
        "artifacts": ["refactor plan", "rollback strategy"],
    },
    "api_client_generator": {
        "focus": "Define maintainable API client generation and lifecycle strategy.",
        "checks": [
            "Client contract aligns with API schema/version.",
            "Auth/retry/error handling policies are explicit.",
            "Generated code boundaries and regeneration flow are defined.",
        ],
        "artifacts": ["client generation checklist", "runtime policy notes"],
    },
    "config_env_manager": {
        "focus": "Centralize environment/config handling with predictable precedence.",
        "checks": [
            "Config sources and precedence are explicit.",
            "Required env vars are validated early.",
            "Secrets/config are separated from code defaults.",
        ],
        "artifacts": ["config contract", "environment matrix"],
    },
    "externalized_logic_handler": {
        "focus": "Move volatile business rules into configurable external forms.",
        "checks": [
            "Rule ownership and update path are explicit.",
            "Runtime validation covers rule shape and required fields.",
            "Fallback/default behavior is deterministic.",
        ],
        "artifacts": ["rule externalization plan", "validation schema notes"],
    },
    "serialization_persistence": {
        "focus": "Define safe, versionable serialization/persistence boundaries.",
        "checks": [
            "Serialization formats are explicit and versioned.",
            "Backward compatibility/migration strategy is defined.",
            "Persistence writes are atomic where needed.",
        ],
        "artifacts": ["serialization contract", "migration notes"],
    },
    "devops_packaging": {
        "focus": "Package and distribute Python artifacts predictably.",
        "checks": [
            "Build metadata/versioning is coherent.",
            "Dependencies and optional extras are explicit.",
            "Release outputs are reproducible and validated.",
        ],
        "artifacts": ["packaging checklist", "release readiness notes"],
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
        raise ValueError("skill_name is required for python quality advisor wrapper.")
    skill_name = skill_name.strip()

    profile = PYTHON_SKILL_PROFILES.get(skill_name)
    if profile is None:
        known = ", ".join(sorted(PYTHON_SKILL_PROFILES.keys()))
        raise ValueError(f"Unknown python advisory skill '{skill_name}'. Known: {known}")

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
        "cluster": "python_quality",
        "focus": profile["focus"],
        "objective": objective_str or None,
        "target_paths": target_paths,
        "constraints": constraints,
        "output_mode": output_mode,
        "primary_output": primary,
        "supporting_artifacts": artifacts,
    }
