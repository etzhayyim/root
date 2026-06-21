---
id: adr-2606072003-kosatsu-crime-sanctions-competing-claim-observatory-r0
renumbered_from: "2606072000"
title: "kosatsu 高札 — crime/sanctions competing-claim observatory (Tier-B actor R0; designation-as-attributed-event over the kotoba Datom log; the politically-neutral, asserter-relative inverse of a sanctions-screening product)"
status: proposed-pending-council-ratification
doc_type: adr
topic: kosatsu-crime-sanctions-competing-claim
authoritative: true
last_verified: 2026-06-07
priority: 6.3
axis: actor
weight: 0.63
priority_note: "Answers 「いまの etzhayyim で犯罪行為・サンクション対象のリスト・人物・組織・思想・DNS などは kotoba Datomic に保存・永続化されているか? それらの関係・system-of-systems の intel/分析は設計されているか? 犯罪は政治的立ち位置で変わるので、それを考慮した事実・イベントログベースの整理・分析」. Audit found broad LEGACY crime/sanctions/intel surfaces (project-sanctions ~50K entities OFAC/EU/UN/JP-MOF, project-intel 30-INT fusion, graph-sos-intel, yabai AML/CTI, malak cybercrime) but ALL on RisingWave/SQL (substrate-non-compliant, ADR-2605262130 + 2605312345), with NO political-neutrality model and a tendency toward a single 'is X sanctioned' boolean + per-subject risk score. The modern kotoba-native accountability family (danjo/tadori/tsumugi/keizu/kanae) is power-scoped and non-adjudicating but none of them is the crime/sanctions competing-claim board. kosatsu is the kotoba-Datom-native answer: a designation is an attributed EVENT (asserter + as-of status) and 'crime/sanction' is ASSERTER-RELATIVE by construction — the neutral, event-log way to record it when what counts as a sanctionable act varies by political position. ZERO invariant amendments."
authoritative_for:
  - "kosatsu actor scope (crime/sanctions designations mirrored into the kotoba Datom log as append-only attributed events + a computed competing-claim/divergence view; design-only)"
  - "the mirror-not-adjudicator invariant (etzhayyim authors no designation; :authority/kind has no self token; :designation/asserted-notice const true)"
  - "the asserter-mandatory invariant (no asserter-less 'global truth' designation; :designation/asserter required)"
  - "the no-verdict invariant (:designation/measure is an authority instrument; criminal/guilty/terrorist/enemy unrepresentable)"
  - "the event-log/as-of invariant (:designation/status :listed|:delisted; a delisting is a new datom with :lifted-at, never an overwrite; 非終末論)"
  - "the edge-primary / no-score invariant (no :subject/risk-score/:guilt/:threat-level; divergence computed on read)"
  - "the political-stance-explicit divergence model (per-subject {contested|unanimous|single-asserter} + coverage-split; silence is reported, never inferred as dissent)"
depends_on:
  - adr-2605301400-tadori-onchain-tracing-actor-and-kotoba-eavt-migration
  - adr-2605301600-danjo-public-accountability-oversight
  - adr-2606066000-keizu-government-relations-graph-tier-b-actor-r0
  - adr-2606011800-tsumugi-engi-knowledge-graph
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605181100-etzhayyim-encrypted-records
  - adr-2606042330-entity-as-actor-society-scale-social-mirror
---

# ADR-2606072000 — kosatsu 高札: crime/sanctions competing-claim observatory (Tier-B actor, R0)

## Context

The question that prompted this ADR: *are crime, sanctions lists, persons, organizations,
ideologies, and DNS stored/persisted in the kotoba Datom log today, and is there intel /
system-of-systems analysis over their relationships — done in a fact / event-log way that accounts
for the fact that **what counts as a crime varies by political position**?*

An audit of `etzhayyim/root` found **two layers**:

