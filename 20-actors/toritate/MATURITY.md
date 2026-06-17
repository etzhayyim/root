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
| Tests | ✅ `methods/test_charter_gates.cljc` — **7 tests, green** (added 2026-06-16; previously NO dedicated test — only sibling cross-refs) — pins on-chain / no-fiat / no-payroll / tithe-split / donor-PII / Council gates; `./run_tests.sh` |
| Methods | ⛔ no offline engine yet (R1) |

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

> **2026-06-17 substrate-native migration (ADR-2606160842):** the charter-gate test above was ported Python→Clojure (`methods/test_charter_gates.py` → `methods/test_charter_gates.cljc`, ns `toritate.methods.test-charter-gates`, reads the lexicons via cheshire/edn) and the Python was pruned. Run via `./run_tests.sh` (now `exec bb`) or `bb run test:charter` (all 34 charter suites; 244 tests / 924 assertions green). Assertions unchanged (1:1 port).
