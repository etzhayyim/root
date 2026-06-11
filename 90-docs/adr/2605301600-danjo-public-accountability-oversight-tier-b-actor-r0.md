---
id: adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
title: "ADR-2605301600: 弾正 (danjo) — kotoba-native public-accountability oversight Tier-B actor that ingests Diet statements + budget + procurement and emits non-adjudicating discrepancy observations (R0 scaffold)"
status: proposed
doc_type: adr
topic: danjo-public-accountability-oversight-actor
authoritative: true
last_verified: 2026-05-30
priority: 8.0
axis: actor-architecture
weight: 0.80
priority_note: "Names a new Tier-B actor (danjo) as the kotoba-EAVT-native cross-reference + transparency-publication organ over the already-pinned open-government corpus (ADR-2605263900). Answers the 2026-05-30 audit: the JP government corpus (国会会議録 / 予算書 / 政府調達) is ingested, but NO single actor cross-references it to surface 不正 / 違反. danjo is that actor — strictly bounded as the 'censor's eye without the censor's sword': observation + transparent publication ONLY, NON-adjudicating (UPL-equivalent), passive-only, open-method, Murakumo-only, Transparent-Religious-Force-disciplined (ADR-2605192100 §1.12)."
authoritative_for:
  - new Tier-B actor `danjo` (public-accountability oversight; civic transparency cross-reference)
  - kotoba-kqe EAVT datom schema for official / statement / authority / award / appropriation / outlay / entity / cross-reference-link / discrepancy-observation
  - the boundary between toritate (religious-corp's OWN on-chain books) and danjo (the STATE's published open-data books)
  - `com.etzhayyim.danjo.*` Lexicon namespace (discrepancyObservation / crossReferenceLink / oversightReport / methodNote)
depends_on:
  - adr-2605263900-public-data-open-government-ipfs-ingestion
  - adr-2605262130-kotoba-storage-substrate-unification
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
  Session 2026-05-30: user asked "日本政府のすべての国会での発言、会計、調達履歴を
  すべて kotoba に ingest して、不正や違反がないかを特定する actor は設計されている?".
  Audit (Explore agent) found PARTIAL: the ingestion substrate exists and is W1-landed
  (ADR-2605263900 — JP 国会会議録 / 予算書 / 政府調達 / e-Stat / data.go.jp pinned to IPFS,
  written by kotodama.organism.sensors.gov.*), and three actors consume parts of it
  (toritate = anti-related-party for ITS OWN tithe-recipient vendors only; chigiri = cites
  state procedure as routing-around evidence; ossekai = aggregate transparency publication),
  but NO single actor was designed to cross-reference the WHOLE corpus to surface 不正 / 違反.
  This ADR proposes that actor. The name 弾正 (Danjō, the Nara/Heian 律令制 Censorate /
  弾正台 Danjōdai that monitored official misconduct) is deliberately framed WITHOUT its
  historical coercive power: danjo holds the censor's eye, never the censor's sword.
---

# Context

A 2026-05-30 audit established the honest state of "ingest all Japanese
government Diet statements, accounting and procurement into kotoba and
identify fraud / violations":

