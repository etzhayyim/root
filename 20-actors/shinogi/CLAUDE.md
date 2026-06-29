# 20-actors/shinogi — CLAUDE.md

## Identity

- **Name**: shinogi (鎬 — the ridge of a blade; 鎬を削る = grind blades in fierce, wearing competition = 内卷 involution)
- **DID**: `did:web:etzhayyim.com:actor:shinogi` (canonical; `alsoKnownAs did:web:shinogi.etzhayyim.com`) — static did.json/profile under `50-infra/etzhayyim-did-web/public/actor/shinogi/` (verificationMethod `[]`, no server-minted key; KV/kotoba ingest = operator step)
- **ADR**: ADR-2606291200 (R0 scaffold)
- **Parent method**: junkan 循環 (ADR-2605290927) — shinogi is its **exam-domain specialization**
- **Parent ADR**: ADR-2605192100 (Mission Charter — §1.13 Wellbecoming + §1.15 non-eschatological + §1.4 anti-individualism)
- **Status**: R0 scaffold — clj-native substrate (ontology + seed + 7 methods + 8 test suites, 43 tests / 446 assertions green)
- **Form**: 任意団体 internal societal-systems-analysis substrate (NOT 法人格)

## What shinogi is

shinogi performs **junkan's systems-thinking on one society-scale problem**: the
**high-stakes examination involution (内卷)** and the **受験失敗 (exam-failure) cycle**.
From passive, public, aggregate data it builds a system-dynamics model — **stocks**,
**flows**, **reinforcing (R) / balancing (B) loops** — over exam-competition drivers and
reads off which loops spin **悪循環 / 好循環** plus **Meadows leverage candidates**.

China's 高考 is the primary subject; Korea 수능 / Japan 受験 / India JEE-NEET / Finland /
Germany are comparative siblings (the involution is not China-only, and the structural
counter-examples — Finland's no-ranking comprehensive school, Germany's de-stigmatized dual
vocational track — are themselves relief leverage).

Like junkan, **it may only look, never touch.**

## Constitutional Discipline (CRITICAL)

1. **G4 — ANALYSIS-ONLY / NO ACTUATION.** No outward channel (no post/mention/email/tx/
   nudge). Enforced by **absence** — there is no dispatch method in the manifest, and
   `:shinogi/actuate` / `:shinogi/dispatch` are unrepresentable (test-enforced).
2. **G5 — no causal overclaim.** Every loop/regime is `:shinogi/hypothesis :true`;
   `:shinogi.exam.loop/proven-cause` unrepresentable.
3. **G6 — aggregate-only / no individual.** Drivers + institutional enactors only. **No
   per-student record, no exam score of any person, no PII** —
   `:shinogi.exam.driver/person` + `:shinogi.exam.student/score` unrepresentable.
