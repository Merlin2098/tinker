"""
load_static_context.py

Lazy-loading context generator for the Tinker framework.

Produces a SKELETON context.json optimized for LLM consumption:
- File tree (max depth 2) instead of full treemap dump
- Skills METADATA ONLY — skill index is loaded separately via _index.yaml
- File REFERENCES (path + exists + size) instead of inline content
- Schema SUMMARIES (top-level keys only) instead of full schema bodies
- Function/class SIGNATURES extracted via AST from Python files

Target: context.json MUST stay under 1,000 lines (governance mandate).
Agents that need full file content MUST use grep/jq to target specific data
at runtime instead of reading the entire context.json.
If generated context exceeds the configured line budget, deterministic
priority truncation is applied; if still above budget, generation fails hard.

Gitignore compliance:
- The initial context FULLY respects .gitignore — no ignored file content is
  included.  Treemap and dependencies_report are gitignored and excluded.
- On-demand loading of ignored files (treemap, dependencies_report) is handled
  by context_loader.py, NOT by this module.
"""

import os
import re
import ast
import yaml
import json
import argparse
from typing import Dict, Any, List, Optional


def _load_framework_config() -> Dict[str, Any]:
    """Load agent_framework_config.yaml from the project root. Returns {} on failure."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(root, "agent_framework_config.yaml")
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


# Paths relativos dentro del proyecto
SKILLS_PATH = os.path.join("agent", "skills", "_index.yaml")
AGENT_RULES_PATH = os.path.join("agent", "rules", "agent_rules.md")
SCHEMAS_PATH = os.path.join("agent", "agent_protocol", "schemas")

# Gitignored analysis files — NOT loaded in static context.
# Available on-demand via context_loader.load_on_demand().
# We'll resolve these dynamically from config now.
DEFAULT_DEPENDENCIES_REPORT_PATH = os.path.join("agent", "analysis", "dependencies_report.md")
DEFAULT_TREEMAP_PATH = os.path.join("agent", "analysis", "treemap.md")

def _get_on_demand_path(file_key: str, default_path: str) -> str:
    """Resolve path from agent_framework_config.yaml or fallback to default."""
    cfg = _load_framework_config()
    on_demand = cfg.get("on_demand_files", {})
    if isinstance(on_demand, dict):
        entry = on_demand.get(file_key)
        if isinstance(entry, dict):
            return entry.get("path", default_path)
    return default_path

DEPENDENCIES_REPORT_PATH = _get_on_demand_path("dependencies_report", DEFAULT_DEPENDENCIES_REPORT_PATH)
TREEMAP_PATH = _get_on_demand_path("treemap", DEFAULT_TREEMAP_PATH)

# Runtime model has no role-specific agent definitions.


# ---------------------------------------------------------------------------
# Config-driven exclusions (read from agent_framework_config.yaml)
# ---------------------------------------------------------------------------
# Defaults are used when the config file is missing (e.g. first run).

_DEFAULT_EXCLUDED_FROM_SIGNATURES = {"agent/skills"}
_DEFAULT_EXCLUDED_DIRS_FROM_TREE = {
    "agent/skills",
    "agent/agent_outputs",
    "agent/agent_logs",
}
_DEFAULT_STATIC_CONTEXT_LIMITS = {
    "max_lines": 1000,
    "file_tree_max_depth": 2,
    "python_signatures_max_depth": 3,
}
_DEFAULT_TRUNCATION_POLICY: Dict[str, Any] = {
    "reducer_order": [
        "trim_python_signatures",
        "trim_file_tree",
        "trim_schema_summaries",
        "trim_agent_rules_sections",
        "drop_python_signatures",
        "drop_schema_summaries",
        "drop_agent_rules_sections",
        "drop_file_tree_to_minimum",
    ],
    "trim_fraction_percent": 10,
    "minimum_file_tree_entries": 0,
    "minimum_agent_rules_sections": 0,
    "minimum_schema_top_level_keys": 3,
}
_DEFAULT_PROFILE_DETECTION: Dict[str, Any] = {
    "enabled": True,
    "fallback_profile": "default",
    "rules": [
        {
            "profile": "vscode",
            "match": "any",
            "env_equals": {"TERM_PROGRAM": "vscode"},
            "env_exists": ["VSCODE_PID", "VSCODE_IPC_HOOK_CLI", "VSCODE_GIT_IPC_HANDLE"],
        },
        {
            "profile": "antigravity",
            "match": "any",
            "env_exists": ["ANTIGRAVITY_ENV", "ANTIGRAVITY_SESSION", "ANTIGRAVITY_SESSION_ID"],
            "env_contains": {"TERM_PROGRAM": "antigravity"},
        },
    ],
}





def _deep_merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge dictionaries. Non-dict override values replace base values."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = _deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def _resolve_static_context_config(
    requested_profile: Optional[str] = None,
) -> tuple[Dict[str, Any], str, str, str]:
    """Resolve static_context config with optional profile override.

    Priority:
    1) requested_profile (CLI/API arg)
    2) TINKER_CONTEXT_PROFILE env var
    3) active_profile in root config
    4) auto-detected profile
    5) default (no profile)
    """
    full_cfg = _load_framework_config()
    base_cfg = full_cfg.get("static_context", {})
    if not isinstance(base_cfg, dict):
        base_cfg = {}

    profiles = full_cfg.get("static_context_profiles", {})
    if not isinstance(profiles, dict):
        profiles = {}

    env_profile = os.getenv("TINKER_CONTEXT_PROFILE")
    config_profile = full_cfg.get("active_profile")
    selected_profile = requested_profile or env_profile or config_profile

    auto_profile, auto_reason = _auto_detect_profile(full_cfg, profiles)
    if selected_profile in (None, "") and auto_profile:
        selected_profile = auto_profile

    if selected_profile in (None, "", "default"):
        return dict(base_cfg), "default", "default", "none"

    if selected_profile not in profiles:
        available = ", ".join(sorted(profiles.keys())) or "(none)"
        raise ValueError(
            f"Unknown static context profile '{selected_profile}'. Available: {available}"
        )

    profile_cfg = profiles.get(selected_profile, {})
    if not isinstance(profile_cfg, dict):
        raise ValueError(f"Profile '{selected_profile}' must be a mapping/dictionary.")

    merged = _deep_merge_dicts(base_cfg, profile_cfg)
    if requested_profile:
        source = "arg"
    elif env_profile:
        source = "env"
    elif config_profile:
        source = "config"
    else:
        source = "auto"
    reason = auto_reason if source == "auto" else "explicit"
    return merged, str(selected_profile), source, reason


def _is_non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def _rule_matches(rule: Dict[str, Any], env: Dict[str, str]) -> bool:
    match_mode = str(rule.get("match", "all")).lower()
    checks: List[bool] = []

    env_equals = rule.get("env_equals", {})
    if isinstance(env_equals, dict):
        for key, expected in env_equals.items():
            checks.append(env.get(str(key), "") == str(expected))

    env_contains = rule.get("env_contains", {})
    if isinstance(env_contains, dict):
        for key, expected_substring in env_contains.items():
            checks.append(str(expected_substring).lower() in env.get(str(key), "").lower())

    env_exists = rule.get("env_exists", [])
    if isinstance(env_exists, list):
        for key in env_exists:
            checks.append(_is_non_empty_str(env.get(str(key))))

    if not checks:
        return False
    return any(checks) if match_mode == "any" else all(checks)


def _auto_detect_profile(full_cfg: Dict[str, Any], profiles: Dict[str, Any]) -> tuple[Optional[str], str]:
    """Auto-detect profile from config rules and runtime env signals."""
    detection_cfg = full_cfg.get("profile_detection", {})
    if not isinstance(detection_cfg, dict):
        detection_cfg = {}

    enabled = detection_cfg.get("enabled", _DEFAULT_PROFILE_DETECTION["enabled"])
    if enabled is False:
        return None, "detection-disabled"

    env = dict(os.environ)

    rules = detection_cfg.get("rules")
    if not isinstance(rules, list):
        rules = _DEFAULT_PROFILE_DETECTION["rules"]

    for idx, rule in enumerate(rules):
        if not isinstance(rule, dict):
            continue
        profile = rule.get("profile")
        if not isinstance(profile, str) or profile not in profiles:
            continue
        if _rule_matches(rule, env):
            return profile, f"rule:{idx + 1}"

    # Built-in heuristic fallback for VS Code terminals.
    if "vscode" in profiles:
        if env.get("TERM_PROGRAM", "").lower() == "vscode":
            return "vscode", "heuristic:term_program"
        if any(_is_non_empty_str(env.get(key)) for key in ("VSCODE_PID", "VSCODE_IPC_HOOK_CLI", "VSCODE_GIT_IPC_HANDLE")):
            return "vscode", "heuristic:vscode_env"

    # Built-in heuristic fallback for Antigravity-like env variables.
    if "antigravity" in profiles:
        if any("ANTIGRAVITY" in key.upper() and _is_non_empty_str(value) for key, value in env.items()):
            return "antigravity", "heuristic:antigravity_env"

    fallback_profile = detection_cfg.get("fallback_profile", _DEFAULT_PROFILE_DETECTION["fallback_profile"])
    if isinstance(fallback_profile, str) and fallback_profile in profiles and fallback_profile != "default":
        return fallback_profile, "fallback-profile"

    return None, "no-match"


def _get_excluded_from_signatures(static_cfg: Optional[Dict[str, Any]] = None) -> set:
    cfg = static_cfg if isinstance(static_cfg, dict) else _load_framework_config().get("static_context", {})
    entries = cfg.get("excluded_from_signatures", None)
    if isinstance(entries, list) and entries:
        return set(entries)
    return set(_DEFAULT_EXCLUDED_FROM_SIGNATURES)


def _get_excluded_dirs_from_tree(static_cfg: Optional[Dict[str, Any]] = None) -> set:
    cfg = static_cfg if isinstance(static_cfg, dict) else _load_framework_config().get("static_context", {})
    entries = cfg.get("excluded_dirs_from_tree", None)
    if isinstance(entries, list) and entries:
        return set(entries)
    return set(_DEFAULT_EXCLUDED_DIRS_FROM_TREE)


def _get_static_context_limits(static_cfg: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    """Get numeric static context limits with safe defaults."""
    cfg = static_cfg if isinstance(static_cfg, dict) else _load_framework_config().get("static_context", {})
    limits: Dict[str, int] = {}
    for key, default in _DEFAULT_STATIC_CONTEXT_LIMITS.items():
        value = cfg.get(key, default)
        if isinstance(value, int) and value > 0:
            limits[key] = value
        else:
            limits[key] = default
    return limits


def _get_truncation_policy(static_cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get truncation policy from config with safe defaults."""
    cfg = static_cfg if isinstance(static_cfg, dict) else _load_framework_config().get("static_context", {})
    policy_cfg = cfg.get("truncation_policy", {})
    if not isinstance(policy_cfg, dict):
        policy_cfg = {}

    policy: Dict[str, Any] = dict(_DEFAULT_TRUNCATION_POLICY)

    reducer_order = policy_cfg.get("reducer_order")
    if isinstance(reducer_order, list) and reducer_order:
        policy["reducer_order"] = [str(item) for item in reducer_order]

    for key in (
        "trim_fraction_percent",
        "minimum_file_tree_entries",
        "minimum_agent_rules_sections",
        "minimum_schema_top_level_keys",
    ):
        value = policy_cfg.get(key, policy[key])
        if isinstance(value, int) and value >= 0:
            policy[key] = value

    if policy["trim_fraction_percent"] <= 0:
        policy["trim_fraction_percent"] = _DEFAULT_TRUNCATION_POLICY["trim_fraction_percent"]

    return policy