1. **A broad LEGACY crime/sanctions/intel stack** — `60-apps/etzhayyim-project-sanctions`
   (`sanctions.etzhayyim.com`, ~50K entities across OFAC SDN / EU / UN / UK-OFSI / AU-DFAT /
   CA-OSFI / JP-MOF), 59 `usTreasuryDept/sanction*` lexicons + `open-ofac-sanctions-sdn` /
   `open-sanctions` / `cryptoMixerSanction` BPMN, `project-intel` (30-INT-discipline fusion,
   person/org/location/event/technology entity graph, classification levels, path-based DIDs),
   `graph-sos-intel` (literally "Graph System-of-Systems intelligence"), `yabai` (AML/CTI risk
   scoring), `malak` (cybercrime threat actors), `ubo`/`saiban`/`business-person`. **But these are
   RisingWave/SQL/Cloudflare-Worker apps** (`kotoba/` migration limbo), they carry **no
   political-neutrality model** (no file in them mentions stance/neutral/jurisdiction/contested),
   and they trend toward a single "is X sanctioned" boolean plus a per-subject risk score.

2. **A modern kotoba-Datom-native accountability family** — danjo (state-corpus discrepancy),
   tadori (authorized on-chain tracing + attribution, already kotoba-EAVT), tsumugi (power-entity
   縁 / influence), keizu (government power-relations weave), kanae (fiscal render), kanjo/kabuto
   (disclosure / supply-chain). These are **non-adjudicating, edge-primary, map-not-target,
   person-excluded/case-anchored** — but they are **power-scoped** and **none of them is the
   crime/sanctions competing-claim board**.

The kotoba substrate already supports exactly what a politically-neutral treatment needs:
**Datom 5-tuple `(E,A,V,Tx,op)` + `as-of`/`since`/`history` + explicit retraction** make a
sanction an **event, not a truth**; **CACAO/DID provenance** binds **who asserted** a fact
(there is no built-in "approved certifier" list — neutral by construction). What was missing is an
actor that uses these to record **designations** the right way.

**The gap**: a kotoba-native actor that mirrors crime/sanctions **designations** as **append-only,
attributed events** and computes a **competing-claim / divergence** view — so that "crime/sanction
is asserter-relative" is a first-class, neutral, computed fact rather than an editorial choice.

## Decision

Introduce **高札 (kosatsu)** — a Tier-B observation actor. 高札 (kōsatsu) was the public
notice-board where **each authority** posted **its own** edicts and designations; kosatsu mirrors
that, globally and content-addressed.

### Core model — designation-as-attributed-event

A **designation** is an append-only EVENT: a **named asserting authority** (OFAC / EU Council /
UN SC / UK-OFSI / JP-MOF / Interpol / **counter-sanction bodies** RU-MFA / CN-MOFCOM) posted a
**measure** against a **subject**, citing the authority's **own** program + **primary** publication,
with an **as-of** status (`:listed` | `:delisted`). The SAME subject under DIFFERENT asserters
coexists as **parallel datoms**; the graph **never collapses them to one boolean**. A computed
**divergence** view classifies each subject and surfaces where jurisdictions disagree.

```
authority (asserter, attributed)  ──designation EVENT──▶  subject (named by a public act)
   :listed | :delisted  (append-only, as-of; a delisting is a NEW datom with :lifted-at)

divergence(subject): contested (active list-vs-delist conflict) | unanimous (opiners agree)
                     | single-asserter (one jurisdiction) ; + coverage_split (listed by some,
                     silent by others — reported, never inferred as dissent)
```

### The 10 structural gates (each in THREE homes — ontology `:db/allowed` + lexicon `:const`/`:enum` + Python `ValueError`)

- **G1 mirror-not-adjudicator** — etzhayyim authors no designation; a self/etzhayyim authority is
  unrepresentable; `:designation/asserted-notice const true` (attributed).
