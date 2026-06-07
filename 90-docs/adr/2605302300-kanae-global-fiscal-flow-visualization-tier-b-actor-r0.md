---
id: adr-2605302300-kanae-global-fiscal-flow-visualization-tier-b-actor-r0
title: "ADR-2605302300: 鼎 (kanae) — kotoba-native global government fiscal-flow visualization Tier-B actor that assembles worldwide fund flows (domestic full-chain + inter-governmental) into kotoba EAVT, narrates them with Murakumo-only LLM, and renders them as kami-engine WASM visualizations (R0 scaffold)"
status: proposed
doc_type: adr
topic: kanae-global-fiscal-flow-visualization-actor
authoritative: true
last_verified: 2026-05-30
priority: 8.0
axis: actor-architecture
weight: 0.80
priority_note: "Names a new Tier-B actor (kanae 鼎) as the kotoba-EAVT-native fiscal-flow ASSEMBLY + Murakumo-LLM NARRATIVE + kami-engine WASM VISUALIZATION organ over the already-pinned open-government corpus (ADR-2605263900) and the danjo cross-reference graph (ADR-2605301600 + extension ADR-2605302245). Answers the 2026-05-30 audit: 全世界の政府の資金の流れを ingest → LLM 分析 → 可視化 → kotoba 永続化 する actor は設計されているか? Verdict was NO — the ingest substrate is global and W1-landed, danjo cross-references it but is JP-first AND visualization is an explicit danjo non-goal. kanae is the missing visualization+narrative lens. SAME constitutional discipline as danjo: NON-adjudicating (G4 UPL-equivalent), Murakumo-only inference (G7), aggregate-first (G10), Transparent Religious Force (G11), no commercial gov-intel terminals (G8), kotoba-native (G2, no Kotoba/Datomic). The name 鼎 (kanae, the ritual bronze tripod cauldron) evokes 鼎の軽重を問う — to weigh the worthiness of those who govern by making the public fiscal record legible; the three legs = the three upstream data substrates (domestic budget / domestic procurement / inter-governmental transfer) it stands on. kanae weighs the public record openly; it renders no verdict."
authoritative_for:
  - new Tier-B actor `kanae` (global government fiscal-flow visualization + narrative)
  - kotoba-kqe EAVT datom schema for fund-flow-edge / flow-narrative / visualization-manifest
  - the boundary between danjo (cross-reference ENGINE; non-adjudicating discrepancy observations) and kanae (fiscal-flow ASSEMBLY + Murakumo narrative + kami-engine WASM visualization)
  - `com.etzhayyim.kanae.*` Lexicon namespace (fundFlowEdge / flowNarrative / visualizationManifest / methodNote)
  - kami-engine WASM as the constitutional render substrate for fiscal-flow visualization (no third-party BI / no ad/analytics SDK in the render path)
depends_on:
  - adr-2605302245-danjo-global-fiscal-flow-extension
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2605263900-public-data-open-government-ipfs-ingestion
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605261800-nvidia-omniverse-compat-kami-engine
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605301400-tadori-onchain-tracing-actor-and-kotoba-eavt-migration
  - adr-2605264000-ossekai-info-arbitrage-actor
  - adr-2605263800-corp-identity-registry-lexicons
supersedes: []
superseded_by: []
notes: |
  Session 2026-05-30: user asked "今の全世界の政府の資金の流れを ingest, llm で分析,
  可視化, datomic kotoba api で永続化、保存する actor は設計されている?". Audit
  (Explore agent) found NO single actor with all four capabilities. The global
  fiscal INGEST substrate exists (ADR-2605263900 pins USAspending / EU Financial
  Transparency System / IMF SDMX / World Bank / OECD / TED / SAM.gov + JP 予算書 /
  政府調達 to IPFS). danjo (ADR-2605301600) cross-references it into kotoba EAVT and
  emits non-adjudicating observations — but is JP-first at R0 and visualization is an
  EXPLICIT danjo non-goal (it is a cross-reference engine + textual publication organ).
  The user chose to pursue BOTH directions: (1) extend danjo to global fiscal-flow
  scope (ADR-2605302245), and (2) create a dedicated visualization actor. This ADR is
  (2). User-selected parameters: name = 鼎 (kanae); scope = domestic full-chain
  (appropriation→outlay→recipient→procurement) + inter-governmental (IMF/WB/OECD aid
  + transfer + loan flows); render = kami-engine WASM (reuse existing isekai/omniverse
  WASM viewer assets). kanae is the LLM-narrative + visualization lens danjo lacks; it
  consumes danjo fund-flow datoms and the global gov.dataset corpus, never re-fetching.
