---
id: adr-2606081800
title: "ADR-2606081800: uchiwake (内訳) — World Product Bill-of-Materials / GTIN Knowledge Graph Tier-B Actor R0"
status: proposed
doc_type: adr
topic: uchiwake-product-bom-gtin-knowledge-graph
authoritative: true
last_verified: 2026-06-08
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "The product-level layer beneath kabuto — GTIN-keyed trade items decomposed to bill of materials (product→part→raw material) + process/logistics/design + subsidiary→ultimate-parent rollup; closes the 'no product/BOM granularity' gap identified in the kabuto/kanjo coverage assessment"
authoritative_for:
  - uchiwake actor charter (R0)
  - product bill-of-materials knowledge-graph constitutional gates G1..G12
  - product-bom-ontology.kotoba.edn vocabulary
  - GTIN normalization + GS1 mod-10 check-digit validation on ingest
  - subsidiary→ultimate-parent rollup (子会社) via GLEIF Level-2 RR ownership edges
related:
  - adr-2606022000-kabuto-public-company-supply-chain-kg
  - adr-2606042330-entity-as-actor-society-scale-social-mirror
  - adr-2605312330-giemon-part-graph-sbom-kotoba
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606022000 (kabuto — shared org.corp.* company id space + resilience-not-target discipline)
  - ADR-2606042330 (entity-as-actor — UNSPSC 18,342-code commodity space reused here)
  - ADR-2605262130 (kotoba storage substrate)
  - ADR-2605312345 (kotoba Datom log = first-class canonical state)
  - ADR-2606013600 (kotoba-wasm browser node — the render target)
  - ADR-2606013800 (actor-profile SSoT + dynamic did.json — the registration path)
  - ADR-2605215000 (Murakumo-only inference)
---

# ADR-2606081800: uchiwake (内訳) — World Product Bill-of-Materials / GTIN Knowledge Graph Tier-B Actor R0

**Date**: 2026-06-08
**Status**: PROPOSED (R0 design-only; live full-universe GS1/GLEIF ingest + live posting Council + operator gated)
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify)

# Context

A coverage assessment of the corporate-observation actors (kabuto 兜, kanjō 勘定, entity-as-actor)
found a hard ceiling: **kabuto's supply graph stops at company → company edges**. It records "ASML
supplies the foundries" but not *what a product is made of* — its parts, its raw materials, the
processing steps, the transport legs, the design standards. The only product-level decomposition
anywhere in the monorepo was the **giemon part graph** (ADR-2605312330) — a hand-curated SBOM for
**two robots**. There was no worldwide, GTIN-keyed product layer, and no modelling of the
**子会社 (subsidiary)** dimension: a brand-owning subsidiary appeared (if at all) as a flat company
node, never rolled up to its ultimate beneficial parent, so concentration was computed at the
marketing-entity level rather than the true-owner level.

The request: design + implement, **assuming worldwide coverage**, a product layer keyed on the GS1
**GTIN** (Global Trade Item Number) that decomposes trade items to their bill of materials and ties
back into kabuto's company space — **including subsidiaries**.

# Decision

Introduce **uchiwake 内訳** ("itemized breakdown"), a Tier-B observation actor that is the
**product-level layer beneath kabuto**. It datafies the world's trade items into the kotoba Datom
log along seven dimensions, all `:representative`/`:authoritative`/`:synthesized`-sourced:

1. **`:product/*`** — a trade item keyed on the **GTIN** (normalized to 14 digits; GS1 mod-10 check
   digit validated on ingest), with brand, **brand-owner → kabuto `:company/id`**, GS1 company
   prefix + prefix-country (honestly noted as *licensing* country, not origin), and GPC / UNSPSC /
   HS classification (reusing the existing 18,342-code UNSPSC space).
2. **`:part/*`** + **`:material/*`** — sub-assemblies/components and raw/refined material inputs.
3. **`:bom.edge/*`** — first-class directed bill-of-materials edges (parent CONTAINS child), with
   quantity, tier, disclosed supplier (→ kabuto), and a **bounded** criticality estimate.
