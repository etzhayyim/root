# etzhayyim-kawase-pool

Religious-corp adherent-to-adherent multi-stable remittance pool contract
family per **ADR-2605282200** (kawase-yui — 為替結).

## What this is

One Solidity contract per Base L2 stablecoin: `KawaseYuiPool<USDC>`,
`KawaseYuiPool<EURC>` (R1 launch), `KawaseYuiPool<JPYC>` (R2), … The
contracts together implement the L6 settlement layer of the kawase-yui
6-layer pool topology — pre-funded local pools + Chainlink mid-market
oracle ±0.5% band + Adherent-SBT-gated deposit / claim + Council Lv6+
  ≥4/7 attested bounded-AMM policy and circuit breaker.

## What this is NOT

- **NOT a commercial remittance MSB.** No license sought; structurally
  pinned to adherent mutual aid via the `onlyAdherent` modifier reading
  `AdherentRegistry.tokenOf(msg.sender) != 0`.
- **NOT proprietary FX arbitrage.** The system does not take directional
  positions or hide an operator spread.
- **NOT an unrestricted DEX.** Constant-product and concentrated-liquidity
  adapters are permitted, but stable pairs, adapter/hook codehashes, LP fee,
  protocol fee, oracle deviation, price impact, liquidity and participant
  min-out are all bounded and disclosed.
- **NOT a custom token.** Settlement uses canonical Base L2 stablecoins
  (USDC + EURC at R1); accounting uses existing mKOTO via ADR-2605282100.

## Status

| Phase | Scope | State |
|---|---|---|
| **R0** | This README + `src/KawaseYuiPool.sol` interface + Constitution wiring (KAWASE_MAX_BAND_BPS + KAWASE_PER_MONTH_CAP_USD_MINOR via `f732e4bc4`) + G7 lint hook (via `6644094ba`) + 8 Lexicons under `com.etzhayyim.kawase.*` (via `23eca3bdc`) | **landed** (path no longer reserved) |
| **R0.1** | Uniswap v4 exact-input adapter + fresh Chainlink cross-rate/sequencer gate + reviewed-runtime registry/observer + local lifecycle tests | **landed locally; not deployed** |
| **R1** | Implementation of `deposit() / claim() / rebalance()` + Chainlink oracle integration + Forge tests + Deploy script + Council Lv6+ ≥3 ratification | post-Bootstrap-Council ratify (RFP closes 2026-06-19) |
| **R2** | +JPYC pool (Polygon-bridged via LayerZero; Council Lv6+ ≥3 bridge audit required) | post-R1 + 30-day public objection |
| **R3** | +KRWO / +GBPe / +CHFe (Council Lv7+ unanimity per pair) | post-R2 |

## Constitutional wiring (read at deploy time)

The skeleton reads two constitutional values from the `Constitution`
contract via the canonical `ConstitutionKeys` library:

```solidity
import {ConstitutionKeys as K} from "../../etzhayyim-chain-contracts/src/ConstitutionKeys.sol";

bytes32 maxBandBps = constitution.getConstant(K.KAWASE_MAX_BAND_BPS);
// 50 (= ±0.5%) — constitutional (G4); cannot be widened by governance.

bytes32 perMonthCap = constitution.getMutable(K.KAWASE_PER_MONTH_CAP_USD_MINOR);
// 1_000_000_000 (= $1,000) R1; Council Lv6+ ≥3 may raise for R2/R3.
```

Both keys are wired into `Deploy.s.sol` + `DeployReligiousCorp.s.sol` and
asserted in `test/ConstitutionReligiousCorpWave.t.sol`
(`test_kawase_yui_constants_set`).

## Hard invariants (Solidity-level structural enforcement)

The R1 implementation MUST honor these without exception. Any future
change that loosens one of these is a constitutional amendment, not a
patch:

- **G3 Adherent-only** — `onlyAdherent(msg.sender)` reverts when
  `adherentRegistry.tokenOf(msg.sender) == 0`. Applied to both
  `deposit()` and `claim()`.
- **G4 Mid-market band** — `deposit()` reverts when
  `|fxRateBps - chainlinkBps| > maxBandBps` where `maxBandBps` is read
  from `Constitution.getConstant(KAWASE_MAX_BAND_BPS)` at call time
  (= 50 bps = ±0.5%).