---

# Context

A 2026-05-30 audit established the honest state of "ingest the fiscal
flows of every government in the world, analyze them with an LLM,
visualize them, and persist them via the kotoba (Datomic-style) API":

1. **The global fiscal INGEST substrate already exists and is
   W1-landed.** ADR-2605263900 ("Global open-government-data ingestion")
   pins worldwide fiscal sources to IPFS via
   `kotodama.organism.sensors.gov.*`, passive-only:
   - **budget / spending** — `gov/budget/usa/usaspending-gov/`,
     `gov/budget/eu/financial-transparency/`, `gov/budget/jpn/yosan/`,
     `gov/budget/gbr/treasury/` (USAspending / EU FTS / 予算書 / HM
     Treasury OSCAR);
   - **procurement** — `gov/procurement/{eu/ted,usa/sam-gov,
     jpn/chotatsu-portal,gbr/contracts-finder}/`;
   - **inter-governmental statistics / flows** —
     `gov/statistics/{worldbank-open-data,imf-sdmx,oecd-stat,un-data}/`
     (World Bank / IMF SDMX / OECD.Stat / UN data).

2. **danjo cross-references that corpus into kotoba EAVT, but does not
   visualize and is JP-first.** danjo (ADR-2605301600) is the
   non-adjudicating cross-reference engine: it ingests the corpus into
   kotoba datoms and emits `discrepancyObservation` + `oversightReport`.
   But (a) at R0 it is Japan-first (jurisdiction `jpn`), and (b)
   **visualization is an explicit danjo non-goal** — danjo is a
   cross-reference engine + textual publication organ, not a renderer.

3. **No actor combines ingest + LLM analysis + visualization + kotoba
   persistence.** The four capabilities are split: ingest lives in the
   cold-path IPFS substrate; cross-reference + kotoba-persist live in
   danjo (JP-first); LLM inference is available fleet-wide (Murakumo);
   visualization exists only for geospatial (`maps`) and 3D
   (`kami-engine`) domains, never for fiscal flows.

4. **The persistence target must be kotoba, not a parallel store.** Per
   ADR-2605262130 the canonical substrate is kotoba (content-addressed
   Datalog; EAVT/AEVT/AVET/VAET arrangements via kotoba-kqe; Kotoba/Datomic /
   Postgres / Lance prohibited as primary store or read backend). The
   `maps` actor's Kotoba/Datomic backend is therefore NOT a usable template
   for fiscal-flow persistence; kanae must build its flow graph as kotoba
   datoms, exactly as danjo (ADR-2605301600) and tadori (ADR-2605301400)
   do.

The gap is a **single kotoba-native fiscal-flow ASSEMBLY + Murakumo-LLM
NARRATIVE + kami-engine WASM VISUALIZATION actor** over the global
open-government corpus and the danjo cross-reference graph. This ADR
names it `kanae` (鼎).

## Constitutional sensitivity (why this needs the danjo bounds, plus two more)

An actor that visualizes "the money flows of every government" sits on
the same three constitutional invariants as danjo, and must inherit all
of danjo's discipline, plus two visualization-specific bounds:

- **§1.12 routing-around state function** is permitted ONLY as
  **Transparent Religious Force** (full on-chain log + open-source +
  1 SBT = 1 vote). kanae's visualizations are open-source and
  reproducible from public kotoba datoms; it is never a proprietary
  intelligence dashboard.
