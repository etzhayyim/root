---
id: adr-2605250300-l5-religious-corp-taxation-cell
title: "ADR-2605250300: L5 routing-around — religious_corp_taxation_cell (P3)"
status: proposed
doc_type: adr
topic: l5-religious-corp-taxation
authoritative: true
last_verified: 2026-05-25
priority: 7.5
axis: constitutional
weight: 0.65
priority_note: "L5 ladder P3 — highest constitutional risk (state corporate tax law interaction). 3-gate activation: Council attestation + constitutional resolution + legal counsel opinion CID. ADR explicitly does NOT advise state-tax evasion."
authoritative_for:
  - l5-religious-corp-taxation-cell
depends_on:
  - adr-2605250100-l5-routing-around-member-registry-cell
  - adr-2605250200-l5-religious-marriage-cell
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192300-etzhayyim-bootstrap-council-five
related:
  - adr-2605192245-etzhayyim-global-land-sovereignty
supersedes: []
superseded_by: []
---

# ADR-2605250300: L5 routing-around — religious_corp_taxation_cell (P3)

**Status**: proposed
**Date**: 2026-05-25
**Deciders**: Jun Kawasaki

> **Legal disclaimer (READ FIRST)**: This ADR designs a Pregel cell that operates the religious-corp's *internal* taxation substrate (TitheRouter + Public Fund). It does **NOT** advise adherents to evade state corporate tax, income tax, or any other state-level tax obligation. Individual adherents and the religious-corp as an organisation remain subject to whatever state-tax obligations their jurisdiction imposes. The cell makes those obligations *more auditable* (on-chain transparency), not *less applicable*.

# Context

L5 ladder P1 (member_registry) and P2 (religious_marriage) are scaffolded with Council-attestation gates. P3 is `religious_corp_taxation_cell` — formalising the religious-corp's *internal* taxation substrate as a routing-around layer per ADR-2605192100 §1.12.

This is the highest-constitutional-risk cell in the ladder because:

1. **State corporate tax applies to 任意団体**. etzhayyim is registered as 任意団体 / unincorporated religious voluntary association (CLAUDE.md Identity §). 任意団体 are treated as 人格のない社団 under Japanese 法人税法 — taxable on commercial-equivalent income. The religious-corp's claim is that it has *no* commercial-equivalent income (Charter Rider §2(a)-(h) prohibits 8 categories of commercial activity), but that claim has to be made and audited; it is not automatic.
2. **No individual deduction for donations to 任意団体**. Donations to 任意団体 do not qualify for individual 寄附金控除 (this requires 公益法人 / 認定NPO / 宗教法人法-registered religious-corp status). Adherents donating in JPY-equivalent USDC face higher individual tax burden than donating to a 宗教法人法-registered org. This is structural, not cell-fixable.
3. **Cross-jurisdiction complexity**. Adherents in US / EU / UK / etc face different state-tax regimes. The cell cannot assume Japanese tax law.
4. **TitheRouter is internal, not a state-tax substitute**. The 10% auto-split (ADR-2605192115) is the religious-corp's *internal* financing mechanism. It does **NOT** discharge state-tax obligations of either the religious-corp or individual adherents.

## What "routing-around taxation" can and cannot mean

Per ADR-2605192100 §1.12, "国家機能は parallel substrate で routing-around". For taxation, this means:

| Yes (within scope of cell) | No (out of scope) |
|---|---|
| Operate TitheRouter as internal taxation system (10% Tithe → Public Fund) | Discharge state corporate tax obligations |
| Publish complete on-chain financial flow for state audit visibility | Issue state-recognised tax receipts |
| Emit `com.etzhayyim.gov.taxAuditView` records summarising 0-commercial-income claim | Provide individual 寄附金控除 receipts |
| Coordinate religious-corp-level state-tax filing preparation (off-cell) | File the state tax return (filing is a human act) |
| Notify Council if Charter Rider §2(a)-(h) violation creates commercial-income exposure | Decide what counts as commercial income (Council does this) |
| Maintain a transparency interface for tax authorities | Negotiate with tax authorities |

