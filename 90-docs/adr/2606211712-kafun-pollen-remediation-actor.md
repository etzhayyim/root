---
id: adr-2606211712-kafun-pollen-remediation-actor
title: "ADR-2606211712: kafun 花粉 — 花粉撲滅 remediation actor (clj-native Tier-B)"
status: accepted
doc_type: adr
topic: kafun-pollen-remediation-actor
authoritative: true
last_verified: 2026-06-21
priority: 6.5
axis: mission
weight: 0.65
authoritative_for:
  - kafun 花粉 actor (20-actors/kafun) — the clj-native Tier-B 花粉撲滅 remediation actor
  - the remediation-verdict gate (撲滅 = 主伐再造林 RESTORATION, never deforestation)
  - kafun's content-addressed remediation-ledger persistence (持続永続化)
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605192245-etzhayyim-global-land-sovereignty
related:
  - adr-2605100100-kafun-bokumetsu-real-world-pipeline
  - adr-2605210928-kafun-public-fund-religious-corp-integration
  - adr-2606073000-inochi-living-world-kg-mirror
  - adr-2606032100-labor-liberation-oss-robotics-wave
  - adr-2605260115-mitate-condition-1-allergic-rhinitis-perennial
supersedes: []
superseded_by: []
---

# ADR-2606211712: kafun 花粉 — 花粉撲滅 remediation actor (clj-native Tier-B)

**Status**: accepted (2026-06-21)
**Scope**: `20-actors/kafun/`
**Deciders**: Jun Kawasaki

## Context

花粉撲滅 (cedar/cypress pollen eradication) already exists in this repo as a
legacy App: `60-apps/etzhayyim-project-public-kafun-bokumetsu/` (nanoid
`n97ik10n`), with a real-world outreach pipeline (ADR-2605100100:
scout→cadastral→envoy over satellite→canopy→parcel→landowner) and a
Public-Fund-grantee re-framing (ADR-2605210928). That work is **TS/Python +
LangGraph + RisingWave-era** and predates two things the repo has since made
canonical:

1. **clj/bb over the kotoba Datom log** for newly-authored operational code
   (repo-wide 実装 convention; the actor port waves).
2. **The Tier-B religious-corp actor pattern** — each actor = ADR + manifest +
   cells + lexicons, an edge-primary concentration scored *on read* and routed
   to a positive outcome, with a content-addressed append-only commit-DAG for
   持続永続化 (the ugachi/busshi/meisai/kakaku family).

The roster had **no Tier-B actor for 花粉撲滅** — only the legacy App. The user
asked to take the design, implementation, and persistence (持続永続化) forward.

The two real bottlenecks identified by ADR-2605100100 remain the spine of the
problem:

- **L1-1** 無花粉苗木の量産 (mass production of pollen-free saplings)
- **L3-1** 主伐再造林スケール (main-cut + **re**-forestation at scale, ~10万 ha/年)

The constitutional risk of a "pollen eradication" actor is that it becomes a
**deforestation / clearcut engine** — felling cedar for profit under a public-health
banner, against 子孫 × Wellbecoming and the biosphere (inochi). The design must
make that **structurally unrepresentable**.

## Decision

Add **`kafun` 花粉** — a **clj-native Tier-B actor** (`20-actors/kafun/`) that is
the actor-ization of the legacy kafun-bokumetsu pipeline onto the kotoba Datom log.

撲滅 is defined as **ecological RESTORATION (主伐再造林), never
deforestation-for-profit.** kafun is a **remediation gate**: it scores
edge-primary pollen-source concentration on read and routes each forest **stand**
to a remediation verdict. **ASSESSMENT + R0 DESIGN ONLY — kafun never cuts and
never plants** (live forestry is the landowner's + operator/Council step;
unrepresentable here, exactly as ugachi never digs).

### The pollen-burden score (edge-primary, on read)

```
pollen-burden = min(1, area-ha/10000) · emission-density · (0.5 + 0.5·exposed-pop-weight)   ∈ 0..1
```

Bigger cedar/cypress stand × more pollen emission × more exposed people = more
pollen on more humans. A ranking aid; the verdict is the gate's, not this number.

### The remediation gate (`methods/remediate.cljc`)

`verdict` → `{:refuse :await-consent :protected-selective :await-sapling-supply
:reforest-priority :monitor}`, evaluated in order (hard refusals first):

