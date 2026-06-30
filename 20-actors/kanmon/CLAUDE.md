# 20-actors/kanmon 関門

**入試 OBSERVATORY / mirror — CN/KR/JP high-stakes entrance-exam systems. ADR-2606291500. Status: R0.**

A KG-mirror in the inochi/tsumugi/busshi lineage. Mirrors the PUBLIC STRUCTURE of the
高考/中考/考研 (CN) · 수능/내신/수시 (KR) · 大学入学共通テスト/二次/中学・高校受験 (JP) exam
systems into the kotoba Datom log, and runs edge-primary **BARRIER-LOAD** (how exclusively a
single exam gates life-opportunity) routed to **OPENING (開放)**. A 関門 is mapped in order
to be OPENED — never to be optimized-into. Sibling of `指南 shinan` (learning support):
kanmon maps the gate, shinan hands the learner an open scaffold; neither scores anyone.

## Hard prohibitions (structurally unrepresentable, not policy)
- **Map-not-target, not exam-prep** (G1): an OPENING map of where the gate is most exclusive —
  NEVER a target-list, NEVER a how-to-pass / gaming guide. `:kanmon/gaming-guide` /
  `:kanmon/target-list` have no representation. Student-facing learning support is `指南 shinan`.
- **No person, no rank, no prediction** (G2): aggregate exam-SYSTEM scale only. There is no
  `:kanmon.student/*` / `:kanmon.person/*` attribute; `:kanmon/rank-student` and
  `:kanmon/pass-prediction` are structurally absent. barrier-load is a property of the GATE,
  never a score of any person (this is the inverse of a 偏差値 / 序列 engine).
- **Opening-only routing** (G4): routes ∈ `{:open-pathway :transparency-gap :destake
  :equity-watch :monitor}` — all toward opening / redundancy / transparency / equity. There
  is no route that captures, entrenches, or optimizes-into the gate.
- **Structure not content** (N2): mirrors 制度/区分/配点, never reproduces official past-exam
  questions (`:kanmon.exam/official-pastquestion` absent).

These are enforced *structurally* — the forbidden attributes are absent from the ontology, the
seed, and the datom emitter — and proven by `test_analyze` + `test_kanmon_edn`.

## The edge-primary metric
```
barrier-load = selectivity · (0.5 + 0.5·single-shot) · (0.5 + 0.5·stakes)    # on read
route (precedence):
  1. transparency < 0.4               → :transparency-gap   (route to disclosure)
  2. single-shot ≥ 0.7 ∧ stakes ≥ 0.7 → :destake            (reduce one-shot life-gating)
  3. equity < 0.4                     → :equity-watch       (access disparity)
  4. barrier-load ≥ 0.5 ∧ alt-pathways < 0.4 → :open-pathway (surface alternatives)
  5. else                             → :monitor            (comparatively open)
```
Synthetic-seed result (12 exams): 高考/수능 → :destake · 考研/二次 → :open-pathway ·
中考/中学受験/수시 → :equity-watch · 综合评价/내신 → :transparency-gap · 共通テスト → :monitor.

## System-dynamics → energy-flow → social-protocol (the wellbecoming chain)
kanmon doesn't stop at the gate map; it turns the gate's **causality** into **wellbecoming**
and **publishes** it:

1. **System-dynamics read** (`methods/dynamics.cljc`, junkan 循環 pattern, **analysis-only**):
   folds the exam factors into 5 accumulating STOCKS (`:exam-pressure` / `:single-shot-stakes`
   / `:access-inequality` / `:credential-signaling` / `:cram-dependence`), reads 6 causal LOOPS
   (3 reinforcing 受験スパイラル/学歴インフレ/一発勝負ロック + 3 balancing 多様化/透明化/脱・一発),
   and ranks the OPENING routes as **Meadows leverage CANDIDATES** (never directives —
   `:prescription? false`; no `:kanmon/actuate` path). Seed read: the system is **vicious**,
   dominated by `:single-shot-stakes`; deepest leverage = **`:destake` (Meadows M3 = goals)**.
