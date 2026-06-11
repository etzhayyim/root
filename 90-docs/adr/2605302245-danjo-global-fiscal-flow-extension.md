---
id: adr-2605302245-danjo-global-fiscal-flow-extension
title: "ADR-2605302245: 弾正 (danjo) global fiscal-flow extension — generalize the budget/procurement ingest cells beyond JP, add an inter-governmental fund-flow datom class, and emit fund-flow datoms that the kanae visualization actor (ADR-2605302300) consumes (still R3-gated, still non-adjudicating)"
status: proposed
doc_type: adr
topic: danjo-global-fiscal-flow-extension
authoritative: true
last_verified: 2026-05-30
priority: 7.5
axis: actor-architecture
weight: 0.75
priority_note: "Extends danjo (ADR-2605301600) along direction (1) of the 2026-05-30 user request (全世界の政府の資金の流れ): generalizes the danjo budget_ledger + procurement_graph ingest cells from JP-first to jurisdiction-parametric over the already-global corpus (ADR-2605263900: USAspending / EU FTS / IMF SDMX / WB / OECD / TED / SAM.gov + JP 予算書 / 政府調達), and adds an inter-governmental fund-flow datom class (donor-juris ↔ recipient-juris ↔ instrument). CONSTRAINT: this does NOT change danjo's constitutional gating — multi-jurisdiction remains R3 (Council Lv7+ unanimity per ADR-2605301600 §7); this ADR is PROPOSED design + datom-schema reservation, not activation. danjo stays the non-adjudicating cross-reference ENGINE; it emits fund-flow datoms but renders nothing. Visualization + Murakumo narrative is the disjoint kanae actor (ADR-2605302300, direction (2))."
authoritative_for:
  - danjo budget_ledger + procurement_graph jurisdiction-parametric generalization (JP-first → global, R3-gated)
  - danjo inter-governmental fund-flow datom class (`intergov-fund-flow`) shared with kanae `fundFlowEdge`
  - the danjo (engine) ↔ kanae (visualizer) handoff contract
depends_on:
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2605263900-public-data-open-government-ipfs-ingestion
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2605302300-kanae-global-fiscal-flow-visualization-tier-b-actor-r0
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
supersedes: []
superseded_by: []
notes: |
  Session 2026-05-30: direction (1) of the user's "全世界の政府の資金の流れ" request.
  danjo (ADR-2605301600) already declares (N12) that it is jurisdiction-generic in
  architecture and JP-first only at R0, with multi-jurisdiction at R3 (Council Lv7+
  unanimity). This ADR makes that generalization explicit for the FISCAL subset
  (budget + procurement + inter-governmental transfer) and reserves the datom schema
  the kanae visualization actor (ADR-2605302300) consumes. It deliberately does NOT
  loosen any danjo gate, advance the R3 timeline, or add a renderer to danjo —
  rendering + Murakumo narrative is kanae's disjoint job. The point of separating this
  from the kanae ADR is to keep the constitutional boundary crisp: danjo finds
  (non-adjudicating cross-reference); kanae renders (narrative + visualization).
---

# Context

The 2026-05-30 user request — visualize the fiscal flows of every
government in the world — has two directions, both chosen by the user:

1. **Extend danjo** to cover global fiscal flows (this ADR).
2. **Create a dedicated visualization actor** — kanae (ADR-2605302300).

danjo (ADR-2605301600) is the kotoba-native, non-adjudicating
cross-reference engine over the open-government corpus. Two facts about
its current design bound this extension:

- danjo is **JP-first at R0** (`jurisdiction: jpn`) but **explicitly
  jurisdiction-generic in architecture** (N12). Its budget_ledger and
  procurement_graph cells already model `appropriation ↔ outlay ↔
  recipientLei` and `authority ↔ award ↔ awardeeLei ↔ amount`,
  jurisdiction-parametrically.
- danjo's **multi-jurisdiction extension is R3**, gated on **Council
  Lv7+ unanimity** (ADR-2605301600 §7). That gate is constitutional and
  this ADR does NOT move it.

The corpus danjo reads (ADR-2605263900) is **already global and
W1-landed** for the fiscal facets: USAspending, EU Financial
Transparency System, IMF SDMX, World Bank Open Data, OECD.Stat, UN data,
EU TED, US SAM.gov, plus JP 予算書 / 政府調達. So the data is present;
what is missing is (a) the explicit jurisdiction-parametric
generalization of the two danjo fiscal ingest cells, and (b) a datom
class for **inter-governmental** flows (donor-jurisdiction →
recipient-jurisdiction transfers, aid, loans) that the domestic
`budget_ledger` schema does not capture.

This ADR supplies (a) + (b) as **proposed design + datom-schema
reservation**, and defines the **handoff contract** to the kanae
visualization actor (ADR-2605302300), which consumes danjo's fund-flow
datoms and renders them (Murakumo narrative + kami-engine WASM) — a job
danjo constitutionally does not do.

# Decision

## §1 — Jurisdiction-parametric fiscal ingest (R3-gated, non-adjudicating)

Generalize danjo's two fiscal ingest cells from JP-first to
jurisdiction-parametric over the already-global corpus, WITHOUT changing
any danjo gate or the R3 multi-jurisdiction timeline:

| danjo cell | R0–R2 (unchanged) | R3 generalization (this ADR) |
|---|---|---|
| `danjo_budget_ledger` | JP 予算書 → `appropriation ↔ outlay ↔ recipientLei ↔ program` datoms | jurisdiction-parametric over USAspending / EU FTS / HM Treasury OSCAR / JP 予算書 — same datom shape, `jurisdiction` carried per record |
| `danjo_procurement_graph` | JP 政府調達 → `authority ↔ award ↔ awardeeLei ↔ amount` datoms | jurisdiction-parametric over EU TED / US SAM.gov / UK Contracts Finder / JP 政府調達 — same datom shape |

