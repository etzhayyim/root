# 20-actors/junkan — CLAUDE.md

## Identity

- **Name**: junkan (循環 — circulation / cycle)
- **DID**: `did:web:junkan.etzhayyim.com`
- **ADR**: ADR-2605290927 (R0 scaffold, 2026-05-29)
- **Parent ADR**: ADR-2605192100 (Mission Charter — §1.4 anti-individualism + §1.13 Wellbecoming + §1.15 non-eschatological + §1.12 routing-around)
- **Status**: R0 scaffold — 8 cells path-reserved + 5 Lexicon skeletons
- **Form**: 任意団体 internal societal-systems-analysis substrate (NOT 一般社団 / NPO / 公益財団 / 宗教法人 法人格 — Preamble §0.4 Lv7+ unanimity lock)

## What junkan is

junkan performs **systems-thinking on society at large**. From **passive,
public, aggregate** data it continuously builds a system-dynamics model —
**stocks**, **flows**, and **reinforcing (R) / balancing (B) causal loops** — and
reads off which loops are currently spinning **virtuous (好循環)**, **vicious
(悪循環)**, **neutral**, or **transitioning**, plus **Meadows leverage-point
candidates**.

It is the **outward** sibling of two existing inward facilities:

- the active-inference prior (`90-docs/2605221243-...`) — the same stock-flow +
  R1–R4 / B1–B4 loop modeling, applied to the organism *itself*;
- `KaizenObserver` (ADR-2605240200) — continuous self-reflection.

junkan turns that systems-thinking *toward society*, under one discipline:
**it may only look, never touch.**

## Constitutional Discipline (CRITICAL — IMMUTABLE)

The defining property is **analysis-only (分析するだけ)**:

1. **G4 — ANALYSIS-ONLY / NO ACTUATION.** junkan has **no outward channel**:
   no AT Proto post, no `@mention`, no email, no nudge, no transaction, no
   actuator. There is **no dispatch cell in the manifest** — G4 is enforced by
   *absence*, not by a bypassable runtime check. `findingRecord.actuationTaken`
   const `false`; `silenJunkanReview.actuationEventsCount` = 0 +
   `outwardChannelAcquiredCount` = 0. Acquiring any outward capability is a
   **critical** violation → cell halt + chigiri.disputeMediation.
2. **G3 — PASSIVE-ONLY collection** (ADR-2605262400) — no live DNS / port-probe
   / traceroute / WHOIS / RDAP / DoH; pre-published public archives only.
3. **G5 — no causal overclaim** — every edge/loop is `hypothesis` + confidence;
   correlation / lagged-sign only, never proven causation.
4. **G6 — aggregate-only / no individual modeling** (Charter §1.4 + §2(c)).
5. **G7 — Wellbecoming-positive, non-eschatological framing** — vicious cycles
   described soberly; no fear / gore / doom / apocalyptic framing (§1.13 + §1.15).
6. **G11 — no prescription / no prediction-as-fact** — leverage *candidates*
   with uncertainty, never directives or point-forecasts-as-fact.
7. **G13 — default audience = Council/internal**; surfacing beyond Council needs
   Council Lv6+ ≥3, and **publication is done by another actor** (ossekai /
   kataribe), never by junkan — preserving G4.

Full gate table G1..G13 + non-goals N1..N12 in ADR-2605290927.

## Governance-asymmetry substrate (clj-native, added 2026-06-21)

The first concrete analysis junkan carries: **全世界の政府で国民と政府を構造的に
不均衡にしている具体的な法律・制度・思想・価値観** を system-dynamics で読み取る
clj-native, kotoba-Datom-native substrate. Each instrument records 誰が定めたか
(`:enactor`), 経緯 (`:origin`), 関係者 (`:stakeholders`) as on-the-record public
facts; junkan reads off, as disclosed hypotheses (G5), which feedback loops spin
好循環/悪循環 + Meadows leverage candidates.

- `kotoba/ontology.junkan-gov.edn` — EAVT schema · 5 asymmetry stocks
  (information / participation / coercion / paradigm / economic) · canonical
  structural loops · Meadows 12 levels · negative space.
- `kotoba/seed.governance-asymmetry.edn` — global instrument seed (grows each
  `/loop`: 35 instruments · 17 jurisdictions at iteration 1).
- `methods/junkan_edn.cljc` — loader/classify.
- `methods/analyze.cljc` — analysis-only read-off (stock regimes + loops +
  leverage candidates + coverage worklist + EAVT datoms + sober report). **No
  outward channel (G4 by absence).**
- `methods/kotoba.cljc` — content-addressed append-only findings ledger
  (commit-DAG, verify-chain tamper-evident, no-server-key, local file only).
