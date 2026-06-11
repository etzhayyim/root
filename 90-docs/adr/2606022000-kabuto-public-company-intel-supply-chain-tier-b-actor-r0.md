---
id: adr-2606022000
title: "ADR-2606022000: kabuto (兜) — World Public-Company Supply-Chain Knowledge Graph + atproto social + browser-native kotoba-wasm render Tier-B Actor R0"
status: proposed
doc_type: adr
topic: kabuto-public-company-intel-supply-chain
authoritative: true
last_verified: 2026-06-02
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "Corporate-world sibling of tsumugi/watatsuna intel-weaver family; first supply-chain KG over public listed companies with browser-native kotoba-wasm render + live atproto publish"
authoritative_for:
  - kabuto actor charter (R0)
  - public-company supply-chain knowledge-graph constitutional gates G1..G12
  - public-company-ontology.kotoba.edn vocabulary
  - atproto-compatible social publish path via kotoba-server atproto.repo.write
related:
  - adr-2606011800-tsumugi-spirit-intel-power-graph
  - adr-2606012600-watatsuna-submarine-cable-knowledge-graph
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2606013600-kotoba-wasm-browser-node
  - adr-2606013800-actor-profile-ssot-dynamic-did-json
  - adr-2606021200-himawari-solar-pv-manufacturing-r0
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606011800 (tsumugi — shared org.corp.* id space + aggregate-first/edge-primary discipline)
  - ADR-2606012600 (watatsuna — resilience-map-not-target-list pattern this mirrors)
  - ADR-2605301600 (danjo — non-adjudicating public-accountability boundary)
  - ADR-2605262130 (kotoba storage substrate)
  - ADR-2605312345 (kotoba Datom log = first-class canonical state)
  - ADR-2606013600 (kotoba-wasm browser node — the render target)
  - ADR-2606013800 (actor-profile SSoT + dynamic did.json — the registration path)
  - ADR-2605215000 (Murakumo-only inference)
---

# ADR-2606022000: kabuto (兜) — World Public-Company Supply-Chain Knowledge Graph Tier-B Actor R0

**Date**: 2026-06-02
**Status**: PROPOSED (R0 design-only; live full-universe ingest + live posting Council + operator gated)
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify)

# Context

