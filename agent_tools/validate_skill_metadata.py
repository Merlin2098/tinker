#!/usr/bin/env python3
"""
Skill metadata validator.

Validates metadata/body coverage for indexed skills and enforces thin-skill
rules for wrapper-backed skills.

Usage:
    python validate_skill_metadata.py
    python validate_skill_metadata.py --verbose
    python validate_skill_metadata.py --tier lazy
    python validate_skill_metadata.py --advisory
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SKILLS_DIR = PROJECT_ROOT / "agent" / "skills"
INDEX_FILE = SKILLS_DIR / "_index.yaml"
RUN_WRAPPER_PATH = PROJECT_ROOT / "agent_tools" / "run_wrapper.py"

REQUIRED_FIELDS = {
    "name",
    "tier",
    "cluster",
    "agent_binding",
    "modes",
    "token_estimate",
}
RECOMMENDED_FIELDS = {"requires", "exclusive_with", "triggers", "body_file", "priority", "purpose"}
EXECUTION_REQUIRED_FIELDS = {"entrypoint", "command"}
EXECUTION_EXEMPT_CLUSTERS = {"runtime"}

# Pattern -> diagnostic label
BUSINESS_LOGIC_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\s*def\s+\w+\s*\(", re.MULTILINE), "python function definition"),
    (re.compile(r"^\s*class\s+\w+", re.MULTILINE), "python class definition"),
    (re.compile(r"^\s*import\s+[A-Za-z_]", re.MULTILINE), "python import statement"),
    (re.compile(r"^\s*from\s+[A-Za-z_][\w.]*\s+import\s+", re.MULTILINE), "python from-import statement"),
    (re.compile(r"if\s+__name__\s*==\s*[\"']__main__[\"']"), "python __main__ block"),
    (re.compile(r"subprocess\."), "subprocess invocation"),
]


def load_yaml(path: Path) -> Any:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(f"PyYAML required: {exc}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def collect_skills_from_index(index_path: Path) -> list[dict[str, Any]]:
    data = load_yaml(index_path)
    if not isinstance(data, dict):
        return []
    index = data.get("index", [])
    return index if isinstance(index, list) else []


def find_meta_file(skill_name: str) -> Path | None:
    matches = list(SKILLS_DIR.rglob(f"{skill_name}.meta.yaml"))
    return matches[0] if matches else None


def find_body_file(skill_name: str) -> Path | None:
    matches = [p for p in SKILLS_DIR.rglob(f"{skill_name}.md") if p.name != "README.md"]
    return matches[0] if matches else None


def load_wrapper_skill_names() -> set[str]:
    if not RUN_WRAPPER_PATH.exists():
        return set()
    content = RUN_WRAPPER_PATH.read_text(encoding="utf-8")
    return set(re.findall(r'^\s*"([^"]+)":\s*_bind_skill', content, re.MULTILINE))


def validate_meta_fields(meta_data: dict[str, Any], skill_name: str) -> tuple[list[str], list[str]]:
    missing_required: list[str] = []
    missing_recommended: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in meta_data:
            missing_required.append(f"{skill_name}: missing required field '{field}'")

    for field in RECOMMENDED_FIELDS:
        if field not in meta_data:
            missing_recommended.append(f"{skill_name}: missing recommended field '{field}'")

    return missing_required, missing_recommended


def validate_execution_contract(
    meta_data: dict[str, Any],
    skill_name: str,
    wrapper_skills: set[str],
) -> list[str]:
    cluster = str(meta_data.get("cluster", "")).strip().lower()
    needs_execution_contract = skill_name in wrapper_skills and cluster not in EXECUTION_EXEMPT_CLUSTERS
    if not needs_execution_contract:
        return []

    execution = meta_data.get("execution")
    if not isinstance(execution, dict):
        return [f"{skill_name}: missing required execution contract mapping"]

    issues = []
    for field in EXECUTION_REQUIRED_FIELDS:
        value = execution.get(field)
        if not isinstance(value, str) or not value.strip():
            issues.append(f"{skill_name}: execution missing required field '{field}'")
    return issues


def scan_business_logic(body_path: Path, skill_name: str) -> list[str]:
    content = body_path.read_text(encoding="utf-8")
    issues: list[str] = []
    for pattern, label in BUSINESS_LOGIC_PATTERNS:
        if pattern.search(content):
            issues.append(f"{skill_name}: thin-skill violation detected ({label}) in {body_path.as_posix()}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate skill metadata and thin-skill contracts")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show details for each skill")
    parser.add_argument("--tier", choices=["core", "lazy", "dormant"], help="Filter by tier")
    parser.add_argument(
        "--strict",
        dest="strict",
        action="store_true",
        default=True,
        help="Fail with non-zero exit on critical issues (default)",
    )
    parser.add_argument(
        "--advisory",
        dest="strict",
        action="store_false",
        help="Report issues without failing",
    )
    parser.add_argument(
        "--check-business-logic",
        dest="check_business_logic",
        action="store_true",
        default=True,
        help="Scan wrapper-backed skill markdown for business-logic patterns (default)",
    )
    parser.add_argument(
        "--no-check-business-logic",
        dest="check_business_logic",
        action="store_false",
        help="Disable business-logic scanning",
    )
    args = parser.parse_args()

    if not INDEX_FILE.exists():
        print(f"[ERROR] Skill index not found: {INDEX_FILE}")
        return 1

    skills = collect_skills_from_index(INDEX_FILE)
    if not skills:
        print("[ERROR] No skills found in index.")
        return 1

    if args.tier:
        skills = [s for s in skills if s.get("tier") == args.tier]
    wrapper_skills = load_wrapper_skill_names()

    with_meta = []
    without_meta = []
    with_body = []
    without_body = []

    strict_issues: list[str] = []
    advisory_notes: list[str] = []

    for skill in skills:
        name = str(skill.get("name", "")).strip()
        tier = str(skill.get("tier", "unknown"))
        if not name:
            continue

        meta_path = find_meta_file(name)
        body_path = find_body_file(name)

        if meta_path:
            with_meta.append({"name": name, "tier": tier, "meta_path": meta_path})
        else:
            without_meta.append({"name": name, "tier": tier})
            strict_issues.append(f"{name}: missing .meta.yaml")

        if body_path:
            with_body.append({"name": name, "body_path": body_path})
        else:
            without_body.append({"name": name, "tier": tier})
            strict_issues.append(f"{name}: missing .md body")

        if not meta_path:
            continue

        try:
            meta_data = load_yaml(meta_path)
        except Exception as exc:
            strict_issues.append(f"{name}: failed to parse metadata: {exc}")
            continue

        if not isinstance(meta_data, dict):
            strict_issues.append(f"{name}: metadata root must be a mapping")
            continue

        missing_required, missing_recommended = validate_meta_fields(meta_data, name)
        strict_issues.extend(missing_required)
        advisory_notes.extend(missing_recommended)

        strict_issues.extend(validate_execution_contract(meta_data, name, wrapper_skills))

        cluster = str(meta_data.get("cluster", "")).strip().lower()
        needs_execution_contract = name in wrapper_skills and cluster not in EXECUTION_EXEMPT_CLUSTERS
        if args.check_business_logic and body_path and needs_execution_contract:
            strict_issues.extend(scan_business_logic(body_path, name))

    total = len(skills)
    tier_label = f" (tier: {args.tier})" if args.tier else ""
    print("=" * 60)
    print(f"SKILL METADATA VALIDATION{tier_label}")
    print("=" * 60)
    print(f"Total skills scanned: {total}")
    print(f"With .meta.yaml:      {len(with_meta)}")
    print(f"Without .meta.yaml:   {len(without_meta)}")
    print(f"With .md body:        {len(with_body)}")
    print(f"Without .md body:     {len(without_body)}")

    if args.verbose and with_meta:
        print(f"\n--- Skills WITH .meta.yaml ({len(with_meta)}) ---")
        for item in with_meta:
            print(f"  [OK] {item['name']} ({item['tier']})")

    if without_meta:
        print(f"\n--- Skills WITHOUT .meta.yaml ({len(without_meta)}) ---")
        for item in without_meta:
            print(f"  [FAIL] {item['name']} ({item['tier']})")

    if without_body:
        print(f"\n--- Skills WITHOUT .md body ({len(without_body)}) ---")
        for item in without_body:
            print(f"  [FAIL] {item['name']} ({item['tier']})")

    if advisory_notes:
        print(f"\n--- Advisory Notes ({len(advisory_notes)}) ---")
        for note in advisory_notes[:50]:
            print(f"  [INFO] {note}")
        if len(advisory_notes) > 50:
            print("  [INFO] ...")

    if strict_issues:
        print(f"\n--- Critical Issues ({len(strict_issues)}) ---")
        for issue in strict_issues[:100]:
            print(f"  [FAIL] {issue}")
        if len(strict_issues) > 100:
            print("  [FAIL] ...")

    print("=" * 60)
    if strict_issues:
        print("STATUS: FAILED")
    else:
        print("STATUS: PASSED")
    print("=" * 60)

    if strict_issues and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
