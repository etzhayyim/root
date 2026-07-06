# toritate 執帳 — Maturity

**Stage: R0** (scaffold) — ADR-2605262900. Accounting aggregation + transparent reporting +
audit-attestation substrate, **NOT a commercial accounting package**. 100% on-chain ledger,
no fiat / no commercial accounting software, no payroll, the 90/10 tithe split. Cross-linked
by 7+ sibling actors (wakai backstop / Public Fund / Tithe / Land Trust).

| Dimension | State |
|---|---|
| Lexicons | ✅ 5 under `com.etzhayyim.toritate.*` (ledgerEntry / financialAttestation / auditObservation / annualReport / externalAuditorEngagement) |
| Cells | 🟡 path-reserved in `40-engine/.../cells/toritate_*` (R0) |
| Manifest | ✅ present |
| Tests | ✅ `methods/test_charter_gates.cljc` + `methods/test_imputed_income.cljc` — **18 tests / 45 assertions, green** (`bb test:toritate` / `./run_tests.sh`) — pins on-chain / no-fiat / no-payroll / tithe-split / donor-PII / Council gates, plus the imputed-income engine's own invariants (incl. a drift guard cross-checking its hardcoded enums against the Lexicons) |
| Methods | ✅ `methods/imputed_income.cljc` — R0 reference implementation for ADR-2605301020 Basic High Income accounting: `compute-imputed-income` (FLOW) + `compute-commons-asset-value` (STOCK), both reading `valuation/v1-retail-equiv.json` rather than duplicating its figures; `basic-high-income-report` (the ADR-2605301020 §5 Liberation Metric `basicHighIncome` block, `cashStipendUsdMicros` structurally always 0); `ledger-entry` (G3/G4/G8/G12). `solve()` raises — accounting computation only, NOT a live ledger write |

## Charter gates pinned by the test

- **G3/G4 100% on-chain** — `ledgerEntry` requires `chain` + `txCid` + `counterpartyDid` +
  `amountUsdMillicents`; `chain` enum is **exactly** {base-l2, geth-private, ipfs-record-only}
  (no off-chain rail representable).
- **G8 no fiat** — `ledgerEntry.nativeAsset` is **exactly** {usdc, eth, n-a}; no fiat token
  (usd/jpy/eur/gbp/cny/fiat) is representable.
- **G8 commercial-software / fiat-leak surfaced** — `auditObservation.observationCategory`
  can flag `commercial-accounting-software-integration-attempt` + `fiat-leak-attempt` +
  `tithe-split-mismatch`.
- **G12 no payroll** — no `salary`/`wage`/`payroll`/`bonus`/`compensation` ledger category;
  the volunteer-economy flows (`subsistence-flow` / `vocation-flow`) exist instead.
- **tithe 90/10** — `tithe-split-90pct-operational` + `tithe-split-10pct-public-fund`
  categories present.
- **donor-PII protection** — `financialAttestation` requires `publishedDonorPii`; enum is
  exactly {none, aggregated-only, opt-in-explicit}.
- **Council attestation** — `annualReport` + `externalAuditorEngagement` require `councilAttestations`.

## R0 → R1 gate

Council Lv6+ ≥3 baseline + the 5 ledger/report/audit cells + the annual audit cycle wired
(MST publish + IPFS pin ≥2 nodes). UPL-equivalent boundary (G5): toritate prepares the
data package; external-auditor opinion stays off-chain.
