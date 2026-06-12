---
id: adr-2606090900
title: "ADR-2606090900: Session-Close — uchiwake (内訳) product-BOM/GTIN worldwide-coverage wave"
status: accepted
doc_type: adr
topic: session-close-uchiwake-product-bom-gtin-coverage
authoritative: true
last_verified: 2026-06-09
priority: 5.0
axis: process
weight: 0.50
priority_note: "Session-close record for the /loop wave that designed + implemented the product-level (GTIN) coverage layer beneath kabuto, measured cross-actor integration, registered the actor, built the first bulk-ingest adapter, and filed the G7 worldwide-ingest authorization proposal."
authoritative_for:
  - session-close summary of the uchiwake product-BOM/GTIN wave (2026-06-08 … 06-09)
  - deps.toml registration of the uchiwake module + ADR-2606081800
related:
  - adr-2606081800-uchiwake-world-product-bom-gtin-kg
  - adr-2606082700-uchiwake-g7-worldwide-ingest-authorization-proposal
  - adr-2606022000-kabuto-public-company-supply-chain-kg
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606081800 (uchiwake actor — the substance of this session)
---

# ADR-2606090900: Session-Close — uchiwake (内訳) product-BOM/GTIN worldwide-coverage wave

**Date**: 2026-06-09
**Status**: ACCEPTED (process record)
**Deciders**: Jun Kawasaki

# Context

A `/loop` session (every 30 min) on the prompt *"gtin なども含めて全世界coverage 想定で設計実装"*
(design + implement assuming worldwide coverage, including GTIN). It began from a coverage
assessment of the corporate-observation actors (kabuto / kanjō / entity-as-actor) which found that
**kabuto's supply graph stops at company→company edges** — there was no product-level layer (no
GTIN, no bill of materials, no subsidiary rollup). This session built that layer.

# What was done (8 iterations)

1. **Actor — uchiwake 内訳** (ADR-2606081800, merged): the product-level layer beneath kabuto.
   GTIN-keyed (`:product/*`, mod-10 validated) trade items decomposed `PRODUCT → PART → raw
   MATERIAL`, plus `:process.step` / `:logistics.leg` / `:design.ref` (the 加工 / 運送 / 設計
   dimensions) and `:company.ownership` (子会社, GLEIF Level-2 RR) rolling a brand-owning
   subsidiary up to its ultimate parent. `product-bom-ontology.kotoba.edn` vocabulary; stdlib
   `analyze.py` (aggregate-first resilience report) + bounded real seed.
2. **Cross-actor measurement** — `crosscheck.py`: *measures* (never claims) integration. Company
   refs wire to real kabuto companies; **80.8%** of distinct refs resolve into kabuto's universe;
   reverse coverage = product-BOM detail on **~6.4%** of kabuto's supply-chain companies / **~1.2%**
   of all 1,719 — emitted with a prioritized ingest worklist. The loop demonstrably self-corrected
   (reverse coverage 2.6% → 6.4% in one iteration by ingesting worklist suppliers).
3. **Registration** (PR #1481): manifest conformed → `did:web:etzhayyim.com:actor:uchiwake`
   resolves + appears in `/search`; 4 AT-Protocol lexicons; root CLAUDE.md index row.
4. **Bulk-ingest adapter** (PR #1484): `methods/adapters/openfoodfacts.py` — turns Open Food Facts
   (CC-BY-SA, ~3M real GTIN items) into datoms; GTIN-validated, `:representative`. The scale-path
   proven offline; LIVE fetch G7-gated.
5. **G7 authorization proposal** (PR #1486, ADR-2606082700): non-self-executing Council request to
   open live full-universe ingest in revocable phases (OFF → GS1 → GLEIF-RR → Open Product Data),
   with full Charter/Rider compliance analysis (G1 public-record, G9 no-PII, no-server-key).

# Honest coverage statement

The **code + governance path to worldwide coverage is complete**; literal coverage is
intentionally **gated**. Today the product-BOM layer covers ~1.2% of even the bounded kabuto
universe and a vanishing fraction of the world's hundreds of millions of GTINs. Reaching genuine
worldwide coverage is now a **Council G7 decision** (ADR-2606082700), not a code task — by
constitutional design. Every BOM decomposition stays `:representative` (public teardown/label,
never an authoritative recipe); output stays aggregate-first + non-adjudicating (G2/G4).

# Decision

- Register the **uchiwake** module + **ADR-2606081800** in `deps.toml` (machine-discoverable SSoT).
- Record this session-close ADR.
- The `/loop` cron was stopped at a no-op steady state (all work complete or in-review); resume
  with `/loop` if further phases are authorized.

# Consequences

uchiwake is a live, registered, self-measuring Tier-B observation actor that closes the
product/BOM/GTIN/subsidiary gap. Three PRs (#1481 registration, #1484 adapter, #1486 G7 proposal)
carry the remaining pieces; merging #1481/#1484 is a routine technical decision, #1486 is a Council
governance decision. No Charter amendments were required.

# Status

ACCEPTED. Actor merged (ADR-2606081800); registration + adapter + G7 proposal in review; loop
stopped. deps.toml updated.
