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

**Model — the whole involution LIFECYCLE.** The spiral does not end at the exam, so `shinogi`
models three coupled phases. Each **driver** (a concrete policy / institution / practice /
norm) feeds one of **nine pressure stocks** with a polarity (`:intensify` / `:relieve` /
`:ambiguous`):

- **Phase 1 EXAM** — **A** positional-scarcity · **B** effort-inflation (the 内卷 core) ·
  **C** credential-signaling · **D** wellbeing-erosion · **E** family-capture ·
  **F** failure-penalty (drivers: gaokao, 985/211/双一流, 户籍 quotas, 双减, 复读, 衡水模式,
  内卷/躺平 norms, 普职分流, one-child legacy, 考研/考公, the 2023 mental-health plan).
- **Phase 2 LABOR** — **G** labor-absorption-deficit = **卒業即失業** (graduate unemployment),
  the user's "no job after graduation" question (drivers: 高校扩招 massification, 毕业即失业,
  学历贬值, 35岁现象, 996).
- **Phase 3 WITHDRAWAL** — **H** effort-efficacy-collapse = **頑張れない** (the user's "youth
  cannot strive," framed structurally per §1.4 — the system eroded effort's efficacy, NOT
  laziness) · **I** withdrawal-prevalence = **躺平/寝そべり** (lying flat), held as a rational +
  self-protective response, never pathologized (drivers: 985废物, 慢就业, 全职儿女, 摆烂, 润 +
  稳就业/grassroots relief).

Ten structural **loops** (HYPOTHESES) join the stocks. Two are foregrounded as sober,
relief-routed read-offs answering the user directly: **R-failure-despair** (the 受験失敗 cycle,
→ kokoro/shiori) and the pair **R-effort-futility + R-lying-flat-spiral** (the 卒業後
頑張れない/躺平 cycle, → kokoro/shiori/manabi), with **R-degree-devaluation** as the through-line
that leaks the exam involution into the labor market. The comparative siblings include the
lost-generation precedents — Japan's 就職氷河期 / さとり世代 / ひきこもり / 8050問題 and Korea's
N포세대 / 헬조선 — showing the withdrawal phenomenon is not China-specific and has documented
precedents (and belated remedies, e.g. Japan's 2019 ice-age-generation support programme).
Each driver records 誰が定めたか (`:enactor`), 経緯 (`:origin`), 関係者 (`:stakeholders`) as
on-the-record public facts; `shinogi` reads off, as disclosed HYPOTHESES (G5), per-stock
regimes (悪循環/好循環), per-loop drive, both cycle relief-gaps, an era trajectory, and
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

**Three deeper layers (R0, landed).** Beyond the static regime read-off, shinogi carries:

1. **Stock-flow SIMULATION** (`simulate.cljc`) — the loops become a coupling matrix and the
   driver net pressures the exogenous forcing; the 9 stocks roll forward (deterministic Euler, no
   Math/random) to an equilibrium. Applying a structural intervention flips the vicious spiral —
   on the seed the involution-index falls **0.59 → 0.16** (頑張れない 1.0→0.03, 躺平 0.80→0.04). A
   structural WHAT-IF (G5), never a forecast (N3), never a directive (G11).
2. **Wellbecoming ENERGY-FLOW design** (`energy_flow.cljc`) — the answer to "design the energy
   flow that turns this causality into wellbecoming." Adopting the uzu 渦 dissipative-energy view
   (ADR-2606211500): society pours an enormous **effort-energy** flow in, but today it **dissipates**
   in the 内卷 zero-sum channels (current wellbecoming ≈ 0.04 despite maximal effort). shinogi
   designs a **re-routing of the same effort-energy** into wellbecoming-yielding channels (intrinsic
   learning / wellbeing protection / alternative pathways / labor absorption) → designed wellbecoming
   ≈ 0.42 (gain 0.38, conserving the total flow). **Two ledgers are never the same unit** (uzu
   G1/G2): effort-energy is a conserved FLOW, wellbecoming a separate INDEX (§1.13); `:yield` is a
   reference coupling, never an identity. The design's drive-overrides feed `simulate` to exhibit the
   flip. A structural DESIGN / CANDIDATE (§1.4 — it re-routes systemic effort, never directs a
   person; G11), every override relief-only (never adds pressure).
3. **Social-protocol ACTIVITY** (`social.cljc`) — shinogi is active on AT-proto: it projects its
   disclosed-hypothesis findings + the energy-flow design into `app.bsky.feed.post`-shaped DRY-RUN
   mirror posts (≥2 sources G5, non-adjudicating + analysis-only disclaimer G7, person-excluded G6,
   `:post/server-held-key false`). **G14**: `build-live` RAISES — live broadcast is gated on a member
   CACAO leash (ADR-2606111400) + Council Lv6+ (ADR-2606281500 seed-and-grow doctrine); G4 is
   preserved BY ABSENCE of any autonomous live-publish path (drafts are inert until a member signs).
   This reconciles "the actor performs social-protocol activity" with shinogi's analysis-only spine.

**Implementation (R0, landed).** clj-native, kotoba-Datom-native (root CLAUDE.md §"Operational
code = clj/bb"): `20-actors/shinogi/` with ontology (9 stocks / 10 loops) + 33-driver/
6-jurisdiction seed + 7 methods (`shinogi_edn` loader · `analyze` read-off · `simulate`
stock-flow simulation · `energy_flow` wellbecoming re-routing · `kotoba` content-addressed
append-only findings ledger · `autorun` deterministic idempotent-by-content heartbeat · `social`
dry-run publication membrane) + 8 test suites (`bb 20-actors/shinogi/run_tests.clj` → **43 tests
/ 446 assertions green**). Static did.json/profile under `50-infra/etzhayyim-did-web/public/actor/shinogi/`
(verificationMethod `[]`, no server-minted key). The loop does no network I/O; live public-data
ingest (MOE/KICE/MEXT/NTA aggregate statistics) is a G7/operator-gated R1 leg.

**Seed read-off (iteration 1, HYPOTHESIS).** The involution spins **vicious** across the whole
lifecycle: the exam core (effort-inflation, positional-scarcity, credential-signaling) and all
three downstream stocks — labor-absorption-deficit (卒業即失業), effort-efficacy-collapse
(頑張れない), withdrawal-prevalence (躺平) — read 悪循環. The 卒業後 withdrawal cycle carries a
large **relief-gap** (pressure ≈2.48 vs relief ≈0.29): the relief drivers (稳就业, Japan's
ice-age support) are small against the pressure, an honest read that the back half of the
spiral is the least-cushioned. The deepest relieving leverage candidates remain the structural
counter-examples (Finland's no-ranking comprehensive school L3, Germany's de-stigmatized dual
vocational track L4, China's 双减 L5). The exam-phase latest era (2020–) nets toward relief
(双减 + mental-health plan + 躺平) — the exam spiral is contested, but the labor/withdrawal
spiral is not yet meaningfully balanced.

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