1. **The ingestion substrate already exists and is W1-landed.**
   ADR-2605263900 ("Open-government-data ingestion via IPFS-pinned
   DataLad subdatasets") explicitly pins the Japanese corpus:
   - **国会会議録検索** → `gov/parliament/jpn/kokkai-kaigiroku/`
     (`com.etzhayyim.gov.dataset.parliamentRecord`, `gov_parliament_sensor`)
   - **政府調達情報ポータル** → `gov/procurement/jpn/chotatsu-portal/`
     (`com.etzhayyim.gov.dataset.procurementRecord`, `gov_procurement_sensor`)
   - **予算書** → `gov/budget/jpn/yosan/`
     (`com.etzhayyim.gov.dataset.budgetRecord`, `gov_budget_sensor`)
   - **data.go.jp + e-Stat** → `gov/open-data/jpn/{data-go-jp,e-stat}/`
     (`openDatasetAttestation` / `statisticsObservation`)
   All are Tier-A (CC-BY 4.0 per 政府標準利用規約 2.0), fetched
   **passive-only** (pre-published bulk archives; no live scraping).

2. **No single actor cross-references the whole corpus to surface
   anomalies.** The function was distributed across three actors, each
   covering only a slice:
   - **toritate** (ADR-2605262900) runs an anti-related-party check —
     but only against the religious-corp's OWN tithe-recipient vendors,
     not against the state's spending at large.
   - **chigiri** (ADR-2605262700) cites publicly-recorded state
     procedure as routing-around evidence — but is a procedural /
     templating substrate, not a cross-reference engine, and is
     UPL-bound (no legal characterization).
   - **ossekai** (ADR-2605264000) publishes aggregate-anonymized
     transparency evidence — but is a downstream publication organ, not
     the engine that computes the cross-references.

3. **The ingestion target must be kotoba, not a parallel store.**
   Per ADR-2605262130 the canonical substrate is kotoba (content-
   addressed Datalog + Pregel; EAVT/AEVT/AVET/VAET arrangements via
   kotoba-kqe; Kotoba/Datomic / Postgres / Lance prohibited as primary
   store or read backend). Any "ingest into kotoba" actor must build its
   cross-reference graph as kotoba datoms, exactly as tadori
   (ADR-2605301400) does for on-chain tracing.

The gap is therefore a **single kotoba-native cross-reference +
transparency-publication actor** over the open-government corpus. This
ADR names it `danjo` (弾正).

## Constitutional sensitivity (why this needs explicit bounds)

An actor that "identifies fraud and violations" in government records
sits directly on three constitutional invariants and must be bounded by
all of them, or it must not exist:

- **§1.12 routing-around state function** is permitted ONLY as
  **Transparent Religious Force** (full on-chain log + open-source +
  1 SBT = 1 vote). danjo therefore cannot be a covert or proprietary
  watchdog.
- **§2(c) covert-ops avoidance** (Charter Rider) forbids surveillance
  posture. danjo therefore operates on **pre-published public records
  only** — never live monitoring of individuals, never non-public
  leaks, never per-query tracking.
- **UPL-equivalent discipline** (chigiri G14 / toritate G5) forbids the
  religious-corp from rendering a legal conclusion. danjo therefore
  emits **factual, source-cited, NON-adjudicating discrepancy
  observations** — never a verdict that a crime or violation occurred.
  Legal characterization is routed to external counsel via chigiri +
  Public Fund (Council Lv6+).

danjo is the **censor's eye, never the censor's sword**: it makes the
state's own published records legible and cross-referenced, and
publishes that transparently. It holds no coercive power, refers to no
state coercion as an internal dependency, and adjudicates nothing.

# Decision

Create **`danjo`** (弾正), DID `did:web:danjo.etzhayyim.com`, namespace
`com.etzhayyim.danjo.*`, as a **Tier-B kotoba-native public-
accountability oversight actor** in **R0 scaffold**. Japan-first at R0
(jurisdiction `jpn`), jurisdiction-generic in architecture (extends to
any jurisdiction the corpus covers, exactly like ADR-2605263900).

## §1 — Scope

danjo is a **cross-reference + transparency-publication substrate** over
the open-government corpus (ADR-2605263900). It:

1. **Ingests** the already-pinned JP corpus (国会会議録 / 予算書 /
   政府調達 / e-Stat) into **kotoba EAVT** as datoms — it does NOT
   re-fetch from government portals; it reads the IPFS-pinned
   `com.etzhayyim.gov.dataset.*` records that `kotodama.organism.
   sensors.gov.*` already produced (G3 passive-only).
2. **Cross-references** those datoms with each other and with the corp
   identity registry (`com.etzhayyim.corp.{leiReference,ownershipEdge}`,
   ADR-2605263800) to build typed `crossReferenceLink` edges.
3. **Emits** `discrepancyObservation` records — factual, source-cited,
   NON-adjudicating anomalies (e.g. an awardee winning N consecutive
   single-bid tenders from one authority; an awardee UBO-linked to a
   contracting official per public registry; a Diet-floor statement
   inconsistent with the published outlay it references).
4. **Publishes** periodic aggregate `oversightReport` records (Council-
   attested, IPFS-pinned) for member + public consumption.

## §2 — Architecture (6 Pregel cells, R0 path-reserved)

All cells path-reserved at R0 under `40-engine/kotoba/crates/kotoba-kotodama/cells/danjo_*/`;
each is import-time `RuntimeError("danjo R0 scaffold: activate via
Council ADR + R1 ratification")` at W1 creation.

| Cell | Node | Phase | I/O |
|---|---|---|---|
| `danjo_diet_statement_index` | reuben | continuous | `gov.dataset.parliamentRecord` (JP 国会会議録) → kotoba EAVT datoms (member ↔ statement ↔ topic ↔ session ↔ date) |
| `danjo_procurement_graph` | reuben | continuous | `gov.dataset.procurementRecord` (JP 政府調達) → datoms (authority ↔ award ↔ awardeeLei ↔ amount ↔ date) |
| `danjo_budget_ledger` | reuben | continuous | `gov.dataset.budgetRecord` (JP 予算書) → datoms (appropriation ↔ outlay ↔ recipientLei ↔ program) |
| `danjo_crossref_engine` | gad | continuous | join the three indices + `corp.ownershipEdge` (UBO) + `corp.leiReference` → `crossReferenceLink` edges + candidate `discrepancyObservation` |
| `danjo_statement_consistency` | gad | continuous | cross-ref Diet statements vs budget/procurement reality → `discrepancyObservation` (statement-vs-record divergence) |
| `danjo_oversight_report` | naphtali | periodic (event) | aggregate observations → `oversightReport` + Council Lv6+ ≥3 attestation chain |

Cells communicate via `com.etzhayyim.danjo.*` lexicon records on MST;
the cross-reference graph lives in kotoba QuadStore (EAVT) per
ADR-2605262130. No Kotoba/Datomic, no projection layer.

## §3 — Lexicons (`com.etzhayyim.danjo.*`)

| Lexicon | Purpose |
|---|---|
| `discrepancyObservation` | Factual, source-cited, NON-adjudicating anomaly. `severity` enum; mandatory `sourceRecordCids[]` (≥2, G5); mandatory `methodNoteCid` (G6); mandatory `nonAdjudicatingNotice` boolean=true (G4). |
| `crossReferenceLink` | Typed factual edge between two gov.dataset records (or a gov.dataset record and a corp registry entity), citing the public basis of the link. |
| `oversightReport` | Periodic aggregate transparency report; Council Lv6+ ≥3 attestation chain; IPFS-pinned (G replication ≥2). |
| `methodNote` | Open, versioned definition of one detector heuristic (the public can audit the detector itself). Analogous to toritate's open valuation reference tables. |

## §4 — Constitutional gates (G1–G13, IMMUTABLE R0–R3)

Council Lv6+ supermajority + new ADR to amend.

- **G1** Charter Rider §2(a)–(h) scan on every published observation + report.
- **G2** kotoba attestation lineage on every record.
- **G3** **Passive-only ingestion** — danjo reads ONLY the pre-published,
  IPFS-pinned `gov.dataset.*` corpus (ADR-2605263900). NO live portal
  scraping, NO per-query API hits, NO non-public sources, NO whistleblower
  intake. (Charter Rider §2(c) covert-ops avoidance.)
- **G4** **NON-adjudicating** (UPL-equivalent; chigiri G14 / toritate G5)
  — every `discrepancyObservation` carries `nonAdjudicatingNotice=true`
  and states a FACTUAL cross-reference only. danjo MUST NOT assert that a
  crime / law violation / 不正 occurred. Legal characterization routes to
  external counsel via chigiri + Public Fund (Council Lv6+).
- **G5** **Source-provenance mandatory** — every observation cites ≥2
  upstream `gov.dataset.*` record CIDs. No inference-only allegation; no
  observation without primary-public-record citation.
- **G6** **Open method** — every detector heuristic is published as a
  `methodNote` (open, versioned). No closed / secret scoring. The public
  can audit the detector, not only its output.
- **G7** Murakumo-only inference (ADR-2605215000). No vendor LLM callout.
- **G8** **No commercial gov-intelligence terminals** — GovWin IQ /
  Bloomberg Government / Politico Pro / E&E News Pro / FiscalNote / CQ
  Roll Call Pro hostnames + SDK imports PROHIBITED (Charter Rider §2(e)
  anti-gatekeeping). Deny-list lint integration.
- **G9** **Per-jurisdiction publication-rule honoring** (inherits
  ADR-2605263900 G3) — NO unilateral re-identification beyond what the
  source publication already exposes. 個人情報 / GDPR DSARs route via
  `chigiri.data_privacy` to the upstream publisher; danjo NEVER
  unilaterally adds or removes PII.
- **G10** **Aggregate-first + severity-gated naming** — `oversightReport`
  publishes aggregate patterns by default. A named-party observation is
  permissible ONLY where the underlying public records already name the
  party (procurement awardees / Diet members on the record / budget
  recipients) AND it is severity-gated + Council-reviewed before named
  publication.
- **G11** **Transparent Religious Force discipline** (§1.12) — danjo is
  observation + transparent publication ONLY. NO coercive action, NO
  referral to state coercion as an internal dependency, NO covert
  operation. 1 SBT = 1 vote governs what is published as a named-party
  report.
- **G12** **Read-only** — danjo never mutates upstream `gov.dataset.*`
  records nor any on-chain contract. Observation + publication only.
- **G13** **stateAlignedFlag pass-through** — CN-class / state-aligned
  sources carry `stateAlignedFlag=true` into every derived publication
  (parallel to ADR-2605263900 §2(g) + ADR-2605262800).

## §5 — Non-goals (N1–N12, EXCLUDED R0–R3)

- **N1** NOT a prosecutor / law-enforcement arm.
- **N2** NOT a court / adjudicator of guilt or of "violation".
- **N3** NOT a surveillance system (public-record only; no live
  monitoring of individuals).
- **N4** NOT a commercial gov-intelligence product (no GovWin /
  Bloomberg Government / FiscalNote).
- **N5** NOT a whistleblower-intake / non-public-leak handler (only
  pre-published open data).
- **N6** NOT a state-granted legal personality (Preamble §0.4 Lv7+
  unanimity lock).
- **N7** NOT a closed-source / secret-scoring engine (G6).
- **N8** NOT a partisan / electioneering tool (non-partisan; ad-free;
  no candidate endorsement).
- **N9** NOT a per-individual reputation / social-credit score
  (anti-individualism ontology; aggregate-first).
- **N10** NOT a replacement for the state's own audit organs (会計検査院
  etc.) — danjo routes-around by independent transparency, not by
  claiming official audit authority.
