#!/usr/bin/env python3
"""
Analyze Python dependencies and generate architecture outputs.

Outputs:
- dependencies_report.md        (narrative summary)
- dependencies_graph.json       (canonical machine graph)
- architecture_metrics.yaml     (structured metrics summary)
"""

from __future__ import annotations

import argparse
import ast
import json
import os
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

try:
    from agents.tools._repo_root import find_project_root
except ImportError:
    from _repo_root import find_project_root  # type: ignore

try:
    import pathspec  # type: ignore
except Exception:
    pathspec = None  # type: ignore


@dataclass
class Node:
    id: str
    kind: str
    label: str
    module: Optional[str] = None
    file_path: Optional[str] = None
    is_package: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    source: str
    target: str
    kind: str
    raw: str
    import_type: Optional[str] = None
    lineno: Optional[int] = None
    col_offset: Optional[int] = None


@dataclass
class Issue:
    type: str
    file: str
    message: str
    lineno: Optional[int] = None


@dataclass
class DependencyGraph:
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    forward: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    reverse: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    issues: List[Issue] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)
        self.forward[edge.source].add(edge.target)
        self.reverse[edge.target].add(edge.source)

    def add_issue(self, issue: Issue) -> None:
        self.issues.append(issue)


def load_gitignore(project_root: Path) -> Tuple[Optional[Any], List[str]]:
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        return None, []
    raw = None
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            raw = gitignore_path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    if raw is None:
        return None, []
    patterns = [
        line.strip()
        for line in raw.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if pathspec is not None:
        return pathspec.PathSpec.from_lines("gitwildmatch", patterns), patterns
    return None, patterns


def is_ignored(rel_path: str, spec: Optional[Any], fallback_patterns: List[str]) -> bool:
    if spec is not None:
        return bool(spec.match_file(rel_path))
    for pat in fallback_patterns:
        clean = pat.rstrip("/")
        if pat.endswith("/") and rel_path.startswith(clean + "/"):
            return True
        if fnmatch(rel_path, pat):
            return True
    return False


def discover_python_files(project_root: Path, spec: Optional[Any], patterns: List[str]) -> List[Path]:
    files: List[Path] = []
    for root, dirs, filenames in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache"}]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            p = Path(root) / filename
            rel = p.relative_to(project_root).as_posix()
            if is_ignored(rel, spec, patterns):
                continue
            files.append(p)
    return files


def module_name_from_path(project_root: Path, file_path: Path) -> Tuple[str, bool]:
    rel = file_path.relative_to(project_root).as_posix()
    is_package = rel.endswith("/__init__.py") or rel == "__init__.py"
    if rel == "__init__.py":
        return "__init__", True
    if rel.endswith("/__init__.py"):
        return rel[:-12].replace("/", "."), True
    return rel[:-3].replace("/", "."), False


def build_module_index(project_root: Path, files: Iterable[Path]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, bool]]:
    module_to_file: Dict[str, str] = {}
    file_to_module: Dict[str, str] = {}
    module_is_package: Dict[str, bool] = {}
    for f in files:
        module, is_package = module_name_from_path(project_root, f)
        rel = f.relative_to(project_root).as_posix()
        module_to_file[module] = rel
        file_to_module[rel] = module
        module_is_package[module] = is_package
    return module_to_file, file_to_module, module_is_package


def pick_internal_module(candidate: str, module_to_file: Dict[str, str]) -> Optional[str]:
    if candidate in module_to_file:
        return candidate
    parts = candidate.split(".")
    for i in range(len(parts) - 1, 0, -1):
        prefix = ".".join(parts[:i])
        if prefix in module_to_file:
            return prefix
    return None


def resolve_relative_base(current_module: str, is_package: bool, level: int) -> Optional[str]:
    package = current_module if is_package else ".".join(current_module.split(".")[:-1])
    pkg_parts = package.split(".") if package else []
    drop = max(level - 1, 0)
    if drop > len(pkg_parts):
        return None
    kept = pkg_parts[: len(pkg_parts) - drop] if drop > 0 else pkg_parts
    return ".".join(kept)


def normalize_config_path(raw: str) -> str:
    return raw.replace("\\", "/")


def extract_config_accesses(tree: ast.AST) -> List[Tuple[str, int, int]]:
    accesses: List[Tuple[str, int, int]] = []
    valid_ext = (".json", ".yaml", ".yml", ".sql", ".txt", ".csv", ".ini", ".toml", ".env")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        first_arg = node.args[0]
        if not isinstance(first_arg, ast.Constant) or not isinstance(first_arg.value, str):
            continue
        raw = first_arg.value
        if not raw.lower().endswith(valid_ext):
            continue

        is_match = False
        if isinstance(node.func, ast.Name) and node.func.id in {"open", "Path"}:
            is_match = True
        elif isinstance(node.func, ast.Attribute) and node.func.attr in {
            "read_csv",
            "read_json",
            "read_sql",
            "read_excel",
            "read_parquet",
            "load",
        }:
            is_match = True

        if is_match:
            accesses.append((normalize_config_path(raw), getattr(node, "lineno", 0), getattr(node, "col_offset", 0)))
    return accesses


