# Implement Analyze Graphs Plan

## Goal
Upgrade dependency context consumption from markdown-only (`dependencies_report.md`) to structured graph artifacts (`dependencies_graph.json`, `architecture_metrics.yaml`) to improve LLM accuracy, latency, and token efficiency while preserving backward compatibility.

## Current State
- Producer: `agents/hooks/analyze_dependencies.py` generates:
  - `agents/logic/analysis/dependencies_report.md`
  - `agents/logic/analysis/dependencies_graph.json`
  - `agents/logic/analysis/architecture_metrics.yaml`
- Consumers currently rely on markdown:
  - `agent_framework_config.yaml` exposes only `dependencies_report`.
  - `agents/tools/load_static_context.py` advertises only `dependencies_report` and `treemap` in `on_demand_files`.
  - `agents/tools/context_loader.py` loads full file contents without structured/partial querying.

## Desired End State
- Structured artifacts are first-class on-demand resources.
- `context_loader` supports targeted retrieval (section/module/top-N/SCC), not full-file by default.
- `load_static_context` points agents to structured artifacts first, markdown second.
- Backward-compatible support for existing `dependencies_report` workflows remains.

## Implementation Phases

### Phase 1: Registry and Metadata Wiring (Low Risk)
1. Update `agent_framework_config.yaml` `on_demand_files`:
   - Add `dependencies_graph`:
     - path: `agents/logic/analysis/dependencies_graph.json`
     - format: `json`
     - generated_by: `agents/hooks/analyze_dependencies.py`
   - Add `architecture_metrics`:
     - path: `agents/logic/analysis/architecture_metrics.yaml`
     - format: `yaml`
     - generated_by: `agents/hooks/analyze_dependencies.py`
2. Update fallback registry in `agents/tools/context_loader.py` with same keys and paths.
3. Update `agents/tools/load_static_context.py` `context["on_demand_files"]` to include both new keys.
4. Keep `dependencies_report` unchanged.

Acceptance criteria:
- `context_loader.list_available()` returns `treemap`, `dependencies_report`, `dependencies_graph`, `architecture_metrics`.
- Existing calls to `load_on_demand('dependencies_report')` continue to work.

### Phase 2: Structured Selective Loading (Core Improvement)
1. Extend `context_loader.load_on_demand(...)` signature to support optional query args:
   - `section: Optional[str]`
   - `module: Optional[str]`
   - `top_n: Optional[int]`
   - `scc_index: Optional[int]`
2. Add format-aware parsing:
   - JSON: `json.loads`
   - YAML: existing YAML loader utility
   - Markdown: unchanged
3. Add extraction rules:
   - `architecture_metrics.yaml`:
     - `section=summary|degree_metrics|cycles|entrypoints|issues`
     - `top_n` applied to hotspot lists
   - `dependencies_graph.json`:
     - `module=<module>` returns node metadata + outbound/inbound neighbors
     - `section=summary|nodes|edges|issues`
     - `scc_index=<i>` returns one SCC
4. Return compact payloads by default for structured formats:
   - include only requested slices + metadata (`exists`, `path`, `size_bytes`, `line_count`).

Acceptance criteria:
- Full file load still possible (no selectors).
- Selector-based responses are materially smaller than full file content.
- Invalid selector combinations return clear structured errors, not crashes.

### Phase 3: LLM-Optimized Dependency Snapshot API
1. Add helper API (same module or small companion file):
   - `load_dependency_snapshot(profile='compact')`
2. `compact` payload should include:
   - summary counts
   - top fan-in and fan-out (default top 10)
   - cycle overview (`scc_count`, `largest_scc_size`, sample SCCs)
   - issue counts by type
3. `debug` profile can include larger slices for diagnostics.

Acceptance criteria:
- Snapshot can replace common markdown consumption paths for agent reasoning.
- Average token footprint for dependency context is reduced.

### Phase 4: Staleness Guardrails
1. Add freshness check utility comparing:
   - artifact mtimes vs latest Python source mtime
2. If stale, return warning object:
   - `stale: true`
   - `recommended_command: python agents/hooks/analyze_dependencies.py`
3. Optional strict mode to fail structured loads when stale.

Acceptance criteria:
- Staleness is detected deterministically.
- Warning appears in returned payload without breaking backward compatibility.

### Phase 5: Prompt/Workflow Alignment
1. Update static context notes to instruct agents:
   - prefer `architecture_metrics` and targeted `dependencies_graph` queries
   - use markdown report only for narrative/human export
2. Keep old loader examples and add new examples.

Acceptance criteria:
- Documentation and context hints align with new loading strategy.
- No workflow break for existing tools or prompts.

## API Contract (Proposed)

### `load_on_demand(name, section=None, module=None, top_n=None, scc_index=None)`
Returns dict with base keys:
- `name`, `path`, `format`, `exists`
- `size_bytes`, `line_count` (if exists)
- `stale` (optional)
- `error` (optional)
- `content` (markdown/full legacy)
- `data` (structured filtered payload)

Validation rules:
- `module` only valid for `dependencies_graph`
- `scc_index` only valid when SCC data exists
- `top_n` must be positive integer

## Backward Compatibility
- Keep existing key names and behavior for:
  - `dependencies_report`
  - `treemap`
- New features are additive.
- Existing CLI interfaces remain unchanged.

## Test Plan
1. Unit tests:
   - registry loading (config and fallback)
   - selector parsing/validation
   - JSON/YAML extraction logic
   - staleness check logic
2. Integration tests:
   - run `python agents/hooks/analyze_dependencies.py`
   - verify on-demand load for all four keys
   - verify compact snapshot output shape
3. Regression tests:
   - existing markdown load path remains functional

## Risk Assessment
- Risk: YAML parser behavior mismatch in selective loads.
  - Mitigation: reuse existing loader utilities and validate output types.
- Risk: selector complexity increases maintenance cost.
  - Mitigation: strict validation and small, well-documented selector surface.
- Risk: stale artifacts causing incorrect reasoning.
  - Mitigation: freshness metadata + explicit regeneration command.

## Rollback Plan
- Revert to Phase 1 only (metadata wiring) and disable selective loading paths.
- Continue using `dependencies_report.md` as primary dependency artifact.
- Keep new artifact generation untouched (non-breaking).

## Definition of Done
- Structured dependency artifacts are discoverable and queryable on demand.
- LLM-facing dependency loads are smaller and more precise than markdown-only loads.
- Legacy markdown flows continue to function without modification.

