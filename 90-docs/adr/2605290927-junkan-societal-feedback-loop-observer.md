---
id: adr-2605290927-junkan-societal-feedback-loop-observer
title: "ADR-2605290927: junkan (循環) — analysis-only societal feedback-loop observer (Python LangGraph + datom/kotoba-kqe)"
status: proposed
doc_type: adr
topic: junkan-societal-feedback-loop-observer
authoritative: true
last_verified: 2026-05-29
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - junkan actor R0 charter
  - societal causal-loop / virtuous-vicious-cycle analysis substrate
  - analysis-only (no-actuation) artificial-organism observer pattern
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262400-public-data-ingestion-organism-ecosystem
  - adr-2605240200-kaizen-observer-self-reflection
  - adr-2605264000-ossekai-information-arbitrage-wellbecoming-nudge
related:
  - adr-2605221243-ideal-ecosystem-state-active-inference-prior
  - adr-2605232345-unspsc-actor-as-organism
supersedes: []
superseded_by: []
---

# ADR-2605290927: junkan (循環) — analysis-only societal feedback-loop observer

**Status**: proposed
**Date**: 2026-05-29
**Deciders**: Jun Kawasaki

# Context

The ecosystem already performs rigorous **system-dynamics analysis on
itself**:

- `90-docs/2605221243-ideal-ecosystem-state-active-inference-prior.md` models
  the religious-corp organism with stock-flow equations (`dS₁/dt … dS₁₀/dt`)
  and an explicit reinforcing/balancing loop table (R1–R4 / B1–B4) plus an
  aliveness functional `A(t) = ⟨M, D, C, P, G⟩`.
- `KaizenObserverCell` (ADR-2605240200) runs a continuous rule registry over
  the organism's own telemetry.

Both are **inward** (self-model). The one **outward** societal-analysis actor,
`ossekai` (ADR-2605264000), has a narrow lens (information asymmetry) and is an
**intervention** actor — it publishes feeds and dispatches `@mention` nudges.

There is **no actor whose mandate is to perform systems-thinking on society at
large** — to continuously map where **virtuous cycles (好循環) and vicious
cycles (悪循環)** are spinning — and **do nothing but analyze**. The vocabulary
(causal-loop diagrams, stock-flow, Meadows leverage points), the math, and the
passive-data + heartbeat substrate all exist; only the outward, analysis-only
synthesis is missing.

This ADR scaffolds that actor: **junkan (循環)**.

## Naming

循環 (junkan) = circulation / cycle. The actor's entire subject matter is the
*loop*. It is the outward, societal sibling of the inward active-inference prior
(2605221243) and of `KaizenObserver` (self) — the same systems-thinking turned
toward society, with the discipline that it may **only look, never touch**.

## The "datomic" requirement — resolved to kotoba-kqe (Datomic-isomorphic)

The design brief specified **Python LangGraph + Datomic**. Feedback-loop
analysis is inherently temporal: a loop's regime (好循環/悪循環) can only be read
from how a *stock* moved over time and which *flows* drove it. The natural data
model is **immutable facts with time** — exactly Datomic's `[E A V T]` datom +
`tx-time` + `as-of`/`history` queries.

The repository's **canonical substrate is `kotoba` / `kotoba-kqe`**
(ADR-2605262130), which is **Datomic-isomorphic by construction**: it provides
content-addressed Datalog with `EAVT / AEVT / AVET / VAET` arrangements (the
exact Datomic index set) over immutable blocks. Substrate boundary
(CLAUDE.md §Substrate boundary) + Charter Rider §2(e) anti-gatekeeping + §2(c)
vendor data-sovereignty **prohibit** introducing the proprietary Datomic
product into religious-corp paths; a literal-Datomic carve-out would require a
Council ADR and would, by default, fail the Rider.

**Decision**: junkan adopts the **datom / Datalog data model** (immutable
society-stock facts, time-travel queries, polarity-typed flow refs) and
**realizes it on kotoba-kqe**. The conceptual schema is written in Datomic
attribute notation below; the storage mapping table shows the 1:1 index
correspondence. No proprietary Datomic.

# Decision

Scaffold **junkan** as a **Tier-B analysis-only artificial-organism observer**
at `did:web:junkan.etzhayyim.com` (`20-actors/junkan/`).

