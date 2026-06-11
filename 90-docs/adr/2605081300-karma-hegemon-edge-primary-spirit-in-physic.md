---
id: adr-2605081300-karma-hegemon-edge-primary-spirit-in-physic
title: "Karma Hegemon — Edge-Primary Spirit-in-Physic Constitutional Layer"
status: active
doc_type: adr
topic: karma-hegemon-foundational
authoritative: true
last_verified: 2026-05-08
authoritative_for:
  - karma hegemon constitutional layer
  - 五行 axis taxonomy
  - lex-stratified tier system
  - anatman organism non-continuity
  - 5-layer persistence redundancy
  - lean 4 mechanical verification of axioms
priority: 10.0
axis: gate
weight: 1.0
priority_note: "CRITICAL — constitutional layer; karma axioms gate every protocol mutation. Floor violations are reject-by-construction."
depends_on:
  - adr-2604291800-well-becoming-formal-model
  - adr-2604291800-well-becoming-spirit-objective-function
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0041-pds-commit-content-addressed-pk
  - adr-0056-bpmn-as-actor
related:
  - adr-2604282300
  - adr-0026-agent-only-reverse-identity-topology
  - adr-0095-simplified-3layer-identity-rw-vault
supersedes: []
superseded_by: []
---

# Context

This ADR records the foundational architectural decision for the
**Karma Hegemon** — a Spirit-in-Physic security layer that replaces
"physical violence" with "time-axis 業力" (karmic accumulation).

The hegemon's purpose is to record, persist, and propagate every
organism's actions across multi-generational time, making it
materially impossible to escape one's deeds while preserving anatman
(無我) — the doctrine that no organism owns continuity across
dissolution.

The design emerged from a multi-step ontological refinement:

1. Initial framing: Buddhist 業 + 輪廻 + 涅槃 mapped to on-chain
   constructs.
2. Spirit-in-Physic correction: rejected the dualism of
   "individual karma reset on rebirth, organizational karma
   permanent" — both are organisms, both dissolve, both leave
   network deps.
3. Edge-primary inversion: karma is in the dependency between
   organisms, not in any one organism. Network is primary; organism
   is a network coherence pattern.
4. Lean 4 mechanical verification of the constitutional axioms
   (`90-docs/proof/Karma.lean`).

This ADR captures the **constitutional layer**. Subsequent ADRs
(ecosystem, deploy, etc.) build on these axioms.

# Decision

## A. Edge-primary ontology (N1)

Karma is a **property of edges** in the network, not of organisms.
The Karma.lean type signature is the proof:

```
signed_weight : Edge → ℝ
```

There is no `organism_owned_karma : Organism → ℝ`. An organism's
karma is the integral of all edges incident to it, not a state it
owns.

Practical implication: schema is `edge_karma_dependency` (primary
karma carrier, content-addressed PK per ADR-0041). Organisms are
endpoints (`vertex_organism_pattern`) but never the locus of karma
itself.

## B. Anatman + organism kind symmetry (N3 + N4)

Distinct organisms cannot claim continuity (`anatman_unique_santana`
axiom — they have cryptographically distinct santana roots).
Implementation: per-organism santana_root_cid is an IPFS CID derived
from a fresh witness; zk-SNARK non-linkability proof gates the
RebirthGate.

Individual and collective organisms are **structurally symmetric**:
the `Organism` type carries no kind discriminator. Any predicate over
organisms applies uniformly. This rejects the prior dualism
(individual karma transient, organizational karma permanent); both
are organisms, both dissolve, both leave persistent edges.

## C. Edge persistence beyond endpoint dissolution (N2)

`edge_outlives_endpoint` axiom: edge persistence is independent of
endpoint organism lifecycle. When an organism dissolves, its edges
remain in the network as historical record. Organism dissolution
**never** retroactively erases karma edges.