# Resolved at import time.
EXCLUDED_FROM_SIGNATURES = _get_excluded_from_signatures()
EXCLUDED_DIRS_FROM_TREE = _get_excluded_dirs_from_tree()
STATIC_CONTEXT_LIMITS = _get_static_context_limits()
TRUNCATION_POLICY = _get_truncation_policy()


# ---------------------------------------------------------------------------
# Lazy-loading helpers
# ---------------------------------------------------------------------------

def _load_gitignore_spec(root: str):
    """Load .gitignore patterns from project root. Returns a pathspec or None."""
    try:
        import pathspec
        gitignore_path = os.path.join(root, ".gitignore")
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r", encoding="utf-8") as f:
                patterns = [p for p in f.read().splitlines() if p.strip() and not p.startswith("#")]
            return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
    except ImportError:
        pass
    return None


def load_yaml_file(path: str) -> Any:
    """Carga un archivo YAML."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _file_metadata(path: str) -> Dict[str, Any]:
    """Return lightweight metadata for a file instead of its full content."""
    if not os.path.exists(path):
        return {"path": path, "exists": False}
    size = os.path.getsize(path)
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    line_count = len(lines)
    # Extract markdown section headers (## / ### headings)
    headers = [
        ln.strip() for ln in lines
        if ln.strip().startswith("#")
    ]
    return {
        "path": path,
        "exists": True,
        "size_bytes": size,
        "line_count": line_count,
        "sections": headers[:10],  # cap to avoid bloat
    }


def _file_ref(path: str) -> Dict[str, Any]:
    """Minimal file reference — path + exists only. Used for agent definitions."""
    return {"path": path, "exists": os.path.exists(path)}


def _compact_skills_index(full_registry: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract a compact index: name, category, purpose only."""
    skills = full_registry.get("skills", [])
    if not skills:
        return []
    return [
        {
            "name": s.get("name", ""),
            "category": s.get("category", ""),
            "purpose": s.get("purpose", ""),
        }
        for s in skills
    ]


