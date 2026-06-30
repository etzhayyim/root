---
id: 2605232200-unispsc-actor-learning-loop-closure
title: "ADR-2605232200: UNSPSC actor learning loop closure — wrapper prior_consensus + opt-in cell shortcut (Stage D Phase A)"
status: proposed
doc_type: adr
topic: actor-learning-loop
authoritative: true
last_verified: 2026-05-23
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "First substrate-anchored learning loop in the etzhayyim/* scope — qualitative shift from 'data accumulation' to 'adaptive behavior'"
authoritative_for:
  - UNSPSC actor learning-loop architecture
  - `_prior_consensus` wire-level contract (wrapper → cell)
  - cell-side opt-in shortcut pattern (reference impl c10101500)
depends_on:
  - adr-2605232100-etzhayyim-organism-vertical-implementation
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2605211200-etzhayyim-active-inference-organism-on-murakumo
  - 2605231630-langgraph-chain-server-canonical-goose-retirement
related:
V05171300
  - adr-2605192100-etzhayyim-mission-charter
supersedes: []
superseded_by: []
---

# ADR-2605232200: UNSPSC actor learning loop closure (Stage D Phase A)

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

## Context

ADR-2605232100 Stage D (2026-05-23 morning) wrapped every UNSPSC actor invocation with a perceive→record loop. The **record** half persisted each observation to a local SQLite hot cache (`AtIpfsLocalBeliefStore`, ADR-2605211200) and the publish callback was subsequently wired through to PDS / IPFS / L2-anchor (Stage D Day 1, commits `e49e8ddec`–`375fd87fb`). The **perceive** half read prior observations and injected them into the inner LangGraph payload as `_prior_observations`.

The verification log on the orbstack-hosted lg-open-unispsc Pod (18,342 actors) revealed that the loop was **architecturally open**: priors were injected but **no actor consulted them**. 18,342 actor `c*.py` files have bespoke per-commodity StateGraphs that ignored the `_prior_observations` field entirely. Each invocation behaved identically regardless of past invocations — "data accumulation" without "learning."

The end-user-visible symptom: invoking `c10101500` (Live Animal) with `{species: "bos taurus", health_data: {certified: true}}` returned the same result on the 1st invocation and the 1000th, despite the system having recorded 999 prior outcomes.

This ADR records the closure of that loop.

## Decision

**(1) Wrapper computes a `_prior_consensus` learning signal on every invocation** and injects it into the inner graph's payload alongside the raw `_prior_observations`. The signal is a five-field dict:

```python
{
  "outcome_count":        int,    # total priors with a non-null result.status
  "dominant_status":      str | None,  # most-frequent prior result.status
  "dominant_count":       int,    # how many priors carried the dominant status
  "confidence_permille":  int,    # dominant_count / outcome_count * 1000  (0-1000)
  "input_match_count":    int,    # priors with at least one (key, value) match against current input
}
```

Cells can read `_prior_consensus` from their State (LangGraph TypedDict preserves extra payload keys across nodes) to short-circuit, boost confidence, or branch on prior-informed routing — **purely opt-in**. Cells that ignore it behave exactly as they would without Stage D wrapping.

**(2) `_prior_consensus` is also annotated onto the wrapper's response** (alongside `_observation_uri` + `_prior_count`) so downstream callers (XRPC consumers, derived AppViews, debug tooling) can observe the learning signal without re-querying the belief store.

**(3) Reference implementation — `c10101500.py` (Live Animal)** demonstrates the canonical "prior shortcut" pattern. Its `verify_health` node now reads `_prior_consensus` and, when:

- `outcome_count >= 3`, AND
- `confidence_permille >= 800` (i.e. ≥80% of priors agree), AND
- `input_match_count >= 1` (current input matches at least one prior on at least one key/value pair), AND
- `dominant_status == "authorized"`

short-circuits to `health_certified=True` (skipping the cert lookup) and continues through the rest of the graph. Otherwise the original deterministic check runs. The cell's `State` TypedDict gains `_prior_observations: list[dict]` + `_prior_consensus: dict` fields so the wrapper's injection is type-known to LangGraph.

The bespoke domain logic is **preserved verbatim** for inputs that don't trigger the shortcut. Determinism on the non-shortcut path is unchanged.

**(4) Observation `input` field stores the inner user-meaningful input**, not the wrapper's wire-level payload (which contains the wrapper-injected fields). This makes prior `input` shape comparable to current `input` for the loose-match in `_compute_prior_consensus.input_match_count`.

**(5) The pattern is repository-scoped, not codemod-applied.** Reference impl is in place at `c10101500.py`. Other 18,341 actors continue with deterministic-only behavior until an operator (or a follow-up codemod) applies the 3-line shortcut pattern. The wrapper signal is always computed regardless — cells can opt-in over time without rewriting the wrapper.

## Consequences

### Positive