def build_dependency_graph(project_root: Path, files: List[Path]) -> DependencyGraph:
    module_to_file, _, module_is_package = build_module_index(project_root, files)
    graph = DependencyGraph()

    for module, rel_path in module_to_file.items():
        graph.add_node(
            Node(
                id=f"module:{module}",
                kind="python_module",
                label=module,
                module=module,
                file_path=rel_path,
                is_package=module_is_package.get(module, False),
            )
        )

    for file_path in files:
        rel_file = file_path.relative_to(project_root).as_posix()
        module_name, is_package = module_name_from_path(project_root, file_path)
        source_id = f"module:{module_name}"
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=rel_file)
        except Exception as exc:
            graph.add_issue(Issue(type="parse_error", file=rel_file, message=str(exc)))
            continue

        # Config edges (module -> config file)
        seen_configs: Set[str] = set()
        for raw_cfg, lineno, col in extract_config_accesses(tree):
            cfg_id = f"file:{raw_cfg}"
            if cfg_id not in graph.nodes:
                graph.add_node(Node(id=cfg_id, kind="config_file", label=raw_cfg, file_path=raw_cfg))
            key = f"{source_id}->{cfg_id}"
            if key not in seen_configs:
                seen_configs.add(key)
                graph.add_edge(
                    Edge(
                        source=source_id,
                        target=cfg_id,
                        kind="config_access",
                        raw=raw_cfg,
                        lineno=lineno,
                        col_offset=col,
                    )
                )

        # Import edges
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported = alias.name
                    target_module = pick_internal_module(imported, module_to_file)
                    if target_module is not None:
                        target_id = f"module:{target_module}"
                    else:
                        target_id = f"external:{imported}"
                        if target_id not in graph.nodes:
                            graph.add_node(Node(id=target_id, kind="external_package", label=imported, module=imported))
                    graph.add_edge(
                        Edge(
                            source=source_id,
                            target=target_id,
                            kind="imports",
                            raw=imported,
                            import_type="import",
                            lineno=getattr(node, "lineno", None),
                            col_offset=getattr(node, "col_offset", None),
                        )
                    )

            elif isinstance(node, ast.ImportFrom):
                level = int(getattr(node, "level", 0) or 0)
                base_module = node.module or ""

                if level > 0:
                    resolved_base = resolve_relative_base(module_name, is_package, level)
                    if resolved_base is None:
                        graph.add_issue(
                            Issue(
                                type="relative_import_error",
                                file=rel_file,
                                message=f"Unable to resolve relative import: level={level}, module={base_module!r}",
                                lineno=getattr(node, "lineno", None),
                            )
                        )
                        continue
                    import_base = ".".join([p for p in [resolved_base, base_module] if p]).strip(".")
                    import_type = "relative_import"
                else:
                    import_base = base_module
                    import_type = "from_import"

                alias_targets: List[str] = []
                if not import_base and node.names:
                    for a in node.names:
                        if a.name != "*":
                            alias_targets.append(a.name)
                elif node.names:
                    for a in node.names:
                        if a.name == "*":
                            alias_targets.append(import_base)
                        else:
                            alias_targets.append(f"{import_base}.{a.name}" if import_base else a.name)
                else:
                    alias_targets.append(import_base)

                for candidate in alias_targets:
                    candidate = candidate.strip(".")
                    if not candidate:
                        continue
                    target_module = pick_internal_module(candidate, module_to_file)
                    if target_module is None and import_base:
                        target_module = pick_internal_module(import_base, module_to_file)

                    if target_module is not None:
                        target_id = f"module:{target_module}"
                    else:
                        target_id = f"external:{candidate}"
                        if target_id not in graph.nodes:
                            graph.add_node(Node(id=target_id, kind="external_package", label=candidate, module=candidate))
                        if level > 0:
                            graph.add_issue(
                                Issue(
                                    type="unresolved_relative_target",
                                    file=rel_file,
                                    message=f"Unresolved relative target: {candidate}",
                                    lineno=getattr(node, "lineno", None),
                                )
                            )

                    graph.add_edge(
                        Edge(
                            source=source_id,
                            target=target_id,
                            kind="imports",
                            raw=candidate,
                            import_type=import_type,
                            lineno=getattr(node, "lineno", None),
                            col_offset=getattr(node, "col_offset", None),
                        )
                    )

    return graph


def internal_module_ids(graph: DependencyGraph) -> List[str]:
    return sorted([nid for nid, n in graph.nodes.items() if n.kind == "python_module"])