- **§2(c) covert-ops avoidance** forbids a surveillance posture. kanae
  visualizes only **pre-published public fiscal records** (via danjo /
  the corpus), never live monitoring, never per-individual targeting.
- **UPL-equivalent non-adjudication** (danjo G4 / chigiri G14 / toritate
  G5) forbids rendering a legal conclusion. kanae's Murakumo-LLM
  `flowNarrative` states **factual, source-cited descriptions** of the
  flow graph — never an allegation that a crime / 不正 / violation
  occurred. A legal verdict is unrepresentable at the schema layer.
- **(viz-specific) §2(e) anti-gatekeeping** — the visualization must be a
  public good, not a paywalled BI product. kanae is NOT a Palantir /
  Bloomberg-terminal / GovWin-class fusion dashboard; its render output
  is Apache-2.0 + Charter Rider and reproducible by anyone from the same
  public kotoba datoms.
- **(viz-specific) advertising / analytics boundary** — the render path
  (kami-engine WASM) carries NO third-party ad / analytics SDK (GA4 /
  Meta Pixel / affiliate), per the Substrate boundary Advertising row.

kanae makes the public fiscal record legible and weighs it openly —
鼎の軽重を問う — but it holds no coercive power, names no individual
beyond what the source records already name, and adjudicates nothing.

# Decision

Create **`kanae`** (鼎), DID `did:web:kanae.etzhayyim.com`, namespace
`com.etzhayyim.kanae.*`, as a **Tier-B kotoba-native global fiscal-flow
visualization actor** in **R0 scaffold**. Global in architecture from
R0 (jurisdiction-generic), with the same JP-first → multi-jurisdiction
activation ramp as danjo (the underlying corpus and danjo cross-reference
graph globalize on the same schedule, ADR-2605302245).

## §1 — Scope

kanae is a **fiscal-flow assembly + narrative + visualization substrate**
over the open-government corpus (ADR-2605263900) and the danjo
cross-reference graph (ADR-2605301600 + ADR-2605302245). It:

1. **Assembles** worldwide fund flows into **kotoba EAVT** as
   `fundFlowEdge` datoms — it does NOT re-fetch from government portals;
   it reads the IPFS-pinned `gov.dataset.*` budget / procurement /
   statistics records and the danjo `crossReferenceLink` / budget-ledger
   datoms already produced upstream (G3 passive-only). The flow graph
   covers the full domestic chain (appropriation → outlay → subaward →
   procurement-award → recipient) AND inter-governmental flows
   (IMF / World Bank / OECD / UN transfers, aid disbursements, loans).
