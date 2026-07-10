# credits — Credit Ledger & Public Fund Routing

**DID**: `did:web:credits.etzhayyim.com`
**Status**: R0 first real slice (2026-07-10) — methods + charter-gate tests only
**See also**: `CLAUDE.md` (full command/policy reference), `MIGRATION-TODO.md`
(substrate-boundary remediation checklist, still pending on the legacy
`actor-manifest.jsonld`)

## Overview

credits is the yoro.etzhayyim.com human-participation credit ledger: Earn
(HC tasks / Murakumo compute) -> Purchase (fixed 30% platform fee) -> Spend
(fixed 10% automatic public-fund allocation), with anti-fraud rate limiting
and an HC reputation gate. Before this slice the actor had only
`CLAUDE.md` + `MIGRATION-TODO.md` + a legacy `actor-manifest.jsonld` (0%
scaffold — no methods, no cells, no tests).

## What this slice adds

| File | Purpose |
|---|---|
| `manifest.edn` | 9 constitutional gates (G1-G9), derived 1:1 from CLAUDE.md's Purchase/Allocation Policy + Anti-Fraud sections and MIGRATION-TODO.md's substrate-boundary list — no invented policy |
| `methods/purchase.cljc` | `preview-purchase` — fixed 30% platform-fee deduction (G1) |
| `methods/spend_allocation.cljc` | `compute-spend-allocation` / `resolve-destination` — fixed 10% public-fund split + the 4-destination enum + default (G2/G3) |
| `methods/anti_fraud.cljc` | `check-spend-allowed` / `check-earn-allowed` — rate limits, high-value-earn reject, HC reputation gate, duplicate-reward reject (G4-G7) |
| `methods/ledger_rails.cljc` | non-fiat native-asset constant + banned-payment-vendor predicate (G8/G9) |
| `methods/test_*.cljc` | per-method unit tests |
| `methods/test_charter_gates.cljc` | the umbrella charter-gate suite (also cross-checks `manifest.edn` declares exactly G1-G9) |

All methods are **pure functions**: no I/O, no live ledger/db write, no
payment-gateway call, no fabricated user/financial data. Test run: **37
tests / 76 assertions, green**. Auto-discovered by `bb test:actors`
(ADR-2606131500 discovery convention) — no `bb.edn` edit was needed or made.

## Constitutional gates (G1-G9)

- **G1** Purchase platform fee is a fixed 30% of `gross_amount`.
- **G2** Spend public-fund allocation is a fixed 10% of every spend.
- **G3** Allocation destination must be one of the 4 declared destinations
  (`public-fund:common` / `-education-family` / `-health-access` /
  `-climate-resilience`); unset preference resolves to `public-fund:common`.
- **G4** Anti-fraud rate limits: spend <=60/hour, earn <=30/hour.
- **G5** A single earn transaction >50 credits is rejected.
- **G6** HC-sourced reward requires `approval_rate >= 50%`.
- **G7** Duplicate reward for the same `task_id`/`session_id` is rejected.
- **G8** The ledger's native asset (`"credit"`) is never a fiat currency.
- **G9** No commercial payment-processor / ads-analytics vendor (Stripe,
  PayPal, GA4, Meta Pixel) is a valid settlement rail.

## Left out of scope this slice (deliberately)

This is a **0% -> first-real-slice** increment, not full charter
completion. Explicitly NOT built:

- Any live ledger / `kotoba-datomic` wiring — methods are pure, in-memory only.
- Lexicon schemas (`00-contracts/lexicons/com/etzhayyim/credits/*`) — none exist yet.
- Pregel cells — none created; no `40-engine/.../cells/credits_*` path-reservation yet.
- The GCC Ethereum token layer (wallet / minter / treasury / Chainlink price feed).
- Real USDC / ERC-4337 / `etzhayyim-tithe-router` integration (MIGRATION-TODO.md's
  Stripe/PayPal -> USDC codemod is still pending — untouched this slice).
- DID-bind authentication wiring (MIGRATION-TODO.md item).
- Replacing/retiring the legacy `actor-manifest.jsonld` (k8s-langserver /
  Cypher-query shape) — left as-is; `manifest.edn` is additive, not a replacement.
- Any credit-scoring / credit-history bureau functionality — out of scope
  for this actor's stated charter entirely (it is a ledger + fee/allocation
  router, not a scoring system) and doubly out of scope for a 30-minute slice.
- No real people's financial data anywhere — all test fixtures are synthetic
  literal numbers (`100`, `10`, `1000`, ...), no fabricated user records.

## Roadmap

| Phase | Scope |
|---|---|
| **R0 first slice** (this) | `manifest.edn` gates + pure methods + charter-gate tests |
| **R1** | Wire one method into a real Pregel cell reading/writing `kotoba-datomic`; author the first Lexicon (`creditWallet` or `creditTransaction`) |
| **R2** | Begin MIGRATION-TODO.md substrate-boundary codemod (Stripe/PayPal -> USDC, DID-bind auth) |
| **R3** | Legacy `actor-manifest.jsonld` retirement once R2 codemod lands |

## Related Files

- `/20-actors/credits/CLAUDE.md` — full command/policy reference (Commands, Credit Rates, Data Model, GCC Token)
- `/20-actors/credits/MIGRATION-TODO.md` — substrate-boundary remediation checklist
- `/20-actors/credits/actor-manifest.jsonld` — legacy k8s-langserver manifest (pre-substrate-boundary; untouched this slice)
