---
id: adr-2606291500-kanmon-entrance-exam-observatory-actor-r0
title: "ADR-2606291500: kanmon 関門 — CN/KR/JP entrance-exam observatory actor (R0)"
status: accepted
doc_type: adr
topic: kanmon-entrance-exam-observatory-actor
authoritative: true
last_verified: 2026-06-29
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/kanmon
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related:
  - adr-2605261045-manabi-education-actor
  - adr-2606291501-shinan-learning-support-actor-r0
  - adr-2606073000-inochi-living-world-kg-mirror
  - adr-2606042330-entity-as-actor-society-scale-social-mirror
supersedes: []
superseded_by: []
---

# ADR-2606291500: kanmon 関門 — CN/KR/JP entrance-exam observatory actor (R0)

**Status**: accepted
**Date**: 2026-06-29
**Deciders**: Jun Kawasaki

# Context

The roster had **zero** coverage of the exam systems that gate access to higher education
across East Asia — China's 高考 (gaokao), Korea's 수능 (CSAT/Suneung), and Japan's
大学入学共通テスト — and zero coverage of "受験 intel" generally. The single education actor,
`manabi 学び` (ADR-2605261045), is *constitutionally anti-examination*: its gates forbid
examination-as-coercion (G10), exam-based gating (G7 anti-credentialism), and gatekeeping
(N3). manabi is therefore the wrong home for any exam-facing work, and was never designed to
mirror exam *structure*.

There are two distinct unmet needs, which must stay separate to stay charter-clean:

1. **Observing the gate** — mirroring the public STRUCTURE of these high-stakes exams
   (制度 / 倍率 / 配点 / 出題区分) and surfacing where the gate is most exclusive, in order to
   route toward OPENING it. This is a KG-mirror in the `inochi`/`tsumugi`/`busshi` lineage.
2. **Supporting the learner** — handing a student an open scaffold toward an exam. This is a
   *different* actor (`指南 shinan`, ADR-2606291501) and even there must never score/rank.

This ADR establishes the **observatory** (need 1). Mixing exam-prep into it would re-import the
exact harms manabi forbids (a gaming guide, a 偏差値/序列 engine, per-student modelling). The
defining design question was therefore *what kanmon must be structurally incapable of*.

# Decision

Create **`20-actors/kanmon`** (関門 = "barrier gate"), a clj-native, kotoba-Datom-native
R0 observatory actor.

## Doctrine — map the gate to OPEN it, never to optimize into it

kanmon mirrors the **public structure** of the CN/KR/JP entrance-exam systems and computes,
**on read** (edge-primary, no stored score-of-a-system), a **barrier-load** — how exclusively a
single exam gates life-opportunity:

```
barrier-load = selectivity · (0.5 + 0.5·single-shot) · (0.5 + 0.5·stakes)
route (precedence):
  1. transparency < 0.4               → :transparency-gap   (route to disclosure)
  2. single-shot ≥ 0.7 ∧ stakes ≥ 0.7 → :destake            (reduce one-shot life-gating)
  3. equity < 0.4                     → :equity-watch       (access disparity)
  4. barrier-load ≥ 0.5 ∧ alt-pathways < 0.4 → :open-pathway (surface alternatives)
  5. else                             → :monitor            (comparatively open)
```

Every route is an **OPENING** (disclosure / redundancy / de-staking / equity). There is no
route that captures, entrenches, or optimizes-into the gate — that property is what makes a
"barrier finder" charter-clean, exactly as `ugachi`/`kaname` have no capture route.

## Gates (structural, test-enforced)

- **G1 map-not-target, NOT exam-prep** — an opening map, never a target-list and never a
  how-to-pass / gaming guide. `:kanmon/gaming-guide` and `:kanmon/target-list` are
  unrepresentable. Student-facing support is `指南 shinan`.