- **G2 asserter-mandatory + non-adjudicating** — `:designation/asserter` required (no "global
  truth"); `:designation/measure` is the authority's instrument (asset-freeze / financial-sanction
  / transaction-ban / travel-restriction / export-control / sectoral-restriction / list-inclusion
  / arrest-warrant / wanted-notice); `criminal`/`guilty`/`terrorist`/`enemy`/`crime` are not enum
  members (danjo G4 boundary; a legal characterization routes to chigiri + external counsel).
- **G3 primary-source-only** — ≥2 of the authority's OWN primary-publication citations; a
  commercial screening terminal (WorldCheck / Refinitiv / Dow-Jones / ComplyAdvantage /
  Chainalysis / …) is a prohibited citation (Charter Rider §2(e) anti-gatekeeping).
- **G4 event-log / as-of** — `:listed` | `:delisted` only; a delisting is a NEW datom with
  `:lifted-at`; nothing is overwritten; no `final`/`permanent`/`convicted` state (非終末論,
  kotoba-canonical ADR-2605312345).
- **G5 subject-dignity / no-doxxing** — a subject exists only as the named target of a public
  official act, carrying only the authority-published identifier; private-life PII unrepresentable
  (encrypted off-graph, ADR-2605181100).
- **G6 stance-explicit** — every authority declares its OWN jurisdiction/legal-regime
  `:authority/stance`, attributed; counter-sanction bodies are recorded with equal attribution;
  never etzhayyim's view.
- **G7 no-server-key + no per-subject score** — posts member-signed (`:post/server-held-key const
  false`, ADR-2605231525); no `:subject/risk-score`/`:guilt`/`:threat-level`; divergence computed
  on read (edge-primary).
- **G8 outward-gated** — live list ingest + live posting = Council Lv6+ + operator + member
  signature; R0 dry-run only; cells `.solve()` raise; `ingest.py --live` refused.
- **G9 map-not-target / no-enforcement** — outputs route to compliance-awareness / due-process
  visibility / de-risking; never a "who-to-freeze/attack" target-list or enforcement instruction;
  the cross-actor bridge emits advisory join keys only.
- **G10 sourcing-honesty** — `:representative` vs `:authoritative` on every datom; the committed
  seed is `:representative` with synthetic subject ids/labels (mirrors no real person/org).

### System-of-systems composition (the intel value)

kosatsu is the **competing-claim board**; the SoS value comes from composing its divergence view
with siblings over the **shared kotoba Datom log** — without reaching into another actor's graph
(`bridge.py` emits only the join keys): a `:designated-wallet`/`:designated-domain` → **tadori**
(authorized on-chain case); a `:designated-org` that is a public power role → **keizu**; each
currently-listed designation → a **tsumugi** asserter→subject "designation-power" 縁 edge; the
divergence / by-authority aggregates → **kanae** render. **tasuke** (cybercrime victim support) is
person-consented and **disjoint** — never auto-linked.

### Where "ideologies" and "DNS" land

- **Ideologies / thought** — out of kosatsu's scope by design (a designation is an authority's
  measure, not a belief). The diachronic *influence* of a tradition is **tsumugi**'s object
  (ADR-2606061500), recorded as influence, never as a truth-claim or a designation.
- **DNS / domains** — a `:designated-domain` subject is admissible (an authority can designate a
  domain); the join key routes to **tadori** (which already holds `dns-observation` in kotoba EAVT,
  ADR-2606031600). kosatsu records only the public designation, never registrant PII (G5).

### Deliverables (R0, all committed, 79 tests green)

- `00-contracts/schemas/crime-sanctions-ontology.kotoba.edn` — the closed structural vocab (SSoT
  of the invariants the test parses).
- `20-actors/kosatsu/lex/` — 6 lexicons (`assertingAuthority` · `subjectEntity` ·
  `designationNotice` · `competingClaimView` · `delistingEvent` · `networkPost`).
- `20-actors/kosatsu/methods/` — `weave.py` (validation + divergence engine, the heart),
  `analyze.py` (→ `out/intel-report.md`), `social.py` (dry-run posts), `ingest.py` (offline
  membrane; `--live` refused), `bridge.py` (cross-actor SoS join keys) + 6 test suites.
