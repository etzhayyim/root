---
id: adr-2606062101-moyai-inference-reciprocity-credit
renumbered_from: "2606062100"
title: "ADR-2606062101: moyai 舫い — non-monetary inference reciprocity credit (give-to-get; reward kept, Basic High Income untouched)"
status: accepted
doc_type: adr
topic: moyai-inference-reciprocity-credit
authoritative: true
last_verified: 2026-06-06
priority: 6.0
axis: architecture
weight: 0.55
priority_note: "resolves the 'reward for inference participation' directive without amending any constitutional invariant"
authoritative_for:
  - the reward for participating in commons inference (moyai credit) and its non-monetary, non-transferable, decaying, commons-scoped nature
  - the charter-clean carve-out to ADR-2606012100 G4 (compute donation grants no benefit) — scoped strictly to a commons-draw-right, never welfare/benefit/governance
  - the Basic-High-Income firewall (subsistence inference floor = information-as-BHI; credit governs only discretionary surplus under contention)
  - the anti-fraud / sybil-resistance design for a non-monetary reward (proof-of-contribution, conservation, non-transferability, decay, earn-rate caps)
  - the supersession of the legacy RisingWave-era credits economy (vertex_credits_af_event / mv_ameno_credits_balance / credits BPMN)
depends_on:
  - ADR-2606012100 (Donation-funded operation + compute-node participation — the three node forms; G4 this ADR carves out)
  - ADR-2605215000 (Murakumo-only inference — the commons donated nodes serve)
  - ADR-2605301020 (Basic High Income — the firewall this ADR must not breach; cash≡0 N1)
  - ADR-2605261000 (Labor Liberation ladder — anti-class N2/N3 the carve-out must not violate)
  - ADR-2605241900 (baien edge-target — frozen edge models = verifiable determinism)
  - ADR-2605231525 (No server-side signing key — node co-signs mints; server cannot mint)
  - ADR-2605312345 (kotoba Datom first-class canonical state — the append-only ledger home)
  - ADR-2605192345 (Steward succession — cites the 入会権 / iriai-ken commons-use-right precedent)
related:
  - adr-2605150600-ameno-browser-inference-platform
  - adr-2604271400-mcp-invoke-fee-and-erc8004-murakumo-bridge
  - adr-2604281400-oss-contribution-royalty-gcc-redistribution
  - adr-2605262130-kotoba-storage-substrate-unification
supersedes:
  - "legacy credits economy: 00-contracts/bpmn/com/etzhayyim/credits/* + ameno vertex_credits_af_event / mv_ameno_credits_balance (ADR-2605150600 §credit) — RisingWave-era, pre-charter, non-compliant"
superseded_by: []
---

# ADR-2606062101: moyai 舫い — non-monetary inference reciprocity credit

