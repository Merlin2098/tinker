#!/usr/bin/env python3
"""
Validate framework config references and protected-file entries.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"PyYAML required: {exc}")

try:
    from agent_tools._repo_root import find_project_root
except ImportError:
    from _repo_root import find_project_root  # type: ignore


OPTIONAL_PROTECTED_FILES = {
    ".env",
    "credentials.json",
    "pyproject.toml",
    "setup.py",
    # Legacy role-doc paths retained in rules for compatibility in some forks.
    "agent/architecture_proposal.md",
    "agent/agent_inspector/agent_inspector.md",
    "agent/agent_executor/agent_executor.md",
}
PROTECTED_FILES_BLOCK = re.compile(
    r"```yaml\s+protected_files:\s*\n(.*?)\n```",
    re.DOTALL | re.IGNORECASE,
)


def load_yaml(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve(root: Path, raw: str) -> Path:
    p = Path(raw)
    return p if p.is_absolute() else (root / p)


def _extract_protected_files(markdown: str) -> dict[str, list[str]] | None:
    match = PROTECTED_FILES_BLOCK.search(markdown)
    if not match:
        return None
    snippet = "protected_files:\n" + match.group(1)
    data = yaml.safe_load(snippet) or {}
    protected = data.get("protected_files", {})
    return protected if isinstance(protected, dict) else None


def validate_config_files(project_root: Path) -> list[str]:
    errors: list[str] = []
    config_path = project_root / "agent_framework_config.yaml"
    rules_path = project_root / "agent" / "rules" / "agent_rules.md"

    if not config_path.exists():
        errors.append(f"CRITICAL: Configuration file not found: {config_path}")
    else:
        try:
            config = load_yaml(config_path) or {}
            if not isinstance(config, dict):
                errors.append(f"Invalid YAML root in {config_path}: expected mapping")
            else:
                footprint = config.get("deployment", {}).get("framework_footprint", [])
                if isinstance(footprint, list):
                    for item in footprint:
                        if isinstance(item, str) and item.strip():
                            resolved = _resolve(project_root, item.strip())
                            if not resolved.exists():
                                errors.append(f"Missing framework footprint item: {item}")

                output_path = config.get("static_context", {}).get("output_path")
                if isinstance(output_path, str) and output_path.strip():
                    out_parent = _resolve(project_root, output_path.strip()).parent
                    if not out_parent.exists():
                        errors.append(f"Missing directory for static context output: {out_parent}")
        except Exception as exc:
            errors.append(f"Error parsing {config_path}: {exc}")

    if not rules_path.exists():
        errors.append(f"CRITICAL: Governance rules not found: {rules_path}")
        return errors

    try:
        content = rules_path.read_text(encoding="utf-8")
        protected = _extract_protected_files(content)
        if protected is None:
            errors.append("Could not find protected_files YAML block in agent_rules.md")
            return errors

        for category, paths in protected.items():
            if not isinstance(paths, list):
                errors.append(f"Invalid protected_files.{category}: expected list")
                continue
            for pattern in paths:
                if not isinstance(pattern, str) or not pattern.strip():
                    continue
                if "*" in pattern:
                    continue
                if pattern in OPTIONAL_PROTECTED_FILES:
                    continue
                resolved = _resolve(project_root, pattern)
                if not resolved.exists():
                    errors.append(f"Missing protected file referenced in rules: {pattern}")
    except Exception as exc:
        errors.append(f"Error parsing protected files in {rules_path}: {exc}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Tinker config/rules file references")
    parser.add_argument(
        "--project-root",
        help="Optional project root override (auto-detected by default)",
    )
    args = parser.parse_args()

    root = Path(args.project_root).resolve() if args.project_root else find_project_root(Path(__file__).resolve().parent)
    print("Starting configuration validation...")
    print(f"Project root: {root}")
    errors = validate_config_files(root)
    if errors:
        print("\n[FAIL] VALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("\n[OK] VALIDATION PASSED. All referenced configuration files exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
