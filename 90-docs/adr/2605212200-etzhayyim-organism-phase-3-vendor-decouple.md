---
id: adr-2605212200-etzhayyim-organism-phase-3-vendor-decouple
title: "ADR-2605212200: etzhayyim active-inference organism — Phase 3 vendor decouple (primitives migration + table drop + NSID rename)"
status: proposed
doc_type: adr
topic: etzhayyim-organism-phase-3-vendor-decouple
authoritative: true
last_verified: 2026-05-21
priority: 9.0
axis: governance
weight: 0.90
priority_note: "STRONG — closes the Phase 2 rollout from ADR-2605211200 by physically moving the organism source-of-truth to etzhayyim/root, dropping the vendor RW tables, and completing the com.etzhayyim.agent.* / com.etzhayyim.consent.capability.* NSID rename to ai.etzhayyim.*. Blocked on Phase 2 30d clean run; not executable before then."
authoritative_for:
  - physical location of active-inference primitives (etzhayyim/root vs vendor monorepo)
  - vertex_agent_* table lifecycle (archive + drop)
  - NSID rename catalog (com.etzhayyim.agent.* / com.etzhayyim.consent.capability.* → ai.etzhayyim.*)
  - vendor monorepo cleanup pass (delete what moved)
depends_on:
  - adr-2605211200-etzhayyim-active-inference-organism-on-murakumo
  - adr-2605152100-etzhayyim-github-org-boundary
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
  - adr-2605181400-bpmn-extract-to-etzhayyim-root
related:
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605172300-etzhayyim-open-telecom-fabric
supersedes: []
superseded_by: []
---

# ADR-2605212200: Phase 3 vendor decouple — organism → etzhayyim/root

**Status**: proposed
**Date**: 2026-05-21
**Blocked on**: ADR-2605211200 Phase 2 30d clean production run
**Deciders**: Jun Kawasaki

# Context

ADR-2605211200 (Phases 1 + 2) landed as a 17-PR stack on 2026-05-21
(#1340 – #1357). The deliverables span scaffolding (12 Lexicons +
BeliefStore protocol + SQLite/AT/IPFS impl + k8s manifests), CF Worker
dispatch routing (synthesisTier + fetchLlm + consent capability), MCP
facade backend (issue/verify/revoke + JWKS + GC), observability (TS +
Python counters + Grafana dashboard + 6 SLO alerts + AlertManager
template).

What landed is **all additive** — the live organism still runs against
the vendor RW (`BELIEF_STORE_BACKEND=rw` default) and the primitives
still physically live in this vendor monorepo. The 17-PR stack is the
preparation; it is not the cutover.

This ADR records the **Phase 3 plan** for the actual cutover. It is
written before execution so the operator runbook can be reviewed +
critiqued without time pressure during the production rollout window.

# Decision

Adopt a 5-stage Phase 3 plan. **No stage may run before the previous
stage's verification gate passes for ≥7 days in production.** The full
sequence takes 5–8 weeks calendar time depending on per-actor cutover
divergence reports.

## Stage A — Phase 2 rollout to production (the 17-PR stack)

Verification gate: all 4 production runbooks from ADR-2605211200
Closure section executed:
  1. `wrangler secret put CONSENT_CAPABILITY_SECRET`
  2. D1 `consent_revocations` created + bound
  3. `kubectl apply -f 50-infra/k8s/organism-langgraph/` (all manifests
     including obs alerts + AlertManager receivers)
  4. Grafana dashboard `etzhayyim-organism-slos` imported

Pass criteria (Prometheus alerts must be green for 7 days):
  - `OrganismPath1RatioBelow90` not firing
  - `OrganismConsentCacheHitBelow50` not firing
  - `OrganismDispatchFailureSpike` not firing
  - `OrganismConsentMintFailureSpike` not firing

This stage runs entirely in the vendor monorepo. No file moves yet.

## Stage B — Per-actor BELIEF_STORE_BACKEND cutover (7 actors × 14d each)

Per-actor sequence (smallest blast radius first; LLM-heaviest last):

```
kobo → kabi → kinoko → koke → saikin → ki → hakkou
```

Per actor:
  1. Day 0: patch `belief-store-config` ConfigMap with
     `BELIEF_STORE_BACKEND_<ACTOR>=dual-write`
  2. Days 0–7: observation window. Materializer divergence report
     ≤0.1% / day (script: `70-tools/scripts/etzhayyim/at-ipfs-belief-materializer.py`)
  3. Day 7: flip to `BELIEF_STORE_BACKEND_<ACTOR>=at-ipfs-local`
  4. Days 7–14: second observation window. Confirm reads now hit the
     AT MST + IPFS path exclusively, RW row count stops growing for
     that actor.

After all 7 actors:
  - Global flip: `BELIEF_STORE_BACKEND=at-ipfs-local`, clear all 7
    per-actor overrides
  - All `vertex_agent_*` table writes from the organism cease