Form = 任意団体 internal societal-systems-analysis substrate (NOT 一般社団 /
NPO / 公益財団 / 宗教法人 法人格 — Preamble §0.4 Lv7+ unanimity lock).

## Core thesis

junkan continuously builds and maintains a **system-dynamics model of society**
from **passive, public, aggregate** data, and reads off it:

1. **Stocks** — society-level accumulations (e.g. routable-address inequality,
   open-data availability, regional connectivity, labor-liberation proxies).
2. **Flows** — `dS/dt` between consecutive observations, with polarity.
3. **Causal loops** — reinforcing (R) or balancing (B), assembled from
   polarity-typed flow edges.
4. **Regime** — for each loop, whether it is currently spinning **virtuous
   (好循環)**, **vicious (悪循環)**, **neutral**, or **transitioning**.
5. **Leverage points** — Meadows' 12 levels, ranked, with the place a loop
   could flip — offered as *candidates with uncertainty*, never directives.

It then **stops**. junkan has **no actuator**: no AT Proto post, no `@mention`,
no email, no nudge, no transaction, no policy directive. Its only output is
structured, append-only **findings** (datoms + advisory records) for the
Council and other actors to read. This is the defining property — "分析するだけ".

## Constitutional discipline (the analysis-only spine)

| Gate | Invariant |
|---|---|
| **G1** | Charter Rider §2(a)-(h) scan on every input **and** output. |
| **G2** | kotoba/kotoba-datomic attestation lineage per tick. |
| **G3** | **PASSIVE-ONLY collection** — no live DNS / port-probe / traceroute / WHOIS / RDAP / DoH / handle-enumeration; only pre-published public archives via `e7m-dataset` (ADR-2605262400). |
| **G4** | **ANALYSIS-ONLY / NO ACTUATION (defining gate)** — junkan has **no outward channel**. Output is read-only findings consumed by humans / other actors. `findingRecord.actuationTaken` const `false` (structural). Acquiring *any* outward capability (post / mention / email / tx / actuator) is a **critical** violation → immediate cell halt + chigiri.disputeMediation. This is what structurally distinguishes junkan from ossekai. |
| **G5** | **NO causal overclaim** — every edge / loop is labelled `hypothesis` with evidence + confidence; junkan asserts correlation / lagged-sign, **never proven causation**. (`causalLoopFinding.hypothesisOnly` const `true`.) |
| **G6** | **Aggregate-only / no individual modeling** — society-level stocks only; no per-person entity, no PII, no de-anonymization (Charter §1.4 anti-individualism + §2(c)). |
| **G7** | **Wellbecoming-positive, non-eschatological framing** — vicious-cycle findings are described soberly; no fear-amplification, gore, doom or apocalyptic framing (Charter §1.13 + §1.15). |
| **G8** | **NO commercial systems-analysis / BI / intelligence SaaS** — Palantir / Recorded Future / Dataminr / Quid / SAS / Stella Architect (iseesystems) / Vensim commercial / AnyLogic commercial / Powersim **PROHIBITED** per Charter Rider §2(e)+§2(c). OSS only: PySD, BPTK-Py, networkx, NumPy/SciPy (Apache/MIT/BSD). |
| **G9** | **Datom immutability** — stocks are append-only datoms on kotoba-kqe; never overwritten or retracted (Datomic semantics + anti-eschatology: trajectory, not destination). |
| **G10** | **Murakumo-only inference** — any LLM-assisted loop-naming flows through judah LiteLLM + `baien-server-moemoekyun-*` (ADR-2605215000); commercial LLM PROHIBITED. |
| **G11** | **No prescription / no prediction-as-fact** — junkan describes present loop regimes and leverage *candidates* with uncertainty; it does **not** prescribe interventions or issue point-forecasts as fact (`leveragePointFinding.prescriptionGiven` const `false`). |
| **G12** | Open-source model + findings (Apache 2.0 + Charter Rider). |
| **G13** | **Default audience = Council/internal.** Surfacing a finding beyond Council requires Council Lv6+ ≥3 attestation, **and even then publication is performed by another actor** (ossekai / kataribe), never by junkan — preserving G4. |

## Non-goals

