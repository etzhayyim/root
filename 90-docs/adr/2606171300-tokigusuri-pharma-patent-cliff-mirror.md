---
id: adr-2606171300-tokigusuri-pharma-patent-cliff-mirror
title: "ADR-2606171300: tokigusuri 時薬 — pharmaceutical patent-cliff / off-patent-access observation mirror"
status: accepted
doc_type: adr
topic: tokigusuri-pharma-patent-cliff-mirror
authoritative: true
last_verified: 2026-06-17
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "Closes the patent-cliff observation gap between yakushi (off-patent OTC manufacture) and ADR-2604271830 (individual patent-expiry handoff) — observation→handoff only, manufacture stays with yakushi."
authoritative_for:
  - tokigusuri 時薬 actor (pharmaceutical patent-cliff / off-patent-access observation mirror)
  - pharma-patent-ontology
depends_on:
  - 2606073400
  - 2606073000
  - 2605250500
  - 2604271830
  - 2606011800
  - 2605262800
  - 2605312345
  - 2605215000
related:
  - 2606073200
  - 2606032000
  - 2605312700
supersedes: []
superseded_by: []
---

# ADR-2606171300: tokigusuri 時薬 — pharmaceutical patent-cliff / off-patent-access observation mirror

**Status**: accepted
**Date**: 2026-06-17
**Deciders**: Jun Kawasaki

# Context

The roster already touches drug patents at two points, but leaves the connecting layer empty:

- **yakushi 薬師** (ADR-2605250500) *manufactures*, and is constitutionally constrained to
  compounds that are **perpetually off-patent** in PMDA / FDA / EMA all-three (G1). It is the
  manufacture-side body, not a map of the patent landscape.
- **ADR-2604271830** bridges an *individual* expired-patent drug → a generic candidate → the
  `open-seiyaku` handoff (a deterministic BPMN worker; explicitly *not* an FTO opinion).

What no actor held was the **patent-cliff landscape itself**: the systematic, public map of
*which essential medicines are gated by remaining exclusivity, which time has already freed
into the generic/biosimilar commons, and which are about to fall*. That map is exactly the
KG-mirror shape the accountability/observation lineage already uses (tsumugi 取-concentration,
hokorobi systemic-risk, inochi biosphere): edge-primary, aggregate-first, non-adjudicating,
routed to a constructive telos. Here the telos is **access to medicine** — directly downstream
of the Charter's structural-liberation mission and §1.16 social-security work.

The anti-pattern to invert is the **commercial drug-patent / FTO terminal**: a paid feed that
sells freedom-to-operate opinions, litigation intelligence, and generic-launch timing as a
profit product, and that frames the question as a legal/financial contest between firms.
tokigusuri must be the opposite — a public, aggregate **release map** that asserts no legal
opinion, names no infringement, and is routed to *lawful* access (generic/biosimilar on
off-patent; MPP voluntary licensing + TRIPS flexibilities on-patent).

# Decision

## 1. Create **tokigusuri 時薬** — the medicine-access mirror

A Tier-B actor, the medicine-access sibling of the KG-mirror lineage (hokorobi / inochi /
tsumugi). Same architecture: edge-primary, non-adjudicating, aggregate-first KG over the
kotoba Datom log. It weaves **drugs / exclusivity-barriers / holders (originator + generic +
biosimilar) / bearers (patients, LMIC populations, health-systems, payers, uninsured)** and
surfaces **access-barrier concentration** (which essential medicines are most gated by
remaining exclusivity = the release surface) vs **release buffers** (generic / biosimilar /
expiry availability), routed to **RELEASE** (解放 — the liberation of the medicine to all).

The name 時薬 ("time is the medicine") encodes the mechanism: the patent cliff is a clock, and
time itself delivers a monopolised drug into the commons.

**Constitutional gates** (full text in `20-actors/tokigusuri/CLAUDE.md`):

- **G1 — RELEASE map, NEVER a patent-busting / FTO-opinion / trading signal** (the defining
  inversion). Never a freedom-to-operate opinion, never an infringement determination, never a
  per-company verdict, never a pharma-equity signal. Aggregate-first. The 取-holder is the
  *exclusivity-barrier*; the bearer is *patients / the public*; the routing is *lawful release*.
