---
id: adr-2606082700
title: "ADR-2606082700: uchiwake (内訳) — G7 Worldwide-Ingest Authorization Proposal (full GTIN / GS1 / GLEIF universe)"
status: proposed
doc_type: adr
topic: uchiwake-g7-worldwide-ingest-authorization
authoritative: true
last_verified: 2026-06-08
priority: 6.0
axis: governance
weight: 0.60
priority_note: "Council authorization request to open uchiwake's G7 gate for live full-universe product ingest (GS1 GDSN / Open Product Data / GLEIF-RR). All code is built + the offline bulk adapter is proven; the only remaining lever for literal worldwide coverage is this gate — by constitutional design (G7), not a code blocker."
authoritative_for:
  - uchiwake G7 live-ingest authorization request + phased rollout plan
  - data-source inventory + volume + license analysis for full product-BOM coverage
  - Charter Rider compliance analysis (G1 public-record, G9 no-PII, no-server-key) for bulk ingest
related:
  - adr-2606081800-uchiwake-world-product-bom-gtin-kg
  - adr-2606022000-kabuto-public-company-supply-chain-kg
  - adr-2606042330-entity-as-actor-society-scale-social-mirror
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606081800 (uchiwake actor — the ingest target + gates G1..G12)
  - ADR-2606022000 (kabuto — shared org.corp.* company id space)
  - ADR-2605262130 (kotoba storage substrate)
  - ADR-2605312345 (kotoba Datom log = first-class canonical state)
  - ADR-2605231525 (no-server-key invariant)
---

# ADR-2606082700: uchiwake (内訳) — G7 Worldwide-Ingest Authorization Proposal

**Date**: 2026-06-08
**Status**: PROPOSED (Council Lv6+ authorization request — NOT self-executing)
**Deciders**: Jun Kawasaki (author), Council Lv6+ (authorize the G7 gate)

# Context

uchiwake 内訳 (ADR-2606081800) is built, merged, registered, and self-measuring. Its
`crosscheck.py` reports the honest gap: product-BOM detail currently covers **~1.2%** of kabuto's
1,719-company universe and a vanishing fraction of the world's hundreds of millions of GTINs. The
seed is a bounded `:representative` illustration; the first bulk adapter (Open Food Facts →
datoms) is proven **offline** end-to-end.

Per the uchiwake charter, **gate G7** makes the *live, full-universe fetch* of external registries
require **Council + operator authorization** (`UCHIWAKE_OPERATOR_GATE=1`). This is a constitutional
design choice, not a missing feature: bulk ingestion of the world's product graph is a
consequential act (volume, licensing, jurisdiction, mirror-vs-target framing) that must be a
deliberate governance decision. **This ADR is the authorization request.** It is non-self-executing
— no live fetch runs until Council records assent.

# Decision (requested)

Authorize uchiwake to run live full-universe product ingest in **phases**, each independently
revocable, all under the existing gates G1–G12. Phased so the first phase is lowest-risk
(open-licensed, no PII) and later phases require their own sign-off.

## Phase A — Open Food Facts (CC-BY-SA, lowest risk)
- **Source**: Open Food Facts full dump (~3M+ food/beverage trade items, real GTIN + brand +
  ingredients). License CC-BY-SA — compatible with Apache-2.0 + Charter Rider attribution.
- **Adapter**: `methods/adapters/openfoodfacts.py` (already merged/proven). GTIN mod-10 validated;
  every datom `:representative`.
- **Volume**: ~3M products → bounded by kotoba block budget; ingest in CID-addressed batches.
- **Risk**: minimal — public, open-licensed, food-only, no personal data.

## Phase B — GS1 Verified / GDSN + GS1 company-prefix registry
- **Source**: GS1 GTIN identity + company-prefix → brand-owner licensee.
- **Constraint**: GS1 API terms must be honored (own-key, no redistribution of restricted fields);
  only public-record fields ingested (GTIN, brand-owner, classification). G1.
- **Risk**: medium — license terms; requires operator GS1 credential (member-held, no-server-key).

## Phase C — GLEIF LEI + Level-2 Relationship Records (the 子会社 universe)
- **Source**: GLEIF golden-copy (CC0) — LEI registry + RR ownership edges.
- **Effect**: rolls every brand-owner subsidiary up to its ultimate parent at scale, making
  concentration honest at the beneficial-owner level across the whole graph.
- **Risk**: low — CC0, corporate-only (no natural-person PII; GLEIF excludes individuals).

## Phase D — Open Product Data / teardown corpora (electronics, durable goods)
- **Source**: open teardown datasets, EU ESPR Digital Product Passport feeds (as they mature),
  published supplier-list filings.
- **Risk**: medium — heterogeneous quality; everything stays `:representative`, never authoritative.

# Charter / Rider compliance analysis

- **G1 (public-record only)** — all four phases ingest only public-record fields. No confidential
  recipes/formulations, no non-public commercial terms, no trade secrets.
- **G2 (resilience-not-interdiction / no clone-recipe)** — output remains aggregate-first
  concentration routed to redundancy + accountability; bulk scale does not change the framing.
- **G5 (sourcing honesty)** — bulk-ingested datoms default `:representative`; GTIN check-digit
  validated; OFF/crowd-sourced never marked `:authoritative`.
- **G9 (no PII)** — corporate + product graph only. GLEIF excludes natural persons; OFF carries no
  consumer data. Any incidental personal field is dropped at the adapter boundary.
- **no-server-key (ADR-2605231525)** — uchiwake holds **no** GS1/GLEIF write credential. Live
  fetch uses a member/operator-held read credential during a documented operator-run; the actor
  itself never persists a platform secret. Ingest writes to the kotoba Datom log (content-addressed).
- **Murakumo-only (G6)** — no third-party inference touched by ingest; any narration stays on-fleet.
- **License** — CC-BY-SA (OFF) + CC0 (GLEIF) attributions recorded in NOTICE; GS1 fields gated by
  GS1 terms.

# Consequences

**If authorized**: uchiwake's reverse-coverage metric rises from ~1.2% toward genuine worldwide
coverage in revocable phases, each measured by `crosscheck.py`. The product-BOM layer becomes a
real global resilience map rather than an illustration.

**If not authorized (default)**: uchiwake remains at bounded-seed + offline-proven-adapter state.
Nothing breaks; the code simply waits. This is an acceptable steady state — the gate exists
precisely so that scale is a choice, not a default.

**Bounded regardless**: even fully ingested, every BOM decomposition stays `:representative`
(public teardown/label, never an authoritative recipe), and the output stays aggregate-first and
non-adjudicating (G2/G4).

# Status

PROPOSED — awaiting Council Lv6+ authorization of Phase A (and per-phase thereafter). No live fetch
executes until assent is recorded. Code + offline adapter are ready (ADR-2606081800 + the merged
bulk-ingest adapter); this ADR is the governance gate, not an implementation task.