- **N1** NOT an intervention / actuator actor (explicitly NOT ossekai — no nudge, post, mention, email, tx).
- **N2** NOT a surveillance / OSINT actor (passive-only, aggregate-only).
- **N3** NOT a forecasting / prediction-market actor (describes present regime; no betting, no point-forecasts-as-fact).
- **N4** NOT a policy-prescription / lobbying actor (candidates with uncertainty only; no directives).
- **N5** NOT a commercial BI / intelligence-for-hire service.
- **N6** NOT a state-aligned intelligence function (§1.12 routing-around, not state intel).
- **N7** NOT a self-model — that is `KaizenObserver`; junkan is the outward/societal sibling.
- **N8** NOT a causation-prover (hypotheses only, per G5).
- **N9** NOT individual profiling / credit-scoring / social-scoring.
- **N10** NOT a real-time crisis-response actor — that is `kazaori`; junkan may feed it read-only.
- **N11** NOT a Murakumo-bypass.
- **N12** NOT a Charter Rider §2 bypass.

## LangGraph graph (Python)

Heartbeat-cadence Pregel/LangGraph DAG. State is a `TypedDict`
(`tick, observations, stock_estimates, cld, loops, leverage, findings`). All
nodes are pure where possible; side effects limited to append-only datom writes
in `emit_findings`.

```
                    ┌──────────────┐
            ┌──────▶│   ingest     │  DatasetSensor.hot_sample_bounded()
            │       │  (passive)   │  e7m-dataset Tier-A/C pins · G3
            │       └──────┬───────┘
            │              ▼
            │       ┌──────────────┐
            │       │estimate_stock│  obs → society-stock level @ tick t
            │       │  (G6 aggreg.)│  append :junkan.stock datoms · G9
            │       └──────┬───────┘
            │              ▼
            │       ┌──────────────┐
            │       │ infer_flows  │  dS/dt between consecutive tx
            │       │              │  classify inflow/outflow + polarity
            │       └──────┬───────┘
            │              ▼
            │       ┌──────────────┐
            │       │  build_cld   │  Datalog over datom HISTORY →
            │       │              │  causal-loop diagram (lagged corr + sign;
            │       │              │  hypothesis only · G5)
            │       └──────┬───────┘
            │              ▼
            │       ┌──────────────┐
            │       │classify_loops│  loop polarity = Π(edge signs)
            │       │              │  → :reinforcing / :balancing
            │       │              │  regime = f(dominant-stock trajectory)
            │       │              │  → 好循環 / 悪循環 / neutral / transitioning
            │       └──────┬───────┘
            │              ▼
            │       ┌──────────────┐
            │       │find_leverage │  Meadows 12 ranking · uncertainty band
            │       │              │  candidates only · G11
            │       └──────┬───────┘
            │              ▼
            │       ┌──────────────┐
            │       │wellbecoming_ │  sober, non-eschatological framing · G7
            │       │   frame      │  Charter Rider §2 output scan · G1
            │       └──────┬───────┘
            │              ▼
            │       ┌──────────────┐
            │       │emit_findings │  WRITE-ONLY: causalLoopFinding /
            │       │ (NO dispatch)│  leveragePointFinding / regimeShiftEvent
            │       │              │  datoms + advisory. NO outward channel · G4
            │       └──────┬───────┘
            │   regime shift? │ no new data?
            └────────────────┘  (conditional edges: idle / escalate-severity)

   periodic ▶ silen_review : self-audit of G1..G13 → silenJunkanReview
```

Conditional edges: `ingest` → idle when no fresh pin; `classify_loops` raises
finding severity when a `regimeShiftEvent` (好循環⇄悪循環) is detected;
`emit_findings` **never** routes to any dispatch/post/mention node (no such node
exists — G4 is enforced by *absence*, not by a runtime check that could be
bypassed).

## Datom / kotoba-kqe schema (the "datomic" substance)

Conceptual schema in Datomic attribute notation (append-only; nothing is ever
retracted — G9):

