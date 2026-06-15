---
id: adr-2606151027-masago-open-materials-discovery-mirror
title: "ADR-2606151027: 真砂 masago — open materials-discovery KG mirror (Meta OMat24 + Materials Project)"
status: proposed
doc_type: adr
topic: masago-open-materials-discovery-mirror
authoritative: true
last_verified: 2026-06-15
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "Closes the AI-driven materials-discovery coverage gap (zero actors); the science-data mirror of the open-materials commons feeding the silicon / energy / robotics lineage."
authoritative_for:
  - masago actor
  - open-materials-ontology
depends_on:
  - "2606101000"   # rasen — public-genetics KG mirror (the science-data ingest pattern)
  - "2606051200"   # hotaru — III-V substrate commons (open-IP-only / no-fabrication stance)
  - "2606073000"   # inochi — living-world KG mirror (map-not-target lineage parent)
  - "2605312345"   # kotoba Datom log = first-class canonical state
  - "2605262400"   # public-data organism IPFS/DataLad ingestion
  - "2605215000"   # inference Murakumo-only (no commercial GPU rental)
  - "2605231525"   # no-server-key
  - "2605181100"   # encrypted-records envelope (N/A here — public data only)
related:
  - "2605242500"   # iwakura/fuigo/tsukuru — ternary silicon (downstream consumer)
  - "2605261100"   # hikari — energy gen/storage (battery-materials consumer)
  - "2606032100"   # sanae/hataori/kiyome — robotics (materials consumer)
supersedes: []
superseded_by: []
---

# ADR-2606151027: 真砂 masago — open materials-discovery KG mirror (Meta OMat24 + Materials Project)

**Status**: proposed
**Date**: 2026-06-15
**Deciders**: Jun Kawasaki

# Context

