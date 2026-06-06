---
id: adr-2606052300-fuchi-maintainer-sustenance-allocator-r0
title: "ADR-2606052300: 扶持 (fuchi) — mission-aligned maintainer sustenance allocator (investment-fund inverse) R0"
status: proposed
doc_type: adr
topic: fuchi-maintainer-sustenance-allocator
authoritative: true
last_verified: 2026-06-05
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - fuchi-maintainer-sustenance-allocator
  - investment-fund-charter-clean-inverse
depends_on:
  - adr-2606032130-displacement-dividend-tenure-weighted-basic-high-income
  - adr-2605301020-basic-high-income-imputed-in-kind
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2605302000-warifu-open-zero-fee-card
  - adr-2605263500-wakai-mutual-aid-tier-b-actor-r0
  - adr-2605301036-mission-funding-earned-revenue-arm
  - adr-2606012100-okaimono-provisioning-commons
supersedes: []
superseded_by: []
---

# ADR-2606052300: 扶持 (fuchi) — mission-aligned maintainer sustenance allocator (investment-fund inverse) R0

**Status**: proposed
**Date**: 2026-06-05
**Deciders**: Jun Kawasaki

# Context

The question: *「etzhayyim として、etzhayyim の business / robotics / remote-control business を
推進する実際の信者(メンテナー)に対して投資を行うビジネス投資ファンドのアクターはあるか?
実世界でのメンテナーはやはり必要なので、必要なプロセス、system-of-systems を設計して。」*

The honest answer before this ADR: **no — and a conventional one is constitutionally prohibited.**
A "business investment fund that invests in members" requires equity / ROI / a return waterfall,
which collides head-on with the constitutional invariants:

- **非営利のみ / donation-only inflow** (ADR-2605192100 §1.3, 2605192115) — no `purchase` /
  `subscription` purpose, no external return.
- **cash≡0 / Basic High Income in-kind** (ADR-2605301020 N1) — benefits are imputed in-kind,
  never a cash stipend.
- **payoff帰属・意思決定権 = etzhayyim only** (repo CLAUDE.md Ownership rule) — a member cannot
  hold an equity stake or a profit claim.
- **speculative finance prohibited** (Charter-Rider §2(b)) — wakai already encodes `G6 NO
  investment return promise` / `N2 NOT investment fund`.

But the *need* is real and the user is right: **real-world maintainers must be able to live.**
Robotics and remote-control work especially cannot maintain itself — physical people repair,
operate, supervise, and keep hardware/software alive. The labor-liberation mission fails if the
humans who do the maintenance are not sustained.

So 扶持 is the **charter-clean INVERSE of an investment fund** — the same pattern by which
okaimono inverts Amazon, yadori inverts GoDaddy, nusa inverts a legalization lobby, and kamado
inverts a fossil refinery. 扶持 (封建期の **扶持米** — the in-kind rice stipend that sustained a
retainer so they could serve) allocates **in-kind sustenance + commons-asset access +
tooling/compute** to the maintainers (信者) who keep etzhayyim's actors alive. It is a
redistribution / sustenance allocator, **never an investor**.

# Decision

Add a Tier-B horizontal control-plane actor **扶持 (fuchi)** that computes and routes
covenant-gated, tenure-weighted, **in-kind** sustenance for real-world maintainers, sitting ON
TOP of the existing Public Fund + Displacement Dividend + Basic-High-Income machinery.

## The system-of-systems

扶持 orchestrates (it does not replace) the existing substrate:

| Layer | Existing system 扶持 stands on | Role |
|---|---|---|
| **Value source** | Public Fund (`50-infra/etzhayyim-public-fund`) + TitheRouter + Mission-funding revenue arm (ADR-2605301036) | the pool that funds sustenance (tithe + vendor surplus donation) |
| **Allocation math** | Displacement Dividend `allocate.py` (ADR-2606032130) | the `ln(1+min(tenure,40))×hazard` tenure curve, reused |
| **Delivery semantics** | Basic High Income in-kind (ADR-2605301020) | cash≡0; imputed in-kind value |
| **In-kind rails** | commons-land (LANDS.md) · mitsuho 食 · hikari エネルギー · Murakumo compute · okaimono 工具 · iyashi/hagukumi/kokoro ケア | how sustenance is actually delivered |
| **External liquidity** | warifu 0% qard-ḥasan (ADR-2605302000) + okaimono assisted-checkout (ADR-2606012100) | the member-principal path for irreducible external fiat |
| **Books / viz** | toritate 執帳 · kanae 鼎 | every allocation booked + rendered |
| **Governance** | 1 SBT = 1 vote + 48h timelock · Council Lv7+ | decides escalated allocations |
| **Memory** | kotoba Datom log `as-of` | append-only Wellbecoming contribution trajectory (非終末論) |

