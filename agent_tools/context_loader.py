"""
context_loader.py

On-demand context loader for the Tinker agent framework.

This module complements load_static_context.py by providing a mechanism
to load specific gitignored files (treemap, dependencies_report) into
the agent context ONLY when explicitly requested.

Design rationale — portable deployment:
- The framework lives inside a HOST project and is gitignored by it.
- treemap.md and dependencies_report.md describe the HOST project, but
  they are generated inside the gitignored agent/ directory.
- The initial static context (context.json) stays small and respects
  .gitignore completely — these files are excluded.
- Agents that need structural or dependency analysis request them
  through load_on_demand(), which returns the content as a temporary
  overlay — it does NOT modify context.json on disk.

Usage:
    from agent_tools.context_loader import load_on_demand, enrich_context

    # Load a single on-demand file
    treemap_data = load_on_demand("treemap")

    # Enrich an existing context dict with on-demand data
    enriched = enrich_context(base_context, ["treemap", "dependencies_report"])
"""

import os
import yaml
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# Project root resolution
# ---------------------------------------------------------------------------

def get_project_root() -> str:
    """Resolve the HOST project root (parent of agent_tools/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


_CONFIG_FILENAME = "agent_framework_config.yaml"


# ---------------------------------------------------------------------------
# On-demand file registry (config-driven)
# ---------------------------------------------------------------------------
# The registry is loaded from agent_framework_config.yaml so that adding
# new on-demand files only requires a config change — no code edits.
# Falls back to a hardcoded default if the config is missing.

_FALLBACK_REGISTRY: Dict[str, Dict[str, str]] = {
    "treemap": {
        "path": os.path.join("agent", "analysis", "treemap.md"),
        "description": "Full project treemap for structural analysis",
        "format": "markdown",
    },
    "dependencies_report": {
        "path": os.path.join("agent", "analysis", "dependencies_report.md"),
        "description": "Dependency analysis report for the project",
        "format": "markdown",
    },
}


def _load_registry() -> Dict[str, Dict[str, str]]:
    """Load the on-demand file registry from agent_framework_config.yaml.

    Falls back to _FALLBACK_REGISTRY if the config is missing or unreadable.
    """
    config_path = os.path.join(get_project_root(), _CONFIG_FILENAME)
    if not os.path.exists(config_path):
        return dict(_FALLBACK_REGISTRY)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except Exception:
        return dict(_FALLBACK_REGISTRY)

    on_demand = config.get("on_demand_files")
    if not isinstance(on_demand, dict) or not on_demand:
        return dict(_FALLBACK_REGISTRY)

    registry: Dict[str, Dict[str, str]] = {}
    for name, entry in on_demand.items():
        if not isinstance(entry, dict) or "path" not in entry:
            continue
        registry[name] = {
            "path": entry["path"],
            "description": entry.get("description", ""),
            "format": entry.get("format", "unknown"),
        }
    return registry if registry else dict(_FALLBACK_REGISTRY)


# Module-level cache — loaded once per process.
_registry_cache: Dict[str, Dict[str, str]] = {}


def _get_registry() -> Dict[str, Dict[str, str]]:
    global _registry_cache
    if not _registry_cache:
        _registry_cache = _load_registry()
    return _registry_cache


def list_available() -> List[str]:
    """Return the names of all on-demand files available for loading."""
    return list(_get_registry().keys())


# ---------------------------------------------------------------------------
# On-demand file loading
# ---------------------------------------------------------------------------

def load_on_demand(name: str) -> Dict[str, Any]:
    """Load a single on-demand file by its logical name.

    Returns a dict with:
      - name: the logical name
      - path: project-relative path
      - exists: whether the file was found
      - content: full file content (only if exists)
      - line_count: number of lines (only if exists)
      - size_bytes: file size (only if exists)
      - error: error message (only on failure)

    Raises KeyError if the name is not in the on-demand registry.
    """
    registry = _get_registry()
    if name not in registry:
        available = ", ".join(registry.keys())
        raise KeyError(
            f"Unknown on-demand file '{name}'. Available: {available}"
        )

    entry = registry[name]
    rel_path = entry["path"]
    abs_path = os.path.join(get_project_root(), rel_path)

    result: Dict[str, Any] = {
        "name": name,
        "path": rel_path,
        "description": entry["description"],
        "format": entry["format"],
    }

    if not os.path.exists(abs_path):
        result["exists"] = False
        result["error"] = f"File not found: {rel_path}"
        return result

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
        result["exists"] = True
        result["content"] = content
        result["line_count"] = content.count("\n") + 1
        result["size_bytes"] = os.path.getsize(abs_path)
    except (IOError, UnicodeDecodeError) as exc:
        result["exists"] = True
        result["error"] = f"Failed to read {rel_path}: {exc}"

    return result


def enrich_context(
    base_context: Dict[str, Any],
    file_names: List[str],
) -> Dict[str, Any]:
    """Return a NEW context dict enriched with on-demand file content.

    This does NOT mutate base_context — it creates a shallow copy and adds
    an '_on_demand' key containing the requested file data.  This keeps
    the enrichment clearly separated from the static context.

    Args:
        base_context: The static context dict from load_static_context().
        file_names:   List of logical names to load (e.g. ["treemap"]).

    Returns:
        A new dict with the same keys as base_context plus '_on_demand'.
    """
    enriched = dict(base_context)  # shallow copy
    on_demand_data: Dict[str, Any] = {}

    for name in file_names:
        on_demand_data[name] = load_on_demand(name)

    enriched["_on_demand"] = {
        "_note": "Temporary on-demand data. NOT persisted to context.json.",
        "files": on_demand_data,
    }
    return enriched


# ---------------------------------------------------------------------------
# CLI / standalone execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    print("On-demand context loader (portable)")
    print(f"Project root: {get_project_root()}")
    print(f"Available files: {list_available()}\n")

    # If names are passed as args, load them; otherwise load all
    names = sys.argv[1:] if len(sys.argv) > 1 else list_available()

    for name in names:
        print(f"--- Loading: {name} ---")
        try:
            result = load_on_demand(name)
        except KeyError as e:
            print(f"  ERROR: {e}\n")
            continue

        if result.get("exists"):
            print(f"  Path:  {result['path']}")
            print(f"  Lines: {result.get('line_count', '?')}")
            print(f"  Size:  {result.get('size_bytes', '?')} bytes")
            # Show first 5 lines as preview
            content = result.get("content", "")
            preview = "\n".join(content.splitlines()[:5])
            print(f"  Preview:\n{preview}\n")
        else:
            print(f"  {result.get('error', 'Not found')}\n")

