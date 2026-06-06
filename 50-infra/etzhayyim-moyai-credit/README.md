# etzhayyim-moyai-credit — 舫い inference reciprocity credit (reference impl)

The **non-monetary, give-to-get reward** for participating in commons inference
(ADR-2606062100). Contribute verified inference → MINT credit; draw discretionary surplus
inference → BURN credit. *To obtain information you must generate information*
(情報を得るためには情報を生成する).

**The reward is real, but it is not money, not a benefit, not governance, and it does not
touch Basic High Income.** It is a commons-use-right (入会権) on the very resource you helped
produce — reciprocity, not welfare.

## Run

```bash
bash run_tests.sh          # 46 tests across 6 suites
python3 methods/analyze.py # end-to-end give-to-get demo + transparency report
```

## Modules (`methods/`)

| File | Role |
|---|---|
| `ledger.py` | Append-only, non-monetary, **non-transferable** credit ledger. mint + burn are the ONLY verbs (no transfer/gift/pool exists). Half-life **decay** (anti-hoarding → a flow, not a store). **Conservation**: minted ≤ verified; no overdraw. |
| `proof_of_contribution.py` | The anti-fraud membrane: **honeypot** challenge jobs + **spot-check** recomputation (against frozen-edge-model core-node oracles) + **dedupe/replay** rejection + per-identity **earn-rate cap** + **all-or-nothing slashing**. Only verified work mints. |
| `fair_share.py` | The **Basic-High-Income firewall** + scheduler. Unconditional subsistence floor = *information-as-BHI*; credit governs only *discretionary surplus under contention*. `affects_basic_high_income()` ≡ False. |
| `analyze.py` | End-to-end: honest contributors mint, a sybil mints 0, draws show free-floor / idle-free / surplus-charge / deferred, invariants asserted. |

## Why this is charter-clean (ADR-2606062100)

Five structural locks (lexicon `const` + code + tests):
`redeemableUsdMicros=0` (cash≡0) · `transferable=false` (anti-sybil) ·
`affectsBasicHighIncome=false` (the firewall) · `grantsGovernanceWeight=false` (1 SBT=1 vote)
· `grantsBenefitOrStage=false` (anti-class; the G4 carve-out is scoped to commons-draw-rights
only). Plus decay (anti-hoarding) and conservation (no inflation).

## Anti-fraud, in one sentence

Because credit is non-monetary, non-transferable, decaying, and redeemable only for the very
compute it took to earn, **faking contribution costs at least what the contribution it
imitates would cost — there is no arbitrage**, so sybil/farming is structurally
self-defeating, not merely policed (test: `faking_no_payoff`).

## Honest R0/R1 status

Design + reference implementation + offline tests. The verification oracle is modelled as a
deterministic frozen-edge-model stand-in; live mint/burn against the running Murakumo mesh +
kotoba Datom log, and live external-node enrollment, remain **Council + operator gated**
(inherits ADR-2606012100 G9). Supersedes the legacy RisingWave credits economy.
