---
id: adr-2606032000-kanjo-corporate-financial-disclosure-ingest-tier-b-actor-r0
title: "ADR-2606032000: kanjō 勘定 — Public-Company Financial-Disclosure (決算) Ingest Tier-B Actor (R0)"
status: proposed
doc_type: adr
topic: kanjo-corporate-financial-disclosure-ingest
authoritative: true
last_verified: 2026-06-03
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Tier-B observation-layer actor that registers PUBLIC-company DISCLOSED 決算 facts (BS / PL / CF line items) from PRIMARY disclosure (JP EDINET 有価証券報告書 + US SEC EDGAR 10-K/20-F, all Tier-A per ADR-2605263800 §2) into the kotoba Datom log, normalized across JP-GAAP / US-GAAP / IFRS onto canonical concepts. Resurrects the financial-fact model of the superseded ADR-2604291500 onto kotoba; consumes the Tier-A primary-disclosure sources of ADR-2605263800. Shares the org.corp.* id space with kabuto (ADR-2606022000) + tsumugi. The EXTERNAL public-company sibling of toritate 執帳 (internal accounting). NON-ADJUDICATING (G2) + NO investment advice (G4, NOT 投資助言業) + NO forecasting (no 業績予想 — exactly what the prohibited 四季報 adds). PROHIBITED inputs: 会社四季報 + all paid commercial terminals (Bloomberg / S&P CapIQ / Refinitiv / FactSet / Moody's / D&B / Pitchbook / Crunchbase) per Charter Rider §2(e) anti-gatekeeping + §2(c) vendor query-tracking. Vocab corporate-financials-ontology.kotoba.edn (:fin.filing/:fin.fact/:fin.concept/:fin.metric/:fin.agg). R0 = design + vocab + concept-map + :representative seed (6 filings / 36 facts / 5 filers) + 3 cells; live full-universe XBRL parse = G7 Council+operator gated. 8 gates as G1-G12 subset + 8 non-goals."
authoritative_for:
  - corporate-financial-disclosure-ingest-actor
  - fin-fact-eavt-vocabulary
  - gaap-concept-normalization-map
depends_on:
  - 2605263800
  - 2606022000
  - 2604291500
  - 2605262900
  - 2605262130
  - 2605312345
  - 2605215000
related:
  - 2605301600
  - 2606011800
  - 2606013800
supersedes: []
superseded_by: []
---

# ADR-2606032000: kanjō 勘定 — Public-Company Financial-Disclosure (決算) Ingest Tier-B Actor (R0)

**Status**: proposed
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

# Context

The question was *「会社四季報などからすべての法人の決算情報を ingest・登録する actor は設計されているか?」*
The answer was no. The closest actors stop short of the financials:

- **kabuto 兜** (ADR-2606022000) holds the public-company graph — name, ticker, exchange, LEI/ISIN,
  HQ, IR contact, sector, and disclosed supplier edges — but explicitly **excludes financial
  statements** (its only number is a `:representative` market-cap snapshot).
- **toritate 執帳** (ADR-2605262900) does etzhayyim's **own internal** accounting (tithe / Public
  Fund), not external corporate disclosure.
- **ADR-2605263800** built the **substrate/plumbing** for corporate disclosure — the `corp/` IPFS
  bucket family, the `kotodama.organism.sensors.corp.*` sensor families, and the EDGAR / EDINET /
  Companies House / GLEIF fetcher path-reserves (all Tier-A) — but it does **not** define a
  financial-fact EAVT vocabulary or an actor that turns a filing's XBRL into queryable 決算 Datoms.
- **ADR-2604291500** (superseded) had the right financial-fact *model* (`fiscal_year` / `period_end`
  / `statement_type` / `concept` / `value`) but targeted a centralized SQL store, now disallowed by
  the kotoba substrate boundary (ADR-2605262130 + 2605312345).

So the missing piece is a **consumer actor**: read primary-disclosure filings (the plumbing of
2605263800), normalize their taxonomy elements across GAAPs, and register the resulting line items
as first-class kotoba Datoms (the model of 2604291500, re-homed on the Datom log).