4. **G7 — wellbecoming-positive / non-eschatological.** The failure cycle is stated
   **soberly** and **routed to RELIEF** (kokoro 心 / shiori 栞), never despair-amplified,
   never doom framing (§1.13 + §1.15). shinogi never counsels (that is kokoro's job).
5. **G8 — relief MAP, not shame-rank.** Never a student shame-list, school league-table, or
   country ranking-to-shame; `:shinogi.exam.student/ranking` unrepresentable.
6. **G9 — append-only / immutable** content-addressed findings (verify-chain tamper-evident).
7. **G11 — no prescription.** Leverage points are CANDIDATES with uncertainty
   (`:prescription? false`); `:shinogi/prescription` unrepresentable.
8. **G13 — default audience = Council/internal**; surfacing beyond is performed by
   ossekai/kataribe on shinogi's behalf, never by shinogi (preserves G4).
9. **G14 — publication membrane dry-run / no-server-key.** `social.cljc` drafts dry-run
   AT-proto mirror posts only (≥2 sources, person-excluded, `server-held-key false`);
   `build-live` raises. Live broadcast = member CACAO leash (ADR-2606111400) + Council Lv6+
   (ADR-2606281500 seed-and-grow). G4 preserved by absence of any autonomous live-publish path.

Full gate table G4..G14 + non-goals N1..N6 in the manifest + ADR-2606291200.

## Substrate (clj-native, kotoba-Datom-native)

- `kotoba/ontology.shinogi-exam.edn` — EAVT schema · **9 pressure stocks** across the
  involution LIFECYCLE: Phase 1 EXAM (A positional-scarcity / B effort-inflation=内卷核 /
  C credential-signaling / D wellbeing-erosion / E family-capture / F failure-penalty) ·
  Phase 2 LABOR (G labor-absorption-deficit = 卒業即失業) · Phase 3 WITHDRAWAL
  (H effort-efficacy-collapse = 頑張れない / I withdrawal-prevalence = 躺平/寝そべり) ·
  **10 canonical loops** · Meadows 12 levels · negative space.
- `kotoba/seed.exam-involution.edn` — 33 drivers / 6 jurisdictions (China-primary; JP/KR
  lost-generation siblings 就職氷河期/さとり/N포세대; grows each /loop).
- `methods/shinogi_edn.cljc` — loader/classify.
- `methods/analyze.cljc` — analysis-only read-off (stock regimes + loops + **two relief
  read-offs: the 受験失敗 cycle + the 卒業後 頑張れない/躺平 cycle** + leverage candidates +
  coverage worklist + EAVT datoms + sober report). **No outward channel (G4 by absence).**
- `methods/simulate.cljc` — deterministic time-series stock-flow simulation: the loops become a
  coupling matrix, driver nets the forcing; an intervention (the energy-flow re-routing) flips the
  vicious spiral (involution-index 0.59→0.16 on the seed). A structural what-if (G5), not a forecast (N3).
- `methods/energy_flow.cljc` — **the wellbecoming energy-flow design** (the answer to "turn this
  causality into wellbecoming"): re-routes the society's effort-energy from the dissipative 内卷
  zero-sum channels into wellbecoming-yielding ones (intrinsic learning / wellbeing protection /
  alternative pathways / labor absorption). Two ledgers never conflated (uzu G1/G2: effort=flow,
  wellbecoming=index). A candidate/design (G11), feeds `simulate`.
- `methods/social.cljc` — **social-protocol activity**: dry-run AT-proto mirror posts of findings +
  the energy-flow design (≥2 sources G5, person-excluded G6, no-server-key, `build-live` raises;
  live = member CACAO leash + Council per G13/G14/ADR-2606281500).
- `methods/kotoba.cljc` — content-addressed append-only findings ledger (commit-DAG,
  verify-chain tamper-evident, no-server-key, local file only).
- `methods/autorun.cljc` — deterministic idempotent-by-content heartbeat.
- Tests: `bb 20-actors/shinogi/run_tests.clj` → 43 tests / 446 assertions green.

## Data model — datom / Datalog on kotoba-kqe (NOT proprietary Datomic)

Loop analysis is temporal: a regime is only readable from how a stock moved over time.
shinogi adopts the **datom data model** (`[E A V T]` + as-of/history) and realizes it on the
Datomic-isomorphic **kotoba-kqe** (ADR-2605262130). Append-only (G9); nothing retracted —
matching §1.15 (trajectory, not destination).

## Boundaries (who shinogi is NOT)

- **NOT ossekai** (ADR-2605264000) — ossekai intervenes; shinogi only analyzes.
- **NOT a test-prep / coaching actor** (N2) — it never helps anyone *win* the involution.
- **NOT manabi** (ADR-2605261045) — manabi *teaches* (open-curriculum); shinogi *maps* the
  competition manabi's learners are caught in; manabi is the alternative-pathway relief lens.
- **NOT kokoro / shiori** — shinogi *routes* the failure cycle to them; it does not counsel.
- **NOT a forecaster / prescriber / student-profiler** (N3/N4/N5).

## Remaining follow-ups (per root CLAUDE.md §Actors completion condition)

R0 lands the `20-actors/shinogi` substrate. To graduate from "未分離":
1. create the child repo `etzhayyim/com-etzhayyim-shinogi`,
2. register it as `orgs/etzhayyim/com-etzhayyim-shinogi` in `manifest/repos.edn` (west, single-entry API commit),
3. add the RAD identity journal (`80-data/kotoba-rad/shinogi.identity.journal.edn`).

## References

- ADR-2606291200 — shinogi R0 charter (this actor)
- ADR-2605290927 — junkan (the parent system-dynamics method)
- ADR-2605262130 — kotoba storage substrate (Datomic-isomorphic kotoba-kqe)
- ADR-2606082102 — shiori (Wellbecoming detractor + relief-gap sibling)
- ADR-2605263700 — kokoro (mental-health support; failure-cycle relief destination)
- ADR-2605261045 — manabi (education; alternative-pathway lens)