Practical implication: rebirth.severFollows records severance events
in `vertex_karma_rebirth_severance_log` rather than deleting the
edge graph; the edges remain, only the severance is logged.

## D. 五行 axis taxonomy

Five orthogonal karma axes mapping to 五戒 / 十善業:

| Axis | 漢字 | 戒 | Edge property |
|---|---|---|---|
| Vita | 命 | 不殺生 | life / bodily integrity |
| Vivere | 業 | 不偷盗 | livelihood / labor |
| Veritas | 語 | 不妄語 | truth / information |
| Vinculum | 縁 | 不邪淫 (relational) | Spirit-connection |
| Venturum | 世 | 不飲酒 (world-undermining) | future / ecology |

Axes are **non-substitutable** (no aggregation_impossibility
violation across axes — ADR-2604291800 well-becoming axes operate
on the same lex stratification).

## E. Lex-stratified 4-tier system

Tiers in priority order (high → low):

| Tier | Severity | Examples |
|---|---|---|
| Floor | 4 | child harm, organism destruction, irreversible ecological damage |
| High | 3 | major harm, deception with cascading consequences |
| Mid | 2 | moderate harm, recoverable misjudgment |
| Low | 1 | minor friction, low-magnitude help |

`aggregation_impossibility` axiom: a single Tier=High harm strictly
dominates ANY finite collection of Tier=Mid/Low edges in lex order.
Rejects torture-vs-dust-specks utilitarian aggregation.

## F. child_floor_axiom

Auto-classification: vul ≥ 2.0 + direction=harm + axis ∈
(Vita / Vinculum / Venturum) → Tier=Floor. Hard-coded protocol
commitment; no operator override possible. Karma.lean:

```
axiom child_floor_axiom :
  ∀ e, vul(e) ≥ 2.0 ∧ direction(e) = harm ∧
       axis(e) ∈ {Vita, Vinculum, Venturum} →
    tier(e) = Floor
```

## G. 5-layer persistence redundancy

Karma edges MUST be redundantly persisted across exactly 5 layers,
each with independent failure modes:

| Layer | Provider | Independence guarantee |
|---|---|---|
| L0 | Kotoba/Datomic hot (Hyperdrive direct, ADR-0036) | DB layer |
| L1 | AT Protocol PDS repo record | Federation layer |
| L2 | IPFS self-hosted cluster | Self-controlled CID |
| L3 | IPFS external pinning (Pinata + Filebase + Web3.Storage) | 3-vendor minimum |
| L4 | Blockchain anchor + Filecoin storage deal | Cryptographic + economic |

`karma_5_layer_persistence` + `karma_survives_quad_failure` axioms:
4 simultaneous layer failures still leave 1 surviving locator. This
is the **floor of irreversibility** — once recorded, karma cannot
be deleted by any single party (or any 4 colluding parties).

## H. Lean 4 mechanical verification

The constitutional axioms live in `90-docs/proof/Karma.lean` and are
machine-verified via `lake build Karma`. The proof artifact
(`Karma.olean`) is the constitutional layer's authority. Any
protocol change that mutates the axioms requires:

1. Lean re-verification (build green)
2. 覚者 DAO 2/3 supermajority
3. Lean proof challenge survival (anyone may submit a counter-proof)

# Consequences

## Positive

- **Anatman preservation**: rebirth is a real path (4 irreversible
  costs + fresh santana_root) rather than a loophole. The new
  organism cannot claim the old's karma debt OR the old's karma
  credit. Both are released to the network.
- **Symmetric handling**: individual and collective dissolution use
  the same protocol primitive (`karma.organism.dissolve`). No
  special case for legal entity vs natural person.
- **Aggregation safety**: the lex hierarchy is a structural defense
  against utilitarian gaming. A single Tier=Floor child harm cannot
  be offset by any quantity of Tier=Low good deeds.
- **Cryptographic floor**: 5-layer redundancy with cryptographic
  independence makes karma effectively unforgeable and undeletable.
