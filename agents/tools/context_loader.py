"""
context_loader.py

On-demand context loader for the Tinker agent framework.

This module complements load_static_context.py by loading selected gitignored
analysis artifacts only when requested. Structured artifacts can be queried
without loading their full content to keep token usage low.
"""

import json
import os
from typing import Any, Dict, List, Optional

try:
    from agents.tools._context_common import load_yaml_file, project_root
except ImportError:
    from _context_common import load_yaml_file, project_root  # type: ignore


def get_project_root() -> str:
    """Resolve the host project root (parent of agents/tools/)."""
    return str(project_root())


_CONFIG_FILENAME = "agent_framework_config.yaml"
_DEP_ARTIFACT_KEYS = {"dependencies_report", "dependencies_graph", "architecture_metrics"}


_FALLBACK_REGISTRY: Dict[str, Dict[str, str]] = {
    "treemap": {
        "path": os.path.join("agents", "logic", "analysis", "treemap.md"),
        "description": "Full project treemap for structural analysis",
        "format": "markdown",
    },
    "dependencies_report": {
        "path": os.path.join("agents", "logic", "analysis", "dependencies_report.md"),
        "description": "Dependency analysis report for the project",
        "format": "markdown",
    },
    "dependencies_graph": {
        "path": os.path.join("agents", "logic", "analysis", "dependencies_graph.json"),
        "description": "Canonical directed dependency graph",
        "format": "json",
    },
    "architecture_metrics": {
        "path": os.path.join("agents", "logic", "analysis", "architecture_metrics.yaml"),
        "description": "Architecture metrics derived from dependency graph",
        "format": "yaml",
    },
}


def _load_registry() -> Dict[str, Dict[str, str]]:
    """Load on-demand file registry from agent_framework_config.yaml."""
    config_path = os.path.join(get_project_root(), _CONFIG_FILENAME)
    if not os.path.exists(config_path):
        return dict(_FALLBACK_REGISTRY)

    try:
        config = load_yaml_file(config_path) or {}
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


_registry_cache: Dict[str, Dict[str, str]] = {}


def _get_registry() -> Dict[str, Dict[str, str]]:
    global _registry_cache
    if not _registry_cache:
        _registry_cache = _load_registry()
    return _registry_cache


def list_available() -> List[str]:
    """Return names of all on-demand files available for loading."""
    return list(_get_registry().keys())


def _normalize_format(raw_fmt: str) -> str:
    val = (raw_fmt or "").strip().lower()
    if val in {"md", "markdown"}:
        return "markdown"
    if val in {"yml", "yaml"}:
        return "yaml"
    if val == "json":
        return "json"
    return val or "unknown"


def _file_metadata(abs_path: str, rel_path: str, result: Dict[str, Any]) -> Optional[str]:
    if not os.path.exists(abs_path):
        result["exists"] = False
        result["error"] = f"File not found: {rel_path}"
        return None
    result["exists"] = True
    result["size_bytes"] = os.path.getsize(abs_path)
    try:
        with open(abs_path, "r", encoding="utf-8") as handle:
            text = handle.read()
        result["line_count"] = text.count("\n") + 1
        return text
    except (IOError, UnicodeDecodeError) as exc:
        result["error"] = f"Failed to read {rel_path}: {exc}"
        return None


def _collect_latest_python_mtime(root: str) -> Optional[float]:
    latest: Optional[float] = None
    excluded_dirs = {".git", "__pycache__", ".venv", "venv", ".pytest_cache"}
    for current_root, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for filename in files:
            if not filename.endswith(".py"):
                continue
            full_path = os.path.join(current_root, filename)
            try:
                mtime = os.path.getmtime(full_path)
            except OSError:
                continue
            if latest is None or mtime > latest:
                latest = mtime
    return latest


def _staleness_info(name: str, artifact_path: str) -> Dict[str, Any]:
    if name not in _DEP_ARTIFACT_KEYS:
        return {"stale": False}
    try:
        artifact_mtime = os.path.getmtime(artifact_path)
    except OSError:
        return {"stale": False}

    latest_py = _collect_latest_python_mtime(get_project_root())
    if latest_py is None:
        return {"stale": False}

    stale = latest_py > artifact_mtime
    return {
        "stale": stale,
        "recommended_command": "python agents/hooks/analyze_dependencies.py" if stale else None,
    }


