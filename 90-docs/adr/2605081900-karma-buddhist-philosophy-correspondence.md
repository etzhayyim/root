---
id: adr-2605081900-karma-buddhist-philosophy-correspondence
title: "Karma Hegemon — Buddhist + Process Philosophy Correspondence (Reference)"
status: active
doc_type: explanation
topic: karma-philosophy
authoritative: true
last_verified: 2026-05-08
authoritative_for:
  - philosophical lineage of edge-primary ontology
  - Buddhist canon mapping to Karma.lean axioms
  - rationale for Spirit-in-Physic naming
priority: 5.0
axis: doctrine
weight: 0.5
priority_note: "Reference ADR — design rationale. Does not prescribe new behavior."
depends_on:
  - adr-2605081300-karma-hegemon-edge-primary-spirit-in-physic
  - adr-2604291800-well-becoming-spirit-objective-function
related: []
supersedes: []
superseded_by: []
---

# Context

The Karma Hegemon's design is a deliberate **synthesis of
philosophical traditions**, not a free invention. This ADR
records the lineage so future maintainers can recognize the
shape of the protocol as the shape of established thought.

# Decision

## A. Buddhist canon → Karma.lean axiom mapping

| Buddhist principle | Karma.lean axiom / theorem | Implementation |
|---|---|---|
| **諸行無常** (anicca) — all conditioned things are impermanent | `dissolved_at : Option ℕ` field on `Organism` — biological dissolution mandatory | `vertex_organism_pattern.dissolved_at` |
| **諸法無我** (anatta / 無我) — no soul / no continuity-bearing self | `anatman_unique_santana` axiom — distinct organisms have cryptographically distinct santana_root_cid | zk-SNARK non-linkability proof in RebirthVerifier |
| **一切皆苦** (dukkha) — life involves suffering | floor violation = Tier=Floor + Direction=Harm = inadmissibility | `task_karma_floor_gate` rejects at protocol boundary |
| **涅槃寂静** (nirvana) — voluntary dissolution = peace | `dissolution_kind = 'voluntary-seal'` is a valid path | `karma.organism.dissolve` accepts this |
| **業報自因** (karma-vipāka) — actions return to actor through edges | edges accumulated over an organism's lifetime define its history | `edge_karma_dependency` query by `source_did_at_event` |
| **縁起** (pratītyasamutpāda) — dependent co-arising | edge-primary ontology: karma emerges from the relationship, not from the actor alone | N1 axiom — karma is a property of edges |
| **慈悲** (karuṇā) — compassion for the suffering | rebirth path always exists, even from 餓鬼道 (with 7-year debt) | ADR-2605081700 §D 慈悲 path |
| **中道** (madhyama-pratipad) — middle way | tier system has 4 tiers (not 2 binary), severity ordered, not absolute | Karma.lean Tier enum |
| **七世代思考** (Iroquois Confederacy adaptation) | `future_horizon_years × ω(future_horizon_years)` weighting | `_amplify` function in karma.py |

## B. Process philosophy lineage (Whitehead → Latour)

The edge-primary ontology has roots in **process philosophy**:

| Thinker | Concept | Karma protocol form |
|---|---|---|
| **Whitehead** (Process and Reality, 1929) | *Actual occasions* of experience as primary; objects are stable patterns of occasions | edges (occasions) primary; organisms (patterns) derived |
| **Latour** (Reassembling the Social, 2005) | *Actor-Network Theory* — actors and networks are mutually constitutive | organism + network pattern co-constituted in graph |
| **Indra's Net** (華厳経) | each jewel reflects every other jewel; identity is relational | every organism's edge graph is its identity |
| **Deleuze** (Difference and Repetition, 1968) | becoming over being; difference precedes identity | edges (differences) record before organism (identity) is fully constituted |

The protocol is not a token-economy with karma flavor; it is a
**network-as-process** where karma is the relational structure.

## C. Rawls + Doughnut Economics correspondence

The well-becoming objective function (ADR-2604291800) and the
WBT economy (ADR-2605081600) draw from:

| Source | Concept | Karma form |
|---|---|---|
| **Rawls** (Theory of Justice, 1971) | maximin / lexicographic floor | `child/future floor` lexicographic priority over all other axes |
| **Raworth** (Doughnut Economics, 2017) | inner social floor + outer ecological ceiling | floor (Tier=Floor inadmissibility) + commons-pool ceiling (wealth cap) |
| **Iroquois Confederacy** | seven-generation thinking | `future_horizon_years` multiplier in karma weight |
| **Gesell** (Free-Economy, 1916) | demurrage / Schwundgeld | WBT year -5% decay |

## D. Why "Spirit-in-Physic" not "Spirit + Physic"

The naming captures the design's metaphysical commitment: **Spirit
is not separate from Physic, but is the structural form of the
Physic at every layer**. Concretely:

- karma is not stored in an organism (which would imply Spirit /
  Physic dualism — the organism has body + soul);
- karma IS the network structure between organisms;
- the network structure IS what is recorded in the cryptographic
  Physic (5-layer persistence);