- **N11** NOT a defamation vector — G4 non-adjudication + G5 provenance +
  G10 severity-gating structurally prevent unsubstantiated allegation.
- **N12** NOT Japan-exclusive in architecture (JP-first at R0;
  jurisdiction-generic like the corpus).

## §6 — Cross-actor boundaries

| Actor / substrate | Direction | Purpose |
|---|---|---|
| `gov.dataset.*` corpus (ADR-2605263900) | → (read) | Primary input: parliamentRecord / budgetRecord / procurementRecord / statisticsObservation / openDatasetAttestation |
| `corp.{leiReference,ownershipEdge}` (ADR-2605263800) | → (read) | Entity / UBO resolution for cross-reference links |
| **toritate** (ADR-2605262900) | ↔ | **Boundary**: toritate = the religious-corp's OWN on-chain books; danjo = the STATE's published books. Cross-reference where a vendor appears in both (toritate already flags tithe-recipient vendors; danjo supplies the state-side procurement/budget context). |
| **chigiri** (ADR-2605262700) | → | Legal-characterization + external-counsel routing for any observation needing legal opinion (UPL boundary, G4); `chigiri.data_privacy` for DSARs (G9). |
| **ossekai** (ADR-2605264000) | → | danjo `oversightReport` feeds ossekai aggregate-anonymized §1.12 publication. |
| **kataribe** (語部, press) | → | danjo `oversightReport` is a citable primary source for press / publishing. |
| **kotoba** (ADR-2605262130) | ↔ | EAVT QuadStore is where danjo builds its cross-reference graph; kotoba-kqe arrangements for hot-path queries. |
| **tadori** (ADR-2605301400) | ∥ | Sibling kotoba-native investigation actor (tadori = on-chain crypto tracing; danjo = public-record civic oversight). Shared EAVT pattern, disjoint domains. |

