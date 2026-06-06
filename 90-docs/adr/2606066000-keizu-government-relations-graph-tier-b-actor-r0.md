---
id: adr-2606066000-keizu-government-relations-graph-tier-b-actor-r0
title: "ADR-2606066000: 系図 (keizu) — government power-relations knowledge graph (procurement · money · statements · committee composition) R0"
status: accepted
doc_type: adr
topic: keizu-government-relations-graph
authoritative: true
last_verified: 2026-06-06
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - keizu-government-relations-graph
  - government-committee-composition-analysis
  - government-money-flow-relation-weave
depends_on:
  - adr-2605301600-danjo-public-accountability-oversight
  - adr-2606011800-tsumugi-engi-knowledge-graph-spirit-in-physics
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605302300-kanae-government-fiscal-flow-visualization
  - adr-2605301400-tadori-onchain-tracing-actor
  - adr-2606021600-ooyake-world-government-atlas
  - adr-2606042330-entity-as-actor-society-wide-social-mirror-graph
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor
supersedes: []
superseded_by: []
---

# ADR-2606066000: 系図 (keizu) — government power-relations knowledge graph R0

## Context

A standing ask: *「いまの政府関係の調達・お金・発言・人間関係などを分析・公開する actor。お金の
流れを公開情報からすべて追う。委員会の構成メンバーなどを分析して datomic として保持し、social
post する。」*

The monorepo already has a family of government-accountability actors, but each covers one slice
and none weaves them together keyed on **public roles**:

- **danjo** 弾正 (ADR-2605301600) ingests 国会会議録 / 予算書 / 政府調達 and emits **non-adjudicating
  discrepancy observations** — but its object is the discrepancy, not the relation graph; committee
  composition + human-relationship networks are not first-class.
- **kanae** 鼎 (ADR-2605302300) **renders** fiscal flows; it is a visualizer, not a data source.
- **tsumugi** 紡ぎ (ADR-2606011800) weaves power-entity 縁 **in general** via spirit-in-physics; it
  does not model government committee composition / statements / procurement specifically.
- **tadori** 辿 (ADR-2605301400) traces **on-chain crypto**; fiat procurement / subsidies are out
  of scope.
- **ooyake** 公 (ADR-2606021600) maps government **structure** (units / windows / procedures); it
  catalogs advisory councils but does not analyze their **composition** or ties.

The clear gap: a **relation graph of public roles** that ties **procurement + money + statements +
human/network relationships + committee/advisory-council composition** together, held in the kotoba
Datom log, narrated as social posts. This ADR establishes that actor — **系図 (keizu)**.

## Decision

Create Tier-B actor **keizu** (`did:web:etzhayyim.com:actor:keizu`) as the global government
**power-relations knowledge graph**. It traces money flows from PUBLIC information, analyzes the
composition of committees / advisory councils, and weaves procurement / money / statements /
relationships into one kotoba Datom relation-graph, then narrates aggregate findings as **dry-run**
social posts.

The whole design is forced into a **charter-clean** shape by 11 gates, the load-bearing four of
which are **structural** (each enforced in THREE places — ontology `:db/allowed`/closed-vocab
vectors + lexicon `:const`/`:enum` + Python `ValueError`, the nusa/tazuna/kamado/ake pattern):

- **G1 public-power-role-only** — a node is a public **seat/organ** (`:node/scope ∈
  {:public-office :public-org :public-committee :public-role}`); `:private-person` / `:individual`
  / `:citizen` are **unrepresentable**. A committee member exists by virtue of a public role, never
  as a private individual. **This is the no-doxxing invariant** (tsumugi G1, ooyake G6).
- **G2 non-adjudicating** — `:rel/kind` and `:money/kind` are **factual** closed vocabs; verdict
  tokens (`corruption`/`bribe`/`kickback`/`collusion`/`guilt`/`不正`/`汚職`/`賄賂`) are **not enum
  members**; `nonAdjudicatingNotice` is `const true`. keizu records observed ties and disclosed
  shares; a legal characterization is unrepresentable and routes to chigiri + external counsel
  (danjo G4).
- **G3 source-provenance mandatory** — every relation / money flow carries **≥2** public-source
  citations (`minLength 2`); an under-sourced tie **raises** (no inference-only allegation).
- **G4 edge-primary, no score-of-soul** — concentration is computed **on read** from incident
  edges; `:node/power-score` / `:node/influence` / `:node/rank` **do not exist** in the schema and
  raise if introduced. Aggregate-first (tsumugi G2).