def compute_scc_tarjan(graph: DependencyGraph, module_ids: List[str]) -> List[List[str]]:
    allowed = set(module_ids)
    adj: Dict[str, List[str]] = {
        m: [t for t in graph.forward.get(m, set()) if t in allowed] for m in module_ids
    }

    index = 0
    stack: List[str] = []
    on_stack: Set[str] = set()
    indices: Dict[str, int] = {}
    lowlink: Dict[str, int] = {}
    sccs: List[List[str]] = []

    def strongconnect(v: str) -> None:
        nonlocal index
        indices[v] = index
        lowlink[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)

        for w in adj.get(v, []):
            if w not in indices:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in on_stack:
                lowlink[v] = min(lowlink[v], indices[w])

        if lowlink[v] == indices[v]:
            comp: List[str] = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                comp.append(w)
                if w == v:
                    break
            sccs.append(sorted(comp))

    for v in module_ids:
        if v not in indices:
            strongconnect(v)
    return sccs


def compute_metrics(graph: DependencyGraph) -> Dict[str, Any]:
    modules = internal_module_ids(graph)
    module_set = set(modules)

    fan_out: Dict[str, int] = {}
    fan_in: Dict[str, int] = {}
    for m in modules:
        fan_out[m] = len([t for t in graph.forward.get(m, set()) if t in module_set])
        fan_in[m] = len([s for s in graph.reverse.get(m, set()) if s in module_set])

    roots = sorted([m for m in modules if fan_in.get(m, 0) == 0])
    sinks = sorted([m for m in modules if fan_out.get(m, 0) == 0])
    isolated = sorted([m for m in modules if fan_in.get(m, 0) == 0 and fan_out.get(m, 0) == 0])

    sccs_all = compute_scc_tarjan(graph, modules)
    cyclic_sccs = [c for c in sccs_all if len(c) > 1]
    self_cycles = []
    for m in modules:
        if m in graph.forward.get(m, set()):
            self_cycles.append([m])

    top_fan_out = sorted(fan_out.items(), key=lambda x: (-x[1], x[0]))[:20]
    top_fan_in = sorted(fan_in.items(), key=lambda x: (-x[1], x[0]))[:20]

    external_count = len([n for n in graph.nodes.values() if n.kind == "external_package"])
    config_count = len([n for n in graph.nodes.values() if n.kind == "config_file"])

    return {
        "summary": {
            "total_nodes": len(graph.nodes),
            "total_edges": len(graph.edges),
            "internal_modules": len(modules),
            "external_packages": external_count,
            "config_files": config_count,
            "issues": len(graph.issues),
        },
        "degree_metrics": {
            "fan_in": fan_in,
            "fan_out": fan_out,
            "top_fan_in": [{"module": m, "value": v} for m, v in top_fan_in],
            "top_fan_out": [{"module": m, "value": v} for m, v in top_fan_out],
        },
        "entrypoints": {
            "roots": roots,
            "sinks": sinks,
            "isolated": isolated,
        },
        "cycles": {
            "scc_count": len(cyclic_sccs),
            "self_cycle_count": len(self_cycles),
            "largest_scc_size": max([len(c) for c in cyclic_sccs], default=0),
            "sccs": cyclic_sccs + self_cycles,
        },
    }