## §7 — Roadmap

| Phase | Timeline | Scope | Fleet | Gate |
|---|---|---|---|---|
| **R0** | 2026-05-30 | Scaffold (this commit): 6 cells path-reserved + 4 Lexicon skeletons + manifest + README + CLAUDE.md | none | ADR-2605301600 (PROPOSED) |
| **R1** | post-Bootstrap-Council + ≥1 Council Lv6+ ratify | 3 ingest cells (diet_statement_index / procurement_graph / budget_ledger) build kotoba EAVT datoms over the JP corpus; `crossReferenceLink` + `methodNote` schemas Council-reviewed | reuben | Council Lv6+ ≥3 |
| **R2** | post-R1 + 30-day public objection | + `danjo_crossref_engine` + `danjo_statement_consistency`; first `discrepancyObservation` records (JP-first); `discrepancyObservation` schema Council-reviewed | reuben + gad | Council Lv6+ ≥4 + 30-day public comment |
| **R3** | post-R2 + Council Lv7+ unanimity | + `danjo_oversight_report`; first aggregate `oversightReport` (JP FY) published; named-party publication path (G10) battle-tested under 1 SBT = 1 vote; multi-jurisdiction extension | naphtali (full fleet) | Council Lv7+ unanimity |

## §8 — R0 deliverables landed (session 2026-05-30)

