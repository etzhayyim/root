---
id: adr-2606122001-tanemaki-public-fund-grant-steward
title: "ADR-2606122001: tanemaki 種蒔き — Public Fund grant-steward (fund-manager inversion): public DD + disclosed criteria, vote-decided"
status: proposed
doc_type: adr
topic: tanemaki-public-fund-grant-steward
authoritative: true
last_verified: 2026-06-12
priority: 5.0
axis: architecture
weight: 0.5
priority_note: "First Public-Fund OUTFLOW steward; the fund-manager inversion — public DD over candidate grantee orgs with disclosed criteria, decision held at 1 SBT = 1 vote."
authoritative_for:
  - public-fund-grant-steward
  - fund-stewardship-ontology
  - public-fund-dd-criteria
depends_on:
  - 2605192145
  - 2605192130
  - 2606052300
  - 2605312345
  - 2605231525
  - 2605215000
  - 2606062100
  - 2606032000
related:
  - 2606022000
  - 2606011800
  - 2606072000
  - 2606021600
  - 2606082100
  - 2606052300
supersedes: []
superseded_by: []
---

# ADR-2606122001: tanemaki 種蒔き — Public Fund grant-steward (fund-manager inversion)

**Status**: proposed
**Date**: 2026-06-12
**Deciders**: Jun Kawasaki

# Context

The founder asked (2026-06-12): does etzhayyim have an actor that performs **investment /
investment-target decisions for the Public Fund, including due diligence**? The survey answer
was: no, and structurally there cannot be one — the investment shape (equity / ROI / return
waterfall) is unrepresentable under the Tier-0 priorities (非営利のみ / Donation 流入のみ,
ADR-2605192100 §1.6; fuchi 扶持 made the inversion explicit for the inflow-to-members side,
ADR-2606052300 G1). What DOES exist is the other half of the question, designed but never
actor-ized: the Public Fund's **outflow judgment** — which existing organizations should
receive Public Fund money — lives in ADR-2605192145 as the GrantGovernor (1 SBT = 1 vote +
timelock) plus a `PublicFundGrantCell` evaluation cell sketch, status proposed, with no DD
substance: no criteria, no screens, no evidence supply, no public scorecard.

Meanwhile the observatory lineage matured into exactly the evidence base a public DD needs:
kanjō 勘定 (disclosed financials, live EDGAR leg), kabuto 兜 (supply-chain concentration),
tsumugi 紡ぎ (取-concentration), kosatsu 高札 (designation landscape), ooyake 公 (government/
registry records), shiori 栞 (relief-gap). All non-adjudicating, all public. The follow-up
direction: design the **fund-manager org role** — public judgment of fund deployment to
favorable existing organizations, evaluation criteria included.

# Decision

Introduce **tanemaki 種蒔き** ("the sower" — seed scattered freely, no return expected), a
Tier-B **Public Fund grant-steward** that is the **charter-clean inversion of a fund
manager**, with the steward boundary **enforced in code and proven by tests**: a fund manager
decides allocations and owes its LPs a return; tanemaki evaluates **in public** and owes the
members the truth — **the vote decides**.

1. **`fund-stewardship-ontology` (`00-contracts/schemas/`)** — nodes `:fs/kind` ∈ `{:org
   :screen :criterion :source :instrument :milestone}`; edges `{:screened (w/ :en/finding)
   :meets (w/ :en/weight + :en/evidence) :sourced-from :disburses-via :watched-by}`. Two
   load-bearing tables: `:instrument/allowlist` (only grant / milestone-escrow / in-kind are
   true — the investment vocabulary is false) and `:decision/authority` (`:tanemaki false`,
   `:sbt-vote true`).
2. **The DD pipeline (公開, screens fire BEFORE weighting)** — intake (anyone may propose,
   per ADR-2605192145) → **hard screens** S1..S6 (適格性, each anchored to a disclosed
   charter/Rider citation: S1 非営利整合 · S2 Rider §2 非抵触 · S3 open-by-default 成果公開 ·
   S4 受領適法性 · S5 私的捕獲なし · S6 透明性床) → **evidence** fused from the observatory
   lineage (public surfaces only) → **weighted rubric** C1..C8 with PUBLIC weights, Σ = 1.0
   (C1 mission-fit 0.20 · C2 openness 0.15 · C3 financial stewardship [kanjō] 0.15 · C5
   取-release [tsumugi/kabuto] 0.15 · C4 governance [ooyake] 0.10 · C6 wellbecoming evidence
   [shiori] 0.10 · C7 additionality 0.10 · C8 capacity [kabuto] 0.05) → **route** ∈
   `{:excluded, :insufficient-evidence, :propose}` — **there is no `:fund` route** → advisory
   proposal → **1 SBT = 1 vote** (GrantGovernor + timelock) → milestone watch
   (attestation-gated tranches, ADR-2605192145 §4).
3. **Edge-primary analyzer (`analyze.py`)** — per org: screen findings, evidence-coverage,
   dd-fit = Σ weight_c × min(1, Σ incident `:meets` weight) computed on READ (no stored org
   score, N1). `criteria()` **raises on a rubric whose disclosed weights do not sum to 1.0**;
   `recommend_route()` **raises if a screen-conflicting org would route to `:propose`**.
4. **Scorecard + proposal (`propose.py`)** — `render_scorecard()` renders the PUBLIC 参考意見
   card (content-addressed CIDv1+SHA-256, voters can verify the bytes); `build_proposal()`
   emits an **UNSENT** `com.etzhayyim.tanemaki.grantProposal` (`advisory: true`, `bindsFund:
   false`, `decidedBy: "1-sbt-1-vote"`, `status: drafted-unsent`) and **refuses + explains**
   for any org whose route is not `:propose`. `assert_instrument` raises on
   equity/debt/convertible/revenue-share/carry/exit (the fuchi G1 pattern);
   `assert_no_investment_language` rejects 出資/持分/配当/ROI/exit/利回り text in a
   justification.
