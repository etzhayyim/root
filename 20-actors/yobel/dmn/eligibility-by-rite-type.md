# DMN — Eligibility by Rite Type

Per [ADR-2605201800](../../../90-docs/adr/2605201800-etzhayyim-yobel-debt-release-actor.md).
Gate for `enrollDebtor` cell + `release_settlement` cell.

**Hit policy**: FIRST (rule order matters — most-specific rule wins).

## Inputs

| Name | Type | Source |
|---|---|---|
| `riteType` | `enum(shmita_7yr, yobel_50yr, tokusei_rei, religious_jubilee, political_amnesty)` | `declareRite.riteType` |
| `debtorSbtLevel` | `integer` (0 if no SBT) | `CouncilSBT.balanceOf(debtorAddress)` |
| `debtorCommunityMember` | `boolean` | DID resolves to `did:web:etzhayyim.com:...` ∨ partner religious-corp DID list |
| `debtOriginationDate` | `date` | `enrollCreditor.debts[].originationDate` |
| `riteCycleStart` | `date` | computed: shmita = year×7 boundary; yobel = year×50 boundary; others = `declareRite.effectiveDate` |
| `jurisdictionIso3` | `string` | derived from creditor + debtor DID jurisdiction claim |
| `riteJurisdictionScope` | `string[]` | `declareRite.scope` parsed list (e.g. `["JPN"]`, `["ISR","global-jewish-community"]`, `["ALL"]`) |
| `debtInstrument` | `enum` | `enrollCreditor.debts[].instrument` |
| `sovereignDecreeRef` | `string?` | `declareRite.doctrinalBasis` (only checked when `riteType=political_amnesty`) |

## Outputs

| Name | Type |
|---|---|
| `eligible` | `boolean` |
| `reasons` | `string[]` (rule label(s) that fired) |
| `warnings` | `string[]` (passed-through tax warnings — see `tax-warning-by-jurisdiction.md`) |

## Rules

| # | riteType | debtorSbtLevel | debtorCommunityMember | debtOriginationDate vs riteCycleStart | jurisdictionIso3 ∈ riteJurisdictionScope | debtInstrument | sovereignDecreeRef | → `eligible` | `reasons` |
|---|---|---|---|---|---|---|---|---|---|
| **R1** | `shmita_7yr` | `≥ 1` | `true` | `< riteCycleStart` | `*` | `≠ sovereign_bond ∧ ≠ tithe_obligation` | — | ✅ | `["shmita: community member + pre-cycle debt"]` |
| **R2** | `shmita_7yr` | `≥ 1` | `true` | `≥ riteCycleStart` | `*` | `*` | — | ❌ | `["shmita: debt originated after cycle start — not within sabbatical horizon"]` |
| **R3** | `shmita_7yr` | `*` | `false` | `*` | `*` | `*` | — | ❌ | `["shmita: not a community member (Deut 15:3 distinguishes foreigner)"]` |
| **R4** | `yobel_50yr` | `≥ 1` | `true` | `< riteCycleStart` | `*` | `*` | — | ✅ | `["yobel: full Jubilee release — debt + bondage + land tenure (Lev 25:10)"]` |
| **R5** | `yobel_50yr` | `*` | `false` | `*` | `*` | `*` | — | ❌ | `["yobel: community membership required"]` |
| **R6** | `tokusei_rei` | `≥ 1` | `*` | `*` | `true` | `≠ sovereign_bond ∧ ≠ corporate_bond` | — | ✅ | `["tokusei: jurisdiction match + non-sovereign debt"]` |
| **R7** | `tokusei_rei` | `*` | `*` | `*` | `false` | `*` | — | ❌ | `["tokusei: outside declared jurisdiction scope"]` |
| **R8** | `religious_jubilee` | `≥ 1` | `true` | `*` | `*` | `tithe_obligation ∨ other` | — | ✅ | `["Catholic Holy Year: indulgentia plenaria for tithe / spiritual debt"]` |
| **R9** | `religious_jubilee` | `≥ 1` | `true` | `*` | `*` | `≠ tithe_obligation ∧ ≠ other` | — | ❌ | `["Catholic Holy Year: applies to spiritual / tithe debt only — monetary debt out of scope"]` |
| **R10** | `political_amnesty` | `*` | `*` | `*` | `true` | `sovereign_bond ∨ corporate_bond ∨ loan` | `≠ null ∧ length > 0` | ✅ | `["political amnesty: sovereign decree referenced + jurisdiction match"]` |
| **R11** | `political_amnesty` | `*` | `*` | `*` | `*` | `*` | `null ∨ length == 0` | ❌ | `["political amnesty: sovereignDecreeRef required (doctrinalBasis must cite the decree)"]` |
| **R12** | `*` | `< 1` | `*` | `*` | `*` | `*` | `*` | ❌ | `["no Council SBT — Charter §1.13 SBT-based identity requirement not met"]` |
| **R13** | `*` (any) | `≥ 1` | — | — | — | `liquidation ∨ margin_call ∨ seizure` | — | ❌ | `["instrument prohibited by Charter Rider §2(b) — yobel is one-way forgiveness only, cannot validate coercive instruments"]` |

R12 is the global SBT gate; R13 is the global Charter Rider §2(b) gate. R12/R13 short-circuit before rite-type-specific rules.

## Implementation note

DMN table は Python LangGraph node で実装 (`cells/debtor_enrollment/nodes.py`)。FIRST hit policy のため評価順は R12 → R13 → R1…R11。誤って `LAST` や `RULE_ORDER` で実装すると Charter Rider §2(b) gate がバイパスされる重大バグ。