def _schema_summary(path: str) -> Dict[str, Any]:
    """Load a schema and return only its top-level keys."""
    if not os.path.exists(path):
        return {}
    if path.endswith((".yaml", ".yml")):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    elif path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        return {}
    if isinstance(data, dict):
        return {"top_level_keys": list(data.keys())}
    return {"type": type(data).__name__}


def _generate_file_tree(root: str, max_depth: int = 2, spec=None) -> List[str]:
    """Generate a file tree respecting .gitignore, capped at max_depth.

    Also skips directories listed in EXCLUDED_DIRS_FROM_TREE to keep the
    static context compact (skills folders, agent outputs, logs).
    """
    ignored_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}
    tree: List[str] = []

    def _walk(directory: str, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            items = sorted(os.listdir(directory))
        except PermissionError:
            return

        visible = []
        for name in items:
            if name in ignored_dirs:
                continue
            full = os.path.join(directory, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")

            # Skip directories explicitly excluded from the tree
            if os.path.isdir(full) and rel in EXCLUDED_DIRS_FROM_TREE:
                continue

            if spec:
                if spec.match_file(rel):
                    continue
                if os.path.isdir(full) and spec.match_file(rel + "/"):
                    continue
            visible.append(name)

        for idx, name in enumerate(visible):
            full = os.path.join(directory, name)
            is_last = idx == len(visible) - 1
            connector = "└── " if is_last else "├── "
            if os.path.isdir(full):
                tree.append(f"{prefix}{connector}{name}/")
                ext = "    " if is_last else "│   "
                _walk(full, prefix + ext, depth + 1)
            else:
                tree.append(f"{prefix}{connector}{name}")

    _walk(root, "", 0)
    return tree


def _extract_python_signatures(
    root: str, max_depth: int = 3, spec=None
) -> Dict[str, List[str]]:
    """Walk Python files up to max_depth and extract class/function signatures via AST.

    Respects .gitignore (via spec) and skips directories listed in
    EXCLUDED_FROM_SIGNATURES to prevent agent implementation folders
    from inflating the output.
    """
    signatures: Dict[str, List[str]] = {}
    ignored_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignored_dirs]
        rel_dir = os.path.relpath(dirpath, root).replace(os.sep, "/")
        depth = 0 if rel_dir == "." else rel_dir.count("/") + 1
        if depth > max_depth:
            dirnames.clear()
            continue

        # Skip directories excluded from signatures (e.g. agent/skills)
        if any(rel_dir == ex or rel_dir.startswith(ex + "/") for ex in EXCLUDED_FROM_SIGNATURES):
            dirnames.clear()
            continue

        # Filter directories via .gitignore
        if spec:
            dirnames[:] = [
                d for d in dirnames
                if not spec.match_file(
                    os.path.relpath(os.path.join(dirpath, d), root).replace(os.sep, "/") + "/"
                )
            ]

        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(fpath, root).replace(os.sep, "/")
            # Skip files matched by .gitignore
            if spec and spec.match_file(rel_path):
                continue
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source, filename=rel_path)
            except (SyntaxError, UnicodeDecodeError):
                continue

            sigs: List[str] = []
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    sigs.append(f"class {node.name}")
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    args = [a.arg for a in node.args.args]
                    sigs.append(f"def {node.name}({', '.join(args)})")
            if sigs:
                signatures[rel_path] = sigs
    return signatures


