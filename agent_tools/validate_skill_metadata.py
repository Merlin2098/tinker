#!/usr/bin/env python3
"""
Skill Metadata Validator (Advisory Linter)

Checks which skills have .meta.yaml files and which rely on implicit defaults.
Reports metadata coverage, missing fields, and potential issues.

This is an ADVISORY tool — it does not block execution.

Usage:
    python validate_skill_metadata.py
    python validate_skill_metadata.py --verbose
    python validate_skill_metadata.py --tier lazy
    python validate_skill_metadata.py --check-fields
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Resolve paths relative to this script's parent (project root)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SKILLS_DIR = PROJECT_ROOT / "agent" / "skills"
INDEX_FILE = SKILLS_DIR / "_index.yaml"

# Minimal required fields for a .meta.yaml to be considered complete
REQUIRED_FIELDS = {"name", "tier", "cluster", "agent_binding", "modes", "max_phase", "token_estimate"}

# Fields that are recommended but not strictly required
RECOMMENDED_FIELDS = {"requires", "exclusive_with", "triggers", "body_file", "priority", "purpose"}

# Implicit defaults (must match _trigger_engine.yaml implicit_defaults section)
IMPLICIT_DEFAULTS = {
    "agent_binding": {"mandatory": ["agent_senior", "agent_inspector"], "optional": []},
    "modes": ["ANALYZE_AND_IMPLEMENT"],
    "token_estimate": 1500,
    "max_phase": 1,
    "requires": [],
    "exclusive_with": [],
}


def load_yaml(path: Path) -> Any:
    """Load a YAML file. Falls back to basic parsing if PyYAML is not available."""
    try:
        import yaml
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        print("[WARN] PyYAML not installed. Install with: pip install pyyaml")
        print("       Falling back to file-existence checks only.")
        return None


def collect_skills_from_index(index_path: Path) -> list[dict]:
    """Parse _index.yaml and return list of skill entries."""
    data = load_yaml(index_path)
    if data is None:
        return []
    return data.get("index", [])


def find_meta_file(skill_name: str) -> Path | None:
    """Search for a .meta.yaml file matching the skill name."""
    matches = list(SKILLS_DIR.rglob(f"{skill_name}.meta.yaml"))
    return matches[0] if matches else None


def find_body_file(skill_name: str) -> Path | None:
    """Search for a .md body file matching the skill name."""
    matches = list(SKILLS_DIR.rglob(f"{skill_name}.md"))
    # Filter out README.md files
    matches = [m for m in matches if m.name != "README.md"]
    return matches[0] if matches else None


def validate_meta_fields(meta_data: dict, skill_name: str) -> list[str]:
    """Check a .meta.yaml for missing required/recommended fields."""
    issues = []
    if meta_data is None:
        return [f"{skill_name}: could not parse .meta.yaml"]

    for field in REQUIRED_FIELDS:
        if field not in meta_data:
            issues.append(f"{skill_name}: missing required field '{field}'")

    for field in RECOMMENDED_FIELDS:
        if field not in meta_data:
            issues.append(f"{skill_name}: missing recommended field '{field}' (not critical)")

    return issues


def main():
    parser = argparse.ArgumentParser(description="Validate skill metadata coverage")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show details for each skill")
    parser.add_argument("--tier", choices=["core", "lazy", "dormant"], help="Filter by tier")
    parser.add_argument("--check-fields", action="store_true", help="Validate fields inside .meta.yaml files")
    args = parser.parse_args()

    if not INDEX_FILE.exists():
        print(f"[ERROR] Skill index not found: {INDEX_FILE}")
        sys.exit(1)

    skills = collect_skills_from_index(INDEX_FILE)
    if not skills:
        print("[ERROR] No skills found in index (PyYAML may be missing)")
        sys.exit(1)

    # Filter by tier if requested
    if args.tier:
        skills = [s for s in skills if s.get("tier") == args.tier]

    # Classify skills
    with_meta = []
    without_meta = []
    with_body = []
    without_body = []

    for skill in skills:
        name = skill.get("name", "unknown")
        tier = skill.get("tier", "unknown")

        meta_path = find_meta_file(name)
        body_path = find_body_file(name)

        if meta_path:
            with_meta.append({"name": name, "tier": tier, "meta_path": meta_path})
        else:
            without_meta.append({"name": name, "tier": tier})

        if body_path:
            with_body.append(name)
        else:
            without_body.append({"name": name, "tier": tier})

    # Report
    total = len(skills)
    tier_label = f" (tier: {args.tier})" if args.tier else ""
    print(f"{'=' * 60}")
    print(f"SKILL METADATA AUDIT{tier_label}")
    print(f"{'=' * 60}")
    print(f"Total skills scanned: {total}")
    print(f"With .meta.yaml:      {len(with_meta)} ({len(with_meta) * 100 // total}%)")
    print(f"Without .meta.yaml:   {len(without_meta)} ({len(without_meta) * 100 // total}%)")
    print(f"With .md body:        {len(with_body)}")
    print(f"Without .md body:     {len(without_body)} (dormant stubs or missing)")
    print()

    # Skills with metadata
    if args.verbose and with_meta:
        print(f"--- Skills WITH .meta.yaml ({len(with_meta)}) ---")
        for s in with_meta:
            print(f"  [OK] {s['name']} ({s['tier']})")
        print()

    # Skills without metadata
    if without_meta:
        print(f"--- Skills WITHOUT .meta.yaml ({len(without_meta)}) ---")
        print(f"    These use implicit defaults from _trigger_engine.yaml:")
        print(f"    agent_binding: {IMPLICIT_DEFAULTS['agent_binding']['mandatory']}")
        print(f"    modes:         {IMPLICIT_DEFAULTS['modes']}")
        print(f"    max_phase:     {IMPLICIT_DEFAULTS['max_phase']}")
        print(f"    token_estimate: {IMPLICIT_DEFAULTS['token_estimate']}")
        print()
        if args.verbose:
            for s in without_meta:
                print(f"  [DEFAULT] {s['name']} ({s['tier']})")
            print()

    # Skills without body files
    if without_body:
        print(f"--- Skills WITHOUT .md body ({len(without_body)}) ---")
        for s in without_body:
            print(f"  [STUB] {s['name']} ({s['tier']})")
        print()

    # Field validation
    if args.check_fields and with_meta:
        print(f"--- Field Validation ---")
        all_issues = []
        for s in with_meta:
            meta_data = load_yaml(s["meta_path"])
            issues = validate_meta_fields(meta_data, s["name"])
            all_issues.extend(issues)

        if all_issues:
            for issue in all_issues:
                required = "required" in issue
                prefix = "[WARN]" if required else "[INFO]"
                print(f"  {prefix} {issue}")
        else:
            print("  All .meta.yaml files have complete required fields.")
        print()

    # Summary
    print(f"{'=' * 60}")
    coverage = len(with_meta) * 100 // total if total > 0 else 0
    if coverage == 100:
        print("STATUS: Full metadata coverage.")
    elif coverage >= 50:
        print(f"STATUS: Partial coverage ({coverage}%). Non-compliant skills use safe defaults.")
    else:
        print(f"STATUS: Low coverage ({coverage}%). Most skills use implicit defaults.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