MIT Technology Review (2026, "The race to find new materials with AI needs more data,
Meta is giving massive amounts away for free") reports that Meta FAIR Chemistry has
released **Open Materials 2024 (OMat24)** — a large openly-licensed dataset of DFT
(density-functional-theory) calculations over inorganic materials (structures with
energies / forces / stresses, on the order of ~10⁸ single-point calculations), together
with pre-trained **machine-learning interatomic potential (MLIP)** models, under a
permissive license (dataset CC-BY-4.0; models released openly). It complements the
Open Catalyst Project and sits alongside the established open-materials commons
(Materials Project, OQMD, NOMAD, AFLOW). The thesis of the field is that **AI-driven
materials discovery is data-bound**, and openly releasing the data is the unlock.

A repo-wide search (2026-06-15) found **zero coverage** of this domain:

- No reference anywhere to OMat24 / Open Materials / Open Catalyst / MLIP / interatomic
  potentials / DFT materials data.
- The closest existing assets are adjacency-only, not discovery:
  - `materials_project-compat`, `asme_materials-compat` — clean-room **API-compat shells**
    (storage/protocol surface, no data, no discovery lens).
  - `hotaru 蛍` (ADR-2606051200) — III-V/InP **substrate design commons** (datafication-only,
    fabrication structurally excluded).
  - `iwakura`/`fuigo`/`tsukuru` (ADR-2605242500) — ternary-silicon **chip** design/fab, not
    materials search.
- `80-data/` holds genome / legal / power / conflict data — **no materials corpus**.

So the open-materials commons that the silicon (`iwakura`), energy/battery (`hikari`),
and robotics (`sanae`/`hataori`/`kiyome`) actors would all draw on **has no mirror**.
This is the same shape the KG-mirror lineage already solves for other public scientific
datasets — `rasen 螺旋` (public genetics) and `inochi 命` (the biosphere): mirror a
PUBLIC, openly-licensed scientific corpus into the kotoba Datom log, run an edge-primary
analysis routed to a charter-aligned telos, **map-not-target, non-adjudicating**.

Charter fit is clean: OMat24 + the Materials Project family are open-licensed public data
(satisfying the open-IP-only stance of `hotaru`); accelerating open materials science is
labor-liberation-adjacent (cheaper batteries / catalysts / structural materials feed the
robotics + energy + silicon bodies); and a datafication mirror introduces no production,
no synthesis, no fabrication. The two real risks are **dual-use** (some materials are
weaponizable — energetics, CW precursors, enrichment-relevant compounds) and **GPU
inference** (the MLIP models are ML, and running them is GPU compute governed by the
Murakumo-only / no-commercial-GPU-rental invariant). Both are handled by gates below;
R0 is datafication-only with **no model execution at all**.

# Decision

Introduce **真砂 (masago)** as a Tier-B **KG-mirror science-data actor**
(`20-actors/masago/`), modeled file-for-file on `rasen` (ingest/analyze/datom-emit/
coverage/cid/publish, pure-stdlib pywasm-runnable) and inheriting `hotaru`'s
open-IP-only / no-fabrication discipline. The name 真砂 ("the countless grains" — 浜の真砂,
the innumerable fine particles) is the metaphor for the vast combinatorial materials space
being mirrored grain-by-grain. _(Working name; rename precedent: 民→継ぎ手. Alternatives
considered below.)_

**Telos**: mirror the PUBLIC computed properties + structures of the open-materials commons
into the kotoba Datom log, run an **edge-primary discovery-evidence** analysis (where computed
property evidence accumulates over a material / composition / application class), and route
the readout to **RESEARCH** (a candidate-shortlist surfaced for human scientists), never to a
make/buy decision and never to a synthesis recipe.

## Vocabulary — `00-contracts/schemas/open-materials-ontology.kotoba.edn`

- **Nodes** `:material/kind` ∈
  `{:material :element :property :structure :application :dataset-source}`
  - `:material/*` — formula, source-id (`mp-…` / OMat id), `:material/sourcing`
    (`:authoritative` = disclosed in source · `:representative` = hand-seed)
  - `:property/*` — property TYPE (`:formation-energy :band-gap :bulk-modulus
    :elastic :magnetic :stability-hull` …), units; the VALUE lives on the edge (N1)
  - `:structure/*` — spacegroup, lattice family, crystal system (public, no privacy concern)
  - `:application/*` — downstream class (`:battery-cathode :catalyst :semiconductor
    :structural :photovoltaic` …)
  - `:dataset-source/*` — `:omat24 :materials-project :oqmd :nomad :aflow`, with license + DOI
- **Edges** `:en/kind` ∈
  `{:composed-of :has-property :candidate-for :derived-from :similar-to}`
  - `:en/value` — the computed property value (DISCLOSED, N3) ON the `:has-property` edge
  - `:en/evidence-load` — 0..1 discovery-evidence burden (edge-primary; karma lives HERE, N1)
  - `:en/clinsig`-analogue → `:en/confidence` ∈ `{:dft :mlip-predicted :experimental}`
    (provenance of the value, never a verdict)
  - `:en/sourcing` ∈ `{:authoritative :representative}`
- **Derived** (transient, computed on READ, NEVER stored; N1/G2):
  `:bond/discovery-priority` (material = integral of incident property evidence × confidence),
  `:bond/application-readiness`, `:bond/composition-breadth` — each `:bond/is-transient true`.

## Cells (pure-stdlib, pywasm-runnable)

- `methods/analyze.py` — edge-primary discovery-evidence analyzer → `discovery-report.md`
- `methods/datom_emit.py` — EAVT Datom-log emitter (ground `:add` + flagged-transient derived)
- `methods/coverage_report.py` — honest coverage vs the ~10⁸ denominator + gap map (G5)
- `methods/cid.py` — kotoba IPFS CIDv1 (raw/sha2-256) parity, copied verbatim from rasen
- `methods/ingest.py` — **OUTWARD (G7)**: bounded public APIs (Materials Project REST,
  OMat24 / NOMAD / OQMD open dumps) → EDN → Datom → CID
- `methods/publish.py` — **OUTWARD (G7)**: IPFS pin + IPNS + `80-data/open-materials/` snapshot
- Seed `data/seed-open-materials-graph.kotoba.edn` — hand-curated OPEN reference (e.g. LiFePO₄,
  TiO₂, GaN, perovskite exemplars) with full attribution.
- Lexicons `00-contracts/lexicons/com/etzhayyim/masago/`:
  `materialRecord.edn` · `datasetSourceAttestation.edn` · `discoveryCandidateReport.edn`.

## Hard gates (immutable; enforced in schema `:db/allowed` = lexicon `enum`/`const` = code, machine-checked)

- **G1 — RESEARCH map, NEVER a weapons or synthesis recipe.** masago mirrors computed
  *properties + structures* only. It MUST NOT emit actionable synthesis / precursor /
  enrichment / processing routes. Dual-use materials (energetics, CW/biological precursors,
  fissile or enrichment-relevant species) are mirrored at the property level only; any
  synthesis-route field is **structurally unrepresentable** (not an enum member → ValueError).
  Mirrors hotaru's no-fabrication + Charter §1.12 (no weapon design).
- **G2 — datafication-only (R0).** No live synthesis, no lab actuation, no automated
  experiment loop. A fabricated/synthesized material is structurally unrepresentable.
  Lab-in-the-loop = R3+, Council-gated, owned/donated compute only.
- **G3 — non-adjudicating.** Property values are DISCLOSED from the source's DFT/MLIP and are
  never re-judged; etzhayyim asserts no "best material" verdict. Discovery output is a
  *readout* (an evidence-ranked shortlist surfaced to human researchers), routed to RESEARCH,
  never a make/buy/trade decision. No `:verdict` route exists.
- **G4 — open-license-only ingest.** Only PUBLIC, openly-licensed sources (OMat24 CC-BY-4.0;
  Materials Project / OQMD / NOMAD / AFLOW under their open licenses). No proprietary or
  vendor formulations. Attribution preserved per source (feeds G5).
- **G5 — sourcing + provenance honesty.** Every node carries source + license + DOI/citation;
  `coverage_report.py` states the mirror is a *tiny representative fraction* of the ~10⁸-scale
  commons — never a completeness claim.
- **G6 — Murakumo-only inference / NO commercial GPU.** Any narration LLM call is
  Murakumo-only (ADR-2605215000). **MLIP/ML model EXECUTION** (running OMat24 potentials) is a
  GPU workload and may run ONLY on owned/donated compute — never RunPod / cloud-GPU rental
  (Rider §2(i)). **At R0 there is NO model execution at all**; mirroring uses pre-computed
  values from the source. Model execution = R2+ Council-gated.
- **G7 — outward-gated, no-server-key.** Live ingest / IPFS pin / IPNS publish require operator
  + Council attestation; the analyzer/datom/coverage loop does **no network I/O** (test-enforced).
  masago holds no signing key.
- **G8 — content-addressed canonical state.** `datom_emit.py` is the canonical state
  (ADR-2605312345); `cid.py` CIDv1 byte-parity with `ipfs add --raw-leaves`; large dumps via
  DataLad → IPFS (ADR-2605262400), **no git-lfs**.

# Consequences

**Positive**

- Closes the AI-driven materials-discovery gap (was zero-coverage) and gives the silicon /
  energy-battery / robotics / construction actors a charter-clean materials commons to draw on.
- Extends the proven KG-mirror lineage (rasen/inochi) to a fourth public scientific corpus with
  no new architectural surface — same ingest/analyze/datom/coverage/cid/publish shape.
- Datafication-only R0 carries no production, synthesis, or fabrication risk; the dual-use and
  GPU-inference risks are both gated, not hand-waved.

**Risks / honest limits**

- The mirror is a *vanishing fraction* of the ~10⁸ commons; coverage_report makes this explicit
  (no completeness claim, G5).
- Dual-use is real: G1 makes property-mirroring safe but means masago deliberately cannot answer
  "how do I make X" — that is a feature, not a gap.
- Running the OMat24 MLIP models would be genuinely useful but is GPU compute; deferred to R2+ on
  owned/donated hardware only (G6). R0/R1 ride the source's pre-computed values.
- OMat24 dataset size/license figures cited from the article should be re-verified against the
  FAIR Chemistry release notes before the R1 live ingest (recorded as an R1 gate task).

**Status**: 🟡 **R0 design-only** (this ADR + scaffold). R1 = live bounded ingest + publish
(G7). R2+ = MLIP execution on owned/donated compute (Council-gated).

# Alternatives Considered

- **Extend `materials_project-compat` instead of a new actor.** Rejected: that is an API-compat
  shell (protocol surface), not a Datom-log KG mirror with an edge-primary discovery lens; the
  charter discipline (gates, EAVT canonical state, coverage honesty) belongs in a first-class
  mirror actor, consistent with rasen/inochi.
- **Run the OMat24 MLIP models at R0 (be a discovery engine, not just a mirror).** Rejected for
  R0: model execution is GPU compute under the Murakumo-only / no-commercial-GPU invariant and
  needs owned/donated hardware + a Council gate. Mirror first; compute later (R2+).
- **Skip dual-use gating (materials data is "just physics").** Rejected: Charter §1.12 forbids
  weapon design; G1's structural exclusion of synthesis routes is the same discipline hotaru
  applies to fabrication.
- **Name alternatives**: 礎 (ishizue, "cornerstone") — collides conceptually with construction
  (tatekata); 鉱脈 (kōmyaku, "ore vein") — reads as mining (kanayama/hodoki space); 素 (su,
  "the elemental") — too abstract. 真砂 chosen for the "countless grains = combinatorial space"
  metaphor, distinct from every existing actor name.

# References

- MIT Technology Review (2026): "The race to find new materials with AI needs more data, Meta
  is giving massive amounts away for free." (motivating article)
- Meta FAIR Chemistry — Open Materials 2024 (OMat24) dataset + MLIP models (CC-BY-4.0 dataset)
- Materials Project / OQMD / NOMAD / AFLOW — sibling open-materials sources
- ADR-2606101000 (rasen — public-genetics KG mirror; the ingest/analyze/datom/cid/publish pattern)
- ADR-2606051200 (hotaru — III-V substrate commons; open-IP-only / no-fabrication stance)
- ADR-2606073000 (inochi — living-world KG mirror; map-not-target lineage parent)
- ADR-2605312345 (kotoba Datom log = first-class canonical state)
- ADR-2605262400 (public-data organism IPFS/DataLad ingestion)
- ADR-2605215000 (inference Murakumo-only — no commercial GPU rental)
- ADR-2605231525 (no-server-key)
- Charter §1.12 (no weapon design) · CHARTER-RIDER §2(i) (no-commercial-GPU)