Pass criteria: 7 days zero RW write from the organism daemon path,
confirmed via `SELECT count(*) FROM vertex_agent_observation WHERE
inserted_at > '<global-flip-time>'` returns 0.

## Stage C — NSID rename catalog (Tranche F follow-up)

Add aliasing in `00-contracts/lexicons/` and the generated registry so
both NSID forms resolve to the same handler for a 30-day overlap
window:

| Current (vendor) | New (etzhayyim) |
|---|---|
| `com.etzhayyim.agent.observation` | `ai.etzhayyim.agent.observation` |
| `com.etzhayyim.agent.beliefState` | `ai.etzhayyim.agent.beliefState` |
| `com.etzhayyim.agent.priorPreference` | `ai.etzhayyim.agent.priorPreference` |
| `com.etzhayyim.agent.activeInferenceTick` | `ai.etzhayyim.agent.activeInferenceTick` |
| `com.etzhayyim.agent.actionProposal` | `ai.etzhayyim.agent.actionProposal` |
| `com.etzhayyim.agent.realworldEffect` | `ai.etzhayyim.agent.realworldEffect` |
| `com.etzhayyim.agent.homeostasisSnapshot` | `ai.etzhayyim.agent.homeostasisSnapshot` |
| `com.etzhayyim.agent.dispatchLedger` | `ai.etzhayyim.agent.dispatchLedger` |
| `com.etzhayyim.agent.delegatedAuthorityPolicy` | `ai.etzhayyim.agent.delegatedAuthorityPolicy` |
| `com.etzhayyim.agent.policyAdaptationProposal` | `ai.etzhayyim.agent.policyAdaptationProposal` |
| `com.etzhayyim.agent.counterpartyModel` | `ai.etzhayyim.agent.counterpartyModel` |
| `com.etzhayyim.agent.protectedAsset` | `ai.etzhayyim.agent.protectedAsset` |
| `com.etzhayyim.consent.capability.issueToken` | `ai.etzhayyim.consent.capability.issueToken` |
| `com.etzhayyim.consent.capability.verifyToken` | `ai.etzhayyim.consent.capability.verifyToken` |
| `com.etzhayyim.consent.capability.revokeToken` | `ai.etzhayyim.consent.capability.revokeToken` |
| `com.etzhayyim.consent.capability.jwks` | `ai.etzhayyim.consent.capability.jwks` |

(16 NSIDs total — 12 from Phase 1, 4 from Phase 2C.3 + 2C.4 + 2C.4.3.)

Implementation: dual-publish the lexicon JSON under both
`00-contracts/lexicons/com/etzhayyim/...` AND
`00-contracts/lexicons/ai/etzhayyim/...` with `aliasFor` cross-refs;
client code at the agent SDK + CF Worker handler reads either form.

Pass criteria after 30 days of dual-publish:
  - All callers in vendor monorepo use the new form (grep returns 0
    `com.etzhayyim.agent.*` / `com.etzhayyim.consent.capability.*` references)
  - PDS bundle includes both forms; deprecation warning logs the
    old form

## Stage D — Physical primitives migration to `etzhayyim/root`

Files to move (`/move` semantics: copy + commit on etzhayyim/root,
then delete from vendor monorepo with `[MOVED]` README stub):

