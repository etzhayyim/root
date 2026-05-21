---
id: adr-2605210300-defense-logistics-ops-bridge
title: "Defense Logistics-Ops Bridge"
status: active
doc_type: adr
topic: defense-logistics-ops
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - defense logistics operations bridge design
  - platform maintenance to procurement flow
  - mission execution to EVM event linkage
priority: 8.0
axis: architecture
weight: 0.8
depends_on:
  - adr-2605190100-defense-cluster-topology
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605082000-langgraph-graph-definition-as-data
supersedes: []
superseded_by: []
---

## Context

Phase 9 of the defense actor system introduced platform telemetry and mission status tracking. However, this operational data is siloed from the Phase 1–8 procurement and contract layer:

- Maintenance events from Phase 9 (battery depletion, sensor faults, actuator failures) cannot trigger resupply purchase orders in the procurement actor.
- EVM (Earned Value Management) events are not linked to mission execution, making it impossible to reconcile mission operational costs against contract budgets.
- The result is a broken feedback loop: platforms can require resupply without any automated procurement signal, and contract budget burn is invisible to operational planners.

## Decision

Add `logistics_ops.py` as a LangGraph-based ops-to-procurement bridge within the `pydefense` module.

The bridge:
1. **Assesses platform status** using telemetry from Phase 9 (battery, fuel, maintenance flags).
2. **Triggers resupply** via XRPC to the procurement actor when battery or fuel falls below threshold.
3. **Links mission execution to EVM events** so contract budget tracking reflects real operational costs.

### Threshold constants

| Constant | Value (permille) | Meaning |
|---|---|---|
| `BATTERY_CRITICAL_THRESHOLD` | `150` | 15% — trigger resupply |
| `FUEL_CRITICAL_THRESHOLD` | `200` | 20% — trigger resupply |

These are integers (permille, ×1000) consistent with the AT Protocol Lexicon integer-only rule and the existing `batteryPermille` field convention in `defPlatform.updatePlatformState`.

### LangGraph nodes

| Node | Responsibility |
|---|---|
| `node_assess_platform_status` | Check battery/fuel thresholds; populate `maintenance_flags`; set `resupply_required` |
| `node_trigger_resupply` | Call XRPC to procurement actor; record `logistics_vertex_id` |
| `node_link_mission_evm` | Record EVM event linking mission execution to contract; set `evm_event_id` |
| `node_log_maintenance` | Persist maintenance record for audit trail |

### Routing (`logistics_route`)

1. `error` set → `"end"`
2. `platform_vertex_id` empty → `"end"`
3. `resupply_required` and no `logistics_vertex_id` → `"resupply"`
4. `maintenance_flags` set + `mission_vertex_id` + `contract_vertex_id` + no `evm_event_id` → `"evm_link"`
5. `maintenance_flags` set + no `logistics_vertex_id` → `"log"`
6. No flags and no `resupply_required` (fresh state) → `"assess"`
7. Default → `"end"`

## Consequences

- **Closes the operational→procurement feedback loop**: low-battery/fuel events now automatically generate resupply orders.
- **Enables EVM contract tracking**: mission execution costs are traceable to specific contract budget lines.
- **Enables automated maintenance scheduling**: maintenance flags from Phase 9 telemetry flow into the logistics layer without manual intervention.
- **Scaffold only (MVP)**: `node_trigger_resupply` and `node_link_mission_evm` are stubs pending XRPC endpoint implementation in the procurement actor.