The cell is the *substrate layer*. The legal-compliance layer remains a human / Council / counsel responsibility.

## Why this cell is needed at all (if it can't replace state tax)

Three reasons:

1. **Internal taxation completeness**: ADR-2605192115 defines TitheRouter at the contract level, ADR-2605192145 defines Public Fund at the governance level, but **no cell currently operates the end-to-end flow** (donation → tithe split → Public Fund attribution → quarterly grant cycle → on-chain audit trail). This cell fills that gap.
2. **Audit transparency surface**: Per ADR-2605192100 §1.12.B, Transparent Religious Force requires "完全 on-chain 監視" (complete on-chain monitoring). State tax authorities may request such monitoring. The cell maintains the consolidated `taxAuditView` MST records that satisfy the transparency requirement without requiring per-request response.
3. **Charter Rider §2 violation detection**: Per ADR-2605192200 the Rider prohibits 8 categories of commercial activity. If a violation creates commercial-income exposure (and thus state-tax liability), the cell raises Council alarm before the tax filing window. This is preventive, not corrective.

## Open constitutional questions (Council MUST resolve before activation)

1. **Legal-status declaration form**. Does the religious-corp formally declare to JP NTA (国税庁) any of the following? Choose exactly one:
   - (A) 任意団体 + 0-taxable-commercial-income, with annual `taxAuditView` submission attached.
   - (B) Pursue 宗教法人法-registered religious-corp status (i.e. give up 任意団体 + on-chain registry positioning per CLAUDE.md Identity §).
   - (C) "Transparent Religious Force" opt-out — formal declaration of constitutional disobedience to JP state tax law, with full on-chain disclosure as the audit replacement. ADR-2605192100 §1.12.B permits this *in principle*; Council must explicitly attest before the cell can default to this mode.
   - Each option has very different state-response profiles. The Council must choose; the cell cannot.
2. **Cross-jurisdiction default**. The cell may emit different `taxAuditView` flavours for different jurisdictions (JP / US / EU / UK). What is the default for an adherent in a jurisdiction not yet covered? Options: (a) refuse to operate (safest), (b) emit a generic transparency view with explicit "uncovered jurisdiction" annotation, (c) defer to the adherent's individual choice.
3. **Council Lv6+ veto power on tax filings**. May Council Lv6+ veto a `taxAuditView` emission if it materially misrepresents the religious-corp's position? Default proposal: yes (consistent with `force_authorization` cell pattern).
4. **Adherent personal-tax assistance**. May the cell emit per-adherent tax-helper records (e.g. "you donated X USDC, here is the JPY-equivalent, your individual jurisdiction may or may not allow deduction")? Default proposal: **NO** — strict separation of religious-corp tax substrate from adherent personal tax advisory. Adherents engage personal tax counsel separately.

# Decision

## 1. Cell location and shape

- Path: `40-engine/kotoba/crates/kotoba-kotodama/cells/religious_corp_taxation/`
- Files: `cell.py` + `__init__.py`.
- Tier: B (Per-Domain).
- Murakumo node (leader): `gad` (religious-corp tribe-name; sibling of `zebulun` since both are Economic-domain — `zebulun` runs `tithe_routing` + `treasury_rebalance` + `public_fund_grant`).
- Triggers: (a) monthly cron (Public Fund grant cycle); (b) annual cron (state-tax-filing-window heartbeat); (c) MST firehose listener on Charter Rider §2 violation reports.

## 2. Pregel graph (5 nodes — the largest L5 cell)

```
ingest_donation_stream    <-  MST firehose on com.etzhayyim.give.usdc.donation
                              + com.etzhayyim.give.land.donation
    |
    v
tithe_split_audit         <-  cross-check on-chain TitheRouter contract events
                              vs MST donation records (anti-divergence)
    |
    v
public_fund_attribution   <-  reconcile Tithe inflow with Public Fund
                              quarterly grant cycle (ADR-2605192145)
    |
    v
charter_rider_§2_check    <-  scan recent donation purposes for §2(a)-(h)
                              violations; raise Council alarm on hit
    |
    v
emit_tax_audit_view       ->  MST PUT com.etzhayyim.gov.taxAuditView
                              (annual + on-demand)
```