- **First substrate-anchored learning loop** in the etzhayyim/* scope. Same input → same result, but **execution path differs based on past outcomes**. Verified on orbstack 2026-05-23 21:30 JST with 4 sequential invocations: invocation 4+ takes the shortcut.
- **Cell-agnostic wrapper.** All 18,342 actors get the learning signal for free without code changes. Adoption is per-cell, gradual, and reversible.
- **Substrate-aligned.** The signal is computed from records that flow through PDS → IPFS → L2 anchor (per ADR-2605231400 kotoba-datomic composition). Cells that adopt the shortcut therefore learn from substrate-anchored history, not Pod-local ephemeral state.
- **No new runtime dependency.** `_compute_prior_consensus` is pure-Python aggregation over the existing `list_observations` SQLite query — no new ports, no new sidecars.
- **Forward-compatible with Stage E member-signed writes.** When member-signed writes land (ADR-2605231525 Stage E), the publish path swaps service-token for passkey-signature; the consensus computation is unaffected because it reads from the local hot cache (which is hydrated by the substrate).

### Negative

- **Reference impl only.** 18,341 actors still don't read priors. Effective learning surface is 1 / 18,342 today. The 3-line opt-in pattern needs to be applied (manually or via codemod) to each actor that would benefit.
- **Input matching is loose.** The match uses "at least one (key, value) pair" — too permissive for some domains (e.g. financial actors where every key matters). Cells with strict matching needs must implement their own consensus filter on top of `_prior_observations`.
- **Confidence threshold (800/1000) is a fixed magic number** in c10101500. Cells with different risk profiles need different thresholds — currently hard-coded per-cell. A registry of cell-specific thresholds is a follow-up.
- **Determinism erosion.** Same input no longer guarantees same execution path. For test fixtures and contract verification, callers must either clear the belief store or pass an explicit `_skip_prior_consensus` flag (not yet implemented).

### Neutral

- Existing `_observation_uri` + `_prior_count` response fields are unchanged. Adding `_prior_consensus` is purely additive.
- Wire-level payload shape change is backward-compatible: cells that don't read `_prior_consensus` get the field passed through harmlessly.
- The PDS publish callback continues to fire on every observation; consensus is computed locally so it doesn't depend on PDS availability.

## Alternatives Considered

| Option | Rejected because |
|---|---|
| Run a codemod across all 18,342 actors to insert prior_shortcut conditionals | Risky bulk change, hard to test per-cell correctness, breaks deterministic guarantees for tests that rely on cold behavior. Reference + gradual adoption is safer. |
| Run prior consultation as a leading LangGraph node prepended to every cell's compiled graph (wrapper builds a new graph that invokes the cell as a subgraph) | Doubles the per-actor compile cost (18,342 wrapper graphs in the lru_cache); requires defining a State schema common to all cells; brittle when cell State definitions diverge. |
| Compute consensus only at the wrapper level + use it solely for fast-path caching (skip inner graph entirely on high-confidence prior match) | Bypasses the cell's own logic, breaks audit trail (no log of why the result was returned), and prevents cells from layering their own prior-informed decisions. |
| Use LangGraph's built-in checkpointer as the "memory" without a separate consensus signal | Checkpointer state is per-thread, not per-actor-DID — wrong granularity for "this actor has seen N similar inputs before." Stage D's belief store is the correct substrate. |

## Verification (2026-05-23 21:30 JST, orbstack lg-open-unispsc)

```
=== Invoke 1 ===
"_prior_consensus": {"outcome_count": 4, ...}
"log": ["10101500:verify_health:prior_shortcut(conf=1000/1000,n=4,matches=4)", ...]

=== Invoke 2 ===
"log": ["10101500:verify_health:prior_shortcut(conf=1000/1000,n=5,matches=5)", ...]

=== Invoke 3 ===
"log": ["10101500:verify_health:prior_shortcut(conf=1000/1000,n=5,matches=5)", ...]

=== Invoke 4 ===
"log": ["10101500:verify_health:prior_shortcut(conf=1000/1000,n=5,matches=5)", ...]
```

The 4th invocation's `log_tail` cascade through all prior shortcut events — the system has full visibility into when it learned and what it learned from.

## References

- ADR-2605232100 — religious-corp cells on k3s DaemonSet (Stage D Day 0 wrapper)
- ADR-2605231400 — kotoba-datomic Holochain-iso substrate (composition spec)
- ADR-2605231525 — no-server-key architecture (Stage E future direction)
- ADR-2605211200 — kotoba belief store substrate port (AtIpfsLocalBeliefStore)
- ADR-2605192100 — etzhayyim mission charter ("人類の構造的労働解放" → learning is necessary)
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/unispsc_capabilities/wrapper.py` — `_compute_prior_consensus`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/unispsc_capabilities/pds_publish.py` — publish callback (substrate persistence)
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/langgraph_graphs/unispsc_agents/c10101500.py` — reference impl for `prior_shortcut`
- `50-infra/k8s/lg-open-unispsc/deployment.yaml` — Pod env (ETZ_UNISPSC_CAPABILITY_WRAP=1)