- `methods/autorun.cljc` — deterministic idempotent-by-content heartbeat.
- `methods/query.cljc` — read-only EAVT/AVET/VAET arrangement queries over the
  findings datoms (the kotoba-kqe index model; e.g. instruments-in / stocks-by-
  regime / loops-including-stock). Read-only (G4 by absence of any write).
- `methods/validate.cljc` — substrate integrity checker (ontology↔seed↔region-map
  consistency: 誰が/経緯/関係者 completeness, enum validity, ranges, unique ids,
  region-mapping, coverage invariants). Runnable scorecard + test-wired.
- `methods/scorecard.cljc` — generates a live `SCORECARD.md` (coverage + continental
  balance + stock regimes + era trajectory + integrity verdict) so the scorecard
  never drifts from the data.
- `methods/history.cljc` — as-of / regime-trajectory reader over the ledger
  commit-DAG: which asymmetry stocks/loops CHANGED regime (好循環⇄悪循環,
  `regimeShiftEvent`) across txs — realizes the ADR's temporal data-model.
- `80-data/junkan-governance/` — DataLad dataset (datoms snapshot + ledger +
  report + provenance).
- Tests: `bash 20-actors/junkan/run_tests.sh` → 33 tests / 564 assertions green.

This substrate keeps junkan's analysis-only spine: G4 (no actuation, no dispatch
path), G5 (hypothesis-only, `:junkan/hypothesis :true` on every derived datom),
G6 (aggregate + institutional enactors only, no person/PII), G7 (a resilience/
leverage MAP, never a target-list or ranking-to-shame), G11 (leverage points are
candidates, never directives). Composes with danjo/keizu/kanae/ooyake/kosatsu
(data) and ossekai (which may publish a finding on junkan's behalf, never junkan).

## Data model — datom / Datalog on kotoba-kqe (NOT proprietary Datomic)

Feedback-loop analysis is temporal: a loop's regime is only readable from how a
stock moved over time. The natural model is **immutable facts with time** —
Datomic's `[E A V T]` datom + `tx-time` + `as-of`/`history`.

The repo's canonical substrate **`kotoba-kqe` (ADR-2605262130) is
Datomic-isomorphic**: content-addressed Datalog with `EAVT / AEVT / AVET / VAET`
arrangements. junkan adopts the **datom data model** and realizes it on
kotoba-kqe. **Proprietary Datomic is NOT used** (substrate boundary + Charter
Rider §2(e) anti-gatekeeping + §2(c) vendor data-sovereignty); a literal-Datomic
carve-out would require a Council ADR.

Append-only (G9); nothing is ever retracted — matching both Datomic semantics
and §1.15 (trajectory, not destination).

## Architecture — LangGraph heartbeat-cadence Pregel graph

```
ingest → estimate_stocks → infer_flows → build_cld → classify_loops
       → find_leverage → wellbecoming_frame → emit_findings (WRITE-ONLY, no dispatch)
periodic: silen_review
```

8 Pregel cells under `40-engine/kotoba/crates/kotoba-kotodama/cells/junkan_*/` (R0 path-reserved,
import-time `RuntimeError` until R1). State is a `TypedDict`
(`tick, observations, stock_estimates, cld, loops, leverage, findings`).
`emit_findings` never routes to any dispatch/post/mention node — that node does
not exist (G4).

## Lexicons (`com.etzhayyim.junkan.*`)

- `societalStockObservation` — append-only; aggregate-only (G6); immutable (G9)
- `causalLoopFinding` — R/B type + currentRegime {virtuous, vicious, neutral, transitioning} + hypothesisOnly const true (G5)
- `leveragePointFinding` — Meadows level 1–12 + prescriptionGiven const false (G11)
- `regimeShiftEvent` — fromRegime → toRegime (好循環⇄悪循環 detection)
- `silenJunkanReview` — G1..G13 const-field structural enforcement

## Boundaries (who junkan is NOT)

- **NOT ossekai** (ADR-2605264000) — ossekai intervenes (posts/nudges); junkan only analyzes.
- **NOT KaizenObserver** (ADR-2605240200) — that is the inward self-model; junkan is outward/societal.
- **NOT kazaori** (ADR-2605263200) — junkan may feed it findings read-only; junkan does not respond.
- **NOT a forecaster / prescriber / surveillance / state-intel actor** (N3/N4/N2/N6).

## References

- ADR-2605290927 — junkan R0 charter (this actor)
- ADR-2605262130 — kotoba storage substrate (Datomic-isomorphic kotoba-kqe)
- ADR-2605262400 — passive public-data ingestion
- ADR-2605240200 — KaizenObserver (inward sibling)
- ADR-2605264000 — ossekai (intervention sibling)
- `90-docs/2605221243-ideal-ecosystem-state-active-inference-prior.md` — inward loop model
