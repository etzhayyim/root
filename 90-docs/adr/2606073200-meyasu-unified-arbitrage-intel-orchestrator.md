---
id: adr-2606073200-meyasu-unified-arbitrage-intel-orchestrator
title: "ADR-2606073200: meyasu 目安 — unified arbitrage / supply-demand intel orchestrator + price-intel cohort maturation"
status: proposed
doc_type: adr
topic: meyasu-unified-arbitrage-intel-orchestrator
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/meyasu
depends_on:
  - 2605091200   # kakaku price comparison (spread + supply/demand source)
  - 2606051800   # mitooshi probabilistic forecasting (distribution source)
  - 2606012100   # okaimono provisioning commons (buyer planner)
  - 2605264000   # ossekai aggregate-first publication discipline
  - 2606071800   # RisingWave/Hyperdrive/Kysely → kotoba-kqe remediation (onion companion)
  - 2605262130   # kotoba storage substrate unification
  - 2605312345   # kotoba Datom = first-class canonical state
  - 2605215000   # Murakumo-only inference
related:
  - 2605091200
  - 2606051800
  - 2606012100
  - 2605264000
supersedes: []
superseded_by: []
---

# ADR-2606073200: meyasu 目安 — unified arbitrage / supply-demand intel orchestrator

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

The cohort answering *「全世界の商品・製品の価格差(arbitrage)／需給／需要を分析・可視化・intel・
social post」* is spread across four actors: **kakaku 価格** (cross-merchant/region price spread +
present supply/demand index + offer ingest, ADR-2605091200), **okaimono 御買物** (provisioning
commons, ADR-2606012100), **ossekai 御節介** (information-arbitrage + aggregate-first publication,
ADR-2605264000), and **mitooshi 見通し** (probabilistic forecasting, ADR-2606051800). The user's
gap audit explicitly names a fifth, missing piece: a **統合 arbitrage アクター** that fuses these
signals into one public-good intel surface.

The constitutional risk is obvious: a "global arbitrage" actor is one rename away from a trading
desk (Charter §1.3 + the yobel prohibition). The design must make speculation **unrepresentable**,
not merely discouraged.

# Decision

Introduce **meyasu 目安** (`did:web:meyasu.etzhayyim.com`, `20-actors/meyasu/`) — a thin
**orchestrator**, named for a *yardstick / guide*, NOT a trade. meyasu computes no price or
forecast math itself; it **fuses** its siblings' outputs:

```
kakaku   price SPREAD + present supply/demand index        (now)
mitooshi forecast DISTRIBUTION of that index               (next)
ossekai  aggregate-first publication discipline            (how)
   ↓ meyasu
 one per-product arbitrage-intel card → aggregate post + planner handoff
```

Three cells over one kotoba Datom graph:

- **fuse** (`handle_fuse`) — `{kakaku, mitooshi}` per product → a unified card (spread, supply/demand
  now, forecast **band**, trajectory tightening/easing/stable, attention flag, planner route). A
  point-asserted or speculative forecast is **refused** (G2).
- **publish** (`handle_publish`) — cards → aggregate-first post + planner handoff for attention cards;
  broadcast operator-gated, default `:draft`.
- **persist** (`handle_persist` + `card_to_datoms`) — flatten cards into kotoba Datoms over
  `kotoba/schema.edn` (`:meyasu.card/* :meyasu.post/*`); the tx is **returned, not written** without
  an operator ref (no-server-key). A forecast is persisted as `:forecast-band-lo/hi`, never a point.

Lexicons `com.etzhayyim.apps.meyasu.{card,post}`; self-driving `kotoba/deploy.sh` (blocking test
gate) + path-scoped `.github/workflows/meyasu-test.yml`. A cohort **end-to-end** test
(`test_cohort_e2e.py`) proves kakaku → mitooshi → meyasu composes leak-free across actor boundaries.

## Gates (the union of its siblings' invariants — do NOT weaken)

- **G1 non-speculative** — intent is `buyer-transparency+supply-resilience`; meyasu emits no trade /
  price target and settles no money. The name 目安 is the structural commitment.
- **G2 distribution-respecting** — a consumed forecast MUST be a distribution (`point_asserted`
  false) with a use in the resilience set; a point/speculative forecast is refused per-item.
- **G3 aggregate-first** — published intel is anonymized aggregate (`shape == "aggregate"`).
- **G4 non-adjudicating** — attention cards (notable spread AND tightening forecast) are routed to a
  planner (`okaimono` buyers / `danjo` resilience); meyasu states, the planner decides.
- **G5 Murakumo-only inference** · **G6 no-server-key** (publication + persist operator-gated).

# Consequences

- The cohort now has a single pane of glass; the fused card is durable + queryable kotoba state, not
  ephemeral. Per-product price-difference + supply/demand + forecast trajectory are one record.
- Speculation is structurally unrepresentable: `:trade`/`:speculation` are not enum members of the
  card's intent, and a point forecast cannot be fused.
- **Companion work this session** (same PR): kakaku offer-ingest extraction pipeline (JSON-LD →
  selector → meta → Murakumo; live fetch G11-gated); mitooshi quantile (pinball-scored) forecaster;
  okaimono live USDC + TitheRouter settlement broadcast (member-signed, no-server-key); ossekai
  completed 8/8 cells; **onion → kotoba-kqe migration** removing the last `createKyselyDb`/Hyperdrive
  read-path violation (ADR-2606071800) + the onion BPMN crawl worker re-homed as a py-kotodama
  primitive running in a kotoba-wasm component (Datom-native, operator-gated fetch).

# Alternatives Considered

- **Fold the fusion into kakaku or mitooshi.** Rejected: it would couple price and forecast concerns
  and blur the non-adjudicating boundary; a thin separate orchestrator keeps each source authoritative.
- **A richer "arbitrage engine" that captures spreads.** Rejected outright — that is a trading desk
  (Charter §1.3 + yobel). meyasu is a guide, never a counterparty.

# References

- ADR-2605091200 — kakaku price comparison (spread + supply/demand source)
- ADR-2606051800 — mitooshi probabilistic forecasting (distribution source)
- ADR-2606012100 — okaimono provisioning commons (buyer planner)
- ADR-2605264000 — ossekai aggregate-first publication discipline
- ADR-2606071800 — RisingWave/Hyperdrive/Kysely → kotoba-kqe remediation wave (onion companion fix)
- ADR-2605262130 / 2605312345 — kotoba Datom canonical state + kotoba-kqe read path
- ADR-2605215000 — Murakumo-only inference