## The allocation process (lifecycle)

```
covenant (信者 SBT, §1.16-gated)
   → need assessment (in-kind envelope: housing/food/energy/compute/tooling/care/liquidity)
   → allocation compute (tenure-weighted share + in-kind floor; cash≡0; G1 instrument allowlist)
   → routing dispatch (envelope → in-kind rails; external fiat → member-principal warifu only)
   → governance gate (pure-function route)
        ├ auto         (optimistic fast-path, below ceiling, in-kind)
        ├ sbt-vote     (1 SBT = 1 vote, 48h timelock, above ceiling)
        ├ council-lv7  (invariant-adjacent, e.g. new commons-land grant)
        └ refused      (Charter-Rider §2 hit — no vote can promote it)
   → in-kind provisioning intents (NOT cash) → toritate books → kanae renders
   → Wellbecoming as-of append (non-eschatological; no "funded/exited" final state)
```

## Resolving the "maintainers need cash" tension (honest)

cash≡0 is an N1 structural invariant; 扶持 cannot and does not make a maintainer's external
fiat obligations vanish. Its honest mandate is twofold:

1. **Maximize in-kind substitution** — commons housing replaces rent, mitsuho food replaces the
   grocery bill, hikari energy replaces the utility bill, Murakumo/okaimono replace tooling spend.
   The `in_kind_coverage` metric reports how much of a maintainer's sustenance never touches fiat.
2. **Route the irreducible external residual to MEMBER-PRINCIPAL 0% liquidity** via warifu
   (qard ḥasan) / okaimono assisted-checkout — where the **member** is the borrower/payer and
   扶持 merely attests eligibility. 扶持 never holds, lends, or pays cash (§1.3 holds **without** a
   Lv7+ amendment; no-server-key). Full fiat-denominated income would require a Charter Lv7+
   amendment (cash≡0 is N1) and is explicitly out of scope (N4).

## Structural invariants (3-place enforcement)

Each invariant lives in three places at once — schema `:db/allowed`/enum + lexicon `:const`/`:enum`
+ Python `ValueError` (the nusa `:thc-class` / tazuna `:weaponizable` / kamado `:fossil-virgin-crude`
pattern), verified by `methods/test_charter_invariants.py`.

- **G1 — no investment vehicle.** `:alloc/instrument :db/allowed [:in-kind-grant :sustenance
  :tooling-access :compute-access]`; `:equity :debt :convertible :revenue-share :profit-claim
  :carry :dividend :exit` are UNREPRESENTABLE. `allocate.assert_instrument` raises on any of them.
- **G2 — cash≡0.** `:envelope/cash-usd-micros` and `:alloc/cash-usd-micros` are `:db/allowed [0]`;
  lexicon `const 0`; `Allocation.__post_init__` raises on nonzero cash.
- **G3 — in-kind rails only.** `:rail/kind` enum has no `:cash-disbursement`; the external residual
  is a `:liquidity-warifu` rail with `member_principal = true` only. `route_envelope` raises on a
  cash line.
- **G4 — covenant-gated.** `:maintainer/covenant ∈ {:outreach :vowed}`; `:anon`/`:server` absent.
- **G5 — payoff帰属 = etzhayyim.** `:maintainer/owns-payoff :db/allowed [false]`; a maintainer
  owning the payoff is a `ValueError`.
- **G6 — Wellbecoming, not productivity-score.** contribution = `:wb/*` as-of trajectory;
  `:score-of-soul` unrepresentable (kizashi G8 / tsumugi G2).