- `20-actors/kosatsu/data/seed-designation-graph.kotoba.edn` — `:representative` competing-claim
  seed (7 authorities / 5 subjects / 13 designation events) exercising contested / unanimous /
  single-asserter / coverage-split / delisting-timeline.
- `20-actors/kosatsu/cells/` — 3 Pregel cell scaffolds (`.solve()` raises at R0) + the publication
  membrane state machine.
- `manifest.jsonld` (→ generated into `tier-b-actors.gen.ts` → `did:web:etzhayyim.com:actor:kosatsu`,
  resolvable on `/search`) + `CLAUDE.md` + `README.md` + `MATURITY.md` + `NOTICE`.

## Consequences

**Positive.** The crime/sanctions domain gets a kotoba-Datom-native home whose **default framing
is neutral**: a designation is an attributed event, "crime/sanction" is asserter-relative, and the
divergence view makes political disagreement a **computed fact** instead of an editorial verdict.
The substrate's as-of/retraction + DID provenance are used exactly as intended. The legacy
RisingWave sanctions/intel scaffolds get a charter-clean target to migrate onto (R1). The
accountability family gains its crime/sanctions sibling without weakening any invariant.

**Negative / honest R0.** Design + offline analyzer + dry-run only; the seed is `:representative`
with synthetic subjects (mirrors no real list). No live ingest, no live posting, no kotoba-EAVT
write — all G8-gated. The legacy 50K-entity `project-sanctions` is **not yet migrated** (R1). The
`bridge.py` keys are advisory, not live links.

**Risk + mitigation.** The chief risk is misreading kosatsu as a sanctions-screening / target
product. Mitigated structurally: no per-subject score (G7), no verdict measure (G2), no
enforcement output (G9), and the mirror/competing-claim disclaimer on every post (G9). A second
risk — over-stating disagreement — is mitigated by the rule that **silence is never inferred as
dissent** (only an active list-vs-delist conflict is `contested`; silence is reported as
`coverage_split`).

## Alternatives Considered

1. **Extend `project-sanctions` in place (RisingWave).** Rejected — violates kotoba-canonical-state
   (ADR-2605262130 + 2605312345) and carries no neutrality model; it would entrench the "single
   boolean + risk score" shape this ADR is correcting.
2. **Fold crime/sanctions into tadori or keizu.** Rejected — tadori is authorized on-chain tracing
   (disjoint domain) and keizu is government power-relations (power-scoped); neither expresses the
   cross-jurisdiction competing-claim board. kosatsu bridges to both instead.
3. **A single canonical "is X sanctioned" status per subject.** Rejected — this is exactly the
   politically non-neutral collapse the question warns against. The competing-claim graph keeps
   every designation attributed to its asserter and never collapses them.
4. **Include a per-subject risk/threat score (yabai-style).** Rejected — a score-of-soul violates
   the edge-primary discipline (tsumugi/keizu G4) and would re-import the legacy stack's bias.
   Divergence is computed on read from the designation edges only.

## References

- ADR-2605312345 (kotoba Datom = first-class canonical state) · ADR-2605262130 (kotoba substrate
  unification) — the substrate this actor is native to.
- ADR-2605301400 (tadori) · ADR-2605301600 (danjo) · ADR-2606066000 (keizu) · ADR-2606011800 /
  2606061500 (tsumugi) — the accountability family kosatsu joins and bridges to.
- ADR-2605215000 (Murakumo-only inference) · ADR-2605231525 (no-server-key) · ADR-2605181100
  (encrypted records) · ADR-2606042330 (mirror invariant) — the platform invariants it inherits.
- ADR-2605192100 §1.12 (Transparent Religious Force) — observation + transparent publication only;
  no coercive action and no state-coercion dependency (the censor's eye, never the sword).