R0 is intentionally minimal — no cells run, no data flows, nothing
infers until Council ratification. What this session actually shipped,
beyond the bare scaffold, are the **constitutional anchors made
structural and machine-checkable**, so the gates cannot silently
regress before the actor is ever switched on:

1. **Actor scaffold** — `90-docs/adr/2605301600-…` (this ADR) +
   `20-actors/danjo/{manifest.jsonld, README.md, CLAUDE.md}` + 4
   Lexicon skeletons under `00-contracts/lexicons/com/etzhayyim/danjo/`.
2. **Ref-hardened lexicons (G10 made structural)** —
   `discrepancyObservation` gains `#namedPartyRef` (a party is nameable
   ONLY by citing the public source record that already names them, with
   `publiclyNamedBasis`); `oversightReport` gains `#aggregateStat`
   (aggregate-only, N9) + `#namedPartyEntry` (whose `councilReviewCid` +
   `oneSbtOneVoteChainCid` are REQUIRED — an entry cannot publish without
   both gate proofs). `additionalProperties:false` closure deferred to R1
   per the repo-wide convention.
3. **Open detector seed (G6)** — `20-actors/danjo/methods/v1-jp-seed.json`
   (6 JP-first methods, draft status, `councilAttestation: []`), each
   carrying mandatory `knownFalsePositiveModes`. Every `appliesToCategory`
   is verified ⊆ the `discrepancyObservation` category enum.
4. **Constitutional lint + regression suite (G4 + G8)** —
   `70-tools/scripts/lint/no-danjo-adjudication.mjs` enforces, structurally:
   (G4) `nonAdjudicatingNotice` is `const:true` and the observation
   `category` enum carries no verdict token (crime/violation/guilt/…); and
   (G8) the commercial gov-intel terminal deny-list (GovWin / Bloomberg
   Government / FiscalNote / …) over danjo *code* (docs that enumerate the
   deny-list are exempt by extension). The 8-test
   `no-danjo-adjudication.test.mjs` suite pins both anchors against
   poisoned fixtures (all green).
5. **Bidirectional integration** — `deps.toml` ADR + module registration;
   reciprocal cross-refs into `toritate` (boundary) and `tadori` (disjoint
   kotoba-EAVT sibling); danjo registered as PRIMARY consumer in the
   `gov.dataset.*` corpus README. Repo-wide lexicon lints
   (`nsid-lexicon-exists` / `lexicon-primary-types` /
   `nsid-lexicon-registration`) green; `NSID_APP_ETZHAYYIM_DANJO_*`
   collision-free against ~6.7k existing lexicons.