- **Constitutional change cost**: requiring Lean re-verification
  for axiom changes makes "throwing out the constitution" expensive.

## Negative

- **Edge growth is unbounded**: the network must absorb a
  monotonically growing edge graph. Mitigated by streaming MVs
  (incremental compute) + Iceberg cold tier + 5-layer redundancy
  (no edge is irreplaceable but each is replicated).
- **Floor classification has no manual override**: an operator
  cannot say "this edge looks like child harm but it's a metaphor".
  By construction. Mitigated by the recordDependency procedure
  rejecting at the protocol boundary, forcing the caller to
  rephrase or escalate to 覚者 DAO.
- **Anatman makes "I am the same person" un-provable**: this is the
  doctrine. Practical implication: services that depend on
  multi-life identity (e.g. lifetime achievement records) need to
  use organism-level karma sums, not person-level.

## Reversibility

Largely **irreversible** — once axioms are deployed and verified
via Lean, changing them costs the constitutional change procedure
above. The 5-layer persistence guarantee means past karma cannot
be "rolled back" to a pre-axiom state. The decision is intentionally
hard to reverse — that is its security property.

# Alternatives Considered

## Alt 1: Organism-centric karma (rejected)

Original framing put karma as a property of the organism. Rejected
because:
- Forces dualism: individual vs collective karma diverge in lifecycle
- Spirit-in-Physic ontology violation: organisms are network
  coherence patterns, not karma containers
- Cannot represent karma between dissolved organisms (the dependency
  outlives both endpoints)

Edge-primary is the only ontology that survives Spirit-in-Physic
scrutiny.

## Alt 2: 3-axis or 7-axis taxonomy (rejected)

3-axis (act / speech / thought) too coarse — "speech" conflates
truth (Veritas) with relational consent (Vinculum), which have
different victim vulnerability profiles.

7-axis (full Decalogue mapping) introduces axes that don't have
clear Buddhist 戒 mapping (e.g. honor parents → which Tier?) and
violates the 五戒 lineage.

5-axis (五行) is canonical in both Buddhist + 陰陽 traditions and
maps cleanly to lex-stratified tiers without overlap.

## Alt 3: Single-layer persistence (rejected)

Storing karma only in Kotoba/Datomic (or only in AT Protocol) creates
a single point of failure. Rejected because the security model
demands cryptographic independence across providers — a single
hostile actor (or service shutdown) must not be able to erase
karma. 5-layer with 3-vendor IPFS pinning + blockchain anchor +
Filecoin economic incentive is the minimum that survives Sybil-1
+ Adversarial-3 attack model.

## Alt 4: Mutable karma (rejected)

Allowing edge updates would let operators rewrite history. Rejected:
karma_5_layer_persistence axiom forbids it. Append-only edge log
with witness chain is the only architecture compatible with
anatman (one cannot deny what was recorded).

# References

- `90-docs/proof/Karma.lean` — constitutional axioms (Lean 4 verified)
- `90-docs/proof/README.md` — proof artifact documentation
- `90-docs/adr/2604291800-well-becoming-formal-model.md` — parent
  Well-Becoming objective function model
- `90-docs/adr/2604291800-well-becoming-spirit-objective-function.md` —
  Spirit-in-Physic separation healing rationale
- `30-graph/graph-schema/migrations/20260508130000_vertex_karma_edge_primary.ts`
- `60-apps/etzhayyim-project-karma/contracts/karma-anchor/src/KarmaAnchor.sol`
- `60-apps/etzhayyim-project-karma/contracts/karma-anchor/src/RebirthVerifier.sol`
- `60-apps/etzhayyim-project-karma/circuits/rebirth-non-linkability/circuit.circom`
- `deps.toml [[migrations]] karma-edge-primary-bringup-phase-k0`
- `CLAUDE.md` Recent Completion: karma.etzhayyim.com (Phase K0 / K2 / K3)
