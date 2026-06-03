# Displacement Dividend (ADR-2606032130)

The redistribution half of the OSS-robotics actor wave (ADR-2606032100). When an
etzhayyim robotics actor (sanae / hataori / kiyome / …) automates a human occupation
away, the displaced workers are made **better off, not worse** — through a
tenure-weighted, **in-kind** Basic-High-Income transition, funded by the displacing
actor's own surplus-donation and governed by the Public Fund.

## The four invariants it never breaks

| Invariant | How this design holds it |
|---|---|
| cash≡0 (N1) | No worker ever receives cash. `cash_stipend_usd_micros == 0` everywhere; the dividend is imputed income + commons-asset access (ADR-2605301020). |
| no payroll | Workers are covenant members on the Liberation Ladder, not employees. |
| donation-only inflow | Cohort pools are funded via `TitheRouter.donate()` earmarked `displacement-dividend`; never a fee/premium. |
| adherent-gated, universally admissible | Full dividend on the conversion covenant (§1.16); the gate is open to every displaced human, none paid as an outside transaction. |

## Tenure-weight formula (勤続年数連動)

```
w_i        = ln(1 + min(tenure_years_i, 40)) * hazard_i      # hazard ∈ [1.0, 2.0]
share_i    = w_i / Σ w_j                                      # Σ share = 1 over the vowed cohort
floor_i(t) = min(prior_imputed_i, stage_ceiling) * clamp(1 - t/5yr, 0, 1)
```

`share` governs **onboarding priority** (who is provisioned first under a scarce stage
cap) and the **in-kind transition floor** — never a cash split. `ln(1+·)` compresses the
gradient (a 40-year veteran ≈ ~2× a 5-year worker, not 8×) so seniority is honoured
without re-creating wage inequality inside the commons (N6 anti-leaderboard).

## Files

- `allocate.py` — pure-stdlib reference allocator (auditable; matches `DisplacementDividend.sol`).
- `test_allocate.py` — invariant tests (`python3 test_allocate.py`, 10/10).
- Solidity module: `50-infra/etzhayyim-chain-contracts/src/DisplacementDividend.sol` (R0 scaffold).
- Lexicon: `00-contracts/lexicons/com/etzhayyim/give/displacementTenureAttestation.json`.

## Status

R0 design-only. Solidity mutators revert `NotYetActivated()`; the allocator is a reference
calculation; pool sizing and `hazard` table are Council-attested at R1. No live disbursement.