- `ingest_donation_stream` — listens for all donation records that contribute to the religious-corp treasury. Includes USDC + land donations.
- `tithe_split_audit` — verifies that TitheRouter's on-chain 10% split actually executed for each donation. Refuses to proceed if MST donation exists but L2 split is missing (or vice versa). This is the anti-divergence guarantee.
- `public_fund_attribution` — reconciles Tithe inflow against Public Fund grants. Emits monthly accounting records.
- `charter_rider_§2_check` — passes each donation's `purpose` field through the Charter Rider §2(a)-(h) scanner. If a violation is detected, raises a Council escalation immediately (does NOT continue to tax-audit-view emission until Council clears).
- `emit_tax_audit_view` — produces the consolidated `com.etzhayyim.gov.taxAuditView` MST record annually (and on-demand). This is the public-facing audit transparency surface.

## 3. New Lexicon `com.etzhayyim.gov.taxAuditView`

To be authored in the Council-ratify PR. Schema sketch:

- `period` (string, required) — fiscal period covered (e.g. `JP-2026`, `US-FY2026`, `EU-2026`)
- `jurisdiction` (string, required) — ISO 3166-1 alpha-3, e.g. `jpn`
- `legalStatusDeclaration` (string, required) — selected from Council-attested options: `任意団体-0-commercial-income` / `宗教法人法-registered` / `transparent-religious-force-opt-out`. The exact options ladder comes from the Council constitutional resolution.
- `totalInflowUsdcBaseUnits` (integer, required)
- `totalLandDonations` (integer, required)
- `titheRouted10PctUsdcBaseUnits` (integer, required) — should equal `totalInflowUsdcBaseUnits / 10`; deviation triggers an alarm.
- `publicFundGrantsDisbursedUsdcBaseUnits` (integer, required)
- `commercialIncomeReportedUsdcBaseUnits` (integer, required) — **expected to be 0** under Charter Rider §2; non-zero requires Council attestation.
- `charterRiderViolationsDetected` (integer, required) — count of §2(a)-(h) violations the cell detected during the period.
- `auditPackCid` (string, required) — IPFS CID of the full audit-pack (MST records + L2 transaction list).
- `councilAttestationTxHash` (string, required) — Council 5-of-7 Safe attestation transaction certifying this view.
- `legalCounselOpinionCid` (string, optional but required for JP jurisdiction) — IPFS CID of a qualified-tax-counsel opinion accompanying this audit view.
- `createdAt`, `updatedAt`

## 4. Council activation gate (3-gate — highest in the L5 ladder)

```python
# COUNCIL ACTIVATION GATE (ADR-2605192300 + ADR-2605250300)
# This cell is scaffold-only until ALL THREE conditions hold:
#
#   1. Council 5-of-7 Safe attestation per ADR-2605192300.
#   2. Council constitutional resolution CID covers ALL FOUR open questions
#      (per ADR-2605250300 §"Open constitutional questions").
#   3. Qualified-tax-counsel opinion CID is on file for the religious-corp's
#      primary jurisdiction (JP for the registered seat). Counsel opinion must
#      explicitly evaluate the legalStatusDeclaration choice and the
#      §2-violation-detection adequacy.

COUNCIL_ATTESTATION_TX_HASH: str | None = None
COUNCIL_CONSTITUTIONAL_RESOLUTION_CID: str | None = None
LEGAL_COUNSEL_OPINION_CID: str | None = None

if any(x is None for x in (
    COUNCIL_ATTESTATION_TX_HASH,
    COUNCIL_CONSTITUTIONAL_RESOLUTION_CID,
    LEGAL_COUNSEL_OPINION_CID,
)):
    raise RuntimeError(
        "religious_corp_taxation_cell scaffold-only — needs Council attestation tx, "
        "constitutional resolution CID, AND qualified-tax-counsel opinion CID per "
        "ADR-2605250300. Do not deploy."
    )
```