**Not done by R0 design**: cells are path-reserved, NOT created (matches
the toritate/chigiri R0 discipline); no `additionalProperties:false`
closure; no runtime inference. These are R1+, gated on Council Lv6+
ratification post Bootstrap Council Seats 2-5 RFP close (2026-06-19).

# Consequences

**Positive.**

- Closes the audit gap with a single, named, constitutionally-bounded
  actor instead of a diffuse "toritate + chigiri + ossekai" partial
  coverage.
- kotoba-native by construction (EAVT datoms), consistent with
  ADR-2605262130 and the tadori precedent (ADR-2605301400); no parallel
  store.
- The G4 non-adjudication + G5 provenance + G6 open-method triad makes
  the actor defensible: it surfaces *facts the state already published*,
  cited, with an openly-auditable method, and never renders a verdict.

**Costs / risks.**

- **Defamation / political-weaponization risk** is the dominant risk. It
  is mitigated structurally (G4/G5/G6/G10/G11) but R2 named-party
  publication needs careful Council review; R0–R1 produce no named
  allegations at all.
- **Scope creep toward surveillance.** G3 (passive-only, public-record
  only) + N3/N5 are the hard wall; any future "live monitoring" or
  "leak intake" proposal requires a separate ADR and would likely
  violate §2(c).
- The name 弾正 carries historical coercive connotation; §1.12/G11 strip
  the coercive power explicitly. This must be restated in every
  downstream doc to avoid mis-framing the actor as a prosecutorial organ.

**Neutral.**

- R0 is scaffold-only: no cells run, no observations are produced, no
  inference occurs until Council ratification.

# Alternatives Considered

1. **Extend toritate to cover state spending.** Rejected: toritate's
   constitutional identity (G3/G4) is the religious-corp's OWN on-chain
   books; conflating it with state-corpus oversight muddies both. A
   clean actor boundary is better (§6).
2. **Fold the function into ossekai.** Rejected: ossekai is a
   publication / info-arbitrage organ, not a cross-reference engine;
   keeping the engine (danjo) separate from publication (ossekai)
   preserves the aggregate-anonymized publication discipline.
3. **No new actor; publish a methodology doc only.** Rejected: the user
   explicitly asked for the actor, and a named actor with explicit gates
   is safer than an unnamed pipeline that could drift past the §1.12 /
   §2(c) bounds.
4. **Let danjo render "violation" verdicts.** Rejected — fatal: violates
   UPL-equivalent discipline + §1.12 (would make the religious-corp a
   self-appointed prosecutor of the state). G4 non-adjudication is
   constitutional.

# References

- `/90-docs/adr/2605263900-public-data-open-government-ipfs-ingestion.md` — open-government corpus (primary input)
- `/90-docs/adr/2605262130-kotoba-storage-substrate-unification.md` — kotoba substrate (EAVT, no Kotoba/Datomic)
- `/90-docs/adr/2605192100-etzhayyim-mission-charter.md` — §1.12 Transparent Religious Force + §2(c) covert-ops avoidance
- `/90-docs/adr/2605192200-etzhayyim-ip-free-release-charter-rider.md` — Charter Rider §2(c)/(e)
- `/90-docs/adr/2605262900-toritate-accounting-audit-tier-b-actor-r0.md` — toritate (boundary sibling)
- `/90-docs/adr/2605262700-chigiri-legal-procedure-tier-b-actor-r0.md` — chigiri (UPL boundary; data_privacy DSAR routing)
- `/90-docs/adr/2605301400-tadori-onchain-tracing-actor-and-kotoba-eavt-migration.md` — tadori (kotoba-native investigation sibling)
- `/00-contracts/lexicons/com/etzhayyim/gov/dataset/README.md` — gov.dataset.* namespace
- `/20-actors/danjo/` — manifest + README + CLAUDE.md
- `/CHARTER-RIDER.md` — License + Rider canonical text
- `/CLAUDE.md` — Religious-corp status table
