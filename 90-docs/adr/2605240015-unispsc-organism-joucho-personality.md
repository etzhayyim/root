---
id: adr-2605240015-unispsc-organism-joucho-personality
title: "ADR-2605240015: UNSPSC organism joucho — deterministic per-code personality + MST writer hook"
status: proposed
doc_type: adr
topic: unispsc-organism-joucho
authoritative: true
last_verified: 2026-05-24
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "Phase 5 of ADR-2605232345. Replaces the constant 50/50/30/50/50 default joucho provider with a deterministic per-code personality derived from the UNSPSC code itself, so all 18,342 organisms have distinct stable moods without requiring an MST round-trip. Defines the future hook for an MST-backed JouchoScore reader."
authoritative_for:
  - deterministic UNSPSC joucho personality function (5-axis from code seed)
  - com.etzhayyim.apps.etzhayyim.joucho.score lexicon shape (proposed)
  - joucho_personality_provider Python contract
depends_on:
  - adr-2605232345-unispsc-actor-as-organism
  - adr-2605240000-unispsc-organism-fleet-mass-deploy
related: []
supersedes: []
superseded_by: []
---

# ADR-2605240015: UNSPSC organism joucho — deterministic personality + MST writer hook

**Status**: proposed
**Date**: 2026-05-24
**Deciders**: Jun Kawasaki

# Context

ADR-2605232345 built the joucho 情緒 5-axis mood machinery for Python
organisms and shipped a default constant provider returning 50/50/30/50/50
for every actor. ADR-2605240000 fans this out to 18,342 organisms across
joseph/issachar/dan.

With the default constant provider, every organism has the same mood
("neutral") and the same cadence. That collapses the "ecosystem" claim:
identical organisms are not an ecosystem. The TS heartbeat-cadence on the
app side reads `JouchoScore` from a Kysely-backed `vertex_joucho_score`
table, but that path is explicitly CHARTER-VIOLATING per the TS comment
("centralized DB forbidden — migrate to AT MST + IPFS + Base L2") and is
unavailable on the Python organism side anyway.

Two needs:

1. **Right now**: give each of the 18,342 codes a stable distinct
   personality without any network or MST round-trip.
2. **Eventually**: hook real per-actor mood signals (web traffic to
   `/profile/c{code}`, classify-call success rate, follower engagement)
   into a substrate-native (MST + IPFS + Base L2 anchor) store.

# Decision

## Layer 1 — Deterministic personality (this ADR, immediate)

A pure function `code → JouchoScores` derives the 5-axis baseline from
the UNSPSC code itself. The mapping is:

- Deterministic (same code → same scores forever).
- Distributed (different codes → meaningfully different scores).
- Domain-aware (segment-prefix biases mood toward the commodity's nature
  — e.g., segment 10 "Live Plant/Animal" leans toward `joy`+`gratitude`;
  segment 14 "Paper Products" leans toward `calm`+`focus`).

The function uses a SHA-256 hash of the code combined with a small
per-segment bias table. Output is clamped to [0, 100] per axis.

Lives in `kotodama.organism.personality`. Exposes:

```python
def joucho_personality_provider(actor_did: str) -> JouchoScores: ...
def joucho_for_code(code: str) -> JouchoScores: ...
```

The fleet cell wires `joucho_personality_provider` as the default provider
for every organism it constructs.

### Segment bias intuition

Per-segment bias (anchored to UNSPSC top-level segments):

| Segment | Theme | Bias |
|---|---|---|
| 10 | Live Plant/Animal | +joy +gratitude |
| 11 | Mineral/Metal | +calm +focus |
| 12 | Chemicals | +focus −joy |
| 13 | Rubber/Plastic | +calm |
| 14 | Paper Products | +calm +focus |
| 15 | Fuels/Lubricants | +stress |
| 20-29 | Industrial Equipment | +focus |
| 30-39 | Components / Structural | +focus +calm |
| 40-49 | Distribution / Logistics | +calm |
| 50-55 | Food / Beverage / Health | +joy +gratitude |
| 56-60 | Lab / Office / Services | +calm +focus |

The bias is small (±15 per axis) layered on top of a hash-driven base.
Net effect: most organisms are distinguishable by segment alone, with
in-segment variation from the hash.

## Layer 2 — MST writer hook (future, scaffolded)

The lexicon shape for the eventual MST record:

```
NSID: com.etzhayyim.apps.etzhayyim.joucho.score
collection record:
  $type: com.etzhayyim.apps.etzhayyim.joucho.score
  actorDid: did:web:etzhayyim.com:actor:c{code}
  scores:
    joy: int 0..100
    calm: int 0..100
    stress: int 0..100
    gratitude: int 0..100
    focus: int 0..100
  observedAt: datetime
  source: enum [personality, profile-traffic, classify-success, follower-engagement, manual]
```

Write path (deferred):

1. Tick-side signal observers (profile-traffic counter, classify success
   rate, follower engagement) emit `JouchoScore` records every N ticks
   via `@etzhayyim/sdk` MST write + IPFS pin + Base L2 anchor batch.
2. `joucho_mst_provider` reads the latest score from the per-actor MST
   collection. Falls back to `joucho_personality_provider` if the MST
   read fails or returns no record.

This ADR ships only the **interface** for Layer 2 (a `MstJouchoProvider`
protocol class). The implementation is deferred to a Wave 3 ADR once the
`@etzhayyim/sdk` Python binding lands.

# Consequences

## 正の効果

- 18,342 organisms get 18,342 distinguishable personalities for zero
  marginal cost. The ecosystem claim becomes observable: c10101500 (Live
  Animal) has different baseline mood than c14101500 (Paper Products).
- Determinism: tests can assert exact joucho values without flakiness.
- Layer 1 has zero substrate dependencies — works on a laptop, in CI,
  and on Murakumo identically.
- Layer 2 interface is forward-compatible: when MST writes land, the
  provider swap is a one-line change in fleet_cell_main.

## 負の効果 / コスト

- Layer 1 personalities are static. An organism's mood doesn't shift in
  response to real-world signals until Layer 2 lands.
- The segment-bias table is opinionated. Segment-to-personality mappings
  are debatable; this ADR fixes them by fiat. Override via Layer 2.
- SHA-256 + small math per tick is ~5 μs overhead per organism. Across
  18k organisms per 5-min sweep that's ~100 ms total — within budget
  per ADR-2605240000.

# Alternatives Considered

## A. Keep constant 50/50/30/50/50 until MST writer lands

却下理由: the ecosystem framing breaks down — identical organisms.
Layer 1 is cheap and the right shape; do it now.

## B. Read joucho from Kotoba/Datomic like the TS side

却下理由: CHARTER-VIOLATION per existing TS code comment. Substrate
rules prohibit centralized DB; Python side won't replicate the TS
shortcut.

## C. Random per-startup mood instead of deterministic

却下理由: nondeterminism breaks tests and operator observability. Same
organism should report the same mood across restarts.

# References

- ADR-2605232345 — UNSPSC actor as ecosystem organism (Wave 1)
- ADR-2605240000 — UNSPSC organism fleet mass-deploy (Wave 2)
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/personality.py`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/joucho.py`
