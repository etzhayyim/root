---
id: adr-2605210200-defense-cyber-operations
title: "Defense Cyber Operations — 5th PMESII Domain"
status: active
doc_type: adr
topic: defense-cyber-operations
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - defense cyber operations graph design
  - cyber effect authorization policy
  - PMESII cyber domain coverage
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

## Problem

PMESII coverage in the defense actor system has four domains modeled (Political, Military, Economic, Social/Information) but the fifth domain — **Cyber** — is unrepresented. Specifically:

1. Cyber effects (disrupt / degrade / deny / destroy) are unmodeled in any LangGraph agent.
2. No classification gate exists for cyber operations; all cyber targeting must be secret-or-above (level ≥ 3).
3. High-lethality cyber effects (`deny`, `destroy`) have no human-authorization invariant, creating an autonomy gap that mirrors the pre-EW risk.

## Decision

Add `cyber_operations.py` as a LangGraph agent for the `defCyber` PMESII domain. The design mirrors `ew_counteruas.py` exactly:

- **Effect escalation map** (analogous to `THREAT_INTERVENTION_MAP`):
  - `disrupt` → `low`
  - `degrade` → `medium`
  - `deny` → `high`
  - `destroy` → `critical`

- **Human-required safety invariant** (`_HUMAN_REQUIRED_EFFECTS = {"destroy", "deny"}`):
  If `autonomy_mode == "autonomous"` and `effect_type in _HUMAN_REQUIRED_EFFECTS`, force `autonomy_mode = "supervised"` and set `human_required = True`. This is a safety downgrade, not a fatal error — `state["error"]` is NOT set.

- **`destroy` always forced `supervised`** — highest-lethality cyber effect; no autonomous path permitted.

- **Classification gate**: `classification_level >= 3` required; rejection sets `state["error"]` and routes directly to audit.

- **Audit-always pattern**: audit node runs on every path including errors, identical to EW.

### Lexicons created under `00-contracts/lexicons/com/etzhayyim/apps/defCyber/`:
- `declareTarget.json` — procedure to register a cyber target (network/endpoint/scada/comms)
- `requestEffect.json` — procedure to request a cyber effect with autonomy mode
- `listEffects.json` — query to list effects by target vertex

## Consequences

- **Positive**: Closes the 5th PMESII domain; `cyber_operations.py` brings PMESII coverage to 100% (Political via `defPlatform`, Military via `defEw`, Economic via `defBudget`/`defContract`, Social via `defIsr`, Cyber via `defCyber`).
- **Positive**: Identical human-authorization pattern as EW kinetic: no new safety primitives required; auditability is structural.
- **Positive**: Integer-only classification levels and effect escalation map are Lexicon-compliant (no floats).
- **Neutral**: `authorizationToken` is optional in the Lexicon but enforced at the node level for `deny`/`destroy` — enforcement lives in `node_authorize_effect`, not the wire schema.
- **Risk**: SCADA targets (`targetType = "scada"`) have physical-world consequences equivalent to kinetic; operators MUST ensure `destroy` authorization tokens come from a certified human-in-loop chain. This is policy, not code.