2. **Narrates** flow subgraphs with **Murakumo-only LLM** (G7) into
   `flowNarrative` records — factual, source-cited, NON-adjudicating
   descriptions (e.g. "in FY2024 this appropriation line disbursed to
   these top-5 recipient classes; the inter-governmental column shows
   this IMF SDR allocation routed to this sovereign account") — never a
   verdict.
3. **Compiles** aggregate-first **kami-engine WASM** visualizations
   (`visualizationManifest`) — Sankey fund-flow diagrams, recipient
   concentration treemaps, a globe of inter-governmental transfers —
   each referencing the kotoba EAVT query that reproduces it.
4. **Publishes** Council-attested, IPFS-pinned visualization artifacts
   for member + public consumption.

## §2 — Architecture (5 Pregel cells, R0 path-reserved)

All cells path-reserved at R0 under `40-engine/kotoba/crates/kotoba-kotodama/cells/kanae_*/`;
each is import-time `RuntimeError("kanae R0 scaffold: activate via
Council ADR + R1 ratification")` at W1 creation.

| Cell | Node | Phase | I/O |
|---|---|---|---|
| `kanae_flow_assembler` | reuben | continuous | danjo `budget_ledger` + `procurement_graph` datoms + `gov.dataset.{budgetRecord,procurementRecord}` → kotoba EAVT `fundFlowEdge` datoms (domestic full chain: appropriation ↔ outlay ↔ subaward ↔ award ↔ recipientLei) |
| `kanae_intergov_flow` | reuben | continuous | `gov.dataset.statisticsObservation` (IMF SDMX / World Bank / OECD / UN) → `fundFlowEdge` datoms (flowClass = intergovernmental-transfer / aid-disbursement / loan; donor-juris ↔ recipient-juris ↔ instrument ↔ amount ↔ period) |
| `kanae_flow_narrative` | gad | continuous | `fundFlowEdge` subgraph → Murakumo-LLM `flowNarrative` (factual, source-cited, NON-adjudicating; G4 + G5 + G7) |
| `kanae_viz_compiler` | gad | periodic (event) | `fundFlowEdge` subgraph + `flowNarrative` → `visualizationManifest` (kami-engine WASM scene; aggregate-first; each manifest carries the reproducing kotoba-kqe query) |
| `kanae_publish` | naphtali | periodic (event) | aggregate `visualizationManifest` → published IPFS-pinned artifact + Council Lv6+ ≥3 attestation chain |

Cells communicate via `com.etzhayyim.kanae.*` lexicon records on MST;
the fund-flow graph lives in kotoba QuadStore (EAVT) per ADR-2605262130.
No Kotoba/Datomic, no projection layer. Murakumo node assignment mirrors
danjo (reuben ingest / gad analysis / naphtali publish).

## §3 — Lexicons (`com.etzhayyim.kanae.*`)

| Lexicon | Purpose |
|---|---|
| `fundFlowEdge` | One typed fiscal flow edge in the kotoba graph: `(sourceEntity → targetEntity, amount, currency, period, jurisdiction[s], flowClass)`. `flowClass` enum is descriptive ONLY (appropriation / outlay / subaward / procurement-award / intergovernmental-transfer / aid-disbursement / loan / repayment) — no value implies wrongdoing. Mandatory `sourceRecordCids[]` (≥2, G5). `stateAlignedFlag` pass-through (G13). |
| `flowNarrative` | Murakumo-LLM-generated factual description of a flow subgraph. Mandatory `nonAdjudicatingNotice` boolean=true (G4); mandatory `sourceRecordCids[]` (≥2, G5); mandatory `methodNoteCid` (G6); mandatory `murakumoInferenceAttestation` (G7 — records the Murakumo node + model; a vendor-LLM origin is unrepresentable). |
| `visualizationManifest` | kami-engine WASM scene descriptor: render type (sankey / treemap / globe-transfer / timeline), the `fundFlowEdgeCids[]` it renders, and the `kotobaQuery` (kqe arrangement) that reproduces it from public datoms (G2 + §2(e) reproducibility). Aggregate-first (G10); named parties only via `#namedPartyRef` citing the public source record. NO ad/analytics SDK reference permitted (G15). |
| `methodNote` | Open, versioned definition of one aggregation / narrative-prompt heuristic (the public audits the aggregation, not only the picture). Mirrors danjo's `methodNote` discipline. |

## §4 — Constitutional gates (G1–G15, IMMUTABLE R0–R3)

Council Lv6+ supermajority + new ADR to amend. G1–G13 are the danjo
gate set, inherited verbatim in spirit; G14–G15 are
visualization-specific.

- **G1** Charter Rider §2(a)–(h) scan on every published narrative + manifest + artifact.
- **G2** kotoba attestation lineage on every record; the flow graph lives in kotoba EAVT — **Kotoba/Datomic / Postgres / Lance / DuckDB / SQLite PROHIBITED** as primary store or read backend (ADR-2605262130). The `maps` Kotoba/Datomic backend is NOT a template.
- **G3** **Passive-only / upstream-only** — kanae reads ONLY the pre-published, IPFS-pinned `gov.dataset.*` corpus and the danjo datoms. NO live portal scraping, NO per-query API, NO non-public sources, NO whistleblower intake (§2(c)).
- **G4** **NON-adjudicating** (UPL-equivalent) — every `flowNarrative` carries `nonAdjudicatingNotice=true` and states FACTUAL descriptions only. kanae MUST NOT assert that a crime / 不正 / violation occurred. The `flowClass` enum carries no verdict token. Legal characterization routes to external counsel via chigiri + Public Fund (Council Lv6+).
- **G5** **Source-provenance mandatory** — every `fundFlowEdge` and `flowNarrative` cites ≥2 upstream `gov.dataset.*` / danjo record CIDs. No inference-only flow; no narrative without primary-public-record citation.
- **G6** **Open method** — every aggregation + narrative-prompt heuristic is published as a `methodNote` (open, versioned). No closed / secret scoring.
- **G7** **Murakumo-only inference** (ADR-2605215000) — the `flowNarrative` LLM analysis runs on the Murakumo fleet ONLY (LiteLLM 127.0.0.1:4000 / EVO-X2 LAN / per-node Ollama). NO vendor LLM callout. `murakumoInferenceAttestation` is mandatory on every narrative; a vendor-origin narrative is unrepresentable at the schema layer.
- **G8** **No commercial gov-intelligence terminals** — GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro / FiscalNote / CQ Roll Call Pro hostnames + SDK imports PROHIBITED (§2(e) anti-gatekeeping). Deny-list lint.
- **G9** **Per-jurisdiction publication-rule honoring** (inherits ADR-2605263900 §5) — NO unilateral re-identification beyond what the source publication already exposes. PII / GDPR DSARs route via `chigiri.data_privacy` to the upstream publisher; kanae NEVER unilaterally adds or removes PII.
- **G10** **Aggregate-first visualization** — every visualization is aggregate by default (recipient classes, program totals, juris-to-juris columns). A named-party element is permissible ONLY where the underlying public records already name the party AND it is severity-gated + Council-reviewed before named publication. NO per-individual targeting (anti-individualism ontology, N9).
- **G11** **Transparent Religious Force discipline** (§1.12) — kanae is assembly + narrative + visualization + publication ONLY. NO coercive action, NO referral to state coercion as an internal dependency, NO covert operation. 1 SBT = 1 vote governs named-party publication.
- **G12** **Read-only** — kanae never mutates upstream `gov.dataset.*` / danjo records nor any on-chain contract. Assembly + narrative + visualization + publication only.
- **G13** **stateAlignedFlag pass-through** — CN-class / state-aligned sources carry `stateAlignedFlag=true` into every derived `fundFlowEdge`, `flowNarrative`, and `visualizationManifest` (parallel to ADR-2605263900 §2(g)).
- **G14** **kami-engine WASM render-only** — the visualization render substrate is kami-engine WASM (ADR-2605261800), reproducible from public kotoba datoms. NO third-party BI engine (Tableau / Power BI / Looker / Palantir Foundry) as the render or fusion layer (§2(e)).
- **G15** **No ad / analytics SDK in the render path** — the WASM viewer carries NO GA4 / Meta Pixel / affiliate / third-party analytics SDK (Substrate boundary Advertising row). Lint-enforced over kanae render assets.

## §5 — Non-goals (N1–N14, EXCLUDED R0–R3)

- **N1** NOT a prosecutor / law-enforcement arm.
- **N2** NOT a court / adjudicator of guilt or of "violation".
- **N3** NOT a surveillance system (public-record only; no live monitoring of individuals).
- **N4** NOT a commercial gov-intelligence / fiscal-intelligence product (no GovWin / Bloomberg Government / FiscalNote / Palantir).
- **N5** NOT a whistleblower-intake / non-public-leak handler (only pre-published open data).
- **N6** NOT a state-granted legal personality (Preamble §0.4 Lv7+ unanimity lock).
- **N7** NOT a closed-source / secret-scoring or secret-aggregation engine (G6).
- **N8** NOT a partisan / electioneering tool (non-partisan; ad-free; no candidate endorsement).
- **N9** NOT a per-individual reputation / social-credit score (anti-individualism ontology; aggregate-first).
- **N10** NOT a replacement for the state's own audit organs (会計検査院 / GAO / ECA) — kanae routes-around by independent transparency, not by claiming official audit authority.
- **N11** NOT a defamation vector — G4 non-adjudication + G5 provenance + G10 aggregate-first structurally prevent unsubstantiated allegation.
- **N12** NOT a vendor-LLM inference path (Murakumo-only per G7).
- **N13** NOT a substrate-engine or projection-layer replacement (kotoba per ADR-2605262130 remains canonical; no Kotoba/Datomic like `maps`).
- **N14** NOT a third-party-BI / Palantir-class fusion dashboard (G14; render is kami-engine WASM, reproducible from public datoms).

## §6 — Cross-actor boundaries

| Actor / substrate | Direction | Purpose |
|---|---|---|
| **danjo** (ADR-2605301600 + ADR-2605302245) | → (read) | **Primary upstream**: danjo `budget_ledger` + `procurement_graph` + `crossReferenceLink` datoms are kanae's fiscal-flow source. **Boundary**: danjo = the non-adjudicating cross-reference ENGINE (discrepancy observations); kanae = the fiscal-flow ASSEMBLY + Murakumo NARRATIVE + WASM VISUALIZATION lens danjo lacks. danjo finds; kanae renders. |
| `gov.dataset.*` corpus (ADR-2605263900) | → (read) | budgetRecord / procurementRecord / statisticsObservation (IMF / WB / OECD / UN) — primary fiscal-flow input where danjo has not yet indexed a jurisdiction. |
| `corp.{leiReference,ownershipEdge}` (ADR-2605263800) | → (read) | recipient / awardee identity resolution for flow-edge endpoints. |
| **kami-engine** (ADR-2605261800) | ↔ | WASM render substrate (G14); kanae `visualizationManifest` compiles to a kami-engine scene reusing the isekai/omniverse WASM viewer assets. |
| **kotoba** (ADR-2605262130) | ↔ | EAVT QuadStore is where kanae builds its `fundFlowEdge` graph; kotoba-kqe arrangements for hot-path render queries. The Datomic-style persistence the user asked for. |
| **ossekai** (ADR-2605264000) | → | kanae aggregate visualizations feed ossekai §1.12 aggregate-anonymized publication. |
| **kataribe** (語部, press) | → | kanae visualization artifacts are citable primary-source graphics for press / publishing. |
| **toritate** (ADR-2605262900) | ∥ | Disjoint domain: toritate visualizes the religious-corp's OWN on-chain books; kanae visualizes the STATE's published fiscal flows. |
| **maps** (geospatial) | ∥ | Sibling visualization actor, disjoint domain (geo vs fiscal) and disjoint backend (maps = Kotoba/Datomic; kanae = kotoba EAVT per G2/N13). |

## §7 — Roadmap

| Phase | Timeline | Scope | Fleet | Gate |
|---|---|---|---|---|
| **R0** | 2026-05-30 | Scaffold (this commit): 5 cells path-reserved + 4 Lexicon skeletons + manifest + README + CLAUDE.md + open method seed + constitutional lint + test | none | ADR-2605302300 (PROPOSED) |
| **R1** | post-Bootstrap-Council + ≥1 Council Lv6+ ratify + danjo R1 (ADR-2605301600) ingest cells healthy | `kanae_flow_assembler` + `kanae_intergov_flow` build kotoba EAVT `fundFlowEdge` datoms (JP-first domestic chain + first global: USAspending / EU FTS / IMF / WB); `fundFlowEdge` + `methodNote` schemas Council-reviewed. NO narratives, NO published viz. | reuben | Council Lv6+ ≥3 |
| **R2** | post-R1 + 30-day public objection | + `kanae_flow_narrative` (Murakumo) + `kanae_viz_compiler`; first `flowNarrative` + first aggregate `visualizationManifest` (JP + global core); `flowNarrative` + `visualizationManifest` schemas Council-reviewed | reuben + gad | Council Lv6+ ≥4 + 30-day public comment |
| **R3** | post-R2 + Council Lv7+ unanimity | + `kanae_publish`; first published global fiscal-flow visualization (multi-jurisdiction + inter-governmental); named-party element path (G10) battle-tested under 1 SBT = 1 vote | naphtali (full fleet) | Council Lv7+ unanimity |

## §8 — R0 deliverables landed (session 2026-05-30)

R0 is intentionally minimal — no cells run, no data flows, nothing
infers or renders until Council ratification. Beyond the bare scaffold,
this session ships the **constitutional anchors made structural and
machine-checkable**, so the gates cannot silently regress before the
actor is ever switched on:

1. **Actor scaffold** — `90-docs/adr/2605302300-…` (this ADR) +
   `20-actors/kanae/{manifest.jsonld, README.md, CLAUDE.md}` + 4 Lexicon
   skeletons under `00-contracts/lexicons/com/etzhayyim/kanae/`.
2. **Non-adjudication made structural (G4)** — `flowNarrative.nonAdjudicatingNotice`
   is `const:true`; the `flowClass` enum on `fundFlowEdge` is descriptive
   only and carries no verdict token (crime / violation / guilt / 不正).
3. **Murakumo-only made structural (G7)** — `flowNarrative` requires a
   `murakumoInferenceAttestation` object; a vendor-LLM origin is
   unrepresentable at the schema layer.
4. **Open aggregation seed (G6)** — `20-actors/kanae/methods/v1-global-seed.json`
   (global fund-flow aggregation + narrative-prompt heuristics, draft
   status, `councilAttestation: []`), each carrying mandatory
   `knownFalsePositiveModes` + a non-adjudication restatement.
5. **Constitutional lint + regression suite (G4 + G7 + G8 + G15)** —
   `70-tools/scripts/lint/no-kanae-adjudication.mjs` enforces structurally:
   (G4) `nonAdjudicatingNotice` `const:true` + no verdict token in the
   `flowClass` enum; (G7) `murakumoInferenceAttestation` required on
   `flowNarrative`; (G8) the commercial gov-intel terminal deny-list; and
   (G15) no ad/analytics SDK token over kanae code. A node `--test` suite
   pins each anchor against poisoned fixtures.
6. **Bidirectional integration** — `deps.toml` ADR + module registration;
   reciprocal cross-refs into `danjo` (the engine/visualizer boundary) and
   the `gov.dataset.*` corpus README (kanae registered as a fiscal-flow
   visualization consumer).

**Not done by R0 design**: cells are path-reserved, NOT created (matches
danjo / tadori R0 discipline); no `additionalProperties:false` closure;
no runtime inference, no rendering. These are R1+, gated on Council Lv6+
ratification post Bootstrap Council Seats 2-5 RFP close (2026-06-19) and
danjo R1.

# Consequences

**Positive.**

- Closes the audit gap with the missing fourth capability —
  visualization — paired with Murakumo narrative, on top of the existing
  ingest (ADR-2605263900) and cross-reference (danjo) substrates. The
  four user-named capabilities (ingest → LLM → visualize → kotoba
  persist) are now covered end-to-end by a clean
  corpus → danjo → kanae pipeline.
- kotoba-native by construction (EAVT `fundFlowEdge` datoms), consistent
  with ADR-2605262130; explicitly NOT Kotoba/Datomic (unlike `maps`), so the
  "datomic kotoba api で永続化" requirement is met structurally.
- Clean actor boundary: danjo finds (non-adjudicating cross-reference),
  kanae renders (narrative + visualization). Neither absorbs the other's
  constitutional identity.

**Costs / risks.**

- **Visualization-as-allegation risk.** A Sankey diagram can imply
  wrongdoing even where the narrative is factual. Mitigated by G4
  (non-adjudication) + G5 (provenance) + G10 (aggregate-first) +
  G11 (1 SBT = 1 vote on named-party elements); R0–R1 produce no
  narratives and no published visualizations at all.
- **LLM-narrative hallucination risk.** A Murakumo narrative could
  misstate a flow. Mitigated by G5 (≥2 source CIDs per narrative) +
  G6 (open method) + the danjo-style "factual cross-reference only"
  discipline; R2 narratives are Council-reviewed before publication.
- **Render-substrate coupling.** kami-engine WASM (G14) ties kanae to the
  kami-engine workspace; acceptable because it keeps the render
  open-source + reproducible from public datoms, which is the §2(e)
  requirement a third-party BI tool would violate.

**Neutral.**

- R0 is scaffold-only: no cells run, no narratives are produced, no
  visualizations are rendered until Council ratification + danjo R1.

# Alternatives Considered

1. **Extend danjo to also visualize (no new actor).** Rejected:
   visualization is a constitutional non-goal of danjo (it is a
   cross-reference engine + textual publication organ). Folding a
   renderer + an LLM-narrative path into danjo would muddy its
   non-adjudication identity and overload one actor. A clean
   engine/renderer boundary is better — this is the (1)+(2) split the
   user chose (danjo extension = ADR-2605302245; kanae = this ADR).
2. **Reuse the `maps` actor (MapLibre + Kotoba/Datomic) for fiscal flows.**
   Rejected: `maps` persists to Kotoba/Datomic, prohibited as primary store
   by ADR-2605262130 (G2/N13). Fiscal-flow persistence must be kotoba
   EAVT — the user explicitly asked for "datomic kotoba api で永続化".
   kami-engine WASM render over kotoba datoms satisfies both the render
   and the persistence requirements.
3. **Static SVG / chart artifacts only (no WASM engine).** Rejected per
   user selection (kami-engine WASM), and because reusing the existing
   isekai/omniverse WASM viewer assets gives interactive, reproducible,
   open-source visualization consistent with G14 + §2(e).
4. **Use a commercial fiscal-intelligence terminal / BI tool.**
   Rejected — fatal: CONSTITUTIONALLY PROHIBITED per §2(e) anti-gatekeeping
   (G8 / G14). The visualization must be a public good reproducible from
   public datoms, not a paywalled product.
5. **Let kanae's narrative render "violation" conclusions.** Rejected —
   fatal: violates UPL-equivalent non-adjudication + §1.12. G4 makes a
   legal verdict unrepresentable at the schema layer.

# References

- `/90-docs/adr/2605302245-danjo-global-fiscal-flow-extension.md` — danjo global fund-flow extension (sibling direction (1); upstream)
- `/90-docs/adr/2605301600-danjo-public-accountability-oversight-tier-b-actor-r0.md` — danjo (cross-reference engine; primary upstream)
- `/90-docs/adr/2605263900-public-data-open-government-ipfs-ingestion.md` — global open-government corpus (fiscal-flow input)
- `/90-docs/adr/2605262130-kotoba-storage-substrate-unification.md` — kotoba substrate (EAVT, no Kotoba/Datomic)
- `/90-docs/adr/2605261800-nvidia-omniverse-compat-kami-engine.md` — kami-engine (WASM render substrate, G14)
- `/90-docs/adr/2605192100-etzhayyim-mission-charter.md` — §1.12 Transparent Religious Force + §2(c) covert-ops avoidance + §2(e) anti-gatekeeping
- `/90-docs/adr/2605192200-etzhayyim-ip-free-release-charter-rider.md` — Charter Rider §2(c)/(e)
- `/90-docs/adr/2605215000-etzhayyim-inference-murakumo-only-no-runpod.md` — Murakumo-only inference (G7)
- `/20-actors/kanae/` — manifest + README + CLAUDE.md
- `/CHARTER-RIDER.md` — License + Rider canonical text
- `/CLAUDE.md` — Religious-corp status table
