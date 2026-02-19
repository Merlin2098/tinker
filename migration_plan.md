# Dependency Analyzer Migration Plan

## Goal
Refactor `agents/hooks/analyze_dependencies.py` from a list-based AST report generator into a true directed graph engine with structured outputs:
- `dependencies_graph.json`
- `architecture_metrics.yaml`
- `dependencies_report.md`

## Scope
- Preserve CLI compatibility:
  - `--project-root`
  - `--output` (Markdown output path)
- Preserve `.gitignore` behavior.
- Keep implementation lightweight (stdlib-first; optional `pathspec` use).

## Phased Implementation Checklist

### Phase A - Graph Core (no workflow break)
- [ ] Introduce explicit graph model (`Node`, `Edge`, `Graph`).
- [ ] Build module index from project Python files.
- [ ] Keep existing command behavior and markdown generation path.

### Phase B - Import Resolution & Reverse Graph
- [ ] Resolve absolute and relative imports using module context.
- [ ] Build forward adjacency and reverse adjacency maps.
- [ ] Track unresolved imports in a structured issues list.

### Phase C - Metrics Engine
- [ ] Add fan-in/fan-out metrics.
- [ ] Add entry-point/root and sink detection.
- [ ] Add SCC cycle detection (Tarjan).

### Phase D - Structured Outputs
- [ ] Emit `dependencies_graph.json` (canonical machine model).
- [ ] Emit `architecture_metrics.yaml` (summary + hotspots + SCC).
- [ ] Keep markdown output generation active.

### Phase E - Markdown from Structured Graph
- [ ] Generate Markdown using graph + metrics data only.
- [ ] Include cycle summary and top dependency hotspots.
- [ ] Keep report path and invocation unchanged.

## Validation Plan
- [ ] Run analyzer with default args and verify all 3 outputs are created.
- [ ] Run analyzer with `--output` custom path and verify JSON/YAML colocate with report.
- [ ] Confirm CLI remains unchanged for existing scripts.
- [ ] Verify no hard dependency on `pathspec` (fallback works when missing).

## Risks
- Import resolution corner cases (`from . import x`, namespace packages).
- False positives/negatives in config file access extraction.
- Output churn in downstream consumers expecting previous markdown-only structure.

## Mitigations
- Record unresolved imports in `issues` instead of silently dropping.
- Keep output filenames deterministic and stable.
- Preserve markdown as a first-class output for continuity.


