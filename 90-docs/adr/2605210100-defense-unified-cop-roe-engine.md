---
id: adr-2605210100-defense-unified-cop-roe-engine
title: "Defense Unified COP + ROE Engine — Phase 10A fan-in aggregator"
status: active
doc_type: adr
topic: defense-cop-roe
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - unified COP alert queue design
  - ROE enforcement code path (deterministic vs LLM-prompt)
  - roc_code escalation authority model (ROC-A / ROC-B / ROC-C)
priority: 8.5
axis: architecture
weight: 0.85
depends_on:
  - adr-2605190100-defense-cluster-topology
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605082000-langgraph-graph-definition-as-data
supersedes: []
superseded_by: []
---

## Problem

Phase 9 produced 4 independent LangGraph graphs (mission, platform, sensor, EW).
Each writes to its own sub-graph vertices with no reactive integration layer.
`roc_code` in `MissionState` was only an LLM context string — no actual ROE validation
logic existed; a model could propose kinetic action under ROC-A with no enforcement.

## Decision

Add `unified_cop.py` as a Phase 10A fan-in LangGraph.

**`CopState`** carries:
- `source_graph` — which of the 4 Phase 9 graphs raised the alert
- `alert_priority` — derived heuristic (ew → critical, mission → high, sensor → medium, platform → low)
- `roc_code` — ROC-A | ROC-B | ROC-C
- `proposed_action` — action string validated against ROC permission set
- `roe_valid`, `roe_violations` — deterministic check results
- `acknowledged`, `operator_did` — operator acceptance record

**ROC permission model** (deterministic code, not LLM prompt):
- `ROC-A`: ISR collection + sensor fusion only
- `ROC-B`: ROC-A + electronic jamming + flare/chaff (non-kinetic EW)
- `ROC-C`: ROC-B + HPM + kinetic soft-kill (requires `classification_level >= 3`)

**Graph nodes**:
1. `node_ingest_alert` — validates source, sets priority heuristic
2. `node_validate_roe` — set-membership check + classification gate for kinetic
3. `node_deconflict` — advisory log; non-fatal (deconfliction does not block the alert)
4. `node_update_cop_state` — XRPC stub to persist alert in graph DB

**Routing** (`cop_route`):
- error present → end
- no alert_id → ingest
- alert_id but roe_violations empty → validate_roe
- roe_valid=False with violations → deconflict
- default → end

## Consequences

- COP alert queue enables real-time deconfliction across all 4 source graphs
- ROE enforcement moves from LLM prompt context to deterministic set-membership code
- Kinetic actions under ROC-C still require `classification_level >= 3` (hardware-gated)
- Node functions are pure (no I/O side-effects in unit tests); XRPC calls isolated to `node_update_cop_state`

## References

- `20-actors/defense/py/src/pydefense/unified_cop.py`
- `00-contracts/lexicons/com/etzhayyim/apps/defCop/`
- ADR-2605190100 (defense cluster topology)