```clojure
;; ── stocks (society-level accumulations) ───────────────────────────
:junkan.stock/id            {:db/valueType :string  :db/unique :identity}
:junkan.stock/level         {:db/valueType :double}        ; estimate @ this tx
:junkan.stock/unit          {:db/valueType :string}
:junkan.stock/valid-time    {:db/valueType :instant}       ; when world observed
:junkan.stock/source-cid    {:db/valueType :string}        ; e7m-dataset pin · G3
;; (tx-time is the datom's own T — gives free history/as-of)

;; ── flows (typed, directional, lagged) ─────────────────────────────
:junkan.flow/from-stock     {:db/valueType :ref}
:junkan.flow/to-stock       {:db/valueType :ref}
:junkan.flow/polarity       {:db/valueType :keyword}        ; :pos | :neg
:junkan.flow/lag-ticks      {:db/valueType :long}
:junkan.flow/evidence       {:db/valueType :string}         ; corr+sign · hypothesis
:junkan.flow/confidence     {:db/valueType :double}         ; G5

;; ── loops ──────────────────────────────────────────────────────────
:junkan.loop/id             {:db/valueType :string  :db/unique :identity}
:junkan.loop/edge           {:db/valueType :ref  :db/cardinality :many}  ; → flows
:junkan.loop/type           {:db/valueType :keyword}        ; :reinforcing | :balancing
:junkan.loop/regime         {:db/valueType :keyword}        ; :virtuous | :vicious
                                                            ; | :neutral | :transitioning
:junkan.loop/dominant-stock {:db/valueType :ref}
:junkan.loop/hypothesis?    {:db/valueType :boolean}        ; const true · G5
```

Representative Datalog queries (run as kotoba-kqe arrangements):

```clojure
;; All vicious loops whose dominant stock is currently worsening
[:find ?loop-id ?stock-id
 :where [?l :junkan.loop/id ?loop-id]
        [?l :junkan.loop/regime :vicious]
        [?l :junkan.loop/dominant-stock ?s]
        [?s :junkan.stock/id ?stock-id]]

;; Regime history of a loop across the last N transactions (TIME-TRAVEL —
;; the property that makes the datom model right for cycle analysis)
;; → kotoba-kqe `as-of` / `history` over EAVT, no separate temporal table
```

**Datomic → kotoba-kqe index mapping** (1:1; no proprietary product):

| Datomic concept | kotoba-kqe realization | Serves |
|---|---|---|
| `[E A V T]` datom | content-addressed block tuple | immutable fact + free history |
| EAVT index | EAVT arrangement | "all attributes of loop L" |
| AVET index | AVET arrangement | "all loops where regime = :vicious" |
| VAET index (reverse ref) | VAET arrangement | "which loops include stock X" |
| `as-of` / `history` | tx-time scan over EAVT | regime trajectory / 好循環⇄悪循環 shift |
| Datalog query | `kotoba-kqe` Datalog | loop discovery + regime read-off |

## Cells (R0 path-reserved)

Eight Pregel cells under `40-engine/kotoba/crates/kotoba-kotodama/cells/junkan_*/`, witness-pair
pattern on a Murakumo node (import-time `RuntimeError` until R1 activation):

`junkan_ingest` · `junkan_stock_estimator` · `junkan_flow_inference` ·
`junkan_cld_builder` · `junkan_loop_classifier` · `junkan_leverage_finder` ·
`junkan_finding_emitter` (analysis-only; no dispatch) · `junkan_silen_review`.

## Lexicons

Five Lexicons under `com.etzhayyim.junkan.*` (R0 skeletons; full schema at R1):

- **societalStockObservation** — append-only; G6 aggregate-only; G9 immutable;
  carries `sourceCid` + `validTime` (+ tx-time from substrate).
- **causalLoopFinding** — `type` enum {reinforcing, balancing} + `currentRegime`
  enum {virtuous, vicious, neutral, transitioning} + `hypothesisOnly` const
  `true` (G5) + `confidence` + `evidenceCids` + `dominantStockId`.
- **leveragePointFinding** — Meadows `level` 1–12 + `targetLoopId` +
  `prescriptionGiven` const `false` (G11) + `uncertaintyBand`.
- **regimeShiftEvent** — `loopId` + `fromRegime` → `toRegime` + `detectedAt` +
  G7 framing-audit attestation.
- **silenJunkanReview** — G1..G13 const-field structural enforcement:
  `actuationEventsCount` = 0 + `outwardChannelAcquiredCount` = 0 +
  `causalOverclaimEventsCount` = 0 + `individualModelingEventsCount` = 0 +
  `commercialAnalysisSoftwarePenetrationPct` = 0 +
  `prescriptionGivenEventsCount` = 0.

## Phased delivery (R0 → R3)