- **G7 — non-adjudicating allocator.** `:gov/route` is a PURE FUNCTION of (imputed-total,
  invariant-touch, rider); `:gov/decision` does not exist. 扶持 computes + routes; the vote /
  Council decides (the ake G2 pattern).
- **G8 — Murakumo-only inference** (ADR-2605215000).
- **G9 — no-server-key.** `:alloc/server-held-key :db/allowed [false]` (ADR-2605231525).
- **G10 — outward-gated.** live disbursement / provisioning / land grant / binding vote =
  Council Lv6+ + operator; invariant-adjacent (new commons-land grant) Lv7+. R0 = compute + dry-run.

## Non-goals

N1 not an investment fund · N2 not a wage/salary employer (no-payroll preserved) · N3 not a
lender (warifu is the 0% creditor; 扶持 only routes) · N4 not cash income (cash≡0) · N5 not a
productivity-surveillance system · N6 not the owner of maintainer work product · N7 not a gig
marketplace · N8 the allocator never decides.

# Artifacts

- Ontology: `00-contracts/schemas/maintainer-sustenance-ontology.kotoba.edn`
- Lexicons (5): `20-actors/fuchi/lex/{maintainerCovenant,sustenanceEnvelope,allocationIntent,routingPlan,governanceDecision}.edn`
- Cells (5, coded state machines; `.solve()` RuntimeError at R0):
  `covenant_intake` / `need_assessment` / `allocation_compute` / `routing_dispatch` / `governance_gate`
- Methods: `allocate.py` (tenure-weighted in-kind, cash≡0, G1 allowlist) · `route.py` (in-kind rail
  decomposition + the pure-function `gov_route`) · `analyze.py` (end-to-end dry-run)
- Seed: `20-actors/fuchi/data/seed-sustenance-graph.kotoba.edn` (5 maintainers, one per route)
- DID: registered in `INFRA_ACTORS` → `did:web:etzhayyim.com:actor:fuchi` + actor-profile seed
- Manifest / CLAUDE.md / MATURITY.md / README.md / run_tests.sh

# Empirical (R0)

`methods/analyze.py` over the `:representative` seed:

| maintainer | covenant | imputed USD/yr | in-kind | route | outcome |
|---|---|---|---|---|---|
| abel (robotics, 8y) | vowed | $8,500 | 100% | auto | accepted |
| seth (remote-teleop, 3y, ext. rent) | vowed | $28,000 | 50% | sbt-vote 11-2/48h | accepted |
| eve (new commons-land housing) | vowed | $18,000 | 100% | council-lv7 | pending |
| noah (pre-vow outreach) | outreach | $5,500 | 100% | auto | accepted |
| cain (requests affiliate ad-share) | vowed | $7,000 | 100% | refused | refused |

**149 tests green** (15 allocate + 13 route + 8 provision + 11 vote + 10 book + 10 couple +
15 analyze + 36 charter-invariants + 3 lexicons + 9 consistency/SSoT-drift-lock + 19 cells;
one-command `run_tests.sh`). cash≡0 holds on every allocation, provisioning intent, ledgerEntry and
seed line; the investment-instrument set is unrepresentable; the routing is the charter-clean
inverse of a cap-table.

# R1 a/b/c/d addendum (landed offline, same session)

The R1 limbs the user asked for, built and tested offline (live execution stays G10-gated):

- **(a) provisioning-intent wiring** (`methods/provision.py` + `provisioningIntent` lexicon +
  `:prov/*`). A `PROVIDER_REGISTRY` maps each in-kind rail to the **real producing actor / commons /
  infra**: food→`mitsuho`, energy→`hikari`, tooling→`okaimono`, care→`iyashi`, housing→`commons-land`
  (LANDS.md), compute→`murakumo`, liquidity→`warifu`. Each intent is a dry-run: `published=false`
  (G10), `cash=0` (G2), `serverHeldKey=false` (G9); the liquidity intent is `member_principal`
  (the member borrows via warifu 0% qard-ḥasan; 扶持 never holds, lends, or pays).