- **G5 No extractive protocol spread** — LP compensation, protocol revenue
  and price impact are separate. R1 protocol fee is zero; the immutable
  ceiling is 5 bps and the LP fee ceiling is 30 bps.
- **G6 Bounded AMM** — `validateAmmQuote()` refuses excessive fees,
  oracle deviation above 50 bps, participant min-out breach and unavailable
  output liquidity. R1 additionally binds deadline and approved
  adapter/hook codehash.
- **G9 Per-month cap** — `deposit()` reverts when sender's rolling 30-day
  USD-equivalent volume would exceed
  `Constitution.getMutable(KAWASE_PER_MONTH_CAP_USD_MINOR)`.
- **G11 No chargeback** — there is no `reverse()` or `unwind()` function.
  Disputes route off-chain via chigiri.disputeMediation per ADR-2605262700.
- **G14 Per-jurisdiction Lv7+ unanimity** — enforced off-chain by the
  `kawase_jurisdiction_compliance` Pregel cell consulting the
  `jurisdictionAttestation` Lexicon set before each pre-flight; the
  contract has no direct jurisdiction check.
- **Council-only rebalance** — `rebalance(...)` reverts when
  `msg.sender != councilSafe`. The Council Lv6+ ≥4/7 threshold is
  enforced at the Safe layer (4-of-7 multisig signing requirement).

## Bounded Uniswap v4 integration

`KawaseYuiV4Adapter.sol` implements one exact-input swap against one immutable
v4 `PoolKey`. It follows PoolManager's unlock callback lifecycle, then settles
the negative input delta and takes the positive output delta. Before settlement
it reads `KawaseYuiChainlinkOracle.sol` itself and applies the policy contract
to the decimal-normalized execution rate, cross-rate, min-out and disclosed fee.
The request cannot supply or override its own oracle value. The oracle validates
both feed rounds, answers, timestamps, feed-specific maximum ages and decimals,
and rejects Base sequencer downtime and the configured post-recovery grace
period. Dynamic fees, native currency,
arbitrary hook data, multicall, delegatecall and liquidity-management entry
points are intentionally absent.

`KawaseYuiAmmRegistry.sol` records the reviewed runtime codehash of the adapter,
PoolManager and optional hook, plus the R1 zero protocol-fee observation. Its
Council pause is fail-closed. Because an external PoolManager's protocol fee can
change without calling this registry, an observer must pause on mismatch before
the next execution; the recorded observation is evidence, not control over the
external contract.

Council may designate safety observers that can only pause—not unpause or
approve—when a nonzero protocol fee is observed for an approved pool. Reading
the external PoolManager state and submitting that observation is still an
off-chain operational responsibility; the registry provides its least-authority
on-chain circuit-breaker endpoint.

This is an integration scaffold, not a deployment authorization. Mainnet
addresses, a fresh-oracle implementation, Council ratification, fork tests and
an independent security review remain R1 gates.

## Related

- ADR-2605282200 — kawase-yui charter (this contract family's authoritative ADR)
- ADR-2605282100 — mKOTO economy (operator-side compute-cost layer)
- ADR-2605263500 — wakai mutual aid (sibling actor)
- ADR-2605262700 — chigiri legal procedure (dispute mediation cross-actor)
- ADR-2605192130 — TitheRouter / 10% tithe (NOT used at R0-R3 per §5 Kisha exemption)
- ADR-2605172100 — payments substrate (Base L2 + USDC + ERC-4337)
- `00-contracts/lexicons/com/etzhayyim/kawase/` — 8 Lexicons (deposit /
  withdraw intent / match execution / fx rate / pool state /
  rebalance / jurisdiction / silen review)
- `50-infra/etzhayyim-chain-contracts/src/ConstitutionKeys.sol` —
  `KAWASE_MAX_BAND_BPS` + `KAWASE_PER_MONTH_CAP_USD_MINOR` keys
- `70-tools/scripts/lint/verify_no_commercial_remittance.py` — G7
  build-time enforcement (Wise / Western Union / etc. import gate)
