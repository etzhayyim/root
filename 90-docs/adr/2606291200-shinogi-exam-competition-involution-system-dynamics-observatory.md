---
id: adr-2606291200-shinogi-exam-competition-involution-system-dynamics-observatory
title: "ADR-2606291200: shinogi 鎬 — exam-competition involution (内卷) + failure-cycle system-dynamics observatory"
status: proposed
doc_type: adr
topic: shinogi-exam-competition-involution-system-dynamics-observatory
authoritative: true
last_verified: 2026-06-29
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/shinogi
depends_on:
  - adr-2605290927-junkan-societal-feedback-loop-observer
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - adr-2606082102-shiori-wellbecoming-detractor-observatory
  - adr-2605263700-kokoro-mental-health-support
  - adr-2605261045-manabi-education
  - adr-2606111500-hakoniwa-forward-simulation-observatory
supersedes: []
superseded_by: []
---

# ADR-2606291200: shinogi 鎬 — exam-competition involution (内卷) + failure-cycle system-dynamics observatory

**Status**: proposed
**Date**: 2026-06-29
**Deciders**: Jun Kawasaki

# Context

A user asked whether the org has an actor that analyzes **China's exam war (高考 /
gaokao)**, its **system dynamics**, and the **system cycle of exam failure (受験失敗)**.
It did not. The repo has a charter-clean toolkit for exactly this — `junkan 循環`
(ADR-2605290927) is an ANALYSIS-ONLY societal **system-dynamics** observer (stocks /
flows / reinforcing-balancing loops / Meadows leverage points), and `hakoniwa 箱庭`
(ADR-2606111500) runs forward-simulation of synthetic cohorts — but no actor pointed
either at the education / examination-competition domain. `manabi 学び` (ADR-2605261045)
*teaches*; it does not *map* the competition its learners are caught in.

The phenomenon is well-named: **内卷 (involution)** — a zero-sum effort arms-race where
everyone must invest ever more just to hold position, with no aggregate gain. Its human
cost concentrates in a **failure cycle**: a single-shot loss → stigma + identity damage →
wellbeing erosion → reduced next-attempt capacity/opportunity → reinforced penalty. This
is a sensitive domain (adolescent mental health, despair, self-harm), so any actor here
must be **wellbecoming-positive** (§1.13) and **non-eschatological** (§1.15): it maps the
spiral toward **relief**, it does not amplify despair, and it never becomes a roster of
"failing students" or a school/country shame-ranking.

# Decision

Author **`shinogi 鎬`** — the `junkan` system-dynamics method specialized to one domain:
**high-stakes examination competition**, China's 高考 first, with Korea 수능 / Japan 受験 /
India JEE-NEET / Finland / Germany as comparative siblings. 名 鎬: 「鎬を削る」 = to grind
the ridge of one's blade against another's — fierce mutual competition that wears everyone
down for no relative gain; the precise idiom for involution.

**Model.** Each **driver** (a concrete policy / institution / practice / norm — the gaokao
itself, 985/211/双一流 tiering, 户籍-linked quotas, 双减, 复读 culture, 衡水模式, the
内卷/躺平 norms, 普职分流, the one-child legacy, 考研/考公 escalation, the 2023 student
mental-health plan, plus the comparative siblings) feeds one of **six pressure stocks** with
a polarity (`:intensify` / `:relieve` / `:ambiguous`): **A** positional-scarcity · **B**
effort-inflation (the 内卷 core) · **C** credential-signaling · **D** wellbeing-erosion ·
**E** family-capture · **F** failure-penalty. Six structural **loops** (HYPOTHESES) join the
stocks; the **R-failure-despair** loop (failure-penalty ⇄ wellbeing-erosion) is the user's
"exam-failure system cycle," foregrounded and **routed toward relief** (kokoro 心 / shiori 栞).
Each driver records 誰が定めたか (`:enactor`), 経緯 (`:origin`), 関係者 (`:stakeholders`) as
on-the-record public facts; `shinogi` reads off, as disclosed HYPOTHESES (G5), per-stock
regimes (悪循環/好循環), per-loop drive, the failure-cycle relief gap, an era trajectory, and
**Meadows leverage candidates** (deepest-leverage relieving drivers to amplify + most
tractable intensifying drivers where the spiral could ease).

**Discipline (gates).** `shinogi` inherits `junkan`'s analysis-only spine:

- **G4 ANALYSIS-ONLY / NO ACTUATION** — no outward channel (no post/mention/email/tx/nudge);
  enforced by *absence* (no dispatch method; `:shinogi/actuate` + `:shinogi/dispatch`
  unrepresentable).
- **G5 no causal overclaim** — every loop/regime is `:shinogi/hypothesis :true`;
  `:shinogi.exam.loop/proven-cause` unrepresentable.