- **(b) real 1 SBT = 1 vote + 48h timelock** (`methods/vote.py` + `voteBallot` lexicon +
  `:ballot/*` `:vote/*`). Ballots dedupe by DID (1 SBT = 1 vote), `weight≡1` (no token-weighted
  plutocracy), a `:server`/`:anon` voter is unrepresentable (no-server-key), ballots cast outside
  `[opened_at, opened_at+48h]` are not counted, quorum is required (no thin-vote auto-accept), and
  `finalize()` **raises** if the timelock has not elapsed. seth's seed allocation now finalizes
  `5-1/48h✓`.
- **(c) toritate booking + kanae flow viz** (`methods/book.py` + `sustenanceBooking` lexicon +
  `:book/*` `:flow/*`). Each accepted in-kind rail is projected into a toritate `ledgerEntry` using
  **toritate's own category enum** (ADR-2605262900: `subsistence-flow`/`vocation-flow`/`care-flow`),
  `cashStipendUsd≡0`, `:payroll`/`:salary`/`:wage` unrepresentable; the member-principal liquidity
  rail is **not booked as income** (it is a member warifu loan, not a Public-Fund disbursement). A
  **kanae-renderable** internal sustenance-flow graph (`:flow/*`: Public Fund → 扶持 → provider →
  maintainer) is emitted for the viz layer — deliberately NOT the government `fundFlowEdge` (which
  is for external fiscal flows and carries mandatory non-adjudication fields).

- **(d) Displacement-Dividend cohort coupling** (`methods/couple.py` + `cohortEarmark` lexicon +
  `:event/*` `:earmark/*` `:couple/*`). The structural join to the labor-liberation mission's other
  half (ADR-2606032130): a **displacing actor's surplus** (sanae/hataori/kiyome/tazuna automating
  toil) → donation → **TitheRouter 10% split** (`gross = tithe + earmark`, exact integer split, the
  okaimono settlement-intent pattern) → a **per-cohort Public-Fund earmark** = the imputed-value
  BUDGET CEILING 扶持's in-kind sustenance for that cohort draws on. The **G2 coupling gate**: a
  displacement is admissible **only** if its cohort earmark is `funded` AND the committed in-kind
  floor is `≤ earmark` — *no live displacement without a funded cohort* (an unfunded or
  over-committed cohort is REFUSED; an actor may not shed human toil faster than the Public Fund can
  sustain the people affected). Honest: the surplus→donation is a REAL USDC inflow into the Public
  Fund (donations are USDC — allowed); what the maintainer/displaced worker RECEIVES stays in-kind,
  cash≡0. Seed demo: `cohort-sanae-2026` ($60k, funded → $6k tithe + $54k earmark) covers its $8.5k
  committed → admissible; `cohort-hataori-2026` ($0, unfunded) → REFUSED.

`analyze.py` runs the full `covenant → envelope → allocate → route → vote → provision → book →
couple` pipeline and writes `out/{allocation-dryrun.md, allocations, provisioning-intents,
toritate-ledger, kanae-flow, cohort-earmarks}.kotoba.edn`. 4 new lexicons (9 total); the
structural-invariant suite grew to 36 tests covering the R1 `:prov/:ballot/:vote/:book/:flow/
:earmark/:couple` invariants (including the exact 10% TitheRouter split and the G2 gate) in all
three places.

# Consequences

- **Positive**: the labor-liberation mission gains its missing limb — a structural, auditable way
  to sustain the real-world maintainers of every actor, without a single cash payment, without
  equity, and without amending a single invariant. Tenure-weighting honours long service; the
  governance gate keeps large/invariant-adjacent allocations under 1 SBT = 1 vote / Council.
- **Honest R0 limitations**: design + offline allocation only; `:representative` seed; no live
  disbursement / provisioning / land grant / binding vote (all G10-gated); the in-kind rails are
  not yet wired to the producing actors (R1); 扶持 cannot eliminate a maintainer's external fiat
  obligations — it maximizes in-kind coverage and routes the residual to member-principal 0%
  liquidity (N4); full fiat income remains a Charter Lv7+ matter.
- **Zero invariant amendments** — STRENGTHENS cash≡0 (ADR-2605301020), no-server-key
  (ADR-2605231525), payoff帰属=etzhayyim, Charter-Rider §2(b), and the non-profit / donation-only
  invariants.