1. `replant=false` (主伐 without 再造林)        → `:refuse :clearcut-without-reforest` (G1/G4)
2. `carbon :net-positive` (after replant)      → `:refuse :carbon-positive`            (G4 / §2(d))
3. consent absent                              → `:await-consent`                      (G3, land sovereignty)
4. `protected` (watershed/steep/habitat)       → `:protected-selective`                (G1, never 皆伐 → gradual/selective)
5. `sapling-supply :none` (無花粉苗木)          → `:await-sapling-supply`               (the L1-1 bottleneck)
6. `burden ≥ 0.3` AND `reforest-viability ≥ 0.5` → `:reforest-priority`                (the L3-1 bottleneck)
7. else                                        → `:monitor`

**Hard refusals precede every other route** — a non-restorative cut is never
"fixed" by high burden or consent (meta-invariant: no `replant=false` /
net-carbon-positive stand anywhere returns a remediation permit; test-enforced).

### 持続永続化 (persistence)

`methods/kotoba.cljc` + `methods/autorun.cljc` are the same content-addressed
append-only commit-DAG machinery as ugachi (ADR-2606170900): the heartbeat
assesses the stands and **appends the verdict datoms as one content-addressed
transaction** (`tx-cid = 'b' + sha256-hex(canonical JSON)`, prev-cid chained,
`verify-chain` tamper-evident). **Idempotent-by-content**: a beat whose verdict
datoms equal the previous beat's is a NO-OP (the ledger records CHANGES, not a
liveness tick → a 6-hour loop over a static seed never bloats the chain).
Deterministic (caller supplies tx-id + as-of, no wall clock, no `Math/random`) →
resume-safe. No-server-key: the writer holds no key and performs no network I/O.

### Gates (proven by tests)

- **G1 remediation-is-restoration** — 主伐 without 再造林 → refuse;
  `:kafun/clearcut` + `:kafun.stand/eradicate-species` unrepresentable.
- **G2 map-not-cut-list / no person data** — a restoration worklist, never a
  cut-list/target-list; `:kafun.person/health` unrepresentable (cohorts aggregate).
- **G3 consent / land sovereignty** (ADR-2605192245) — no remediation without
  landowner + community consent.
- **G4 carbon-balance** (§2(d)) — net-positive carbon (net of 再造林) → refuse.
- **G5 assessment-R0-only** — no actuation; `:kafun/actuate` unrepresentable;
  live forestry is the landowner's + operator/Council step.
- **G6 no-server-key** · **G7 synthetic seed** (real cadastral/satellite ingest =
  the legacy scout→cadastral→envoy pipeline behind an operator flip) ·
  **G8 kotoba-EAVT-native**.

### Cross-actor routing

- `:reforest-priority` → **sanae** (OSS planting robotics, ADR-2606032100) ·
  **inochi** (biosphere restoration, ADR-2606073000)
- `:await-sapling-supply` → **sanae** / nursery (the L1-1 無花粉苗木 production line)
- allergic-rhinitis care is out of scope (N4) → **mitate** (diagnosis routing,
  ADR-2605260115) + **iyashi** (care)
- the legacy App (`60-apps/etzhayyim-project-public-kafun-bokumetsu`) remains the
  outreach/Public-Fund surface; kafun is its clj-native Datom-log core.

## Consequences

- **+** 花粉撲滅 is now a first-class Tier-B actor on the canonical substrate, with
  a charter-clean definition (撲滅 = restoration) that makes the deforestation
  failure mode unrepresentable, not merely discouraged.
- **+** 持続永続化 is real: a tamper-evident, resume-safe, idempotent-by-content
  remediation ledger; 22 tests / 62 assertions green (babashka).
- **+** The two real bottlenecks (L1-1 / L3-1) are explicit verdict routes, not
  prose — the actor produces a prioritized restoration worklist.
- **−** R0 is synthetic-seed only. The bridge to real stands (cadastral +
  Sentinel-2/ALOS canopy → kotoba) is the legacy ADR-2605100100 pipeline behind a
  G7 operator flip; not wired here.
- **Follow-ups (R1+)**: inochi-grounding bridge (habitat sensitivity as a real
  gate input, ugachi/busshi bridge pattern); Murakumo-narrated remediation digest;
  fleet registration (cell-runner + healthz, the ugachi/kaname maturity track);
  live kotoba-engine bridge (ibuki-R3 pattern); lexicon JSON under
  `00-contracts/lexicons/com/etzhayyim/kafun/`.

## Status

🟢 **R0 landed** — clj-native gate + content-addressed remediation-ledger
persistence + deterministic idempotent-by-content heartbeat; 22 tests / 62
assertions green. Live forestry stays the landowner's + operator/Council step
(never kafun). ZERO charter-invariant amendments.