**Why not 四季報.** The user's instinct — *"it's public information, why is it blocked?"* — is
correct about the **facts**. A company's decided earnings ARE public, and the primary disclosures
that carry them (EDINET 有価証券報告書, SEC EDGAR 10-K) are Tier-A **admissible** (ADR-2605263800 §2).
What is inadmissible is the **会社四季報 product**: a copyrighted editorial compilation by 東洋経済新報社,
sold for a fee, whose distinctive value is its **業績予想 (forecasts)** layered on top of the public
facts. Ingesting it fails on two independent grounds — (1) **copyright/license**: it carries no open
license, so it cannot be redistributed into an Apache-2.0 / IPFS open corpus (the same bar any
proprietary dataset fails); (2) **Charter Rider §2(e)+§2(c)**: as a paid, gatekept financial-data
product whose vendor would learn the member's query posture, it sits in the same family the Rider
prohibits (Bloomberg / S&P CapIQ / Refinitiv / FactSet / Moody's / D&B / Pitchbook / Crunchbase). The
Charter does not block facts; it blocks building on a proprietary vendor moat. kanjō therefore reads
the **primary filing**, never the terminal — and, mirroring the same principle, **does not forecast**
(forecasting is exactly the value-add 四季報 sells).

# Decision

Introduce **kanjō 勘定** (*reckoning / account*), a Tier-B observation-layer actor at
`did:web:etzhayyim.com:actor:kanjo`, sharing the `org.corp.*` id space with kabuto / tsumugi. It is
the **external public-company sibling of toritate** and the **financials face of kabuto**.

## §1. Vocabulary — `00-contracts/schemas/corporate-financials-ontology.kotoba.edn`

Five entity families on the kotoba Datom log:

- **`:fin.filing/*`** — one primary disclosure (provenance anchor): `:source` (`:edinet|:edgar|…`),
  `:form` (`:yuho|:10-K|:20-F|:teisei|…`), `:fiscal-year`, `:period-start/-end`, `:filed-date`,
  `:accession` (EDINET docID / EDGAR accession), `:doc-cid` (IPFS CID of the XBRL/PDF, G8),
  `:currency`, `:accounting` (`:jgaap|:ifrs|:usgaap`).
- **`:fin.fact/*`** — ONE disclosed line item: `:statement` (`:bs|:pl|:cf|:eps`) × `:concept`
  (canonical) × `:value`/`:unit`/`:scale` × `:context` (`:consolidated|:nonconsolidated`).
  `:concept-raw` retains the source taxonomy element (audit). `:superseded-by` links a restated fact
  to its 訂正 (forward pointer; the original Datom is RETAINED — 非終末論).
- **`:fin.concept/*`** — the canonical concept DICTIONARY (GAAP-normalization map).
- **`:fin.metric/*`** — derived ratio / YoY (always `:synthesized`).
- **`:fin.agg/*`** — sector / currency aggregate (always `:synthesized`, coverage-honest).

## §2. GAAP normalization — `methods/concept_map.py`

A single canonical concept catalogue (17 concepts across BS / PL / CF / per-share) with a reverse
index mapping each **source taxonomy element** onto a canonical concept per standard:

- JP EDINET `jppfs_cor:NetSales` · US `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax` ·
  IFRS `ifrs-full:Revenue` → **`:revenue`** (one comparable concept).
- **Honest non-comparability**: `:ordinary-income` (経常利益) is **JGAAP-only** — it has no US-GAAP /
  IFRS twin and carries a `:fin.concept/note` forbidding cross-standard comparison.

## §3. Sources (G1 — Tier-A primary disclosure only, per ADR-2605263800 §2)

SEC EDGAR (10-K/20-F, public-domain) · JP EDINET (有報, 金融庁 free-redistribution) · UK Companies
House (OGL v3.0) · EU OAM (per-member-state). **Prohibited**: 会社四季報 + all paid commercial
terminals (Charter Rider §2(e)+§2(c)).

## §4. Cells

- `concept_map.py` → `out/concept-dictionary.kotoba.edn` (the `:fin.concept` dictionary).
- `ingest.py` → EDGAR companyfacts JSON + EDINET pre-extracted element JSON → `:fin.filing`/`:fin.fact`
  EAVT, merged with the seed (`:authoritative` wins). Offline default; **live fetch G7-gated**
  (`KANJO_OPERATOR_GATE=1` + explicit `--fetch-edgar CIK`, single polite request, passive-only per
  ADR-2605262400 §7). Full XBRL-XML parse of the EDINET universe is **R1**.
- `analyze.py` (stdlib) → per-company per-FY ratios (`:fin.metric`) → YoY (as-of history) →
  sector/currency aggregates (`:fin.agg`, **no FX cross-currency sums in R0**) → aggregate-first
  `out/intel-report.md`.

## §5. Gates (12)

| # | Gate |
|---|---|
| **G1** | PRIMARY public disclosure ONLY (EDINET/EDGAR/Companies House/EU OAM, Tier-A). Prohibited: 四季報 + paid terminals (Charter Rider §2(e)+§2(c)). Read the filing, never the terminal. |
| **G2** | NON-ADJUDICATING — facts + transparent ratios; never a rating, valuation, solvency/fraud verdict, or label (kabuto G4 / danjo sibling). |
| **G3** | aggregate-first output; per-company facts mirror the filing verbatim. |
| **G4** | NO investment advice / securities recommendation (NOT 投資助言業, 金商法); NO forecasting (no 業績予想). |
| **G5** | sourcing honesty (:authoritative \| :representative \| :synthesized); metrics/aggregates :synthesized, never re-ingested as fact; Σ coverage-bounded, never a market total. |
| **G6** | Murakumo-only narration (ADR-2605215000). |
| **G7** | outward-gated INGEST — live EDGAR/EDINET fetch = KANJO_OPERATOR_GATE + Council; full-universe XBRL = R1; passive-only (ADR-2605262400 §7). |
| **G8** | no git-lfs — source XBRL/PDF → DataLad → IPFS (80-data/corporate-financials); CID on :fin.filing/doc-cid. |
| **G9** | PII/redaction — ingests financial line items, not the officer roster; incidental PII follows ADR-2605263800 §5 (GDPR / 個情法) → encrypted envelope, excluded by default. |
| **G10** | NO market-abuse enablement — published filings only; never non-public / pre-disclosure material facts (金商法). |
| **G11** | restatement-as-history (非終末論) — 訂正 asserts a new fact via :superseded-by; prior Datom retained; read as-of. |
| **G12** | read-only — never mutates upstream filings. |

## §6. Non-goals (8)

N1 NOT investment advice / 投資判断 · N2 NOT a credit-rating agency · N3 NOT 四季報 / no commercial-
terminal data · N4 NOT fraud/solvency adjudication (state/court matter) · N5 NOT forecasting / 業績
予想 · N6 NOT real-time quotes / valuation · N7 NOT private-company financials · N8 NOT tax/accounting
advice.

## First live EDGAR ingest (R1 first leg — 2026-06-10, PR #1533, recorded in ADR-2606101540)

The G7 gate was flipped by **explicit operator instruction** for the first time: 12 real EDGAR
filers (Apple / Microsoft / NVIDIA / Amazon / Alphabet / Meta / Berkshire / Broadcom / Tesla /
Intel / AMD / Micron) ingested via the documented offline-bridge workflow (companyfacts JSON →
`data/ingest/` (gitignored) → offline merge). Result, committed as `data/facts.merged.kotoba.edn`:
**183 filings / 2,484 facts (2,462 `:authoritative`) / 15 companies → 1,631 `:synthesized` metrics
+ 88 aggregates**; `EDGAR_CIK_TO_ORG` extended 2→12 preserving kabuto `org.corp.*` linkage; the
autorun heartbeat weaves the live graph (+~40k datoms/cycle, chain OK); 1,744 autorun tests green.
This is the cohort's first `:authoritative` live capture. EDINET live fetch, the full
EDINET/EDGAR-universe parse, and any live-node push remain Council + operator gated (G7 unchanged).

# Consequences

## Positive

- Closes the 決算 gap with a kotoba-native, constitutionally-bounded actor that COMPLETES the
  corporate picture: kabuto (supply) + tsumugi (power-graph) + **kanjō (financials)** over one
  `org.corp.*` id space.
- Cross-GAAP normalization makes JP / US / IFRS filers comparable at the concept level, with explicit
  honesty where standards diverge (経常利益).
- Powers downstream consumers already specified in ADR-2605263800 §0: toritate recipient-transparency
  cross-reference, danjo public-accountability, manabi financial-literacy curriculum — without any
  proprietary-vendor dependency.
- Demonstrates the substrate boundary working as intended: the public *facts* flow freely; the
  proprietary *compilation* (四季報 / terminals) is excluded by the Charter, not the facts.

## Negative / risks

- R0 ships a `:representative` seed (headline figures, rounded), not authoritative line-item XBRL —
  clearly flagged, but consumers must respect `:sourcing` before relying on a figure.
- Full EDINET-universe XBRL-XML parsing is non-trivial (taxonomy versioning, context dimensions) and
  deferred to R1 behind G7.
- No FX layer — cross-currency aggregates are deliberately not computed; a future FX-normalization
  concern must itself be sourcing-honest (which rate, as-of when).

# Alternatives Considered

1. **Extend kabuto with financial attributes.** Rejected: financials are a different cardinality
   (many facts × many periods per company) and a different constitutional surface (投資助言 boundary)
   than kabuto's supply-chain lens; co-locating them muddies kabuto G2/G4. A sibling sharing the id
   space keeps each actor's gates clean.
2. **Implement only ADR-2605263800 W1 plumbing.** Rejected as insufficient: it fetches and pins
   filings but produces no queryable 決算 vocabulary or report — the user asked to *register* the
   financial information, which requires the fact model + normalization this ADR adds.
3. **Ingest 会社四季報 directly.** Rejected: copyright/license (no open license) + Charter Rider
   §2(e)+§2(c). Primary disclosure carries the same facts, openly.

# References

- ADR-2605263800 — global corporate-disclosure IPFS ingestion (Tier-A source ladder; the plumbing kanjō consumes)
- ADR-2606022000 — kabuto (shared org.corp.* id space; public-company graph)
- ADR-2604291500 — JP corporate financial-disclosure ingest (superseded; financial-fact model re-homed here)
- ADR-2605262900 — toritate (internal accounting; kanjō is its external sibling)
- ADR-2605262130 + 2605312345 — kotoba Datom log canonical state
- ADR-2605215000 — Murakumo-only inference
- `/CHARTER-RIDER.md` §2(e) anti-gatekeeping + §2(c) surveillance — the 四季報 / paid-terminal prohibition
- `00-contracts/schemas/corporate-financials-ontology.kotoba.edn` — the `:fin.*` vocabulary
- `20-actors/kanjo/` — manifest + CLAUDE.md + cells + seed