def _serialized_line_count(data: Dict[str, Any]) -> int:
    """Count lines as persisted with json.dumps(indent=2)."""
    return json.dumps(data, indent=2, ensure_ascii=False).count("\n") + 1


def _trim_python_signatures_once(context: Dict[str, Any], trim_fraction_percent: int) -> bool:
    signatures = context.get("python_signatures")
    if not isinstance(signatures, dict) or not signatures:
        return False
    keys = sorted(signatures.keys())
    drop_count = max(1, len(keys) * trim_fraction_percent // 100)
    for key in keys[-drop_count:]:
        signatures.pop(key, None)
    return True


def _trim_file_tree_once(context: Dict[str, Any], trim_fraction_percent: int) -> bool:
    file_tree = context.get("file_tree", {})
    tree = file_tree.get("tree") if isinstance(file_tree, dict) else None
    if not isinstance(tree, list) or not tree:
        return False
    drop_count = max(1, len(tree) * trim_fraction_percent // 100)
    del tree[-drop_count:]
    return True


def _trim_schema_summaries_once(context: Dict[str, Any], minimum_schema_top_level_keys: int) -> bool:
    schemas = context.get("schemas")
    if not isinstance(schemas, dict) or not schemas:
        return False

    candidate = None
    max_keys = 0
    for name, summary in schemas.items():
        if not isinstance(summary, dict):
            continue
        keys = summary.get("top_level_keys")
        if isinstance(keys, list) and len(keys) > max_keys:
            max_keys = len(keys)
            candidate = name

    if candidate is None or max_keys <= minimum_schema_top_level_keys:
        return False

    schemas[candidate]["top_level_keys"] = schemas[candidate]["top_level_keys"][:-1]
    return True


def _trim_agent_rules_sections_once(context: Dict[str, Any], minimum_agent_rules_sections: int) -> bool:
    rules = context.get("agent_rules")
    if not isinstance(rules, dict):
        return False
    sections = rules.get("sections")
    if not isinstance(sections, list) or len(sections) <= minimum_agent_rules_sections:
        return False
    rules["sections"] = sections[:-1]
    return True


def _drop_python_signatures(context: Dict[str, Any]) -> bool:
    signatures = context.get("python_signatures")
    if not isinstance(signatures, dict) or not signatures:
        return False
    context["python_signatures"] = {}
    return True


def _drop_schema_summaries(context: Dict[str, Any]) -> bool:
    schemas = context.get("schemas")
    if not isinstance(schemas, dict) or not schemas:
        return False
    context["schemas"] = {}
    return True


def _drop_agent_rules_sections(context: Dict[str, Any]) -> bool:
    rules = context.get("agent_rules")
    if not isinstance(rules, dict):
        return False
    sections = rules.get("sections")
    if not isinstance(sections, list) or not sections:
        return False
    rules["sections"] = []
    return True


def _drop_file_tree_to_minimum(context: Dict[str, Any], minimum: int = 0) -> bool:
    file_tree = context.get("file_tree")
    if not isinstance(file_tree, dict):
        return False
    tree = file_tree.get("tree")
    if not isinstance(tree, list) or len(tree) <= minimum:
        return False
    file_tree["tree"] = tree[:minimum]
    return True


def _enforce_context_line_budget(
    context: Dict[str, Any],
    max_lines: int,
    policy: Dict[str, Any],
) -> Dict[str, Any]:
    """Enforce the context line budget using deterministic truncation priority."""
    trim_fraction_percent = int(policy.get("trim_fraction_percent", 10))
    minimum_file_tree_entries = int(policy.get("minimum_file_tree_entries", 0))
    minimum_agent_rules_sections = int(policy.get("minimum_agent_rules_sections", 0))
    minimum_schema_top_level_keys = int(policy.get("minimum_schema_top_level_keys", 3))

    reducers = {
        "trim_python_signatures": lambda c: _trim_python_signatures_once(c, trim_fraction_percent),
        "trim_file_tree": lambda c: _trim_file_tree_once(c, trim_fraction_percent),
        "trim_schema_summaries": lambda c: _trim_schema_summaries_once(c, minimum_schema_top_level_keys),
        "trim_agent_rules_sections": lambda c: _trim_agent_rules_sections_once(c, minimum_agent_rules_sections),
        "drop_python_signatures": _drop_python_signatures,
        "drop_schema_summaries": _drop_schema_summaries,
        "drop_agent_rules_sections": _drop_agent_rules_sections,
        "drop_file_tree_to_minimum": lambda c: _drop_file_tree_to_minimum(c, minimum_file_tree_entries),
    }
    reducer_order = policy.get("reducer_order", _DEFAULT_TRUNCATION_POLICY["reducer_order"])

    actions: List[str] = []
    line_count = _serialized_line_count(context)

    for action_name in reducer_order:
        reducer = reducers.get(action_name)
        if reducer is None:
            continue
        while line_count > max_lines:
            changed = reducer(context)
            if not changed:
                break
            actions.append(action_name)
            line_count = _serialized_line_count(context)
        if line_count <= max_lines:
            break

    if line_count > max_lines:
        raise RuntimeError(
            f"context.json exceeds max_lines after truncation: {line_count} > {max_lines}"
        )

    # Add budget metadata and ensure metadata itself does not push over budget.
    while True:
        context["_context_budget"] = {
            "max_lines": max_lines,
            "final_lines": line_count,
            "truncation_applied": bool(actions),
            "truncation_actions": actions,
        }
        final_count = _serialized_line_count(context)
        context["_context_budget"]["final_lines"] = final_count
        if final_count <= max_lines:
            return context

        context.pop("_context_budget", None)
        line_count = _serialized_line_count(context)

        reduced = False
        for action_name in reducer_order:
            reducer = reducers.get(action_name)
            if reducer is None:
                continue
            if reducer(context):
                actions.append(action_name)
                line_count = _serialized_line_count(context)
                reduced = True
                break

        if not reduced:
            raise RuntimeError(
                f"context.json exceeds max_lines after budget metadata: {final_count} > {max_lines}"
            )


# ---------------------------------------------------------------------------
# Main loader
# ---------------------------------------------------------------------------

def load_static_context(profile: Optional[str] = None) -> Dict[str, Any]:
    """Load a SKELETON static context (lazy-loading mode)."""
    global EXCLUDED_FROM_SIGNATURES, EXCLUDED_DIRS_FROM_TREE, STATIC_CONTEXT_LIMITS, TRUNCATION_POLICY

    static_cfg, active_profile, profile_source, profile_reason = _resolve_static_context_config(profile)
    EXCLUDED_FROM_SIGNATURES = _get_excluded_from_signatures(static_cfg)
    EXCLUDED_DIRS_FROM_TREE = _get_excluded_dirs_from_tree(static_cfg)
    STATIC_CONTEXT_LIMITS = _get_static_context_limits(static_cfg)
    TRUNCATION_POLICY = _get_truncation_policy(static_cfg)

    limits = STATIC_CONTEXT_LIMITS
    truncation_policy = TRUNCATION_POLICY
    file_tree_depth = limits["file_tree_max_depth"]
    signature_depth = limits["python_signatures_max_depth"]
    max_lines = limits["max_lines"]

    context: Dict[str, Any] = {}
    context["_context_profile"] = {
        "name": active_profile,
        "source": profile_source,
        "reason": profile_reason,
    }

    # 1. Skills registry — loaded from generated SSOT (_index.yaml)
    if os.path.exists(SKILLS_PATH):
        full_registry = load_yaml_file(SKILLS_PATH)
        
        # Adaptation for new _index.yaml structure
        skills_list = full_registry.get("index", [])
        
        # Create a compact summary for the context window
        compact_skills = []
        for s in skills_list:
            compact_skills.append({
                "name": s.get("name"),
                "cluster": s.get("cluster", "misc"),
                "purpose": s.get("purpose", "")
            })

        context["skills_registry"] = {
            "metadata": {
                "version": full_registry.get("version"),
                "last_updated": full_registry.get("last_updated"),
                "generated_from": full_registry.get("generated_from")
            },
            "skills": compact_skills,
            "_note": "Live registry from _index.yaml. Full details in agent/skills/.",
            "_index_path": "agent/skills/_index.yaml",
            "_trigger_engine_path": "agent/skills/_trigger_engine.yaml",
        }
    else:
        context["skills_registry"] = {}
        print(f"[WARNING] Skills registry not found at {SKILLS_PATH}")

    # 2. Agent rules — metadata reference only (governance content, always tracked)
    context["agent_rules"] = _file_metadata(AGENT_RULES_PATH)

    # 3. Gitignored files — path-only references.
    #    These files are NOT included in the initial context.
    #    Use context_loader.load_on_demand("treemap") or
    #    context_loader.load_on_demand("dependencies_report") to fetch them.
    context["on_demand_files"] = {
        "treemap": {
            "path": TREEMAP_PATH,
            "loader": "context_loader.load_on_demand('treemap')",
            "_note": "Gitignored. Load on demand for structural analysis.",
        },
        "dependencies_report": {
            "path": DEPENDENCIES_REPORT_PATH,
            "loader": "context_loader.load_on_demand('dependencies_report')",
            "_note": "Gitignored. Load on demand for dependency analysis.",
        },
    }

    # Shared .gitignore spec for file tree and signatures
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gitignore_spec = _load_gitignore_spec(project_root)

    # 4. File tree (max depth 2) — folders only, no individual skill files
    context["file_tree"] = {
        "max_depth": file_tree_depth,
        "tree": _generate_file_tree(project_root, max_depth=file_tree_depth, spec=gitignore_spec),
    }

    # 5. Python signatures — class/function index (.gitignore respected, agent/skills excluded)
    context["python_signatures"] = _extract_python_signatures(
        project_root, max_depth=signature_depth, spec=gitignore_spec
    )

    # 6. Schemas — summaries only
    context["schemas"] = {}
    if os.path.exists(SCHEMAS_PATH):
        for fname in os.listdir(SCHEMAS_PATH):
            fpath = os.path.join(SCHEMAS_PATH, fname)
            context["schemas"][fname] = _schema_summary(fpath)
    context = _enforce_context_line_budget(
        context,
        max_lines=max_lines,
        policy=truncation_policy,
    )
    return context


def save_static_context_as_json(
    context: Dict[str, Any],
    output_path: str = "agent/agent_outputs/context.json",
    max_lines: Optional[int] = None,
) -> None:
    """Save static context to a JSON file for agent consumption."""
    if max_lines is None:
        budget = context.get("_context_budget", {})
        if isinstance(budget, dict) and isinstance(budget.get("max_lines"), int):
            max_lines = budget["max_lines"]
        else:
            max_lines = STATIC_CONTEXT_LIMITS["max_lines"]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2)

    size = os.path.getsize(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        line_count = sum(1 for _ in f)
    if line_count > max_lines:
        raise RuntimeError(
            f"Refusing to persist oversized context.json: {line_count} > {max_lines}"
        )
    print(f"Static context saved: {output_path}")
    print(f"  Size: {size:,} bytes ({size / 1024:.1f} KB)")
    print(f"  Lines: {line_count:,}")


# Ejecución de prueba
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate compact static context for Tinker.",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Optional static context profile name (overrides env/config).",
    )
    args = parser.parse_args()

    static_context = load_static_context(profile=args.profile)
    save_static_context_as_json(static_context)
    skills = static_context.get("skills_registry", {})
    metadata = skills.get("metadata", {})
    print(f"\nSkeleton context generated:")
    profile = static_context.get("_context_profile", {})
    if profile:
        print(
            f"  Active profile: {profile.get('name', 'default')} "
            f"({profile.get('source', 'default')}, reason={profile.get('reason', 'n/a')})"
        )
    print(f"  Skills registry version: {metadata.get('version', 'unknown')}")
    print(f"  Skills total: {metadata.get('total_skills', 0)} (index loaded separately via _index.yaml)")
    print(f"  Python files with signatures: {len(static_context.get('python_signatures', {}))}")
    print(f"  Schemas summarized: {list(static_context.get('schemas', {}).keys())}")
    print(f"  File tree entries: {len(static_context.get('file_tree', {}).get('tree', []))}")
    budget = static_context.get("_context_budget", {})
    if budget:
        print(
            f"  Context budget: {budget.get('final_lines', '?')}/{budget.get('max_lines', '?')} lines"
            f" (truncated={budget.get('truncation_applied', False)})"
        )



