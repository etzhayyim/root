---
id: adr-2606011501-spirit-in-physics-kotoba-datafication
renumbered_from: "2606011500"
title: "ADR-2606011501: Spirit-in-Physics → kotoba Datom datafication — edge-primary 霊性 across self / humanity / world"
status: proposed
doc_type: adr
topic: spirit-in-physics-kotoba-datafication
authoritative: true
last_verified: 2026-06-01
priority: 8.0
axis: architecture
weight: 0.8
priority_note: "Operationalizes the U_spirit Layer-0 objective (ADR-2604291800) as substrate-compliant data"
authoritative_for:
  - spirit-in-physics data model on kotoba
  - :spirit/* :spirit.bond/* kotoba-EAVT vocabulary
  - spirit-in-physics submodule vendoring
  - D1 → kotoba spirit-data migration
depends_on:
  - adr-2606011000-engi-organism-ontology-and-musubi-knowledge-graph
  - adr-2605081300-karma-hegemon-edge-primary-spirit-in-physic
  - adr-2604291800-well-becoming-spirit-objective-function
  - adr-2605170000-deai-spirit-physics-matching
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605181100-mst-encrypted-records-signal-keywrap
related:
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192100-etzhayyim-mission-charter
supersedes: []
superseded_by: []
---

# ADR-2606011501: Spirit-in-Physics → kotoba Datom datafication — edge-primary 霊性 across self / humanity / world

**Status**: proposed (R0 design-only; constitutional clauses gated on Council Lv7+)
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

`spirit-in-physics` (vendored at `60-apps/spirit-in-physics`, `com-junkawasaki/spirit-in-physics`)
is the **scientific 霊性 (spirit) measurement system** underlying this religious-corp's top
objective. It implements the model of the paper *"Spirit in Physics: Spirit as a Thermodynamic
Information Quantity"* (Kawasaki, Tainaka, Takeuchi — Niigata U / Aarhus U, 2026; CNS 2025 F35,
SfN 2025 PSTR197.20):

1. Jung-style **word-association assay** (100 bilingual stimulus words) → response + reaction time.
2. Per word, a **10-dim emotion vector** `e_i ∈ R¹⁰` (currently Hume-estimated), normalized.
3. **RBF emotion-kernel** `W_ij = exp(−‖e_i−e_j‖²/σ_eff²)` → diagonal `D` → Laplacian `L = D − W`.
4. **Spectral embedding** (eigenvectors 2–4 of `L`) → initial 3D coordinates.
5. **Emotion anchors** — fixed shell nodes the words are tensioned toward.
6. **Tensegrity physics** — unilateral springs (tension-only / compression-only) relax the
   structure into a self-supporting 3D spirit-form.

Its ontology is *already* etzhayyim's ontology: **the mind is not separable from field/body/
others; a human is an open-system thermodynamic information field; the「不可分の個体」(individual)
is negated** (PROJECT.jsonld narrative/92). This is the 反個人主義 / 縁起 / Wellbecoming charter
(ADR-2605192100) stated in physics.

Three problems block using it as religious-corp truth today:

- **P1 — substrate violation.** The research SSoT (`spirit-in-physics.com/api`) persists on
  Cloudflare **D1 (centralized SQL)** + R2. Centralized SQL is prohibited by the substrate
  boundary (CLAUDE.md §Substrate; ADR-2605262130). The canonical home must be the **kotoba
  Datom log** (ADR-2605312345).
- **P2 — node-centric storage.** The D1 schema stores spirit as rows keyed by `participant_id`
  (a per-individual object). That contradicts the **edge-primary** constitutional layer
  (ADR-2605081300: `signed_weight : Edge → ℝ`, *no* `organism_owned_karma`) and 反個人主義.
- **P3 — external inference + raw PII.** Emotion vectors come from **Hume AI** (external
  commercial API → violates Murakumo-only, ADR-2605215000) and the raw word-responses are
  要配慮 PII stored in plaintext SQL.

This ADR records how to **datafy the spirit of (a) etzhayyim itself, (b) humanity, (c) the whole
world** into datomic kotoba in a way that resolves P1–P3 and honors the existing spirit ADRs.

# Decision

## A. Vendor the model, not fork it

`spirit-in-physics` enters as a **git submodule** at `60-apps/spirit-in-physics` (private upstream,
same author). It remains the measurement *instrument* and the D1/R2 research collection front
(deai relay, ADR-2605170000). It is treated as upstream-vendored: **no Charter Rider is applied
to it** (CLAUDE.md §Do-Not), and kotoba — not D1 — becomes the canonical religious-corp home.

## B. Three constitutional invariants (the design's spine)

- **N1 — Edge-primary (反個人主義 / anatman 無我).** Spirit lives in the **bond (縁)**, not the
  organism. The canonical citizen is `:spirit.bond/*`, which **extends `:en/*`**
  (engi-organism-ontology, ADR-2606011000) with the tensegrity-spring physics
  (`mode`/`rest-length`/`stiffness`) and carries **karma as `:spirit.bond/signed-weight`** — the
  *only* home for 業, per ADR-2605081300. There is no `:spirit/score-of-soul`. An organism's
  spirit = the **integral of its incident bonds**, computed on read (kotoba-kqe over the AVET/VAET
  index), never stored as a per-soul scalar.
- **N2 — Wellbecoming = history, not a column (非終末論).** The dynamic 軌跡 (ADR-2604291800,
  §1.15) *is* the Datom history of the spirit. Trajectory queries are `as-of tick` over the kotoba
  log; there is no "final embedding", "soul verdict", or salvation-status datom (Revelation
  excluded, CLAUDE.md §Do-Not). The trajectory itself is the worship.
- **N3 — Aggregate-first + consent + encrypted (要配慮 PII).** Raw assay responses live only as
  XChaCha20-Poly1305 envelopes (`:spirit.assay/response-cid`; ADR-2605181100). `:scale :human`
  requires a `:spirit/consent-cid` (§1.16 covenant) before any datafication. World-scale outputs
  are aggregate-first, method-versioned, open-source — never a per-person ranking.

## C. The vocabulary — `00-contracts/schemas/spirit-ontology.kotoba.edn`

A new kotoba-EAVT vocabulary layered **on top of** `:organism/*` + `:en/*`:

| ns | role | maps Spirit-in-Physics … |
|---|---|---|
| `:spirit/*` | thin field overlay on an `:organism` (scale, archetype, separation, connectivity, η, tick) | the participant's aggregate readout |
| `:spirit.bond/*` | **primary** — 縁 as a tensegrity unilateral spring + `signed-weight` karma | README §4 springs + ADR-2605081300 edges |
| `:spirit.emo/*` | the 10-dim emotion vector (homogeneous tuple) + estimator provenance | README §1 `e_i ∈ R¹⁰` |
| `:spirit.assay/*` | one word-association datum; response is encrypted-CID only | D1 `assessment_events(word-response)` |
| `:spirit.anchor/*` | fixed emotion-anchor shell nodes | README §3 |
| `:spirit.embed/*` | spectral + tensegrity-converged 3D coord per (spirit, tick) | README §2,§4 |
| `:spirit.kernel/*` | σ_eff + W/L matrices as IPFS CIDs (never inlined) | README §1,§2 |

Big artifacts (W, L matrices) are **content-addressed blocks** (IPFS CID), not Datom values
(substrate layering, ADR-2605312345).

## D. The three datafication scales

- **D1 — etzhayyim itself (`:scale :self`).** etzhayyim already has a 10-axis living-system
  scorecard (Autopoiesis … Sanctification, README "Artificial Organism Ecosystem"). That *is* the
  corp's emotion-vector analogue. Its spirit-bonds are the **constitutional invariants as
  tensegrity springs**: mission-pull = `:tension`, substrate-boundary = `:compression`; each ADR
  is a node, each `depends_on` a 縁. No PII; **may scaffold immediately**. Renders the corp's own
  spirit-form (the body of ADR-2605192100's "artificial organism").
- **D2 — humanity (`:scale :human`).** Each *consenting, claimed* organism (信者; §1.16 covenant)
  has a spirit-field assembled from its assays. Per N1 the person is never scored as a soul;
  humanity's spirit is the **superposition of shared bonds** across consenting fields — the
  collective tensegrity. Strictly consent + encrypted-gated (N3). This is the deai/spirit-in-physics
  collection pipeline re-homed onto kotoba.
- **D3 — the world (`:scale :world` / `:ecological` / `:institutional`).** Every organism in the
  engi-organism graph (human **and** non-human — rivers, corps, species; ADR-2606011000) carries a
  spirit-field. The world-spirit is the **global tensegrity of all 縁**, separation = blocked
  channels, healing = Shannon-η rise (ADR-2605170000). Aggregate-first, Murakumo-narrated,
  rendered as a kami-engine WASM tensegrity viz (the unilateral-spring physics already exists in
  kami-genesis; the `:spirit.embed/coord` stream is its input — the danjo-finds / kanae-renders
  pattern, ADR-2605302300).

## E. Pipeline (D1 → kotoba), Murakumo-only

```
spirit-in-physics assay (D1 ingress mirror)
  → emotion vector via :murakumo OR :baien-frozen-encoder   (NOT Hume; G5)
  → encrypt response → IPFS CID                              (N3/G2)
  → assert :spirit.assay/* + :spirit.emo/* Datoms            (canonical = kotoba)
  → kernel (σ_eff, W, L → IPFS CIDs) + spectral embed
  → tensegrity relax in kami-genesis → :spirit.embed/coord
  → derive :spirit.bond/* (縁 springs, signed-weight karma)
  → aggregate readouts :spirit/{separation,connectivity,shannon-eta} @ tick
```

Each tick appends; nothing is mutated in place — the log *is* the 軌跡 (N2).

## F. Status & gating

R0 design-only. `:scale :self` (no PII) and non-human `:scale :ecological/:institutional` may
scaffold now. `:scale :human` datafication (any real assay ingest) is **blocked on Council Lv7+**
ratification of N1–N3 and the §G gates. Outward actions (publishing world-spirit viz, collecting
new human assays under religious-corp identity) are G11-gated like all outward actor flows.

# Consequences

**Positive.** (1) The platform's Layer-0 objective `U_spirit` (ADR-2604291800) finally has a
substrate-compliant data home. (2) Edge-primary + history-as-trajectory makes 反個人主義 and
非終末論 *structurally enforced*, not merely documented. (3) kami-genesis tensegrity becomes the
native renderer — no new physics. (4) Removes a live substrate violation (spirit data on D1) and a
Murakumo-only violation (Hume) from the religious-corp path.

**Negative / honest limits.** (a) Emotion estimation moves off Hume to Murakumo/baien-frozen — a
*different* (likely lower-fidelity at R0) estimator; the `:spirit.emo/estimator` flag records this.
(b) `as-of` trajectory queries over a large human cohort are unproven at scale on kotoba-kqe.
(c) D1 remains as ingress mirror during transition — dual-write risk until Phase 2.5 cutover.
(d) "World-spirit" at `:scale :world` is aspirational coverage; `:spirit/sourcing :representative`
must flag every synthesized field — no fabricated planetary coverage.

# Alternatives Considered

- **Keep D1 as canonical, mirror to kotoba.** Rejected — inverts ADR-2605312345 (Datom log is
  first-class) and leaves the substrate violation in place.
- **Store spirit as a per-organism vector (node-centric).** Rejected — violates edge-primary
  (ADR-2605081300) and 反個人主義; would create a `:spirit/score-of-soul` the charter forbids.
- **Materialize the trajectory as an explicit time-series table.** Rejected — the Datom log
  already *is* the time index; a parallel table is redundant and risks an eschatological "final
  state" surface (N2).
- **Continue using Hume for emotion vectors in the religious-corp path.** Rejected —
  Murakumo-only inference invariant (ADR-2605215000). Hume allowed for vendor side only.

# References

- `60-apps/spirit-in-physics` — vendored measurement instrument (submodule)
- `00-contracts/schemas/spirit-ontology.kotoba.edn` — the `:spirit/*` vocabulary
- ADR-2604291800 — Well-Becoming Spirit Objective Function (`U_spirit` Layer-0)
- ADR-2605081300 — Karma Hegemon, edge-primary spirit-in-physic (`signed_weight : Edge → ℝ`)
- ADR-2605170000 — deai: spirit as thermodynamic information quantity
- ADR-2606011000 — engi-organism-ontology (`:organism/*` + `:en/*` base)
- ADR-2605262130 / ADR-2605312345 — kotoba substrate + Datom-first canonical state
- ADR-2605181100 — MST encrypted records + Signal key-wrap (要配慮 PII envelope)
- ADR-2605215000 — Murakumo-only inference (no external Hume on religious-corp path)