5. **Seed (G6, ALL FICTIONAL)** — 8 representative orgs exercising all three routes (3
   `:propose` · 3 `:excluded` via S2/S5 conflicts · 2 `:insufficient-evidence`), 6 screens
   with real charter anchors, the 8-criterion rubric, 7 evidence sources mapped to actors,
   3 give-only instruments, 2 milestones. **A real org in the committed seed is test-enforced
   to fail** — evaluating a real organization is a G7-gated live leg from primary disclosure
   only (the kanjō pattern, ADR-2606032000).
6. **Lexicons** — `com.etzhayyim.tanemaki.{ddScorecard, grantProposal}`: the public advisory
   card (route enum has no funding member; `advisory`/`decidedBy` structurally fixed) and the
   unsent proposal record (give-only instrument enum; `bindsFund` must be false).
7. **kotoba pywasm component** — `analyze`/`datoms`/`coverage`/`scorecard`/`propose` exports;
   G1 + no-server-key hold in WASM (the component can refuse, draft and explain; it cannot
   move funds, vote, or submit).

**Constitutional gates**: G1 steward-not-sovereign (no :fund route; refusals raise;
vote-decided) · G2 no investment instrument (give-only allowlist; investment language
rejected) · G3 non-adjudicating DD (disclosed facts w/ named sources, never worth-verdicts) ·
G4 public-by-default (rubric Σ=1.0 enforced; scorecards content-addressed; no data room) ·
G5 evidence honesty (coverage floor; undetermined ⇒ insufficient) · G6 synthetic seed
(real-org DD G7-gated) · G7 outward-gated (on-chain submission = member/operator + Council) ·
G8 no-server-key · G9 conflict-of-interest disclosure (相互監視) · G10 Murakumo-only.
**31 tests green**, incl. the G1 no-conflicted-proposable, G2 unrepresentability, G4
rubric-sum and G6 synthetic-seed invariants.

# Consequences

- **Positive**: closes the Public-Fund outflow gap with a working, tested steward whose
  every judgment input — criteria, weights, screens, findings, evidence sources, scorecards —
  is public on the append-only Datom log; the decision stays exactly where ADR-2605192145 put
  it (1 SBT = 1 vote + timelock). The observatory lineage becomes a DD evidence supply without
  any observatory gaining adjudication power. fuchi (inflow, internal members) and tanemaki
  (outflow, external orgs) now bracket the fund with the same give-only instrument algebra.
- **Boundary**: tanemaki is **not** a fund manager, an investor, or a grant decider — it
  cannot represent an investment, cannot vote, cannot move funds, and refuses to draft for
  ineligible or under-evidenced orgs. The 参考意見 framing is identical to the
  PublicFundGrantCell positioning ("判断は cell が出すが、決定権は SBT holder の vote にある").
- **Negative / deferred**: R0 is offline + synthetic — no live observatory fusion (the
  `:meets` evidence edges are representative fixtures), no on-chain GrantGovernor submission
  (contracts await Base testnet, post-Council), no real-org evaluation (G7), and the G9
  conflict-of-interest declaration is schema + gate only, not yet a signed-record flow.
  Council Seats 2-5 RFP (closes 2026-06-19) precedes any binding vote.

# Alternatives Considered

- **A literal investment arm (fund manager as-is)** — rejected categorically: equity/ROI is
  unrepresentable under 非営利のみ / Donation 流入のみ (Tier-0); fuchi ADR-2606052300 already
  established the inversion pattern. The whole point is to invert the model, not replicate it.
- **Fold into fuchi 扶持** — rejected: fuchi allocates sustenance to covenanted INTERNAL
  maintainers (need-based, tenure-weighted); tanemaki evaluates EXTERNAL organizations
  (evidence-based screens + rubric). Same instrument algebra, different subject, different
  failure modes (fuchi: paternalism; tanemaki: reputational adjudication) — each needs its own
  guards.
- **Let the PublicFundGrantCell sketch stand without an actor** — rejected: the cell sketch
  has no criteria, no screens, no evidence supply and no public-scorecard surface; the user's
  ask ("評価基準なども含めて, public に判断") is precisely the substance the sketch lacks.
  tanemaki implements the cell's lane and can back it when the cell runtime lands.
- **Score real organizations in the seed** — rejected: a committed scorecard over a real org
  is reputational adjudication (N3) regardless of intent; the sukashi/hakoniwa synthetic-seed
  precedent applies. Real-org DD enters only through the G7 gate from primary disclosure.

# References

- ADR-2605192145 (Public Fund architecture — GrantGovernor + PublicFundGrantCell + milestone escrow)
- ADR-2605192130 (10% tithe → Public Fund) · ADR-2605192100 (Mission Charter §1.6 非営利)
- ADR-2606052300 (fuchi 扶持 — the give-only instrument-allowlist inversion pattern)
- ADR-2605312345 (kotoba Datom = canonical state) · ADR-2605231525 (no-server-key) · ADR-2605215000 (Murakumo-only)
- ADR-2606062100 (3-Tier Charter) · ADR-2606032000 (kanjō — primary-disclosure live-leg pattern)
- evidence siblings: ADR-2606022000 (kabuto) · 2606011800 (tsumugi) · 2606072000 (kosatsu) · 2606021600 (ooyake) · 2606082100 (shiori)