def graph_to_json_payload(graph: DependencyGraph, metrics: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    return {
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "nodes": [asdict(n) for n in sorted(graph.nodes.values(), key=lambda x: x.id)],
        "edges": [asdict(e) for e in graph.edges],
        "adjacency": {
            "forward": {k: sorted(v) for k, v in sorted(graph.forward.items())},
            "reverse": {k: sorted(v) for k, v in sorted(graph.reverse.items())},
        },
        "issues": [asdict(i) for i in graph.issues],
        "metrics": metrics,
    }


def to_simple_yaml(data: Any, indent: int = 0) -> str:
    pad = "  " * indent
    if isinstance(data, dict):
        lines: List[str] = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.append(to_simple_yaml(value, indent + 1))
            else:
                lines.append(f"{pad}{key}: {yaml_scalar(value)}")
        return "\n".join(lines)
    if isinstance(data, list):
        lines = []
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.append(to_simple_yaml(item, indent + 1))
            else:
                lines.append(f"{pad}- {yaml_scalar(item)}")
        return "\n".join(lines)
    return f"{pad}{yaml_scalar(data)}"


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    if not s:
        return "''"
    if any(ch in s for ch in [":", "#", "{", "}", "[", "]", ",", "\n", '"', "'"]) or s.strip() != s:
        return json.dumps(s)
    return s


def generate_markdown_report(graph: DependencyGraph, metrics: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Project Dependency Analysis\n")
    lines.append("> Report generated from explicit directed dependency graph.\n")
    lines.append("## Executive Summary\n")
    summary = metrics["summary"]
    lines.append(f"- Total nodes: {summary['total_nodes']}")
    lines.append(f"- Total edges: {summary['total_edges']}")
    lines.append(f"- Internal modules: {summary['internal_modules']}")
    lines.append(f"- External packages: {summary['external_packages']}")
    lines.append(f"- Config files: {summary['config_files']}")
    lines.append(f"- Issues: {summary['issues']}\n")

    lines.append("## Entry Points\n")
    roots = metrics["entrypoints"]["roots"]
    if roots:
        for r in roots[:50]:
            lines.append(f"- `{r.replace('module:', '')}`")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Dependency Hotspots\n")
    lines.append("### Top Fan-Out")
    for row in metrics["degree_metrics"]["top_fan_out"][:15]:
        lines.append(f"- `{row['module'].replace('module:', '')}`: {row['value']}")
    lines.append("")
    lines.append("### Top Fan-In")
    for row in metrics["degree_metrics"]["top_fan_in"][:15]:
        lines.append(f"- `{row['module'].replace('module:', '')}`: {row['value']}")
    lines.append("")

    lines.append("## Cycles (SCC)\n")
    cycles = metrics["cycles"]
    lines.append(f"- SCC count (>1 node): {cycles['scc_count']}")
    lines.append(f"- Self-cycle count: {cycles['self_cycle_count']}")
    lines.append(f"- Largest SCC size: {cycles['largest_scc_size']}\n")
    for idx, comp in enumerate(cycles["sccs"][:20], start=1):
        pretty = ", ".join(f"`{m.replace('module:', '')}`" for m in comp)
        lines.append(f"{idx}. {pretty}")
    if not cycles["sccs"]:
        lines.append("- No cycles detected.")
    lines.append("")

    lines.append("## Config File Access\n")
    config_nodes = sorted([n for n in graph.nodes.values() if n.kind == "config_file"], key=lambda n: n.id)
    if not config_nodes:
        lines.append("- No config file access detected.\n")
    else:
        for cfg in config_nodes[:100]:
            consumers = sorted(graph.reverse.get(cfg.id, set()))
            short = [f"`{c.replace('module:', '')}`" for c in consumers if c.startswith("module:")]
            lines.append(f"- `{cfg.label}` <- {', '.join(short) if short else 'none'}")
        lines.append("")

    if graph.issues:
        lines.append("## Analysis Issues\n")
        for issue in graph.issues[:200]:
            loc = f"{issue.file}:{issue.lineno}" if issue.lineno else issue.file
            lines.append(f"- `{issue.type}` at `{loc}`: {issue.message}")
        lines.append("")

    lines.append("## Notes\n")
    lines.append("- Imports are resolved via AST with absolute and relative import handling.")
    lines.append("- This report is derived from the directed graph and associated metrics outputs.")
    return "\n".join(lines) + "\n"


def write_outputs(project_root: Path, markdown_output: Path, graph: DependencyGraph, metrics: Dict[str, Any]) -> None:
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    graph_path = markdown_output.parent / "dependencies_graph.json"
    metrics_path = markdown_output.parent / "architecture_metrics.yaml"

    json_payload = graph_to_json_payload(graph, metrics, project_root)
    graph_path.write_text(json.dumps(json_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    metrics_payload = {
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        **metrics,
    }
    metrics_path.write_text(to_simple_yaml(metrics_payload) + "\n", encoding="utf-8")

    markdown = generate_markdown_report(graph, metrics)
    markdown_output.write_text(markdown, encoding="utf-8")

    print(f"Report generated: {markdown_output}")
    print(f"Graph JSON generated: {graph_path}")
    print(f"Metrics YAML generated: {metrics_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze Python dependencies and generate markdown report")
    parser.add_argument("--project-root", help="Optional project root override")
    parser.add_argument("--output", help="Optional report output path")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve() if args.project_root else find_project_root(Path(__file__).resolve().parent)
    print("Analyzing project structure...")

    gitignore_spec, fallback_patterns = load_gitignore(project_root)
    if gitignore_spec is not None:
        print(".gitignore patterns loaded (pathspec)")
    elif fallback_patterns:
        print(".gitignore patterns loaded (stdlib fallback)")
    else:
        print("Warning: .gitignore not found")

    py_files = discover_python_files(project_root, gitignore_spec, fallback_patterns)
    if not py_files:
        print("No Python modules found in project")
        return 1

    graph = build_dependency_graph(project_root, py_files)
    metrics = compute_metrics(graph)

    print(f"Analyzed {metrics['summary']['internal_modules']} Python modules")

    default_report = project_root / "agents" / "logic" / "analysis" / "dependencies_report.md"
    markdown_output = Path(args.output).resolve() if args.output else default_report
    write_outputs(project_root, markdown_output, graph, metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
