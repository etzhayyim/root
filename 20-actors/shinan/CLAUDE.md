# 20-actors/shinan 指南

**学習支援 (learning-support) — CN/KR/JP exam students, 学習解放 framing. ADR-2606291501. Status: R0.**

Hands the learner an OPEN scaffold (足場) toward the reality of an exam — and nothing more.
It maps the OPEN-learning **supply** (resources, open-license only) against the **demand**
(study topics in the 高考/수능/共通テスト space) and surfaces where open learning exists and
where the gap is. It is the charter-clean inverse of a paywalled cram platform, and the
learning-support sibling of `関門 kanmon` (kanmon maps the gate; shinan hands the scaffold).

> **学習解放 — no carve-out.** shinan inherits `manabi 学び`'s anti-credentialism (G7),
> anti-examination-coercion (G10), and anti-addictive-design (G3). It does **not** score,
> grade, rank, gate, credential, or predict pass/fail. There is **no learner** in the data
> model at all. We sow the scaffold; growth belongs to the learner.

## Hard prohibitions (structurally unrepresentable, not policy)
- **No scoring / grade / rank** (G1): `:shinan/score` · `:shinan/grade` · `:shinan/rank`
  have no representation (no 偏差値 / 序列). manabi G7.
- **No pass-prediction** (G2): `:shinan/pass-prediction` absent. manabi N11/N3.
- **No gatekeeping / credential / transcript** (G3): `:shinan/gate` · `:shinan/credential` ·
  `:shinan/transcript` absent. manabi G7.
- **No coercion / addiction** (G4): `:shinan/timed-test` (self-paced only) · `:shinan/leaderboard`
  · `:shinan/streak` absent. manabi G10 + G3.
- **No person** (G5): no `:shinan.learner/*` / `:shinan.person/*` — the model has topics and
  resources, never a student.
- **Open-license only** (G6): a proprietary / paid / enrollment-gated resource is inadmissible —
  non-open licenses are not enum members; `validate-open!` refuses them on load AND at the
  heartbeat (test-enforced).
- **Structure, not official content** (G7): never reproduces official past-exam questions
  (`:shinan/official-pastquestion` absent). cert_prep G16.

All enforced *structurally* (absent from ontology/seed/emitter) and proven by `test_analyze` +
`test_shinan_edn` (incl. the proprietary-license-refused and the no-score/rank/gate/predict tests).

## The coverage map
```
topic route ∈ {:covered :needs-localization :coverage-gap}
  :covered            — ∃ open resource covering it in the topic's country language
  :needs-localization — covered, but no resource in the country language (→ translate)
  :coverage-gap       — no open resource covers it (→ create open material)
resource route ∈ {:offer :monitor}     # :offer if openness ≥ 0.6, else :monitor
```
Synthetic-seed result (11 topics / 11 open resources): 8 covered · 2 needs-localization
(高考英语, 수능영어 — English-only OER) · 1 coverage-gap (高考理科综合). The
**学習解放 worklist** = the gaps + localization needs (where open learning is missing).

## Layout
- `manifest.edn` — actor charter + gates G1–G9 + non-goals N1–N5 + methods + ledger + seed.
- `kotoba/ontology.shinan.edn` — EAVT schema + enums (open licenses only) + `:unrepresentable`
  negative space (the 学習解放 heart).
- `kotoba/seed.edn` — `:synthetic` seed (11 topics + 11 OPEN resources across CN/KR/JP).
- `methods/shinan_edn.cljc` — seed loader + classify + `validate-open!` open-license guard.
- `methods/analyze.cljc` — coverage engine (topic/resource routes + worklist) + EAVT `datoms` + report.
- `methods/kotoba.cljc` — content-addressed append-only COVERAGE LEDGER (`tx-cid`/`verify-chain`).
- `methods/autorun.cljc` — deterministic, idempotent-by-content heartbeat (refuses non-open resources).
- `methods/test_*.cljc` — shinan_edn / analyze / kotoba / autorun suites.
- `run_tests.clj` — bb-native runner (no shell — repo clj/bb rule).

## Run (scripts are bb — repo clj/bb rule; no shell)
```
bb 20-actors/shinan/run_tests.clj                                  # 20 tests / 151 assertions
bb --classpath 20-actors 20-actors/shinan/methods/analyze.cljc     # open-learning coverage map + worklist
bb --classpath 20-actors 20-actors/shinan/methods/autorun.cljc     # one heartbeat → append to the ledger
```

## Gating
Live curated open-resource ingest (open-courseware / gov-open catalogs) is an operator/Council
step (G9). The heartbeat performs no network I/O (no-server-key, G8). R0 seed is `:synthetic`.

## DID (follow-up, R0)
Target `did:web:etzhayyim.com:actor:shinan`. Child repo `etzhayyim/com-etzhayyim-shinan` +
west entry + RAD identity journal (`80-data/kotoba-rad/shinan.identity.journal.edn`) are the
separation follow-up per the root CLAUDE.md §Actors completion criteria.