- **R0** — landed this session: charter ADR + actor scaffold + 5 Lexicon
  skeletons + 8 fleet cell paths reserved + deps.toml `[[adrs]]`/`[[modules]]` +
  adr/README index. **Plus the pure-stdlib R1-preparatory analysis core**
  (`40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/junkan/`:
  `datom`/`stocks`/`flows`/`loops`/`leverage`/`graph`) — `DatomStore` with
  EAVT/AVET + `as-of`/`history`, lagged sign-aware correlation flow inference,
  loop-polarity regime read-off (好循環/悪循環/neutral/transitioning), Meadows
  candidate ranking, and a stdlib `run_analysis` orchestrator (+ optional
  LangGraph `build_junkan_graph` wiring), all offline (no fleet / no inference /
  no network), with a 16-case `test_junkan.py` unittest suite. The analysis core
  ships runtime code on purpose — it carries no outward channel (G4 by absence)
  and binds no fleet/sensors; the 8 Murakumo Pregel cells stay import-time
  `RuntimeError`-gated until R1.
- **R1** — post Bootstrap-Council ratify (Seats 2-5 RFP close 2026-06-19): wire
  the LangGraph graph + kotoba-kqe datom schema; 3 core cells (ingest,
  stock_estimator, loop_classifier); ≥3 Tier-A societal stocks from
  ADR-2605262400 W1 foundations (RIR / GeoLite2 / IANA); Council-internal
  findings only (G13).
- **R2** — +30-day public objection: +3 cells (flow_inference, cld_builder,
  leverage_finder); first `silenJunkanReview`; first cross-actor read-only feed
  to kazaori; ossekai/kataribe may publish a junkan finding *on junkan's behalf*
  under Council Lv6+ ≥3 (G13) — junkan still never posts.
- **R3** — post-R2 + Council Lv7+ + ≥1 full quarterly cycle: +2 cells
  (finding_emitter full, silen_review); Meadows leverage candidates surfaced to
  Council; broader (still aggregate, still non-eschatological) advisory corpus.

# Consequences

**Positive**

- Closes the systems-thinking gap surfaced in the conversation: the inward
  active-inference prior (2605221243) + KaizenObserver (self) now have an
  outward, societal sibling that continuously maps 好循環/悪循環.
- "Analysis-only" is enforced **structurally** (G4 by *absence* of any dispatch
  node + `actuationTaken` const false + `silenJunkanReview` count = 0), not by
  policy alone — the cleanest possible expression of "分析するだけ".
- The datom/Datalog model gives free time-travel, which is precisely what
  loop-regime detection needs — and lands on the canonical kotoba-kqe substrate
  with no new engine and no proprietary dependency.

**Negative / risks**

- **Causal overclaim** is the central epistemic risk; mitigated by G5
  (hypothesis-only, structural) but requires honest LLM-assist prompting
  (Murakumo, G10) and Council review.
- **Leverage-point candidates** can read as directives; G11 (`prescriptionGiven`
  const false) + uncertainty bands + N4 keep junkan descriptive.
- **Scope creep toward intervention** is the existential risk for an
  analysis-only actor; G4 + N1 + the deliberate *absence* of any outward cell
  are the defense; any PR adding an outward channel must be rejected at review.

# Alternatives Considered

1. **Extend `ossekai` instead of a new actor.** Rejected: ossekai is an
   *intervention* actor (posts, nudges). Folding analysis-only systems-thinking
   into it would blur the bright line that G4 draws and weaken the discipline
   that makes "分析するだけ" credible. Clean separation is the point.
2. **Literal proprietary Datomic behind a boundary.** Rejected by default:
   violates substrate boundary + Charter Rider §2(e)/§2(c); would need a Council
   ADR. kotoba-kqe is Datomic-isomorphic and canonical, so the data model
   (the part that actually matters for cycle analysis) is preserved at zero
   constitutional cost.
3. **A scalar "society health score."** Rejected per §1.15 non-eschatological:
   like the aliveness functional, society's loops are a *trajectory shape*, not
   a number to maximize. junkan reports a set of typed loops + regimes, never a
   single index.
4. **Make junkan a KaizenObserver rule.** Rejected: KaizenObserver is the
   inward self-model; conflating self and society breaks the N7 boundary and the
   passive-only / aggregate-only societal-data discipline (G3 + G6).

# Implementation status

**R0 scaffold + R1-preparatory analysis core LANDED 2026-05-29.** Fleet cell
activation, the kotoba-kqe production binding, and live passive sensors remain
**Council-gated** (Bootstrap Council Seats 2-5 RFP close 2026-06-19).