All danjo gates G1–G13 (ADR-2605301600 §4) apply unchanged: passive-only
(G3), non-adjudicating (G4), ≥2 source CIDs (G5), open method (G6),
Murakumo-only (G7), no commercial gov-intel terminals (G8), per-juris
publication-rule honoring (G9), aggregate-first (G10), Transparent
Religious Force (G11), read-only (G12), stateAlignedFlag pass-through
(G13). The CN-class §2(g) flag propagates per G13.

## §2 — Inter-governmental fund-flow datom class (`intergov-fund-flow`)

Add a new kotoba EAVT datom class to danjo's schema for flows the
domestic `budget_ledger` cannot express — donor-jurisdiction →
recipient-jurisdiction transfers:

```
intergov-fund-flow:
  donorJurisdiction      # ISO-3 OR supra (EU / OECD / UN / WB / IMF)
  recipientJurisdiction  # ISO-3
  instrument             # grant / loan / SDR-allocation / aid-disbursement / repayment / quota-subscription
  amount + currency
  period                 # fiscal period
  sourceRecordCids[]     # ≥2 (G5); from gov.dataset.statisticsObservation (IMF SDMX / WB / OECD / UN)
  stateAlignedFlag       # G13 pass-through
```

This datom class is produced by danjo's existing `danjo_crossref_engine`
discipline (a cross-reference over `gov.dataset.statisticsObservation`),
NOT by a new cell — it is a schema reservation. It is descriptive only;
`instrument` carries no verdict token (G4). It is the shared vocabulary
the kanae `fundFlowEdge` lexicon (ADR-2605302300 §3) maps onto for
inter-governmental flows.

## §3 — danjo (engine) ↔ kanae (visualizer) handoff contract

| Concern | danjo (ADR-2605301600 + this ADR) | kanae (ADR-2605302300) |
|---|---|---|
| Role | non-adjudicating cross-reference ENGINE | fiscal-flow ASSEMBLY + Murakumo NARRATIVE + WASM VISUALIZATION |
| Output | `crossReferenceLink` + `discrepancyObservation` + budget/procurement/`intergov-fund-flow` datoms | `fundFlowEdge` + `flowNarrative` + `visualizationManifest` |
| Inference | indexing + cross-reference (G7 Murakumo for any LLM step) | Murakumo-LLM narrative (G7) |
| Rendering | NONE (textual publication only; visualization is a danjo non-goal) | kami-engine WASM (G14) |
| Persistence | kotoba EAVT (G2, no Kotoba/Datomic) | kotoba EAVT (G2, no Kotoba/Datomic) |

kanae reads danjo's fiscal datoms (read-only, G12 on both sides) and
never writes back. danjo remains fully functional without kanae; kanae
is a downstream lens.

## §4 — What this ADR does NOT do

- Does **not** move danjo's R3 multi-jurisdiction gate (Council Lv7+
  unanimity remains; ADR-2605301600 §7 unchanged).
- Does **not** loosen any danjo gate G1–G13.
- Does **not** add a renderer, a dashboard, or an LLM-narrative path to
  danjo (those are kanae's, ADR-2605302300).
- Does **not** create new cells — `danjo_budget_ledger` /
  `danjo_procurement_graph` / `danjo_crossref_engine` already exist
  (path-reserved); this generalizes their scope + reserves one datom
  class.

# Consequences

**Positive.** danjo's fiscal cross-reference becomes explicitly global
(over data already pinned), and the inter-governmental flow vocabulary
the kanae visualization needs is reserved at the engine layer, keeping
the engine/visualizer boundary crisp.

**Costs / risks.** Multi-jurisdiction publication amplifies danjo's
existing defamation / political-weaponization risk (ADR-2605301600
Consequences); mitigated identically (G4/G5/G6/G10/G11) and still gated
at R3 Council Lv7+ unanimity. No new attack surface beyond the corpus
danjo already reads.

**Neutral.** Proposed design only; no activation, no timeline change.

# Alternatives Considered

1. **Fold this into the kanae ADR.** Rejected: the danjo engine
   generalization is a distinct constitutional concern (it touches
   danjo's R3 gate and its non-adjudication identity) from kanae's
   visualization role. The user asked for BOTH directions explicitly;
   two ADRs keep the boundary auditable.
2. **Advance danjo's R3 multi-jurisdiction gate to unblock global fiscal
   flows sooner.** Rejected — fatal: the R3 Council Lv7+ unanimity gate
   is constitutional (ADR-2605301600 §7); a fiscal-scope request does not
   justify weakening it.
3. **Give danjo the renderer too.** Rejected: visualization is a danjo
   non-goal; kanae (ADR-2605302300) is the disjoint renderer.

# References

- `/90-docs/adr/2605301600-danjo-public-accountability-oversight-tier-b-actor-r0.md` — danjo master ADR (gates, cells, R3 gate)
- `/90-docs/adr/2605302300-kanae-global-fiscal-flow-visualization-tier-b-actor-r0.md` — kanae visualization actor (downstream; direction (2))
- `/90-docs/adr/2605263900-public-data-open-government-ipfs-ingestion.md` — global fiscal corpus (USAspending / EU FTS / IMF / WB / OECD / TED / SAM.gov)
- `/90-docs/adr/2605262130-kotoba-storage-substrate-unification.md` — kotoba EAVT (no Kotoba/Datomic)
- `/90-docs/adr/2605192100-etzhayyim-mission-charter.md` — §1.12 + §2(c) + §2(e)
- `/20-actors/danjo/` — danjo manifest + README + CLAUDE.md