2. **Energy-flow rectification** (`methods/ie_flow.cljc`, embeds the SHARED
   `etzhayyim.ie-flow.metrics`): kanmon is a **整流器** — scattered barrier-load (disorder =
   diffuse harm to students' wellbecoming) flows in, and is concentrated onto the high-leverage
   OPENINGs (weighted by wellbecoming) and **exported** to downstream actors (shiori 栞 relief /
   shinan 指南 scaffold / danjo 弾正 disclosure / kaname 要 leverage) = the **system of systems**.
   Seed: order-index 0.092 · η 16.23× · net-gain +3.7 · non-parasitic. Self-contained
   `viz/energy-flow.html`. kanmon moves INFORMATION-energy, never students or money.
3. **Social-protocol publication** (`methods/social.cljc` + `cells/social_post/state_machine.cljc`,
   seed-and-grow doctrine ADR-2606281500): kanmon self-publishes its OPENING map + leverage
   digest to AT-proto **autonomously by default**, bounded by the **seed (rails, NOT lifted)**:
   self-`did:key` present-only + revocable member CACAO leash (off-switch) + append-only public
   log (相互監視) + **Rider §2 catastrophe-veto content scan before emit** (+ kanmon negative space
   — no 偏差値/序列/合否予測/person) + no person-targeting + Murakumo-default narration. R0 =
   dry-run membrane; live broadcast self-signs in the mesh runtime (`build-live` raises here).
   **PUBLICATION ≠ ACTUATION**: kanmon publishes a map, it never grants a permit or launches anything.

## Layout
- `manifest.edn` — actor charter + gates G1–G7 + non-goals N1–N5 + methods + membrane + ie-flow + social + ledger + seed.
- `kotoba/ontology.kanmon.edn` — EAVT schema + enums + thresholds + `:unrepresentable` negative space.
- `kotoba/seed.edn` — `:representative` seed (12 real CN/KR/JP exam systems; illustrative public
  figures — precise live 倍率/受験者数 are an operator/Council ingest step, G7).
- `methods/kanmon_edn.cljc` — seed loader + classify (pure stdlib).
- `methods/analyze.cljc` — barrier-load → OPENING route + tally/by-country/top + EAVT `datoms` + report.
- `methods/dynamics.cljc` — system-dynamics (stocks/loops/Meadows leverage), analysis-only.
- `methods/ie_flow.cljc` — energy-flow rectification → wellbecoming (shared ie-flow metrics) + viz.
- `methods/social.cljc` — dry-run AT-proto self-publication projection (seed-and-grow rails).
- `cells/social_post/state_machine.cljc` — publication membrane (≥2 sources / no-server-key / dry-run / content-scan).
- `methods/kotoba.cljc` — content-addressed append-only OBSERVATION LEDGER (`tx-cid`/`verify-chain`).
- `methods/autorun.cljc` — deterministic, idempotent-by-content heartbeat (assess → append on change).
- `kotoba.app.edn` — mesh app manifest: observe / energy-flow / social on-tick triggers (seed wiring).
- `viz/energy-flow.html` — self-contained ie-flow Sankey (generated from the seed; committed artifact).
- `methods/test_*.cljc` — kanmon_edn / analyze / dynamics / ie_flow / social / kotoba / autorun suites.
- `run_tests.clj` — bb-native runner (no shell — repo clj/bb rule; classpath adds `70-tools/src`).

## Run (scripts are bb — repo clj/bb rule; no shell)
```
bb 20-actors/kanmon/run_tests.clj                                          # 38 tests / 287 assertions
bb --classpath 20-actors 20-actors/kanmon/methods/analyze.cljc             # barrier-load → OPENING map
bb --classpath 20-actors 20-actors/kanmon/methods/dynamics.cljc            # causal loops + Meadows leverage
bb -cp "20-actors:70-tools/src" 20-actors/kanmon/methods/ie_flow.cljc      # rectify → wellbecoming + viz
bb --classpath 20-actors 20-actors/kanmon/methods/autorun.cljc             # one heartbeat → append to the ledger
```

## Gating
Live primary-source ingest (official ministry / test-body 受験者数・倍率・配点) is an
operator/Council step (G7). The heartbeat performs no network I/O — it appends to a local
ledger only (no-server-key, G6). R0 seed is `:representative`.

## DID (follow-up, R0)
Target `did:web:etzhayyim.com:actor:kanmon`. Child repo `etzhayyim/com-etzhayyim-kanmon` +
west entry (`manifest/repos.edn` single-entry GitHub-API commit) + RAD identity journal
(`80-data/kotoba-rad/kanmon.identity.journal.edn`) are the separation follow-up per the
root CLAUDE.md §Actors completion criteria.
