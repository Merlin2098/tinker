#!/usr/bin/env python3
"""
User task builder.

Creates or overwrites agent/user_task.yaml from explicit CLI inputs.
No inference is performed; all required fields must be provided.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

try:
    import yaml
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"PyYAML required: {exc}")


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def load_yaml_file(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Input file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return project_root() / path


def parse_config_sources(raw: List[str]) -> List[dict]:
    sources = []
    for item in raw:
        parts = item.split("::", 2)
        if len(parts) != 3 or not all(p.strip() for p in parts):
            raise SystemExit(
                "Invalid --config-source. Expected format: id::path::purpose"
            )
        src_id, path, purpose = parts
        sources.append(
            {"id": src_id.strip(), "path": path.strip(), "purpose": purpose.strip()}
        )
    return sources


def validate_inputs(
    role: str,
    mode: str,
    objective: str,
    files: List[str],
    constraints: str,
    risk_tolerance: str,
    phase: str,
    validation_status: str,
    validated_by: Optional[str],
    validated_at: Optional[str],
    config_sources: List[dict],
) -> None:
    if not objective.strip():
        raise SystemExit("Objective cannot be empty.")
    if not constraints.strip():
        raise SystemExit("Constraints cannot be empty.")
    if not files:
        raise SystemExit("At least one --file is required.")
    if not config_sources:
        raise SystemExit("At least one --config-source is required.")
    if phase == "B_EXECUTION":
        if validation_status != "PASSED":
            raise SystemExit("phase=B_EXECUTION requires validation.status=PASSED.")
        if not validated_by or not validated_by.strip():
            raise SystemExit("phase=B_EXECUTION requires --validated-by.")
        if not validated_at or not validated_at.strip():
            raise SystemExit("phase=B_EXECUTION requires --validated-at.")
    if role in {"executor", "junior"} and phase != "B_EXECUTION":
        raise SystemExit("role=executor/junior requires phase=B_EXECUTION.")


def validate_payload(payload: dict) -> None:
    role = str(payload.get("role", "")).strip()
    mode = str(payload.get("mode", "")).strip()
    objective = str(payload.get("objective", "")).strip()
    files = payload.get("files") if isinstance(payload.get("files"), list) else []
    config = payload.get("config") if isinstance(payload.get("config"), dict) else {}
    sources = config.get("sources") if isinstance(config.get("sources"), list) else []
    constraints = str(payload.get("constraints", "")).strip()
    risk_tolerance = str(payload.get("risk_tolerance", "")).strip()
    phase = str(payload.get("phase", "")).strip()
    validation = (
        payload.get("validation") if isinstance(payload.get("validation"), dict) else {}
    )
    status = str(validation.get("status", "")).strip()
    validated_by = validation.get("validated_by")
    validated_at = validation.get("validated_at")

    validate_inputs(
        role=role,
        mode=mode,
        objective=objective,
        files=files,
        constraints=constraints,
        risk_tolerance=risk_tolerance,
        phase=phase,
        validation_status=status,
        validated_by=validated_by,
        validated_at=validated_at,
        config_sources=sources,
    )


def multiline_str_representer(dumper, data: str):
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build agent/user_task.yaml from explicit inputs"
    )
    parser.add_argument("--role", choices=["senior", "executor", "inspector", "junior"])
    parser.add_argument(
        "--mode",
        choices=["ANALYZE_ONLY", "ANALYZE_AND_IMPLEMENT", "IMPLEMENT_ONLY"],
    )
    parser.add_argument("--mode-profile", choices=["LITE", "STANDARD", "FULL"])
    parser.add_argument("--input", help="Input YAML to validate and write as user_task.yaml")
    parser.add_argument(
        "--from-template",
        help="Template YAML to load and override with explicit inputs",
    )
    parser.add_argument("--objective")
    parser.add_argument("--objective-file")
    parser.add_argument("--file", action="append", dest="files", default=[])
    parser.add_argument("--constraints")
    parser.add_argument("--constraints-file")
    parser.add_argument("--risk-tolerance", choices=["LOW", "MEDIUM", "HIGH"])
    parser.add_argument("--phase", choices=["A_CONTRACT_VALIDATION", "B_EXECUTION"])
    parser.add_argument("--validation-status", choices=["PENDING", "PASSED", "FAILED"])
    parser.add_argument("--validated-by")
    parser.add_argument("--validated-at")
    parser.add_argument("--validation-notes")
    parser.add_argument(
        "--config-source",
        action="append",
        default=[],
        help="Repeatable. Format: id::path::purpose",
    )
    parser.add_argument(
        "--output",
        default="agent/user_task.yaml",
        help="Output path relative to project root",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing file",
    )
    args = parser.parse_args()

    if args.input and args.from_template:
        raise SystemExit("Use only one of --input or --from-template.")

    explicit_fields_provided = any(
        [
            args.objective,
            args.objective_file,
            args.constraints,
            args.constraints_file,
            args.files,
            args.config_source,
            args.mode_profile,
        ]
    )

    if args.input:
        if explicit_fields_provided:
            raise SystemExit("--input cannot be combined with explicit field flags.")
        payload = load_yaml_file(resolve_path(args.input))
        validate_payload(payload)
    else:
        required_flags = {
            "role": args.role,
            "mode": args.mode,
            "risk_tolerance": args.risk_tolerance,
            "phase": args.phase,
            "validation_status": args.validation_status,
            "validation_notes": args.validation_notes,
        }
        missing = [k for k, v in required_flags.items() if not v]
        if missing:
            raise SystemExit(f"Missing required flags: {', '.join(missing)}")

        if bool(args.objective) == bool(args.objective_file):
            raise SystemExit("Provide exactly one of --objective or --objective-file.")
        if bool(args.constraints) == bool(args.constraints_file):
            raise SystemExit("Provide exactly one of --constraints or --constraints-file.")

        objective = (
            args.objective
            if args.objective is not None
            else read_text(resolve_path(args.objective_file))
        )
        constraints = (
            args.constraints
            if args.constraints is not None
            else read_text(resolve_path(args.constraints_file))
        )

        config_sources = parse_config_sources(args.config_source)

        if args.from_template:
            template = load_yaml_file(resolve_path(args.from_template))
            if not template:
                raise SystemExit("Template must be a valid YAML mapping.")
            payload = template
            payload.update(
                {
                    "role": args.role,
                    "mode": args.mode,
                    "objective": objective,
                    "files": args.files,
                    "config": {"sources": config_sources},
                    "constraints": constraints,
                    "risk_tolerance": args.risk_tolerance,
                    "phase": args.phase,
                    "validation": {
                        "status": args.validation_status,
                        "validated_by": args.validated_by,
                        "validated_at": args.validated_at,
                        "notes": args.validation_notes,
                    },
                }
            )
            if args.mode_profile:
                payload["mode_profile"] = args.mode_profile
        else:
            payload = {
                "role": args.role,
                "mode": args.mode,
                "objective": objective,
                "files": args.files,
                "config": {"sources": config_sources},
                "constraints": constraints,
                "risk_tolerance": args.risk_tolerance,
                "phase": args.phase,
                "validation": {
                    "status": args.validation_status,
                    "validated_by": args.validated_by,
                    "validated_at": args.validated_at,
                    "notes": args.validation_notes,
                },
            }

            if args.mode_profile:
                payload["mode_profile"] = args.mode_profile

        validate_payload(payload)

    out_path = project_root() / args.output
    if out_path.exists() and not args.overwrite:
        raise SystemExit("Output file exists. Use --overwrite to replace it.")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    yaml.SafeDumper.add_representer(str, multiline_str_representer)
    out_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