def _slice_top_lists(payload: Dict[str, Any], top_n: Optional[int]) -> Dict[str, Any]:
    if top_n is None:
        return payload
    if top_n <= 0:
        raise ValueError("top_n must be a positive integer")

    out = dict(payload)
    degree = out.get("degree_metrics")
    if isinstance(degree, dict):
        degree = dict(degree)
        for key in ["top_fan_in", "top_fan_out"]:
            value = degree.get(key)
            if isinstance(value, list):
                degree[key] = value[:top_n]
        out["degree_metrics"] = degree

    cycles = out.get("cycles")
    if isinstance(cycles, dict) and isinstance(cycles.get("sccs"), list):
        cycles = dict(cycles)
        cycles["sccs"] = cycles["sccs"][:top_n]
        out["cycles"] = cycles
    return out


def _module_snapshot(graph: Dict[str, Any], module: str) -> Dict[str, Any]:
    module_id = module if module.startswith("module:") else f"module:{module}"
    nodes = graph.get("nodes", [])
    adjacency = graph.get("adjacency", {})
    forward = adjacency.get("forward", {}) if isinstance(adjacency, dict) else {}
    reverse = adjacency.get("reverse", {}) if isinstance(adjacency, dict) else {}

    node_entry = None
    if isinstance(nodes, list):
        for node in nodes:
            if isinstance(node, dict) and node.get("id") == module_id:
                node_entry = node
                break

    return {
        "module": module_id,
        "node": node_entry,
        "imports": forward.get(module_id, []),
        "imported_by": reverse.get(module_id, []),
    }


def _extract_structured(
    name: str,
    data: Any,
    section: Optional[str],
    module: Optional[str],
    top_n: Optional[int],
    scc_index: Optional[int],
) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {"data": data}

    if top_n is not None and top_n <= 0:
        raise ValueError("top_n must be a positive integer")

    if module and name != "dependencies_graph":
        raise ValueError("module selector is only supported for dependencies_graph")

    if module:
        return {"data": _module_snapshot(data, module)}

    if scc_index is not None:
        metrics = data.get("metrics", data)
        cycles = metrics.get("cycles", {}) if isinstance(metrics, dict) else {}
        sccs = cycles.get("sccs", []) if isinstance(cycles, dict) else []
        if not isinstance(sccs, list):
            raise ValueError("SCC data is not available")
        if scc_index < 0 or scc_index >= len(sccs):
            raise ValueError(f"scc_index out of range: {scc_index}")
        return {"data": {"scc_index": scc_index, "component": sccs[scc_index], "scc_count": len(sccs)}}

    if section:
        if section not in data:
            raise ValueError(f"Unknown section '{section}'. Available: {', '.join(sorted(data.keys()))}")
        section_payload = data[section]
        if isinstance(section_payload, dict):
            section_payload = _slice_top_lists(section_payload, top_n)
        return {"data": section_payload}

    if name == "architecture_metrics":
        compact = {
            "summary": data.get("summary", {}),
            "degree_metrics": data.get("degree_metrics", {}),
            "entrypoints": data.get("entrypoints", {}),
            "cycles": data.get("cycles", {}),
        }
        return {"data": _slice_top_lists(compact, top_n or 10)}

    if name == "dependencies_graph":
        metrics = data.get("metrics", {}) if isinstance(data.get("metrics"), dict) else {}
        compact = {
            "summary": metrics.get("summary", {}),
            "degree_metrics": metrics.get("degree_metrics", {}),
            "entrypoints": metrics.get("entrypoints", {}),
            "cycles": metrics.get("cycles", {}),
            "issues_count": len(data.get("issues", [])) if isinstance(data.get("issues"), list) else 0,
        }
        return {"data": _slice_top_lists(compact, top_n or 10)}

    return {"data": data}