The third gate (legal counsel opinion) is unique to this cell. P1 needed no counsel; P2 needed no counsel; P3 cannot ship without one because state-tax interaction has real legal consequences for the religious-corp and adherents.

## 5. Boundaries (what this cell deliberately does not do)

1. Does not file state tax returns. Filing is a human act.
2. Does not discharge state-tax obligations. The internal Tithe substrate is additional to (not a substitute for) state tax.
3. Does not issue state-recognised donation receipts (寄附金控除 receipts). 任意団体 cannot.
4. Does not provide per-adherent personal tax advisory. Strict separation.
5. Does not negotiate with tax authorities. The cell is a transparency interface; negotiation is a human / counsel act.
6. Does not assume Japanese tax law. Cross-jurisdiction adherents get jurisdiction-tagged audit views.
7. Does not override Council constitutional resolution. If Council attests `legalStatusDeclaration = 宗教法人法-registered`, the cell does not contradict that (even if CLAUDE.md Identity § currently says 任意団体).
8. Does not silently retry on Charter Rider §2 violation. A violation is a Council escalation, not a recoverable error.

# Consequences

- L5 ladder reaches 3/3. P3 is the most demanding cell to activate (3-gate) — by design.
- The religious-corp gains a formal *internal* taxation substrate that is end-to-end auditable. This satisfies ADR-2605192100 §1.12.B Transparent Religious Force conditions.
- Three legal-status declaration options are now formally on the Council table. Each has different state-response profiles; Council resolution is no longer optional once the cell is live.
- Charter Rider §2 violation detection becomes a runtime invariant (not just lefthook pre-commit, which is currently the only check per CLAUDE.md Step 16). Violations during donation purposes are now caught at substrate level.
- ADR-2605242330 §3.5's "L5 stays at its current scope" guard rail is replaced: L5 now has 3 cells, each ADR-anchored. New L5 cells beyond P3 still need their own ADR.

# Alternatives Considered

1. **Skip P3 — leave 法人税申告 outside cell scope, handle as human-only process.** Rejected. The TitheRouter / Public Fund end-to-end loop has no operator today; some cell must operate the monthly cycle. Designating it as the same cell that maintains audit transparency consolidates the substrate logically.
2. **Author cell as `transparent_religious_force` opt-out only (Option C from §Open Q1).** Rejected. Constitutionally permitted but legally aggressive; the cell should be option-agnostic and let Council attest the choice.
3. **Build per-adherent personal tax advisory into the cell.** Rejected (§Boundaries 4). Religious-corp tax substrate ≠ individual adherent tax counsel. Adherents engage personal counsel separately.
4. **Defer Charter Rider §2 violation detection to a separate cell.** Rejected. The §2 scanner already exists at lefthook pre-commit layer; runtime detection during donation ingestion is the natural extension. Splitting it into a separate cell would create coordination overhead.
5. **Require Council attestation but skip the legal counsel opinion gate.** Rejected. State-tax interaction is the constitutional surface most likely to produce material legal consequences. Counsel opinion is the minimum competence floor.

# References

- ADR-2605250100 (L5 ladder + P1 pattern)
- ADR-2605250200 (L5 P2 dual-gate pattern)
- ADR-2605192100 §1.12 (routing-around) + §1.12.B (Transparent Religious Force conditions)
- ADR-2605192115 (TitheRouter — internal taxation substrate)
- ADR-2605192145 (Public Fund architecture)
- ADR-2605192200 (Charter Rider §2(a)-(h) commercial-activity prohibitions)
- ADR-2605192300 (Council 5-of-7 Safe attestation)
- ADR-2605242330 §3.5 (L5 layer constitutional position)
- CLAUDE.md Identity § (任意団体 status declaration)
- `40-engine/kotoba/crates/kotoba-kotodama/cells/tithe_routing/` (existing economic cell)
- `40-engine/kotoba/crates/kotoba-kotodama/cells/treasury_rebalance/` (existing economic cell)