**Status**: accepted (landed on `main` 2026-06-06 via PR #1184, merge `62e4c2c`; 46 tests green. Council Lv6+ ratification of the live mint/burn enablement remains the standing gate per §5/§6.)
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki (author); Council Lv6+ ≥3 (ratify live enablement); 30-day public objection period
**ADR Hierarchy**: extends ADR-2606012100 (compute-node participation) with a reward layer; carves out its G4 narrowly; does **not** amend any constitutional invariant.

## Context

The directive: **keep a reward for participating in inference — but it must not affect Basic High Income; it is the give-to-get kind, where to obtain information you must generate information (情報を得るためには情報を生成する).** And: **raise the maturity** of the design past an R0 stub.

Three facts frame this.

1. **A reward for inference participation already existed — then was (rightly) deleted.** The RisingWave-era ameno design (ADR-2605150600) credited a "Tier 2 wallet" (`vertex_credits_af_event` / `mv_ameno_credits_balance`) on every browser inference, and `00-contracts/bpmn/com/etzhayyim/credits/*` (`rewardFromCompute`, `spendCredits`, …) modelled a spend economy. The religious-corp charter wave then made **compute participation a pure, uncompensated donation** (ADR-2606012100): `compensatedUsdMicros=0`, `grantsBenefit=false`, no quid-pro-quo (G4). That was correct *as a defence of cash≡0 and anti-class* — but it threw out the reward entirely, and the credits substrate it replaced was RisingWave (now forbidden, ADR-2605262130).

2. **A reward is forbidden only if it is money, a benefit, or governance.** The constitutional invariants are specific: `non_profit_only` / `donation_only`, cash≡0 (N1, ADR-2605301020), anti-class (N2/N3, ADR-2605261000), 1 SBT = 1 vote. None of these forbids a **non-monetary use-right on a commons you helped produce.** That is exactly the **入会権 (iriai-ken, commons-use-right)** the repo already recognises (ADR-2605192345): a villager earns the right to draw firewood from the common woodland by helping maintain it — never "income", never a "benefit", never a vote. Reciprocity is not welfare.

3. **The honest objection to a reward is sybil/farming — and that objection has a structural answer.** ADR-2606012100 deleted the reward partly to kill the farming incentive. But a reward that is **non-monetary, non-transferable, decaying, and redeemable only for the very compute it took to earn** has *no arbitrage to farm*: faking contribution costs at least what the contribution it imitates would cost.

So the reward can be **kept** and **matured**, charter-clean, if and only if it is shaped as a give-to-get reciprocity credit with a hard Basic-High-Income firewall and a real proof-of-contribution membrane.

## Decision

Introduce **moyai 舫い** — a non-monetary inference **reciprocity credit**. (舫い / もやい: mooring lines that tie boats together; communal mutual-aid and shared ownership — もやい直し. The credit *ties a contributor to the commons*.)

### 1. The give-to-get loop

- **Earn (mint)**: a donated node (ameno / e7m / kotoba — ADR-2606012100 §3) contributes inference to the Murakumo commons. **Verified** work (see §4) MINTS `moyai` credit, bound to the contributing DID.
- **Spend (burn)**: a member draws *discretionary surplus* inference from the commons by BURNING credit. "To draw from the well you must have fed it."
- The credit is the **reward** — the thing the directive says to keep. It is real: verified work yields a positive, spendable balance that secures surplus compute under contention.

### 2. Five structural locks (what makes a reward charter-clean)

Enforced in three places each — lexicon `const` + Python construction + test — mirroring the repo's invariant-enforcement pattern (nusa `:thc-class`, kamado `:fossil-virgin-crude`, fuchi `:alloc/instrument`):

| Lock | Value | Invariant defended |
|---|---|---|
| `redeemableUsdMicros` | **const 0** | non-monetary; cash≡0 (N1); cannot be income → **does not affect Basic High Income** |
| `transferable` | **const false** | non-transferable; the ledger has no transfer/gift/merge/pool verb → sybils cannot recombine credit |
| `affectsBasicHighIncome` | **const false** | the explicit directive: moyai never touches BHI |
| `grantsGovernanceWeight` | **const false** | 1 SBT = 1 vote untouched (anti-class) |
| `grantsBenefitOrStage` | **const false** | never a Liberation-Ladder / welfare / priority-for-benefits path — the G4 carve-out is scoped *strictly* to commons-draw-rights |

Plus **decay** (half-life): credit is a *flow*, never a hoardable store of wealth/power (Wellbecoming 動的軌跡; anti-class). And **conservation**: minted ≤ verified contribution; a burn can never exceed live balance.

### 3. The Basic-High-Income firewall (the load-bearing constraint)

moyai is a **congestion fair-share scheduler, not a toll-gate** (`fair_share.py`):

| Situation | Served | Credit |
|---|---|---|
| within the **subsistence floor** | always, unconditionally — *information-as-Basic-High-Income* | 0 |
| above floor, **mesh idle** | free for everyone | 0 |
| above floor, **mesh congested** | discretionary surplus; contributors first | burns credit |
| above floor, congested, **no credit** | **deferred, not denied** — essential floor already served | 0 |

Every member (and the public read path) gets the floor **by need, never by contribution**. A zero-credit member is *never* denied essential information and their BHI is *completely untouched*; they only wait — behind contributors — for *non-essential surplus when the mesh is busy*. `affects_basic_high_income()` is a const-`False` function, and the test suite proves a credit-rich whale and a zero-credit member receive the **identical** floor.

This is the precise reading of the directive: the reward governs *discretionary surplus information under scarcity*, which is reciprocity; it never gates *essential information*, which would make information a benefit.

### 4. Anti-fraud / sybil-resistance (now load-bearing — a reward exists again)

`proof_of_contribution.py`, defence-in-depth:

1. **Honeypot challenge jobs** — a fraction of each batch have answers the commons already knows (precomputed on pinned core Murakumo nodes against **frozen, deterministic edge models**, ADR-2605241900). Fabricators fail; frozen-model determinism makes the oracle exact and cheap.
2. **Spot-check recomputation** — a deterministic-but-unpredictable (`hash mod`) fraction of ordinary jobs are recomputed on core nodes.
3. **Duplicate / replay rejection** — work is content-hashed and bound to (node, nonce); the same work cannot be double-submitted.
4. **Per-identity earn-rate cap** — caps minting per identity per period (anti-whale; and, with non-transferability, anti-sybil-split: each fake identity caps independently and the splits can't be merged).
5. **All-or-nothing batch slashing** — any verification miss ⇒ the batch mints **zero** and the node cools down.

The economic core, made a test (`faking_no_payoff`): a fabricated batch mints 0; an honest batch of equal size mints full. Because credit is non-monetary, non-transferable, and decays, the **only** thing it buys is *your own* discretionary surplus draw — earnable only by doing the very verified work a draw would consume. **Faking contribution costs at least as much as the contribution it pretends to be. There is no arbitrage.** Sybil is structurally self-defeating, not merely policed.

`no-server-key` (ADR-2605231525): the contributing node co-signs each contribution attestation; the server cannot mint unilaterally.

### 5. Maturity (past R0)

This ADR ships, not just designs:

- **Lexicons** `00-contracts/lexicons/com/etzhayyim/moyai/` — `contributionAttestation` (mint) + `drawReceipt` (burn), carrying the five const locks.
- **Reference implementation** `50-infra/etzhayyim-moyai-credit/methods/` — `ledger.py` (append-only, decay, conservation, non-transferable by construction), `proof_of_contribution.py` (the anti-fraud membrane), `fair_share.py` (the BHI firewall + scheduler), `analyze.py` (end-to-end demo).
- **46 tests green** (`run_tests.sh`): ledger 10 · proof-of-contribution 10 · fair-share 9 · lexicons 6 · charter-invariants 7 · analyze 4 — including a structural charter-invariant suite (cash≡0 / non-transferable / BHI-firewall / no-governance / anti-class-decay / reward-actually-exists / conservation) asserted across code **and** parsed lexicons.

The empirical demo: three honest contributors mint (60/40/20); a sybil submitting fabricated work mints **0**; draws show free-floor + idle-free + surplus-charge + deferred, with the freeloader's essentials guaranteed on every draw and BHI provably untouched.

### 6. Supersession of the legacy credits economy

moyai is the kotoba-native, charter-clean successor to the RisingWave-era reward economy: `00-contracts/bpmn/com/etzhayyim/credits/*` and the ameno `vertex_credits_af_event` / `mv_ameno_credits_balance` credit path (ADR-2605150600) are **superseded**. Those minted on raw inference with no verification, no BHI firewall, no non-transferability, and on a forbidden store (RisingWave, ADR-2605262130). moyai replaces them on the kotoba Datom log with the locks above.

## Consequences

**Positive**
- The reward is **kept** (directive satisfied) without amending a single constitutional invariant: it is non-money, non-benefit, non-governance, BHI-neutral.
- Scarcity → contribution: the Charter's Murakumo-only / no-commercial-GPU bottleneck becomes a reciprocity engine — contribute compute, draw surplus compute.
- Sybil/farming is structurally unprofitable, not merely policed; the anti-fraud story is stronger *with* a non-monetary reward than the deleted-reward baseline claimed.
- Replaces a forbidden (RisingWave) reward substrate with a kotoba-native, append-only, auditable one.

**Negative / risks**
- **Verification cost**: honeypot + spot-check consume core-node compute (the price of trustless mint). Mitigation: tunable fractions; coverage floor kept modest; honeypots are cheap on frozen deterministic models.
- **"Reward → benefit" misread** (the prosperity-gospel optics ADR-2606012100 feared). Mitigation: the five const locks + the public framing that moyai buys only discretionary surplus compute and *nothing else*, ever.
- **Floor calibration**: too low a subsistence floor could make essential info feel gated. Mitigation: the floor is method-versioned + Council-attested, generous by policy, and the firewall is tested to be credit-independent.
- **Determinism dependency**: verification leans on frozen-edge-model determinism. Mitigation: governance/actor-critical inference still cross-checks/pins to core nodes (inherits ADR-2606012100 mitigations); non-deterministic models are out of the honeypot path.

## Alternatives Considered

1. **Keep compute donation rewardless (status quo, ADR-2606012100).** Rejected by the directive — a reward is explicitly wanted; and a charter-clean one exists.
2. **Pay contributors cash / a redeemable token.** Rejected: commercial GPU rental + cash≡0 + anti-class violation (this is exactly what ADR-2606012100 Alt-2 rejected). moyai is non-monetary and non-redeemable.
3. **Make the reward a Liberation-Ladder / benefit priority.** Rejected: anti-class N2/N3 (ADR-2605261000); `grantsBenefitOrStage=false`.
4. **Gate all inference behind credit (pure pay-per-use).** Rejected: that gates *essential information* → makes information a benefit and dents BHI. The subsistence floor + idle-free rule confine credit to discretionary surplus under contention.
5. **Transferable/tradeable credit (a market).** Rejected: transferability re-enables sybil pooling and a shadow currency. Non-transferable + decaying by construction.
6. **Resurrect the RisingWave credits BPMN/MV.** Rejected: forbidden store (ADR-2605262130), no verification, no firewall. moyai supersedes it on kotoba.
7. **Trust self-reported contribution (no verification).** Rejected: re-opens the farming hole. Proof-of-contribution (honeypot + spot-check + dedupe + cap + slash) is the membrane.

## Outcome (closing, 2026-06-06)

**Landed.** Lexicons (`com.etzhayyim.moyai.{contributionAttestation,drawReceipt}`), reference
implementation (`50-infra/etzhayyim-moyai-credit/` — ledger / proof_of_contribution /
fair_share / analyze), and the **46-test** suite merged to `main` (PR #1184, `62e4c2c`),
green pre- and post-merge. The directive is satisfied with **zero invariant amendments**: a
reward for inference participation **exists** (verified work mints a spendable balance that
wins scarce surplus compute) yet is structurally non-money, non-benefit, non-governance, and
**Basic-High-Income-neutral** (the subsistence inference floor is served by need, never by
contribution; credit governs only discretionary surplus under contention). The legacy
RisingWave credits economy is superseded.

**Standing gate (not closed):** this ADR ships the design + offline reference impl. Live
mint/burn against the running Murakumo mesh + kotoba Datom log, and live external donor-node
enrollment, remain **Council Lv6+ + operator** gated (inherits ADR-2606012100 G9). The
verification oracle is a deterministic frozen-edge-model stand-in until wired to pinned core
nodes. Follow-ups: Murakumo-mesh binding of the fair-share scheduler; toritate aggregate
transparency of minted/burned totals (no per-donor leaderboard); ameno/e7m client surfaces.

## References

- ADR-2606012100 (compute-node participation — the three node forms; G4 carved out here)
- ADR-2605215000 (Murakumo-only inference — the commons)
- ADR-2605301020 (Basic High Income — cash≡0 N1; the firewall)
- ADR-2605261000 (Labor Liberation ladder — anti-class N2/N3)
- ADR-2605241900 (baien edge-target — frozen-model determinism)
- ADR-2605231525 (no server-side signing key)
- ADR-2605312345 / 2605262130 (kotoba Datom canonical state; no RisingWave)
- ADR-2605192345 (steward succession — 入会権 commons-use-right precedent)
- ADR-2605150600 / 2604271400 / 2604281400 (legacy reward designs — superseded/related)
- `00-contracts/lexicons/com/etzhayyim/moyai/` (contributionAttestation + drawReceipt)
- `50-infra/etzhayyim-moyai-credit/` (reference impl + 46 tests)