def load_on_demand(
    name: str,
    section: Optional[str] = None,
    module: Optional[str] = None,
    top_n: Optional[int] = None,
    scc_index: Optional[int] = None,
    include_content: Optional[bool] = None,
) -> Dict[str, Any]:
    """Load one on-demand file by logical name, with optional selective query."""
    registry = _get_registry()
    if name not in registry:
        available = ", ".join(sorted(registry.keys()))
        raise KeyError(f"Unknown on-demand file '{name}'. Available: {available}")

    entry = registry[name]
    rel_path = entry["path"]
    abs_path = os.path.join(get_project_root(), rel_path)
    fmt = _normalize_format(entry.get("format", "unknown"))

    result: Dict[str, Any] = {
        "name": name,
        "path": rel_path,
        "description": entry.get("description", ""),
        "format": fmt,
        "query": {
            "section": section,
            "module": module,
            "top_n": top_n,
            "scc_index": scc_index,
        },
    }

    text = _file_metadata(abs_path, rel_path, result)
    if text is None:
        return result

    result.update(_staleness_info(name, abs_path))

    structured = fmt in {"json", "yaml"}
    if include_content is None:
        include_content = not structured

    if include_content:
        result["content"] = text

    if not structured:
        return result

    try:
        parsed: Any
        if fmt == "json":
            parsed = json.loads(text)
        else:
            parsed = load_yaml_file(abs_path)
    except Exception as exc:
        result["error"] = f"Failed to parse {fmt} content from {rel_path}: {exc}"
        return result

    try:
        result.update(_extract_structured(name, parsed, section, module, top_n, scc_index))
    except ValueError as exc:
        result["error"] = str(exc)

    return result


def load_dependency_snapshot(profile: str = "compact", top_n: int = 10) -> Dict[str, Any]:
    """Return an LLM-optimized dependency snapshot.

    profile='compact' returns high signal, low token data.
    profile='debug' includes additional structured sections.
    """
    metrics_result = load_on_demand("architecture_metrics", top_n=top_n)
    graph_issues_result = load_on_demand("dependencies_graph", section="issues")

    snapshot: Dict[str, Any] = {
        "profile": profile,
        "metrics_path": metrics_result.get("path"),
        "graph_path": graph_issues_result.get("path"),
        "stale": bool(metrics_result.get("stale") or graph_issues_result.get("stale")),
        "recommended_command": metrics_result.get("recommended_command") or graph_issues_result.get("recommended_command"),
    }

    if metrics_result.get("error"):
        snapshot["error"] = metrics_result["error"]
        return snapshot

    metrics_data = metrics_result.get("data", {})
    if not isinstance(metrics_data, dict):
        snapshot["error"] = "Unexpected architecture_metrics shape"
        return snapshot

    issue_counts: Dict[str, int] = {}
    issues = graph_issues_result.get("data", [])
    if isinstance(issues, list):
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            kind = str(issue.get("type", "unknown"))
            issue_counts[kind] = issue_counts.get(kind, 0) + 1

    snapshot["summary"] = metrics_data.get("summary", {})
    snapshot["hotspots"] = {
        "top_fan_out": metrics_data.get("degree_metrics", {}).get("top_fan_out", []),
        "top_fan_in": metrics_data.get("degree_metrics", {}).get("top_fan_in", []),
    }
    snapshot["cycles"] = metrics_data.get("cycles", {})
    snapshot["entrypoints"] = metrics_data.get("entrypoints", {})
    snapshot["issue_counts"] = issue_counts

    if profile == "debug":
        snapshot["metrics_full"] = metrics_data
    return snapshot


def enrich_context(base_context: Dict[str, Any], file_names: List[str]) -> Dict[str, Any]:
    """Return a new context dict enriched with on-demand file data."""
    enriched = dict(base_context)
    on_demand_data: Dict[str, Any] = {}

    for name in file_names:
        on_demand_data[name] = load_on_demand(name)

    enriched["_on_demand"] = {
        "_note": "Temporary on-demand data. NOT persisted to context.json.",
        "files": on_demand_data,
    }
    return enriched


if __name__ == "__main__":
    import sys

    print("On-demand context loader (portable)")
    print(f"Project root: {get_project_root()}")
    print(f"Available files: {list_available()}\n")

    names = sys.argv[1:] if len(sys.argv) > 1 else list_available()

    for name in names:
        print(f"--- Loading: {name} ---")
        try:
            result = load_on_demand(name)
        except KeyError as exc:
            print(f"  ERROR: {exc}\n")
            continue

        if result.get("exists"):
            print(f"  Path:  {result['path']}")
            print(f"  Lines: {result.get('line_count', '?')}")
            print(f"  Size:  {result.get('size_bytes', '?')} bytes")
            if result.get("stale"):
                print(f"  Stale: true ({result.get('recommended_command')})")
            if "content" in result:
                preview = "\n".join(str(result["content"]).splitlines()[:5])
                print(f"  Preview:\n{preview}\n")
            elif "data" in result:
                print("  Structured data loaded (content omitted).\n")
        else:
            print(f"  {result.get('error', 'Not found')}\n")