The remaining gates: **G5** mirror-not-target (`isMirror const true`, accountability-map
disclaimer, never speaks AS a government — ADR-2606042330); **G6** Murakumo-only inference
(ADR-2605215000); **G7** no-server-key (member-signed posts, `serverHeldKey const false` —
ADR-2605231525); **G8** outward-gated (live ingest + live posting Council Lv6+ + operator + member
signature; R0 dry-run, `:post/status` is `:dry-run` only, every cell `.solve()` raises); **G9**
PII-encrypted (ADR-2605181100); **G10** non-eschatological as-of (append-only composition history —
ADR-2605312345); **G11** sourcing-honesty (`:representative` | `:authoritative`).

## Architecture

- **State**: kotoba Datom log (ADR-2605312345 / 2605262130) — `:node`/`:committee`/`:rel`/`:money`/
  `:statement`/`:post`. No Kotoba/Datomic/SQL.
- **Schema**: `00-contracts/schemas/government-relations-ontology.kotoba.edn` (the closed structural
  vocab is the SSoT the invariant test parses).
- **Lexicons**: `com.etzhayyim.keizu.{relationEdge, committeeComposition, moneyFlowObservation,
  networkPost}` (`20-actors/keizu/lex/*.edn`).
- **Cells** (5 Pregel scaffolds, `.solve()` raise at R0): `ingest`, `committee_graph`, `money_graph`,
  `relation_weave`, `social_post`. Each has a coded, self-contained state machine.
- **Methods** (stdlib, coded + tested): `weave.py` (validate + build graph + aggregate edge-primary
  concentration — the heart + the G1/G2/G3/G4 anchor), `social.py` (dry-run post projection — the
  G5/G7/G8 anchor), `ingest.py` (offline normalizer; `--live` refuses without the G8 gate),
  `analyze.py` (end-to-end → `methods/out/intel-report.md`).

## Empirical (R0)

`./run_tests.sh` — **74 tests green across 8 suites** (weave 12 / social 5 / ingest 9 /
charter-invariants 21 / analyze 4 / lexicons 5 / consistency 6 / cells 12). `analyze.py` over the
`:representative` global seed (18 public-role/organ nodes, 3 committees, 15 relations, 6 money flows,
3 statements) produces: committee cross-organ concentration, **one cross-committee co-membership
seat** (`jp-fsc-biz-1` on 財政制度等審議会 + 規制改革推進会議), **money HHI = 0.96** (top payee 98%),
**one revolving-door chain** (METI → 規制改革推進会議 industry seat), and **2 dry-run mirror posts**
(`status=:dry-run`, `serverHeldKey=false`, ≥2 sources). The charter-invariant suite parses all
three homes of each structural gate and asserts they agree.

## Honest R0

Design + data-model + offline analyzer + dry-run posts only. The seed is bounded `:representative`
(public roles/organs, rounded figures) — **not** a live authoritative capture; nodes are public
seats/organs, never named private individuals. Live full-universe ingest (官報 / 政治資金収支報告書 /
調達ポータル / Federal Register / USAspending / TED / OECD rosters) and live social posting are
Council Lv6+ + operator gated (Lv7+ for live publication under 1 SBT = 1 vote). **Zero invariant
amendments** — keizu STRENGTHENS non-adjudication (danjo), edge-primary karma (tsumugi),
no-server-key (ADR-2605231525), kotoba-canonical state (ADR-2605312345), and the mirror invariant
(ADR-2606042330).

## Non-goals

N1 not a prosecutor / adjudicator of guilt (danjo/chigiri boundary) · N2 not a surveillance system
(public-record only) · N3 not a per-individual reputation / influence / social-credit score · N4
not a target-list (accountability map by construction) · N5 not a commercial gov-intelligence
product (GovWin / Bloomberg Government / FiscalNote prohibited, Charter Rider §2(e)) · N6 not a
partisan / electioneering tool · N7 not a Kotoba/Datomic/SQL store · N8 not a doxxing vector (nodes
are public seats/organs, never private individuals).

## Consequences

- A fifth member of the government-accountability family with a distinct object (the relation
  graph), composable with danjo (cites observations), kanae (renders `:money`), tsumugi (shares
  edge-primary discipline), and ooyake (binds onto gov-unit structure).
- The `did:web:etzhayyim.com:actor:keizu` resolves and appears in `/search` via the tier-B
  generated registry + actor-profile seed.
- R1+ activates the ingest / committee_graph / money_graph cells over offline public-source batches
  behind Council Lv6+; live posting stays Lv7+.