- **G2 — edge-primary (N1).** access-barrier lives only on `:en/barrier-load`; the node integral
  is computed on read; no `:tokigusuri/monopoly-of-drug`. **A medicine is never tallied as a
  取-holder** — only an exclusivity-barrier or originator-holder can be a barrier *source*
  (enforced by `analyze`'s `holder-imposed-kinds`; a drug is the gated object, never the villain).
- **G3 — non-adjudicating (N3).** patent status / expiry / exclusivity are DISCLOSED facts
  (FDA Orange Book / Purple Book, EPO & national registers, WHO EML, Medicines Patent Pool),
  never tokigusuri verdicts; **no FTO / infringement determination, no investment advice**
  (the yakushi legal boundary).
- **G4 — lawful-routes-only** (the access-not-piracy invariant). Generic / biosimilar entry is
  surfaced only for off-patent / expiring drugs; on-patent routes are limited to the disclosed
  lawful mechanisms (MPP voluntary licensing, TRIPS/Doha flexibilities). **Circumvention or
  inducement to infringe a live patent is unrepresentable** (no edge kind exists for it).
- **G5 public venue · G6 sourcing honesty · G7 Murakumo-only · G8 outward-gated,
  observation→handoff only** (manufacture stays with yakushi + ADR-2604271830).

## 2. pharma-patent-ontology + kotoba Datom-log implementation

- `00-contracts/schemas/pharma-patent-ontology.kotoba.edn` — nodes (`:drug` / `:barrier` /
  `:holder` / `:bearer`), 縁 (`:monopolizes` / `:blocks` / `:evergreens` / `:delays` /
  `:gates-access` = barrier; `:generic-of` / `:biosimilar-of` / `:supplies` / `:overcomes` =
  release) carrying `:en/barrier-load`; transient derived readouts; disclosed
  `:drug/essentiality` (WHO EML tier) → access weight.
- `methods/datom_emit.cljc` projects to canonical **EAVT Datoms** `[e a v tx op]`
  (ADR-2605312345): ground node/edge datoms durable (`:add`); derived access-barrier / release
  integrals flagged `:bond/is-transient` (computed on read, never persisted — N1/G2).

## 3. kotoba **pywasm** actor design

Pure `.cljc` (no native deps) → componentize-py WASM Component, browser-local (ameno) / mesh
(e7m-wasm-runner), no-server-key. A read-only, content-addressed component holds no live patent
feed and emits no legal opinion or signal — the right trust posture for G1/G4. WIT world +
build/verify + trust model in `20-actors/tokigusuri/wasm/README.md`.

## 4. R0 deliverables (this ADR, all green)

- actor scaffold: `manifest.jsonld`, `CLAUDE.md`, `wasm/README.md`
- seed graph: 34 nodes (14 drugs across small-molecule / biologic, on-/expiring/off-patent,
  eml-core … on-market · 7 exclusivity-barriers · 8 holders · 5 bearers) · 31 縁; patent /
  exclusivity / biosimilar-existence facts `:authoritative` (WHO EML / Orange Book / MPP),
  barrier-load values representative severities
- methods: `analyze.cljc`, `datom_emit.cljc`, `coverage_report.cljc` (pure `.cljc`)
- tests: **8 green** (edge-primary barrier-integral identity, top-is-essential sanity,
  source-is-true-holder, transient-flagging, determinism, cliff-both-ends coverage)

In the seed run the lens ranks **sofosbuvir** (HCV, on-patent, eml-complementary) and
**dolutegravir** (HIV, eml-core, MPP-licensed) as the top access-barrier concentrations — both
real-world access landmarks — routed to release; the 取-holder table cleanly surfaces
primary-patent / secondary-patent (evergreening) / patent-thicket / originators, with **no
medicine appearing as a barrier source**.

# Consequences

**Positive.** The patent-cliff landscape becomes observable as a public release map without any
new manufacturing or any legal-opinion capability. tokigusuri composes the previously-disjoint
pieces: its candidates feed **yakushi** (off-patent OTC manufacture) and the **ADR-2604271830**
generic handoff; its holder cross-link (`:barrier/links`) feeds **tsumugi** power-concentration;
it gives the Charter's social-security / access work (§1.16) a public read on where patients
bear the access barrier. The release framing (generic/biosimilar + MPP/TRIPS) keeps the actor
on the lawful side of the access debate by construction.

**Costs / risks.** (1) **G1/G4 are load-bearing.** Any future enrichment must never add an FTO
verdict, an infringement determination, a tradeable signal, or a circumvention route — CI
should assert no `:fto/*` / `:infringement/*` / `:signal/*` attribute and no circumvention edge
kind enters tokigusuri graphs. (2) The seed barrier-load values are *representative severities,
not measured exclusivity terms* — `coverage_report.cljc` + G6 keep that honest. (3) Live ingest
(Orange Book / WHO EML / MPP / patent registers) is G8/Council-gated — R0 ships offline only.
(4) Patent law is jurisdiction-specific; the ontology treats status as a DISCLOSED, per-source
fact (N3), never a global truth-claim.

# Alternatives Considered

- **Fold the patent-cliff map into yakushi.** Rejected: yakushi is the *manufacture* body,
  constitutionally constrained to perpetually-off-patent OTC APIs; it carries neither the
  exclusivity/barrier ontology nor the bearer (public-access) axis that is tokigusuri's
  defining structure.
- **Extend ADR-2604271830's worker instead of a new actor.** Rejected: that worker is a
  deterministic *per-drug* expiry→handoff bridge, not an aggregate observatory; the landscape
  map is a different shape (KG-mirror) and a different telos (access surface, not a single
  candidate).
- **A drug-patent / FTO intelligence terminal.** Rejected outright: that is the paid-terminal /
  legal-opinion pattern tokigusuri exists to invert (G1/G3/G5) — it asserts no FTO opinion,
  names no infringement, and never trades.

# References

- `20-actors/tokigusuri/` — actor (manifest, CLAUDE.md, methods, tests, wasm, seed)
- `00-contracts/schemas/pharma-patent-ontology.kotoba.edn`
- ADR-2606073400 (hokorobi — sibling mirror pattern) · ADR-2606073000 (inochi — KG-mirror lineage)
- ADR-2605250500 (yakushi — off-patent OTC manufacture) · ADR-2604271830 (patent-expiry → open-seiyaku handoff)
- ADR-2606011800 (tsumugi — 取-concentration) · ADR-2605262800 (legal-corpus — TRIPS/Bolar/SPC statutes)
- ADR-2605312345 (kotoba Datom = first-class canonical state)
- ADR-2606014500 / 2606014600 (one-Worker many-WASM-actors / componentize-py)
- ADR-2605215000 (Murakumo-only inference)