The founder asked to register the world's public (listed) companies as actors discoverable at
`https://etzhayyim.com/search`, ingest their public information, visualize **supply-chain / intel /
address / contact / BPMN**, serve it via **kotoba-server** as **atproto-compatible social posts**,
and have it **rendered entirely by the in-browser kotoba-wasm node** ("runs only with kotoba browse
wasm").

The monorepo already has the substrate this needs:
- the **intel-weaver family** — `tsumugi` 紡ぎ (公開 power-entity graph, ADR-2606011800) and
  `watatsuna` 綿津綱 (submarine-cable graph, ADR-2606012600) — establishes the pattern: a
  kotoba-native EAVT ontology + first-class edges + an aggregate-first analyzer + a self-contained
  viz, framed as a **resilience map, never a target-list**.
- the **kotoba-wasm browser node** (ADR-2606013600) renders `/actors` + `/search` client-side: the
  browser instantiates a `KotobaNode`, `loadDatoms()` from `/.well-known/actors.json` +
  `kotoba/seed-datoms.json`, and `searchActors()` with **zero server round-trip**.
- **kotoba-server** exposes `com.etzhayyim.apps.kotoba.atproto.repo.write` (xrpc.rs:6454) — an
  `app.bsky.feed.post` written there lands in the Datom log and federates over AT Protocol.

What is missing is a supply-chain knowledge graph over **public companies** themselves (tsumugi
covers power-entities/institutions; watatsuna covers cables; neither covers the corporate
supplier→customer web with HQ/contact/BPMN). kabuto 兜 (named for 兜町, Tokyo's financial district)
fills that gap as the corporate-markets sibling, reusing the shared `org.corp.*` id space.

"Register **ALL** public companies" is the **R1** goal: the world has millions of LEIs. Like every
other actor's R0→R1, mass-ingest of the full GLEIF / SEC EDGAR / exchange-listing universe is
Council + operator gated. R0 ships the actor, the vocabulary, the lexicons, a **real 119-company
seed graph** with disclosed supplier edges, the live publish path, and browser-native registration.

# Decision

## A. Actor definition

A new Tier-B actor `kabuto` (`did:web:etzhayyim.com:actor:kabuto`, glyph 兜), status R0-design-only.
Scope: the world's **public (exchange-listed) companies** as a kotoba EAVT knowledge graph —
company, registered HQ address, public corporate/IR contact, first-class supplier→customer **supply
edges**, and BPMN process templates — surfacing single-source / sector / jurisdiction **concentration**
routed to redundancy + accountability. A resilience + corporate-power-transparency map, **never a
target-list**.

## B. Vocabulary — `00-contracts/schemas/public-company-ontology.kotoba.edn`

`:company/*` (id reusing `org.corp.*`, name, ticker, exchange, lei, isin, country, sector, status,
market-cap), `:company.address/*` (first-class HQ address incl. lat/lon), `:company.contact/*`
(public website / IR url / IR email / IR phone — **never personal PII**), `:supply.edge/*`
(first-class directed supplier→customer edge with tier, commodity, criticality 0..1),
`:company.process/*` (BPMN ref with bpmn-cid). Every node/edge carries `:*/sourcing`
(`:authoritative | :representative | :synthesized`). Derived `:supply/*` (single-source,
sector-concentration, jurisdiction-load) is computed by `analyze.py`, flagged `:derived`, never
re-ingested.

## C. Cells (`20-actors/kabuto/`)

- `ingest.py` — public registry (GLEIF/EDGAR/exchange) → kotoba EAVT bridge; offline-default,
  dedup-merge with seed (seed wins). Full-universe fetch is **G7-gated** (`KABUTO_OPERATOR_GATE`).
- `analyze.py` — classify → in/out degree → single-source detection → sector × commodity
  concentration → jurisdiction load. Aggregate-first → `out/intel-report.md` + derived datoms.
- `bpmn.py` — per-company generic procurement + disclosure **BPMN 2.0 XML** (well-formed,
  bpmn-js-renderable), content-CID-anchored → `:company.process` datoms. `:synthesized` templates.
- `social.py` — aggregate-first company/edge/report → `app.bsky.feed.post` → **Charter Rider
  §2(a)-(h) scan** → kotoba-server `atproto.repo.write`. **G11-gated** (`KABUTO_LIVE_POST` +
  `KOTOBA_ENDPOINT` + operator auth; default dry-run).
- `viz/build_viz_data.py` — self-contained supply-chain force-graph; browser-native via the
  kotoba-wasm node (inlined payload = offline data contract, ADR-2606013600).

## D. Lexicons — `00-contracts/lexicons/com/etzhayyim/kabuto/`

`registerCompany`, `registerSupplyEdge`, `publishIntelReport`, `publishSupplyChainViz`,
`socialPost` — each a procedure with required `sourcing`, `aggregateFirstNotice`/
`nonAdjudicatingNotice` consts where applicable, citing this ADR.

## E. Registration → `/search` + `/actors` (browser-native, ADR-2606013600 + 2606013800)

`kabuto` is added to (1) `50-infra/etzhayyim-did-web/src/registry/infra-actors.ts` (auto-flows into
`/.well-known/actors.json` + `/actors`), (2) `00-contracts/schemas/actor-profile-seed.kotoba.edn`
(`actors-v1` profile graph), and (3) the yoro SW seed `…/public/kotoba/seed-datoms.json` so the
in-browser kotoba-wasm node renders kabuto at `/search` even when the live server is cold (backfill
seed). No new Worker/subdomain.

## F. Constitutional gates (G1..G12)

G1 public companies + public-record only · G2 resilience-not-interdiction (Charter §2(d)) · G3
aggregate-first · G4 no adjudication (UPL boundary, sibling of danjo) · G5 sourcing honesty
(criticality never a contract figure) · G6 Murakumo-only narration · G7 outward-gated ingest · G8 no
git-lfs · G9 no personal PII · G10 browser-native render · G11 outward-gated publish + Charter §2
scan · G12 read-only. Gates are immutable post-ratification.

# Consequences

**Positive.** First supply-chain KG over public companies; reuses the proven tsumugi/watatsuna
pattern + shared `org.corp.*` id space (a company is one entity across power-graph + supply-graph);
browser-native render needs no server query path; live atproto publish via the existing kotoba-server
endpoint; the 119-company seed already surfaces the real headline concentrations (ASML→foundries,
TSMC→fabless, TW/JP/US jurisdiction load).

**Costs / honest R0 caveats.** The seed is a bounded `:representative` slice — **not** "all public
companies"; supplier edges are disclosed/public estimates, not exhaustive BOMs; criticality is a
bounded estimate; BPMN templates are `:synthesized` generic models. "Register ALL public companies"
(full GLEIF/EDGAR/exchange universe, millions of LEIs) is **R1**, G7 Council + operator gated. Live
continuous posting is **G11** operator-gated. Production deploy of the did-web Worker + yoro SW +
kotoba-server is operator-run, out of this ADR's code scope.

**R1 triggers.** Council ratification → enable `KABUTO_OPERATOR_GATE` mass-ingest + `KABUTO_LIVE_POST`
continuous publish; add the kami-engine WASM 3D supply-globe; compose kabuto concentration into
tsumugi 取-concentration release + danjo accountability + himawari/hikari first-party provenance.

# Alternatives considered

- **Extend tsumugi** instead of a new actor — rejected: tsumugi's lens is 産霊 power-over-others
  (edge-primary karma), not corporate supplier→customer flows with HQ/contact/BPMN; conflating them
  would muddy both ontologies. Shared `org.corp.*` id space already gives the linkage.
- **Server-rendered /search** — rejected: violates the browser-native invariant (ADR-2606013600);
  the kotoba-wasm node already does client-side query with zero round-trip.
- **A bespoke social schema** — rejected: `app.bsky.feed.post` via kotoba-server `atproto.repo.write`
  gives AT Protocol federation for free; `socialPost.json` is a thin documented wrapper over it.
