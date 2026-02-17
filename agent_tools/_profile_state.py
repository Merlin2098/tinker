#!/usr/bin/env python3
"""
Shared helpers for kernel/profile state management.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"PyYAML required: {exc}")


VALID_PROFILES = {"LITE", "STANDARD", "FULL"}


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def resolve_state_path(agent_id: str | None, explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    runtime_dir = project_root() / "agent" / "agent_outputs" / "runtime"
    if agent_id:
        return runtime_dir / f"active_profile.{agent_id}.json"
    return runtime_dir / "active_profile.json"


def profile_path(profile: str) -> Path:
    return project_root() / "agent" / "profiles" / f"{profile.lower()}.yaml"


def normalize_profile(value: object) -> str:
    return str(value or "").strip().upper()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_state(path: Path, profile: str, *, agent_id: str | None, source: str) -> dict[str, Any]:
    payload = {
        "profile": profile,
        "agent_id": agent_id,
        "profile_path": str(profile_path(profile)),
        "updated_at": now_iso(),
        "source": source,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload



def _deep_merge_profiles(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Merges two profile dicts.
    - Lists (allowlists) are concatenated and deduped.
    - Dicts are merged recursively.
    - Scalars in override overwrite base.
    """
    merged = base.copy()
    
    for key, value in override.items():
        if key == "inherits":
            continue
            
        if key == "capabilities" and "allowlist" in value:
            # Specialized merging for capabilities.allowlist
            base_caps = base.get("capabilities", {}).get("allowlist", {})
            ovr_caps = value.get("allowlist", {})
            
            merged_allowlist = {}
            for field in ["skills", "clusters"]:
                base_list = base_caps.get(field, [])
                ovr_list = ovr_caps.get(field, [])
                # Union and sort
                merged_allowlist[field] = sorted(list(set(base_list + ovr_list)))
            
            # Ensure structure exists
            if "capabilities" not in merged:
                merged["capabilities"] = {}
            merged["capabilities"]["allowlist"] = merged_allowlist
            
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_profiles(merged[key], value)
        else:
            merged[key] = value
            
    return merged


def load_profile_definition(profile: str) -> dict[str, Any]:
    """
    Loads profile definition with recursive inheritance.
    Checks for 'inherits' key in YAML.
    """
    profile = normalize_profile(profile)
    p_path = profile_path(profile)
    
    # Handle _BASE (or any profile that doesn't exist as a separate file logic if needed)
    # But _base.yaml should exist.
    
    if not p_path.exists():
        # Fallback for _BASE if requested safely
        if profile == "_BASE": 
             return {} # Should allow clean slate if base missing? Or error?
        raise FileNotFoundError(f"Profile {profile} not found at {p_path}")

    data = load_yaml(p_path)
    
    # Recursion
    parent_name = data.get("inherits")
    if parent_name:
        parent_data = load_profile_definition(parent_name)
        return _deep_merge_profiles(parent_data, data)
        
    return data


