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

## Layout
- `manifest.edn` — actor charter + gates G1–G7 + non-goals N1–N5 + methods + ledger + seed.
- `kotoba/ontology.kanmon.edn` — EAVT schema + enums + thresholds + `:unrepresentable` negative space.
- `kotoba/seed.edn` — `:representative` seed (12 real CN/KR/JP exam systems; illustrative public
  figures — precise live 倍率/受験者数 are an operator/Council ingest step, G7).
- `methods/kanmon_edn.cljc` — seed loader + classify (pure stdlib).
- `methods/analyze.cljc` — barrier-load → OPENING route + tally/by-country/top + EAVT `datoms` + report.
- `methods/kotoba.cljc` — content-addressed append-only OBSERVATION LEDGER (`tx-cid`/`verify-chain`,
  tamper-evident, no-server-key) — the kafun/busshi/meisai family machinery.
- `methods/autorun.cljc` — deterministic, idempotent-by-content heartbeat (assess → append on change).
- `methods/test_*.cljc` — kanmon_edn / analyze / kotoba / autorun suites.
- `run_tests.clj` — bb-native runner (no shell — repo clj/bb rule).

## Run (scripts are bb — repo clj/bb rule; no shell)
```
bb 20-actors/kanmon/run_tests.clj                                  # 19 tests / 174 assertions
bb --classpath 20-actors 20-actors/kanmon/methods/analyze.cljc     # barrier-load → OPENING map
bb --classpath 20-actors 20-actors/kanmon/methods/autorun.cljc     # one heartbeat → append to the ledger
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