- **G6 aggregate-only / no individual** — drivers + institutional enactors only; **no
  per-student record, no exam score of any person, no PII** (`:shinogi.exam.driver/person`
  + `:shinogi.exam.student/score` unrepresentable).
- **G7 wellbecoming-positive / non-eschatological** — the failure cycle is stated soberly and
  routed to RELIEF (kokoro/shiori), never despair-amplified (§1.13 + §1.15).
- **G8 relief MAP, not shame-rank** — never a student/school/country ranking-to-shame
  (`:shinogi.exam.student/ranking` unrepresentable).
- **G9 append-only / immutable** content-addressed findings (verify-chain tamper-evident).
- **G11 no prescription** — Meadows leverage points are CANDIDATES with uncertainty
  (`:prescription? false`); `:shinogi/prescription` unrepresentable.
- **G13 council-internal default** — surfacing beyond Council is performed by ossekai/kataribe
  on shinogi's behalf, never by shinogi (preserves G4).

**Implementation (R0, landed).** clj-native, kotoba-Datom-native (root CLAUDE.md §"Operational
code = clj/bb"): `20-actors/shinogi/` with ontology + 18-driver/6-jurisdiction seed + 4 methods
(`shinogi_edn` loader · `analyze` read-off · `kotoba` content-addressed append-only findings
ledger · `autorun` deterministic idempotent-by-content heartbeat) + 5 test suites
(`bb 20-actors/shinogi/run_tests.clj` → **26 tests / 256 assertions green**). Static
did.json/profile under `50-infra/etzhayyim-did-web/public/actor/shinogi/` (verificationMethod
`[]`, no server-minted key). The loop does no network I/O; live public-data ingest
(MOE/KICE/MEXT/NTA aggregate statistics) is a G7/operator-gated R1 leg.

**Seed read-off (iteration 1, HYPOTHESIS).** The involution core spins **vicious**:
effort-inflation, positional-scarcity, and credential-signaling all read 悪循環; the strongest
intensifying driver is the gaokao itself; the deepest relieving leverage candidates are the
structural counter-examples (Finland's no-ranking comprehensive school L3, Germany's
de-stigmatized dual vocational track L4, China's 双减 L5). The latest era (2020–) nets toward
relief (双减 + mental-health plan + 躺平) — the spiral is contested, not monotone.

# Consequences

- The org gains a charter-clean, analysis-only map of the gaokao/内卷 involution and the
  exam-failure cycle, composing with `junkan` (method), `shiori` (relief-gap), `kokoro`
  (relief destination), `manabi` (alternative-pathway lens), and `hakoniwa` (forward-sim).
- The failure cycle — a sensitive, life-safety-adjacent topic — is handled within the
  Wellbecoming invariant: mapped soberly, routed to relief, never a despair amplifier or a
  shame-list (enforced in code + tests, not just documented).
- R0 lands the substrate only. Per the root CLAUDE.md Actors completion condition, the actor
  is **未分離** until: (1) child repo `etzhayyim/com-etzhayyim-shinogi`; (2) west
  `manifest/repos.edn` single-entry registration; (3) RAD identity journal
  `80-data/kotoba-rad/shinogi.identity.journal.edn`. These are tracked follow-ups.
- ZERO charter-invariant amendments.

# Alternatives Considered

- **A gaokao-scoped fork of junkan inside junkan's substrate.** Rejected: a distinct
  domain, stocks, loops, and the failure-cycle/relief-routing discipline warrant a distinct
  actor; junkan's governance-asymmetry substrate stays focused.
- **Name `uzu 渦` (whirlpool, for involution's "inward rolling").** Rejected on discovery
  that `uzu` is already taken (ADR-2606211500, a thermodynamic information-energy organism);
  `shinogi 鎬` (鎬を削る) was chosen as the precise, unused involution idiom.
- **Let `manabi` carry it.** Rejected: manabi teaches; it is explicitly anti-competitive-
  ranking and does not model competition dynamics. shinogi maps; manabi is its relief lens.
- **Allow an outward channel (publish findings).** Rejected for R0: like junkan, shinogi is
  analysis-only (G4 by absence); surfacing is carried by ossekai/kataribe (G13).

# References

- ADR-2605290927 — junkan (the parent system-dynamics method)
- ADR-2605192100 — Mission Charter (§1.13 Wellbecoming / §1.15 non-eschatological / §1.4 anti-individualism)
- ADR-2605262130 — kotoba storage substrate (Datomic-isomorphic kotoba-kqe)
- ADR-2606082102 — shiori (Wellbecoming detractor + relief-gap)
- ADR-2605263700 — kokoro (mental-health support; failure-cycle relief destination)
- ADR-2605261045 — manabi (education; alternative-pathway lens)
- ADR-2606111500 — hakoniwa (forward-simulation observatory)
- `20-actors/shinogi/` — implementation (manifest + ontology + seed + methods + tests)