What is implemented (pure stdlib; offline; **no fleet, no network, no inference,
no outward channel** — G4 holds by absence of any dispatch path):

- `20-actors/junkan/` actor scaffold (CLAUDE.md / README.md / manifest.jsonld /
  NOTICE) + 5 Lexicon skeletons under `com.etzhayyim.junkan.*` (commit
  `d2b0f2d60`, "bundle: junkan R0").
- `kotodama.organism.junkan` analysis core (commit `d2b0f2d60`):
  - `datom.py` — Datomic-isomorphic append-only `DatomStore` (EAVT entity /
    AVET `find` / VAET `referencing` / `as_of` / `history`; no retraction API, G9).
    Reference impl; canonical production binding = kotoba-kqe.
  - `stocks.py` — society-level stock observations (G6: `record_stock` rejects
    individual fields; G9 append-only).
  - `flows.py` — lagged sign-aware Pearson flow-polarity inference; abstains on
    zero variance / too-few points (G5).
  - `loops.py` — loop polarity (even-negatives → reinforcing) + regime read-off
    (好循環 / 悪循環 / neutral / transitioning) + regime-shift detection.
  - `leverage.py` — Meadows 12-level candidates (`prescription_given` const
    False, G11).
  - `graph.py` — stdlib `run_analysis` orchestrator + optional LangGraph
    `build_junkan_graph` (no dispatch node — G4 by absence).
- **CLD auto-discovery + passive dry-run** (commit `28d71340c`, branch
  `feat/junkan-cld-dry-run`):
  - `cld.py` — `infer_adjacency` over all ordered stock pairs at `min_conf` +
    bounded simple-cycle enumeration (deduped by directed edge-set) →
    `discover_loops`; **no `LoopSpec` required** — loops are discovered from data.
  - `ingest.py` — `series_from_observations` / `load_fixture` reshape
    already-fetched passive public-archive samples into stock series; G3
    (`source_cid` required) + G6 (individual fields rejected) enforced
    structurally. No network I/O.
  - `models.py` — shared `StockSeries` / `LoopSpec` / `FindingBundle`.
  - `graph.run_analysis(auto=True)` — discovers loops when no `LoopSpec` given.
  - `tests/fixtures/junkan_netreg_dry_run.json` — Tier-A-shaped offline fixture
    (RIR delegated concentration / smallholder share / IANA root anchor 1437).

**Verification**: 23 junkan tests pass (`uv run python -m pytest`). The dry-run
auto-discovers the vicious "address-concentration ↔ smallholder-share"
reinforcing loop from data alone, correctly excludes the flat IANA control
stock, and asserts G3/G4/G6 invariants. `findingRecord.actuationTaken` is False
throughout.

**Deferred to R1 (Council-gated)**: kotoba-kqe datom binding (replace the
in-memory `DatomStore`); real `DatasetSensor` adapters for live passive Tier-A
pins; the 8 fleet Pregel cells under `40-engine/kotoba/crates/kotoba-kotodama/cells/junkan_*/`
(currently path-reserved, import-time `RuntimeError`); Charter Rider §2 real
scan in `wellbecoming_frame`; Murakumo-only LLM-assisted loop-naming.

# References

- ADR-2605192100 (Mission Charter — §1.4 anti-individualism, §1.13 Wellbecoming, §1.15 non-eschatological, §1.12 routing-around)
- ADR-2605192200 (Charter Rider v2.0 — §2(c) covert-ops avoidance, §2(e) anti-gatekeeping)
- ADR-2605215000 (Murakumo-only inference)
- ADR-2605262130 (kotoba storage substrate — Datomic-isomorphic kotoba-kqe EAVT/AEVT/AVET/VAET)
- ADR-2605262400 (Public-data ingestion via IPFS-pinned DataLad subdatasets — PASSIVE-ONLY)
- ADR-2605240200 (KaizenObserver self-reflection — inward sibling)
- ADR-2605264000 (ossekai information-arbitrage + Wellbecoming-nudge — intervention sibling)
- `90-docs/2605221243-ideal-ecosystem-state-active-inference-prior.md` (inward stock-flow + R1–R4 / B1–B4 loop model)
- Donella Meadows, *Leverage Points: Places to Intervene in a System* (12 levels; referenced, not vendored)
