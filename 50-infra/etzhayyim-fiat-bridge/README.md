# etzhayyim-fiat-bridge — Stripe Issuing → ERC-4337 + USDC bridge (etzhayyim side)

**Status**: Phase δ P0 landed — Reserve.sol Foundry contract + 25 tests. XRPC handler + Sepolia deploy + lexicons pending.
**Design**: ADR-2605212050
**Tracking**: ADR-2605211950 Open Item (4)

## What this directory holds

The **etzhayyim side** of the fiat → on-chain bridge. The vendor (etzhayyim) keeps Stripe Issuing + fiat receivable accounting; this side mints USDC on Base L2 from a Council-controlled reserve when vendor calls
`org.etzhayyim.payment.creditFromFiat`. Per ADR-2605211950 substrate axis: fiat = centralized = vendor; chain mint = decentralized = etzhayyim.

## Phase δ P0 — what landed

- `contracts/src/Reserve.sol` — Council-owned USDC reserve with:
  - **operator** allowlist (the etzhayyim XRPC service address) — only operators can call `creditFromFiat`
  - **daily cap** (mutable, Council-governed; default 50,000 USDC equivalent)
  - **idempotencyKey** mapping prevents Stripe authorization replay
  - **atomic 90% / 10% split** to recipient + Public Fund Safe per ADR-2605192130 tithe
  - **mutable titheBps** (Council-governed, capped at 50% to make accidental misconfig a revert)
  - **withdraw** by Council for monthly excess reconciliation
  - reads: `reserveBalanceMicros`, `remainingDailyCapMicros`, `isIdempotencyKeyConsumed`
- `contracts/script/Deploy.s.sol` — `run(councilSafe, usdc, publicFundSafe, dailyCapMicros)`.
  Base mainnet USDC: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
  Base Sepolia USDC: `0x036CbD53842c5426634e7929541eC2318f3dCF7e`
- `contracts/test/Reserve.t.sol` — 25 tests (construction / credit happy + reverts / daily cap rollover / tithe behavior / Council config / withdraw). All passing.
- `contracts/lib/forge-std` submodule.

## Phase δ P1+ — what's next

- **XRPC handler** Worker scaffold at `src/` (mirrors etzhayyim-authz/src/). Endpoints:
  - `org.etzhayyim.payment.creditFromFiat` (vendor → etzhayyim, x-internal-trust JWT auth)
  - `org.etzhayyim.payment.requestFiatBridgeRefund` (recipient → etzhayyim)
- **Lexicons** under `00-contracts/lexicons/org/etzhayyim/payment/`:
  - `creditFromFiat.json` (procedure)
  - `requestFiatBridgeRefund.json` (procedure)
  - `fiatBridgeReceipt.json` (record)
  - `fiatBridgeRefundReceipt.json` (record)
- **Vendor-side callback** lexicon for refund hook (`com.etzhayyim.authz.fiatBridgeRefundCallback`) — lands in vendor repo via cross-repo PR.
- **Reserve solvency monitor**: cron that pages Council when `reserveBalanceMicros` drops below the 30-day burn minimum.
- **Base Sepolia deploy + smoke**: same pattern as etzhayyim-authz / etzhayyim-k2.
- **Operator key custody**: the XRPC service's signing key for `creditFromFiat` lives in CF Secrets; Council rotates per security policy.

## Solvency invariant

Per ADR-2605212050 §D5: **etzhayyim never mints USDC it does not have**. `creditFromFiat` reverts with `InsufficientTreasuryReserve` if the reserve balance is below the requested amount. Vendor then refunds the Stripe authorization on its side and the user sees a declined card. There is no synthetic USDC issuance.

## Council escalation path

- Service-key compromise → Council `setOperator(compromised, false)` immediately.
- Daily cap tunable via `setDailyCap` for traffic ramps; default 50,000 USDC/day.
- Tithe ratio tunable via `setTitheBps` (capped 0–50%); default 1000 bps = 10.00% per ADR-2605192130.
- Withdraw excess via `setOwner` / `withdraw` → Council Safe.
