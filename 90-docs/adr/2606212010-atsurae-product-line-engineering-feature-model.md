---
id: adr-2606212010-atsurae-product-line-engineering-feature-model
title: "ADR-2606212010: atsurae 誂え — Product Line Engineering (PLE) feature-model engine"
status: proposed
doc_type: adr
topic: atsurae-ple-feature-model
authoritative: true
last_verified: 2026-06-21
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - atsurae-product-line-engineering
depends_on:
  - 2606037200
  - 2606081800
related:
  - 2606032100
  - 2606013400
  - 2606010030
  - 2606033601
supersedes: []
superseded_by: []
---

# ADR-2606212010: atsurae 誂え — Product Line Engineering (PLE) feature-model engine

**Status**: proposed
**Date**: 2026-06-21
**Deciders**: Jun Kawasaki

# Context

A coverage review of the enterprise-software replacement stack found ERP fully covered by
open-kyber 開 (ADR-2606037200) and per-product BOM covered by uchiwake 内訳 (ADR-2606081800),
but a real gap at the **product-family** layer:

- The manufacturing actors (sanae 早苗 / hataori 機織 / kiyome 清め OSS-robotics; giemon /
  sarutahiko 猿田彦 / funadaiku 船大工 / igata) each build a *family* of products — a robot body
  with wheels OR tracks OR legs, battery OR fuel-cell, optional arm/autonomy — but nothing in the
  roster modelled that **commonality + variability** explicitly.
- This is exactly what **Product Line Engineering (PLE)** and its commercial tools (pure::variants,
  Gears, IBM Rational, SAP variant configuration) do: a **feature model** with mandatory /
  optional / alternative / or features + cross-tree constraints, from which valid **variants** are
  derived and each variant's BOM composed.
- uchiwake holds the BOM of *one* product; it cannot answer "what is the common platform across
  the whole family, and which variants are even valid?"

The charter angle matters: commercial PLE/PLM tools are proprietary configurators that **lock**
a product line to a vendor. A charter-clean PLE must be the inverse — an **open commons spec**.

# Decision

Introduce **atsurae 誂え** (誂え = bespoke / configured-to-order) — a clj-native R0 Tier-B actor
implementing a PLE feature-model engine over the kotoba Datom log.

**Model** (`methods/feature_model.cljc`):
- `FEATURE {:id :parent :kind :group}` — `:kind ∈ {:root :mandatory :optional}` governs a
  non-grouped child; `:group ∈ {:xor :or nil}` imposes cardinality on a feature's children
  (`:xor` = exactly 1, `:or` = ≥1).
- `CONSTRAINT {:kind :from :to}` — `:requires` (A⇒B) / `:excludes` (¬(A∧B)).
- `BINDING {:feature :parts [{:part :qty}…]}` — feature → parts for BOM derivation.

**Computed**:
- `valid-config?` — structural cardinalities (mandatory / xor / or / orphan) + cross-tree
  constraints → `{:valid? :violations}`.
- `variants` — bounded structural enumeration ∩ constraint satisfaction (every valid complete
  variant).
- `commonality` — feature → fraction of variants including it (1.0 = common platform; 0<·<1 =
  variation point; 0.0 = constraint-dead).
- `derive-bom` — a variant's BOM (∪ of selected features' parts, qty summed) → hands off to
  uchiwake 内訳 (BOM KG) + open-kyber 開 (ERP).

**Constitutional stance (gates, enforced in code + tests)**:
- **G1 commons-spec-not-license-key** — `:atsurae/license-lock` / `:atsurae/drm` unrepresentable
  (test-pinned). A feature model is an OPEN spec, never a vendor lock.
- **G2 spec-only-never-manufactures** — `:atsurae/manufacture` unrepresentable; the manufacturing
  actors build a chosen variant under Council Lv7+ gate, never atsurae.
- **G3 structural-not-adjudicating** — `:atsurae.product/verdict` unrepresentable; validity is
  structural constraint satisfaction, never a good/bad product judgement.
- **G4 no-person-data** · **G5 kotoba-EAVT-native** · **G6 no-server-key** · **G7 synthetic-seed**.

**Persistence**: `methods/kotoba.cljc` content-addressed append-only product-line ledger
(commit-DAG, verify-chain); `methods/autorun.cljc` deterministic, idempotent-by-content heartbeat
(identical analysis = no-op — the ledger records product-line CHANGES, not liveness ticks).

**Empirical R0 result**: a synthetic 15-feature OSS-robotics mobility-base line enumerates **176
valid variants**; the common platform is `{robot-base, locomotion, power}` (commonality 1.0); the
constraints (`autonomy requires lidar`, `legs excludes tethered`, `autonomy excludes tethered`)
prune the space and create genuine variation points. 11 tests / 41 assertions green.

# Consequences

- The manufacturing actors gain an explicit **product-family model**: configure a variant from
  the open feature model → derive its BOM → uchiwake/open-kyber → build (under Council gate). The
  CAD→BOM→ERP→MES lifecycle gains its missing PLE front-end.
- "誂え" (bespoke configuration) is realised as a member-principal flow at R1: a member configures
  a variant from the commons model; atsurae validates + derives; the build is gated.
- **No charter amendment**: a new spec/derivation actor under the labor-liberation manufacturing
  frame; the open-commons stance (G1) is the charter-clean inverse of proprietary PLM lock-in
  (Rider §2 collective-commons axis), and spec-only (G2) preserves the manufacturing actors' own
  Council gates.
- R0 enumerates a bounded space; the honest limit (SAT/BDD for very large models) is named in the
  R1 worklist.

# Alternatives Considered

- **Extend uchiwake 内訳 to cover variants.** Rejected: uchiwake is the per-product BOM *knowledge
  graph* (GTIN-keyed, observational); a feature model with cardinality/constraint *derivation* is
  a different shape and would overload uchiwake's mirror stance. atsurae derives; uchiwake holds.
- **Put variant config inside each manufacturing actor.** Rejected: every robotics/vehicle/ship
  actor would re-implement feature-model logic; one shared PLE engine is the DRY, commons answer.
- **Model variability inside open-kyber's ISIC packs.** Rejected: ISIC packs are industry CoA
  templates (accounting), not product feature models — orthogonal concern.
- **Adopt a proprietary PLE/PLM tool's format.** Rejected on charter grounds (G1): the whole point
  is an open commons spec, not a vendor-locked configurator.

# References

- ADR-2606037200 (open-kyber 開 — kotoba-Datom ERP + ISIC packs; the ERP atsurae feeds)
- ADR-2606081800 (uchiwake 内訳 — product BOM / GTIN KG; the BOM layer derive-bom hands off to)
- ADR-2606032100 (sanae/hataori/kiyome — OSS-robotics bodies that build a configured variant)
- ADR-2606013400 (funadaiku 船大工 — Nagi-class ships) · ADR-2606010030 (giemon factory)
- ADR-2606033601 (sumitsubo 墨壺 — CAD geometry behind a feature)
