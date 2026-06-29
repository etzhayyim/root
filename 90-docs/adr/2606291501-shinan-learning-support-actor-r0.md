---
id: adr-2606291501-shinan-learning-support-actor-r0
title: "ADR-2606291501: shinan 指南 — CN/KR/JP exam learning-support actor (学習解放, R0)"
status: accepted
doc_type: adr
topic: shinan-learning-support-actor
authoritative: true
last_verified: 2026-06-29
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/shinan
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related:
  - adr-2605261045-manabi-education-actor
  - adr-2605264400-manabi-cert-prep-subcell
  - adr-2606291500-kanmon-entrance-exam-observatory-actor-r0
supersedes: []
superseded_by: []
---

# ADR-2606291501: shinan 指南 — CN/KR/JP exam learning-support actor (学習解放, R0)

**Status**: accepted
**Date**: 2026-06-29
**Deciders**: Jun Kawasaki

# Context

`関門 kanmon` (ADR-2606291500) maps the entrance-exam GATE in order to open it, but provides
no learner-facing material by design. The complementary need — handing a CN/KR/JP exam student
an actual **scaffold** toward the exam — collides head-on with the constitution: `manabi 学び`
(ADR-2605261045) structurally forbids examination-as-coercion (G10), credentialism and
exam-based gating (G7), and addictive design (G3); its only cert-prep lane (ADR-2605264400) is
scoped to IT certifications, generates no scores, and reproduces no official questions.

The founder was asked how to reconcile a 受験対策 actor with manabi's anti-credentialism. Three
options were weighed: (a) a **学習解放 framing** where learning support is offered as an open
commons but scoring/ranking/pass-prediction/gating are structurally unrepresentable (no
carve-out); (b) a **full carve-out** ADR relaxing manabi G7/G10/N3 inside this actor to allow
conventional scoring/模試/合否予測; (c) folding the support into an **observatory** of open
materials. The founder chose **(a) 学習解放**.

# Decision

Create **`20-actors/shinan`** (指南 = "a guide / compass that points the way"), a clj-native,
kotoba-Datom-native R0 learning-support actor under the **学習解放 (learning-liberation)**
framing — **no carve-out**.

## Doctrine — sow the scaffold; growth belongs to the learner

shinan maps the OPEN-learning **supply** against the **demand** and surfaces where open
learning exists and where the gap is:

```
node-kinds:  :topic  (a study topic in the exam space — the DEMAND)
             :resource (an OPEN-license learning resource — the SUPPLY)

topic route ∈ {:covered :needs-localization :coverage-gap}
  :covered            — ∃ open resource covering it in the topic's country language
  :needs-localization — covered, but no resource in the country language (→ translate)
  :coverage-gap       — no open resource covers it (→ create open material)
resource route ∈ {:offer :monitor}     # :offer if openness ≥ 0.6, else :monitor
```

The **学習解放 worklist** = the gaps + localization needs — i.e. *where open learning is
missing*. That is the actor's value: it hands learners freely-available 足場 and points the
commons at what to build/translate next.

## The 学習解放 guarantee — what shinan is structurally incapable of (no carve-out)

shinan inherits manabi's gates WITHOUT relaxing them. The following are **unrepresentable**
(absent from the ontology/seed/datom-emitter, proven by `test_analyze` + `test_shinan_edn`):

- `:shinan/score` · `:shinan/grade` · `:shinan/rank` — never scores/grades/ranks a learner
  (no 偏差値/序列). *manabi G7.*
- `:shinan/pass-prediction` — never predicts pass/fail. *manabi N11/N3.*
- `:shinan/gate` · `:shinan/credential` · `:shinan/transcript` — gatekeeps nothing, issues no
  credential. *manabi G7.*
- `:shinan/timed-test` · `:shinan/leaderboard` · `:shinan/streak` — self-paced only, no
  addictive design. *manabi G10 + G3.*
- `:shinan.learner/*` · `:shinan.person/*` — **there is no learner in the model**; only topics
  and resources.
- `:shinan/official-pastquestion` — never reproduces official past-exam content. *cert_prep G16.*
- **Open-license-only** — non-open licenses are not enum members; `validate-open!` refuses a
  proprietary/paid/enrollment-gated resource on load AND at the heartbeat. The inverse of a
  paywalled cram platform.

## Implementation (R0, landed)

clj-native pure-stdlib methods (`shinan_edn` loader + `validate-open!` guard / `analyze`
coverage engine + worklist + EAVT `datoms` + report / `kotoba` content-addressed append-only
coverage ledger / `autorun` deterministic idempotent-by-content heartbeat that refuses non-open
resources) + `kotoba/ontology.shinan.edn` (open-license enum + `:unrepresentable` negative
space) + an 11-topic / 11-open-resource `:synthetic` seed across CN/KR/JP. **20 tests / 151
assertions green** under babashka (`bb 20-actors/shinan/run_tests.clj`). Seed result: 8
`:covered` / 2 `:needs-localization` (高考英语, 수능영어 — English-only OER) / 1
`:coverage-gap` (高考理科综合).

# Consequences

- The roster gains charter-clean exam learning-support that *cannot* become a scoring/ranking
  engine or a paywalled cram platform — the 学習解放 guarantee is structural, not policy.
- Composes with `関門 kanmon`: kanmon's `:open-pathway`/`:destake` routes inform shinan's
  coverage priorities (the gate ↔ the scaffold).
- **Separation follow-ups (R0)**: DID `did:web:etzhayyim.com:actor:shinan`, child repo
  `etzhayyim/com-etzhayyim-shinan`, west entry, RAD identity journal. Live curated
  open-resource ingest (open-courseware/gov-open catalogs) is G9-gated (operator/Council).
- Zero invariant amendments — by reusing manabi's gates rather than relaxing them, shinan
  needs no charter amendment.

# Alternatives Considered

- **Full carve-out (conventional 受験対策 with scoring/模試/合否予測)** — rejected by the
  founder: would require relaxing manabi G7/G10/N3, a Council Lv7+ amendment, and re-imports
  the credentialism/coercion harms the constitution rejects.
- **Observatory-lean (only catalog open materials)** — rejected as too thin for learning
  support; the supply/demand coverage map keeps the actor useful while staying clean.
- **Fold into manabi 学び** — rejected: manabi's gates forbid exam-facing work; a separate,
  named actor with its own structural guarantees is clearer and safer.

# References

- `20-actors/shinan/` — implementation (manifest, ontology, methods, seed, tests, CLAUDE.md)
- ADR-2606291500 — 関門 kanmon (the exam-gate observatory sibling)
- ADR-2605261045 — manabi 学び (the inherited anti-examination gates)
- ADR-2605264400 — manabi cert_prep sub-cell (the prior, IT-only study substrate)
- ADR-2605262130 / 2605312345 — kotoba storage substrate + Datom-first-class canonical state
- root `CLAUDE.md` §Actors — actor completion criteria (child repo → west → RAD)