- **G2 no person, no rank, no prediction** — aggregate exam-SYSTEM scale only; no
  `:kanmon.student/*` / `:kanmon.person/*`; `:kanmon/rank-student` and
  `:kanmon/pass-prediction` unrepresentable. barrier-load is a property of the GATE, never a
  score of a person (the inverse of a 偏差値 engine).
- **G3 non-adjudicating** — mirrors DISCLOSED structure; routes are openings, not verdicts on
  people or institutions.
- **G4 opening-only routing** — routes ∈ `{:open-pathway :transparency-gap :destake
  :equity-watch :monitor}`.
- **G5 edge-primary on read** — barrier-load computed from disclosed factors; derived datoms
  flagged `:kanmon/derived` + `:kanmon/sourcing`.
- **G6 no-server-key / no network** — the heartbeat appends to a local ledger only.
- **G7 sourcing-honest** — R0 seed is `:representative` (real systems, illustrative public
  figures); precise live 受験者数/倍率 are an operator/Council ingest step.

These are enforced by *absence from the ontology/seed/datom-emitter* and proven by
`test_analyze` (negative-space test) + `test_kanmon_edn`.

## Implementation (R0, landed)

clj-native pure-stdlib methods (`kanmon_edn` loader / `analyze` barrier-load→route engine +
EAVT `datoms` + report / `kotoba` content-addressed append-only observation ledger
(`tx-cid`/`verify-chain`, the kafun/busshi/meisai family machinery) / `autorun` deterministic
idempotent-by-content heartbeat) + `kotoba/ontology.kanmon.edn` + a 12-exam `:representative`
seed spanning all five routes. **19 tests / 174 assertions green** under babashka
(`bb 20-actors/kanmon/run_tests.clj`). Synthetic-seed result: 高考/수능 → `:destake`;
考研/二次 → `:open-pathway`; 中考/中学受験/수시 → `:equity-watch`; 综合评价/내신 →
`:transparency-gap`; 共通テスト → `:monitor`.

# Consequences

- The roster gains its first East-Asian exam-system coverage as an OPENING observatory, with
  the anti-exam-prep / anti-ranking boundary enforced in code, not policy.
- Composes with `指南 shinan`: kanmon's `:open-pathway`/`:destake` routes inform shinan's
  coverage priorities (the gate ↔ the scaffold).
- **Separation follow-ups (R0, not yet done — consistent with other recent R0 actors)**: DID
  `did:web:etzhayyim.com:actor:kanmon`, child repo `etzhayyim/com-etzhayyim-kanmon`, west
  entry (`manifest/repos.edn` single-entry GitHub-API commit), and RAD identity journal. Live
  primary-source ingest of official 受験者数/倍率/配点 is G7-gated (operator/Council).
- Zero invariant amendments.

# Alternatives Considered

- **Extend manabi 学び** — rejected: manabi's G7/G10/N3 structurally forbid exam-facing work;
  an exam observatory inside it would be incoherent.
- **One actor for observatory + learning-support** — rejected: fusing the gate-map with
  learner-facing material is exactly how a gaming guide / ranking engine creeps in. Splitting
  into kanmon (gate) + shinan (scaffold) keeps each structurally clean.
- **A "受験対策" actor with scoring/合否予測** — rejected for the observatory; and for the
  learning-support sibling the founder chose the 学習解放 framing (no carve-out) over a manabi
  G7/G10 carve-out (see ADR-2606291501).

# References

- `20-actors/kanmon/` — implementation (manifest, ontology, methods, seed, tests, CLAUDE.md)
- ADR-2606291501 — 指南 shinan (the learning-support sibling)
- ADR-2605261045 — manabi 学び (education actor; the anti-examination gates inherited-around)
- ADR-2605262130 / 2605312345 — kotoba storage substrate + Datom-first-class canonical state
- ADR-2606073000 — inochi (KG-mirror lineage pattern)
- root `CLAUDE.md` §Actors — actor completion criteria (child repo → west → RAD)
