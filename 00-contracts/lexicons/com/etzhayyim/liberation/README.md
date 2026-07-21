# com.etzhayyim.liberation.* — Lexicons

Per ADR-2605261000 (Labor Liberation Transition Mechanism — 7-Stage Liberation Ladder L0..L6).

These lexicons operationalize the mission KPI (`labor_hours_liberated_per_adherent_per_week`) and the Adherent SBT stage state machine.

**PRIVACY INVARIANTS**:
- `metricReport`: aggregate-only, no PII (structural via `additionalProperties: false`)
- `wellbecomingAttestation`: `encryptedPayloadCid` mandatory (ADR-2605181100 envelope)
- `adherentExitNotice`: only `exitHappened: true` public; cause stays encrypted

**BASIC HIGH INCOME (ADR-2605301020)**: `metricReport` carries a required
`basicHighIncome` block — non-cash income/asset accounting (imputed income FLOW
+ commons-asset access STOCK). `cashStipendUsd` is pinned `const: 0`: its
presence-and-zero in every report is the structural on-chain proof that §5 N1
(no fiat-replacement UBI) holds. Figures are computed by toritate
(ADR-2605262900) against open valuation tables in
`orgs/etzhayyim/com-etzhayyim-toritate/valuation/`. Aggregate-only (no per-adherent leaderboard).

| Lexicon | Purpose |
|---|---|
| `metricReport` | Quarterly mission KPI (aggregate hours liberated + `basicHighIncome` block; no PII) |
| `stageAdvanceAttestation` | Per-stage L_n → L_{n+1} Council multisig + gate checks |
| `wellbecomingAttestation` | Quarterly self-report (encrypted; failure → stage hold not revoke) |
| `adherentExitNotice` | Voluntary stage exit (only fact-of-exit public) |

## Related ADRs

- ADR-2605261000 — Liberation Ladder master
- ADR-2605301020 — Basic High Income doctrine (imputed-income + commons-asset; `basicHighIncome` block)
- ADR-2605262900 — toritate accounting (computes `basicHighIncome` figures; valuation tables)
- ADR-2605181100 — Encrypted records (wellbecoming envelope)
- ADR-2605260215 — Aggregation pattern (yakushi×mitate cross-actor AE — same pattern for `metricReport`)
- ADR-2605172600 — Adherent SBT issuance base
- ADR-2605192145 — Public Fund Architecture (reserve sizing source)