4. **`:process.step/*`** — transformation steps (extraction → refining → fabrication → assembly →
   finishing → packaging → testing), with operator (→ kabuto) and jurisdiction.
5. **`:logistics.leg/*`** — transport legs (origin → dest, mode, carrier → kabuto).
6. **`:design.ref/*`** — design/standard/spec references (IEC/ISO/JEDEC/USB-IF/regulatory).
7. **`:company.ownership/*`** — the **子会社** edge: child → parent (GLEIF Level-2 Relationship
   Records). `analyze.py` follows these to roll a brand-owning subsidiary up to its **ultimate
   parent**, so material/brand concentration is computed at the true beneficial-owner level.

`analyze.py` (stdlib) emits an **aggregate-first resilience report**: recursive BOM material-closure
(which raw materials the most products depend on — e.g. li-ion cell materials reached by both a
phone and an EV pack via the shared cell), processing-jurisdiction load, ultimate-parent rollup, and
single-source/high-criticality diversification candidates. Derived datoms are flagged
`:concentration/derived true` and are never re-ingested as fact.

## Worldwide-coverage ingestion architecture (R1, G7-gated)

| Dimension | Public source |
|---|---|
| Product identity (GTIN) | GS1 GDSN + GS1 Verified; open mirrors Open Food/Beauty/Products Facts (CC) |
| Classification | GS1 GPC brick + UNSPSC + HS (WCO) |
| Brand-owner → company | GS1 prefix licensee → GLEIF LEI |
| Subsidiary → parent (子会社) | GLEIF Level-2 Relationship Records (RR) |
| BOM / materials | public teardowns, ingredient labels, supplier-list filings, EU ESPR DPP |
| Process / logistics | public origin declarations, UN Comtrade HS flows, factory-list pledges |
| Design / standards | cited IEC/ISO/JEDEC/USB-IF specs, public regulatory monographs (USP/Ph.Eur.) |

R0 ships a bounded real seed (6 products, 2 with real public GTINs); full ingest (hundreds of
millions of GTINs) is **R1** and `UCHIWAKE_OPERATOR_GATE` + Council gated.

## Constitutional gates (G1..G12)

Same family as kabuto, with two product-specific tightenings:
- **G2** extends "never a target-list" with **"never a clone/counterfeit recipe"** — quantities and
  mass fractions are bounded public estimates, never a manufacturer's confidential formulation.
- **G5** adds **GTIN check-digit validation** on ingest; a datom with a bad GS1 check digit is
  refused. BOM decompositions are `:representative`, not authoritative recipes.

G1 public-record-only · G3 aggregate-first · G4 non-adjudicating (no legality/conformity/origin
verdicts) · G6 Murakumo-only · G7 outward-gated ingest · G8 no-git-lfs · G9 no-PII (no consumer
purchase data) · G10 browser-native render · G11 outward-gated publish (deferred) · G12 read-only.

# Consequences

**Positive.** Closes the product/BOM granularity gap with a worldwide-coverage-shaped design: GTIN
as the global product key, recursive BOM closure to raw materials, processing/logistics/design
dimensions, and the 子会社 rollup that makes concentration honest at the beneficial-owner level.
Reuses kabuto's `org.corp.*` company space and the existing UNSPSC commodity space — no parallel
ontology. stdlib-only cells (pywasm-ready), 15 tests green.

**Negative / bounded.** R0 is a 6-product illustrative seed — coverage of the ~50,000 listed
companies' products and the hundreds of millions of GTINs worldwide is **0.00x%** today; the value
is the *shape*, not the *coverage*. BOM decompositions are public-estimate `:representative`, never
authoritative recipes. Full ingest is gated. Live posting (G11) and browser viz (G10) are deferred
to later iterations.

# Status

R0 design + bounded real seed landed; 15 tests green. Full GS1 GDSN / GLEIF-RR / Open Product Data
universe ingest is R1 (G7 Council + operator gated). Registry slot + did.json + lexicons + viz +
social are follow-on iterations.