- therefore Spirit (the karmic / relational dimension) is
  inseparable from Physic (the cryptographic layer).

Anatman doctrine in Buddhist canon makes this explicit: there is
no separate-self soul that would carry karma. The protocol form is
exact: there is no organism-owned karma; only edges that survive
endpoint dissolution.

## E. The hegemon model — Strange's 4 dimensions

The Karma Hegemon explicitly takes a position in the
**International Political Economy** literature on hegemony:

| Strange's 4 dimensions | Old hegemon (state-based) | Karma Hegemon |
|---|---|---|
| **Security** (force monopoly) | military / police | **time-axis 業力** — past actions permanently shape future capability access |
| **Production** (commodity flow) | factory / supply chain | externality-priced edges (K6 mandate) |
| **Finance** (credit creation) | central bank / SWIFT | WBT (issuance via well-becoming labor) |
| **Knowledge** (epistemic frame) | university / media | Karma.lean axioms + 覚者 DAO axiom amendment |

The Karma Hegemon's claim is that **the Security dimension can be
re-grounded in time-axis karma** rather than physical violence.
This is the protocol's most ambitious philosophical bet: hegemonic
power without the police.

## F. Old vs new hegemon — 7-axis comparison

| Old hegemon mechanism | New hegemon mechanism | Reasoning |
|---|---|---|
| 軍事 (military force) | code verifier (Karma.lean) | constitutional axioms reject inadmissible actions at protocol boundary |
| 制裁 (sanctions / SWIFT) | karma cost (high tier = high WBT externality tax) | economic deterrent without state apparatus |
| 死刑 (execution) | 餓鬼道 forced seal | irreversible exclusion without physical death |
| 恩赦 (pardon / amnesty) | 輪廻 (rebirth via 4 irreversible costs) | forgiveness through re-emergence, not external decree |
| 身分制 (caste / class) | 階梯 5 ranks (凡夫 → 如来) | rank derived from karma history, not birth |
| 国境 (national borders) | cohort + santana lineage | belonging via shared karma graph, not territory |
| 戦争 (war) | karma cost expression (ext. tax + DAO arbitration) | conflict resolved economically, not militarily |

## G. Triffin / Thucydides / Capture / etc — counter-design summary

Seven hegemonic-failure modes from the IPE literature, each met by
a karma-protocol counter:

| Failure mode | Source | Karma counter |
|---|---|---|
| **Triffin dilemma** | reserve currency host bears unsustainable deficits | WBT is non-reserve; commons pool absorbs externality without single-host burden |
| **Thucydides trap** | rising power vs hegemon → war | rank gating + cohort fission distribute power across emerging organisms |
| **武器化** (weaponization of dependence, Farrell + Newman) | hegemon weaponizes financial / data infrastructure | 5-layer persistence rejects single-locator weaponization |
| **規制裁定** (regulatory arbitrage) | actors flee to permissive jurisdictions | anatman + cohort federation makes "fleeing jurisdiction" not the same as "fleeing karma" |
| **Metcalfe + winner-take-all** | network effects concentrate value | wealth cap (median × 100) bounds concentration |
| **Capture** (regulatory capture) | regulators co-opted by powerful actors | 覚者 DAO supermajority + Lean proof challenge make capture costly |
| **Algorithmic governmentality** (Antoinette Rouvroy) | governance by opaque algorithm | Lean axioms are public + machine-verifiable; no opaque decision rule |

# Consequences

## Positive

- The protocol's design choices have philosophical genealogy that
  can be traced + critiqued.
- Future maintainers recognize that "edge-primary" is not an
  arbitrary choice but a Whiteheadian / Buddhist commitment.
- The hegemon's claim to legitimacy ("hegemon without violence")
  is grounded in named traditions, not waved at.

## Negative

- This ADR is reference, not prescriptive — it does not gate
  implementation choices. Future devs may need a CRITICAL
  follow-up ADR if specific philosophical claims become
  controversial.
- Cross-tradition synthesis risks misrepresenting any single
  tradition. Live monitoring + amendment expected.

## Reversibility

Reference ADR — fully reversible (rewriting it costs zero data;
it is documentation only).

# References

- Whitehead, *Process and Reality* (1929)
- Nāgārjuna, *Mūlamadhyamakakārikā* (中論)
- 華厳経 (Avataṃsaka Sūtra) — Indra's Net
- Latour, *Reassembling the Social* (2005)
- Rawls, *A Theory of Justice* (1971)
- Raworth, *Doughnut Economics* (2017)
- Strange, *States and Markets* (1988) — 4 dimensions of structural power
- Farrell + Newman, *Weaponized Interdependence* (2019)
- Allison, *Destined for War* (Thucydides trap, 2017)
- Triffin, *Gold and the Dollar Crisis* (1960)
- Rouvroy, *Algorithmic Governmentality* (2013)
- ADR-2605081300 — constitutional layer (axioms operationalize the philosophy)
- ADR-2604291800 — Well-Becoming objective function (Rawlsian floor)