| Source (vendor) | Destination (etzhayyim/root) |
|---|---|
| `20-actors/magatama/py/src/pymagatama/primitives/active_inference.py` | `20-actors/magatama/py/src/pymagatama/primitives/active_inference.py` |
| `20-actors/magatama/py/src/pymagatama/primitives/rl_active_inference.py` | (same) |
| `20-actors/magatama/py/src/pymagatama/primitives/rl_policy.py` | (same) |
| `20-actors/magatama/py/src/pymagatama/primitives/rl_preferences.py` | (same) |
| `20-actors/magatama/py/src/pymagatama/primitives/rl_signal.py` | (same) |
| `20-actors/magatama/py/src/pymagatama/primitives/active_inference_substrate.py` | (same) |
| `20-actors/magatama/py/src/pymagatama/primitives/at_ipfs_belief_store.py` | (same) |
| `20-actors/magatama/py/src/pymagatama/primitives/rw_belief_store.py` | NOT moved (vendor-only — keeps RW shim for legacy paths) |
| `20-actors/magatama/py/src/pymagatama/primitives/telemetry_counters.py` | (same) |
| 7 worker modules (`kabi_worker_main.py` etc.) | `20-actors/magatama/py/src/pymagatama/{kabi,kobo,kinoko,koke,saikin,ki,hakkou}_worker_main.py` |
| `agent_daemon_main.py` write path | refactored copy to etzhayyim/root with no `insert_direct_row` (writes via `BeliefStore.put_row` only) |
| `agent_status_main.py` read path | (same) |
| 16 Lexicon JSON files (12 agent + 4 capability) | `00-contracts/lexicons/ai/etzhayyim/{agent,consent/capability}/` (already dual-published per Stage C) |
| `00-contracts/lexicons/com/etzhayyim/{agent,consent/capability}/` | DELETED after Stage C 30d window |
| 50-infra/k8s/organism-langgraph/* | moved to etzhayyim/root/50-infra/k8s/organism-langgraph/ |
| `50-infra/cloudflare/workers/atproto/src/consent-capability-handler.ts` | NOT moved — MCP facade stays at mcp.etzhayyim.com (vendor capability per ADR D3c) |
| `50-infra/cloudflare/workers/atproto/src/llm-dispatch.ts` | NOT moved — CF Worker edge proxy stays vendor (consumes etzhayyim capability) |

Pass criteria:
  - `grep -r "from pymagatama.primitives.active_inference" vendor-monorepo` returns 0
  - `grep -r "com.etzhayyim.agent\." vendor-monorepo` returns 0 (Stage C condition reused)
  - etzhayyim/root organism k8s deployment runs ≥7 days clean
  - vendor monorepo build still passes (delete pass should not have broken any imports)

## Stage E — `vertex_agent_*` table drop

After Stage B passes its second observation window AND Stage D passes:

```sql
-- Archive snapshot to Iceberg S3 (legal retention)
COPY vertex_agent_observation TO 's3://etzhayyim-iceberg/archive/2606/vertex_agent_observation.parquet' (FORMAT PARQUET);
-- ... (12 tables, mirror Stage B order)

-- Drop after 30-day archive grace
DROP TABLE vertex_agent_observation;
-- ... (12 tables)
```

Schema files to remove from `30-graph/graph-schema/migrations/`:
  - `20260507110100_vertex_agent_active_inference.ts` (7 tables)
  - `20260507131300_vertex_agent_dispatch_ledger.ts` (1 table)
  - `20260507131400_vertex_agent_policy_adaptation_proposal.ts` (1 table)
  - `20260507220000_vertex_agent_delegated_authority_policy.ts` (1 table)
  - `20260507610000_agent_counterparty_minimax_graph.ts` (3 tables)

(14 tables total; the 12 ADR-2605211200 D3b tables + 2 read-only minimax/information tables not in D3b but moved together for table-set coherence.)

Pass criteria: zero rows lost (parquet row count matches RW row count at archive time) + 7 days no read errors from any caller pointing at the dropped tables.

# Consequences

## Positive

- Organism source-of-truth physically lives in etzhayyim/root (matches
  the Liability + Custody axes of the 3-axis split per ADR-2605172400)
- `vertex_agent_*` tables eliminated from vendor RW (Custody axis fully
  resolved — operator no longer holds any organism state)
- NSID namespace cleanup (`com.etzhayyim.agent.*` retired, single `ai.etzhayyim.*`
  surface)
- Vendor monorepo shrinks by ~7 worker modules + 5 primitive modules +
  16 lexicons + 14 schema migration files

## Negative / risks

- 5–8 week calendar window for the per-actor cutover sequence
- Stage D delete pass risks breaking vendor build if any import was
  missed — mitigated by `pnpm exec vitest run` + `pytest` smoke after
  each migration step
- Stage E archive parquet must be verifiable against RW row counts; if
  archive fails the operator must roll back to Stage D and re-run
  archive before dropping
- During Stage C 30-day overlap, MCP facade dispatch must route both
  NSID forms to the same handler (operationally simple but bug-prone)

## Re-judgment triggers

- Phase 2 SLO alerts firing during Stage A → re-judge whether the
  scaffolding had a bug; do not enter Stage B until alerts are clean
- Per-actor divergence report > 0.1% during Stage B for any actor →
  pause that actor, investigate root cause, do not flip to
  at-ipfs-local until divergence resolves
- Stage E archive parquet row count ≠ RW row count → STOP, do not drop,
  re-archive
- Any production incident on the live organism during Stages A–B →
  fallback runbook: patch `BELIEF_STORE_BACKEND_<ACTOR>=rw` to revert
  that actor immediately

# Verification

Verification gates listed inline per stage above. The full Phase 3
completion criterion is:

1. All 14 vertex_agent_* tables DROPped + archived
2. All 16 lexicon NSIDs renamed to `ai.etzhayyim.*`
3. 12 primitive Python modules physically reside in etzhayyim/root
4. Vendor monorepo grep for `com.etzhayyim.agent.*` + `vertex_agent_*` returns 0
5. ≥30 days clean SLO alerts post-completion

When all 5 are met, this ADR can be flipped from `proposed` →
`active` and a Phase 4 ADR can be drafted if any further work is
needed (e.g. multi-region replication of the organism state on AT MST).

# References

- ADR-2605211200 — Phase 1 + 2 implementation (parent)
- ADR-2605152100 — etzhayyim/root org boundary
- ADR-2605172000 — etzhayyim RW-free substrate
- ADR-2605172100 — payments on-chain only
- ADR-2605172400 — 3-axis split rule
- ADR-2605181400 — BPMN extract precedent (similar dual-publish pattern)
- ADR-2605091400 — MCP cell-membrane (Lexicon dual-wire SSoT)
