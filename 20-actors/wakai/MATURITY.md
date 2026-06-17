# wakai 和会 — Maturity

**Stage: R0** (scaffold) — ADR-2605263500. Member-to-member SOLIDARITY POOL, **NOT
insurance** (no premium-as-contract / actuarial pricing / claim adjudication / policy
denial / underwriting / investment-return / commercial (re)insurance / DeFi speculation).

| Dimension | State |
|---|---|
| Lexicons | ✅ 5 under `com.etzhayyim.wakai.*` (contribution / distribution / poolStateReport / publicFundBackstopRequest / silenWakaiReview) — const fields fully populated (README's "R0 skeleton" note is now outdated) |
| Manifest | ✅ `manifest.jsonld` |
| Tests | ✅ `methods/test_charter_gates.cljc` — **7 tests, green** (added 2026-06-16; previously NO dedicated test — only sibling cross-refs in mimamori/kawase-yui) — pins the anti-insurance / anti-speculation const ledger; `./run_tests.sh` |
| Cells | ⛔ none yet (R1 — contribution / distribution / pool-state / backstop cells) |
| Methods | ⛔ no engine yet (R1) |

## Charter gates pinned by the test

- **G3 NOT insurance** — `mutualAidDistributionAttestation.claimAdjudicated` const false;
  `silenWakaiReview.claimDenialEventsCount` const 0.
- **G4/G5 no commercial (re)insurance** — `silenWakaiReview.commercialInsuranceSoftwarePenetrationPct`
  + `commercialReInsurancePenetrationPct` const 0.
- **G6 no investment-return / no speculation** — `contribution.investmentReturnPromised`
  const false; `poolStateReport.poolAssetClass` const "usdc-stable-only";
  `defiYieldFarmingActiveCount` + `tokenSpeculationActiveCount` const 0.
- **G7 no pre-existing-condition exclusion / no underwriting** —
  `distribution.noPreExistingConditionExclusion` const true;
  `silenWakaiReview.preExistingConditionExclusionEventsCount` const 0.
- **G9 community discernment** — distribution requires `communityDiscernmentAttestations`
  + `councilAttestations` (Council Lv6+ ≥3), not claim adjudication.
- **G11 administrator vocation-flow** —
  `silenWakaiReview.administratorVocationFlowCompliantRatioPctIntegerHundredths` const 10000 (=100.00%).

## R0 → R1 gate

Council Lv6+ ≥3 baseline (silenWakaiReview, witness ≥3) + the 4 pool cells + Public-Fund
backstop wired (Council Lv6+ ≥4/7 + toritate ledger cross-link).

> **2026-06-17 substrate-native migration (ADR-2606160842):** the charter-gate test above was ported Python→Clojure (`methods/test_charter_gates.py` → `methods/test_charter_gates.cljc`, ns `wakai.methods.test-charter-gates`, reads the lexicons via cheshire/edn) and the Python was pruned. Run via `./run_tests.sh` (now `exec bb`) or `bb run test:charter` (all 34 charter suites; 244 tests / 924 assertions green). Assertions unchanged (1:1 port).
