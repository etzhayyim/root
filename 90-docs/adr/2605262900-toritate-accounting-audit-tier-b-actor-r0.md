---
id: adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
title: "ADR-2605262900: toritate (執帳) — non-profit religious-corp accounting + audit substrate Tier-B actor R0 charter"
status: proposed
doc_type: adr
topic: toritate-accounting-audit-r0
authoritative: true
last_verified: 2026-05-26
priority: 6.5
axis: governance
weight: 0.55
priority_note: "Second-priority gap-closure actor (sibling of chigiri ADR-2605262700; gap audit row 2). 任意団体 internal accounting + audit substrate for religious-corp's on-chain financial flows: TitheRouter income / Public Fund disbursement / Council compensation (typically zero) / steward subsistence flow per Liberation Ladder L0..L6 / Land Trust acquisition records. 100% on-chain transparency invariant (G3) — no off-chain books, no commercial accounting software (QuickBooks / Xero / FreeAgent / Wave / FreshBooks PROHIBITED per G8 + Charter Rider §2(e) anti-gatekeeping + §2(c) vendor data-sovereignty). NOT a tax-advice service (chigiri.tax_receipt handles donor receipts per ADR-2605262700; toritate aggregates the religious-corp side only). NOT a payroll system (volunteer ≠ employee per ADR-2605261000 G13). 6 cells / 5 Lexicons under com.etzhayyim.toritate.* / 12 immutable gates / 12 non-goals / 4-phase R0..R3. Powered by the existing on-chain primitives (no new substrate engine introduced). Annual audit by ≥3 distinct Council Lv6+ attestations (G6); external auditor engagement (when needed for jurisdictional compliance) contracted via Public Fund Safe per Council Lv6+ approval — toritate orchestrates the data preparation, NOT the audit opinion itself."
authoritative_for:
  - toritate actor R0 charter
  - religious-corp accounting + audit substrate single SoT
  - `com.etzhayyim.toritate.*` Lexicon namespace boundary
  - 100% on-chain transparency invariant for religious-corp financial flows
  - prohibition on commercial accounting software (QuickBooks / Xero / FreeAgent / Wave / FreshBooks)
  - annual transparency report contract
  - external auditor engagement gating (via Public Fund Council Lv6+, not toritate-direct)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192130-etzhayyim-tithe-redistribution
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605261000
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
related:
  - adr-2605262800-public-data-legal-corpus-ipfs-ingestion
supersedes: []
superseded_by: []
---

# ADR-2605262900: toritate (執帳) — non-profit religious-corp accounting + audit substrate Tier-B actor R0 charter

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

The gap audit (session 2026-05-26) identified accounting + audit as the
second-highest-priority remaining miss after legal procedure (chigiri
ADR-2605262700). Religious-corp already has on-chain financial primitives:

- **TitheRouter** (ADR-2605192130) — 10% auto-split on donation /
  kisha income;
- **Public Fund Safe** (ADR-2605192145) — 5-of-7 Council multisig
  for grant disbursement;
- **Council Safe** (ADR-2605192300) — 5-of-7 Council governance multisig;
- **Land Registry** (ADR-2605192245) — waqf-equivalent inalienable
  donation registry;
- **TitheRouter transactions / Public Fund grants / Council
  attestations** are all on-chain receipts.

What is MISSING is the **accounting + audit layer**: a procedural
substrate that aggregates these on-chain flows into transparent
reports, runs continuous categorization + anomaly detection on the
on-chain ledger, supports annual transparency reports for member +
public consumption, and orchestrates data preparation for external
auditor engagement when jurisdictional compliance requires it.

Constitutional constraints (inherited; not adjustable):

- **NOT 宗教法人法 登記** — Preamble §0.4 Lv7+ unanimity lock. Toritate
  MUST NOT introduce a code path that depends on state-granted legal
  personality (which would imply state-mandated 会計 standards
  applicable only to registered religious corps in JP);
- **On-chain primary ledger** (ADR-2605172100) — USDC + Base L2 +
  ERC-4337 Smart Account is the canonical financial substrate; fiat
  reconciliation is NOT a primary ledger (G4);
- **NO commercial accounting software** — QuickBooks / Xero /
  FreeAgent / Wave / FreshBooks / Sage / etc. are PROHIBITED per
  Charter Rider §2(e) anti-gatekeeping + §2(c) covert-ops vendor
  concern (vendor closed query-tracking exposes member financial
  posture);
- **Murakumo-only inference** (ADR-2605215000) — any LLM-assisted
  categorization or anomaly description flows through judah LiteLLM
  → gemma4:e4b;
- **kotoba canonical substrate** (ADR-2605262130) — accounting reports
  live in MST + IPFS + Base L2 anchor via @etzhayyim/sdk;
- **chigiri.tax_receipt boundary** (ADR-2605262700) — toritate
  aggregates religious-corp side accounting; donor-side tax receipts
  remain in chigiri.tax_receipt. The two cells cross-link via shared
  TitheRouter transaction CID;
- **Liberation Ladder L0..L6** (ADR-2605261000) — steward subsistence
  flow tracking honors G13 (volunteer ≠ employee). Toritate does NOT
  produce payroll records;
- **UPL-equivalent: no tax advice** — toritate does NOT render tax
  advice or accounting opinion. Where external opinion is needed
  (501(c)(3) equivalent determination, jurisdictional audit), the
  engagement is contracted through Public Fund Safe (Council Lv6+),
  same pattern as chigiri G14.

# Decision

Create `toritate` (執帳) as a Tier-B religious-corp accounting + audit
substrate actor at `20-actors/toritate/`, with DID
`did:web:toritate.etzhayyim.com`, Lexicon namespace
`com.etzhayyim.toritate.*`. R0 = scaffold only; all cells import-time
`RuntimeError` (same scaffold discipline as chigiri R0 + hagukumi R0).

## §1. Identity and naming

| Field | Value |
|---|---|
| Name | `toritate` (執帳) |
| Etymology | 執帳 = bookkeeping ledger (Heian-era 律令制 financial-record term); 執 = handle / hold + 帳 = ledger / book |
| DID | `did:web:toritate.etzhayyim.com` |
| Lexicon root | `com.etzhayyim.toritate.*` |
| Form | 任意団体 internal accounting + audit substrate (NOT 一般社団 / NPO / 公益財団 / 宗教法人 法人格) |
| Tier | Tier-B per-domain leader actor |
| Cross-actor | `chigiri` (tax_receipt boundary, 2-way) / Public Fund Safe (disbursement read) / TitheRouter (income read) / Land Registry (acquisition read) / Council Safe (compensation flow read) |

## §2. Scope (5 sections)

### A. Income-side accounting

- Aggregate TitheRouter on-chain income (donation / kisha / grant);
- Apply 10% Tithe auto-split tracking (90% to operational / 10% to
  Public Fund per ADR-2605192130);
- Per-period summary (daily / monthly / quarterly / annual);
- NO donor PII in published reports (aggregate amounts only; donor
  DIDs are pseudonymous and remain so).

### B. Disbursement-side accounting

- Public Fund Safe grant disbursement tracking (per-grant + per-period);
- Council Safe operational expense tracking (typically minimal —
  Council compensation is structurally zero per §1.10 of Mission
  Charter; only operational tooling expenses);
- External counsel / external auditor / external tax counsel contract
  disbursement tracking (cross-link to chigiri.ipLicenseClaim + chigiri.taxReceipt
  External-counsel-engagement records).

### C. Steward subsistence flow accounting

- L2 Sustenance flow (food / shelter access via Land Trust + Public Fund
  grant) tracking per-steward;
- L3 Shelter flow tracking;
- L4 Care flow tracking (chigiri.stewardLaborAttestation cross-link);
- L5 Vocation flow tracking;
- L6 Liberation flow tracking (rare; full subsistence + grant);
- **Volunteer ≠ employee** structural invariant per G13 of
  ADR-2605262700; toritate does NOT generate payroll records.

### D. Land Trust + asset accounting

- Land Registry acquisition CIDs (waqf-equivalent inalienable
  donations; ADR-2605192245);
- Land Trust valuation NOT computed (per N12 — donated land is
  inalienable and has no market price; reporting is square-meterage +
  donor-DID + date-of-acquisition aggregate);
- Other asset acquisitions (computing infrastructure, vehicles for
  steward use, etc.) — tracked at acquisition cost with depreciation
  schedule per asset class.

### E. Annual transparency report + audit attestation

- Annual transparency report (calendar year) — published to MST + IPFS
  pin at year-end + 90 days;
- Council audit attestation — ≥3 distinct Council Lv6+ DIDs sign the
  annual report (G6);
- External auditor engagement — when jurisdictional compliance
  requires (e.g., US 501(c)(3) eq-determination opinion letter for
  donor recognition flow), engagement is contracted through Public
  Fund Safe per Council Lv6+ approval. Toritate prepares the data
  package; the opinion is rendered by external counsel.

## §3. Cells (6 Pregel cells under `40-engine/kotoba/crates/kotoba-kotodama/cells/toritate_*/`)

All R0 path-reserved; import-time `RuntimeError("toritate R0 scaffold: activate via Council ADR + R1 ratification")` at W1 creation.

| # | Cell | Murakumo node | Phase | I/O |
|---|---|---|---|---|
| 1 | `tithe_accounting` | gad | continuous | TitheRouter tx → income summary entry |
| 2 | `public_fund_accounting` | gad | continuous | Public Fund Safe disbursement → grant summary entry |
| 3 | `council_compensation` | gad | continuous | Council Safe tx → operational expense summary (typically zero) |
| 4 | `steward_subsistence_accounting` | gad | continuous | chigiri.stewardLaborAttestation → L0..L6 subsistence flow summary |
| 5 | `transaction_ledger` | reuben | continuous | raw on-chain Base L2 tx parsing + categorization |
| 6 | `annual_audit_report` | reuben | annual (event) | aggregate cells (1-5) → annual transparency report + Council attestation chain |

R1 activation gates each cell separately (Council Lv6+ ≥3 attestation per cell).

## §4. Lexicons (5, all under `com.etzhayyim.toritate.*`)

| # | Lexicon | Cell consumer | Description |
|---|---|---|---|
| L1 | `financialAttestation` | annual_audit_report | Per-period (daily / monthly / quarterly / annual) summary attestation |
| L2 | `ledgerEntry` | transaction_ledger | Single on-chain transaction with category enum + amount + counterparty DID + supporting CID |
| L3 | `annualReport` | annual_audit_report | Annual transparency report; Council ≥3 attestation chain |
| L4 | `auditObservation` | any cell | Anomaly / finding (e.g., unrecognized counterparty / amount delta > threshold / Tithe split mismatch); routes to Council mediation if critical |
| L5 | `externalAuditorEngagement` | annual_audit_report | External auditor contract record; Public Fund Safe contract CID + scope + Council Lv6+ attestation |

All 5 records require schema-level field validation. R0 = scaffold + skeleton schemas. R1 = full schemas + structural enforcement.

## §5. Gates (12, immutable R0..R3, Council Lv6+ to amend)

| Gate | Description |
|---|---|
| **G1** | Every report MUST pass `kotodama.organism.sensors.charter_rider.scan()` §2(a)-(h). Fail = block. |
| **G2** | Every record MUST emit `com.etzhayyim.toritate.*` Lexicon with kotoba-datomic attestation lineage. |
| **G3** | **100% on-chain transparency** — toritate MUST NOT maintain an off-chain primary ledger. All financial state derives from on-chain transactions. |
| **G4** | **No fiat reconciliation as primary ledger** — USDC + Base L2 + TitheRouter + Public Fund Safe are canonical SoT. Fiat reporting (if any) is a derived projection only, never primary. |
| **G5** | UPL-equivalent: toritate MUST NOT render tax advice or accounting opinion. Templates document procedure; opinion happens via external counsel contracted through Public Fund Safe. |
| **G6** | Annual audit attestation = ≥3 distinct Council Lv6+ DIDs sign the annual report. |
| **G7** | Murakumo-only inference per ADR-2605215000 — no vendor LLM API callout. |
| **G8** | **No commercial accounting software** — QuickBooks / Xero / FreeAgent / Wave / FreshBooks / Sage / Zoho Books PROHIBITED (Charter Rider §2(e) anti-gatekeeping + §2(c) vendor data-sovereignty). |
| **G9** | Multi-year (≥3) ledger retention via IPFS pin per ADR-2605241500 (replicationMin: 2). |
| **G10** | NO donor PII in published reports (aggregate amounts + pseudonymous donor DIDs only; member-by-name donor disclosure requires per-donor opt-in attestation). |
| **G11** | NO transaction approval gating — toritate is read-only on the financial chain. TitheRouter + Public Fund Safe + Council Safe enforce all approval logic. |
| **G12** | Steward subsistence flow records honor G13 of ADR-2605262700 — `payroll` is NOT a valid category; classifications are subsistence-flow / vocation-flow / grant / reimbursement. |

## §6. Non-goals (12, immutable R0..R3)

| # | Non-goal |
|---|---|
| N1 | NOT a commercial accounting firm. No fee-for-service. |
| N2 | NOT a fiat reconciliation system (G4). |
| N3 | NOT a tax-prep service for donors (chigiri.taxReceipt handles donor-side per-jurisdiction routing). |
| N4 | NOT a payroll system (volunteer ≠ employee; Liberation Ladder subsistence flow ≠ wage). |
| N5 | NOT a commercial-accounting-software integrator (G8 PROHIBITED). |
| N6 | NOT a financial-statement audit firm (external auditor engagement via Public Fund Safe; toritate prepares data, NOT opinion). |
| N7 | NOT a budgeting / forecasting tool (Council Lv6+ sets allocation; toritate reports actual). |
| N8 | NOT transaction approval gating (G11; on-chain Safes do that). |
| N9 | NOT donor surveillance (G10). |
| N10 | NOT closed-source. Apache 2.0 + Charter Rider on all reports + tooling. |
| N11 | NOT a state-granted legal personality (Preamble §0.4 invariant; no 一般社団 / NPO / 公益財団 / 宗教法人 法人格 dependency). |
| N12 | NOT a Land Trust valuation engine (donated land is inalienable per ADR-2605192245; reporting is square-meterage + donor + date only, never market price). |

## §7. Roadmap (R0 → R3)

| Phase | Date / gate | Scope | Murakumo placement |
|---|---|---|---|
| **R0** | 2026-05-26 (this ADR) | Scaffold only. 6 cells path-reserved. 5 Lexicons schema skeleton. manifest + README + CLAUDE.md. | No deployment |
| **R1** | post-Bootstrap-Council + ≥1 Council Lv6+ ratify of this ADR | Activate 3 core cells: `transaction_ledger`, `tithe_accounting`, `public_fund_accounting`. L1 + L2 + L4 Lexicons full schema. Monthly summary reports begin emission. | gad + reuben (2 nodes) |
| **R2** | post-R1 + ≥30-day public objection | +3 cells: `council_compensation`, `steward_subsistence_accounting`, `annual_audit_report`. L3 + L5 Lexicons full schema. First annual transparency report (calendar 2026) published. | gad + reuben (2 nodes; light placement) |
| **R3** | post-R2 + Council Lv7+ unanimity (annual audit completed) | All 6 cells live. External auditor engagement framework battle-tested (≥1 US 501(c)(3) eq-determination opinion procured via Public Fund). Cross-jurisdictional ALERT thresholds calibrated. | Full 10-node fleet for redundancy |

## §8. Cross-actor relationship table

| Cross-actor | Direction | Purpose |
|---|---|---|
| `chigiri.tax_receipt` | ↔ | Donor-side tax receipt boundary; toritate aggregates religious-corp side, chigiri handles donor-side per-jurisdiction routing; cross-link via TitheRouter tx CID |
| `chigiri.ip_licensing` | ← | External counsel contract events (when L2/L3/external-counsel-engagement remedy used); toritate records the disbursement |
| TitheRouter | → (read) | On-chain income source |
| Public Fund Safe | → (read) | On-chain grant disbursement source |
| Council Safe | → (read) | On-chain operational expense source |
| Land Registry | → (read) | Land acquisition records |
| chigiri.stewardLaborAttestation | → (read) | L0..L6 classification for subsistence flow categorization |
| baien-distill | → (consumer) | Accounting reasoning specialist artifacts (future R3+; informed by chigiri-procedural-r1 + tax-receipt-multi-juris-r1 recipes from ADR-2605262800) |

## §9. R0 deliverables (this commit)

1. This ADR (`90-docs/adr/2605262900-toritate-accounting-audit-tier-b-actor-r0.md`);
2. Actor scaffold (`20-actors/toritate/manifest.jsonld` + `README.md` + `CLAUDE.md`);
3. 5 Lexicon JSON skeleton schemas under `00-contracts/lexicons/com/etzhayyim/toritate/` + README;
4. `deps.toml` [[adrs]] + [[modules]] entries;
5. `90-docs/adr/README.md` index update;
6. `CLAUDE.md` Status table row 69 + Repo Layout entry.

No code activation in R0. 6 cells are path-reserved at
`40-engine/kotoba/crates/kotoba-kotodama/cells/toritate_*/` (created at R1 ratification).

# Consequences

**Positive**:

- Closes the gap-audit #2 priority (accounting + audit) — religious-
  corp finally has a transparent reporting layer above the existing
  on-chain primitives (TitheRouter + Public Fund + Council Safe +
  Land Registry);
- 100% on-chain transparency invariant (G3) prevents Enron-class
  off-chain-bookkeeping drift constitutionally, not just by policy;
- Annual transparency report becomes a real artifact (R2);
- External auditor engagement framework battle-tested at R3 — first
  US 501(c)(3) equivalent-determination opinion enables US donor tax
  receipt routing via chigiri.tax_receipt (currently blocked);
- The G8 commercial-accounting-software prohibition documents an
  existing Charter Rider §2(e) + §2(c) constraint that has been
  latent.

**Negative / cost**:

- 100% on-chain ledger discipline (G3 + G4) creates UX friction for
  any future workflow that wants fiat reconciliation as a primary
  view — those workflows MUST be derived projections only;
- External auditor cost (US 501(c)(3) eq-determination ~$5-15k) is
  funded from Public Fund per Council Lv6+ approval — Council
  bandwidth required;
- Annual report assembly is a Council-attestation-bound deliverable;
  in R2 + R3 the first reports take meaningful Council time.

**Forward-compatibility**:

- The `ledgerEntry` Lexicon (L2) is extensible — future asset
  categories plug in via `category` enum extension under Council
  Lv6+ ≥3 attestation;
- The `annualReport` Lexicon (L3) supports multi-year diff reporting
  natively (R3+);
- Cross-religious-corp federation (if another religious-corp adopts
  Charter Rider in future) gets a clean financial-comparison
  integration via this Lexicon namespace.

# Alternatives Considered

1. **Extend chigiri to include accounting cells**. Rejected — chigiri
   is a legal procedure substrate. Mixing procedural + accounting
   responsibilities violates actor SRP and conflates UPL boundary
   (legal advice) with accounting opinion (accountant advice).

2. **Use QuickBooks / Xero / FreeAgent as the bookkeeping layer**.
   Rejected per Charter Rider §2(e) + §2(c). Vendor data-sovereignty
   exposure on religious-corp financial posture is structurally
   unacceptable.

3. **Skip accounting layer — TitheRouter + Public Fund Safe are
   self-attesting on-chain receipts**. Rejected — Council members
   + donors + members deserve aggregate transparency reports that
   are human-readable, not raw chain logs. Aggregation is the
   value-add.

4. **Single annual report (no continuous cells)**. Rejected — anomaly
   detection (G2 via auditObservation Lexicon) requires continuous
   processing; annual-only loses signal.

5. **Defer until chigiri R2 is live**. Considered. Rejected because
   toritate R0 scaffolding has zero governance cost (path-reserved,
   all cells RuntimeError) and the accounting gap is independent of
   chigiri R2 timing.

# References

- ADR-2605170900 — etzhayyim/root canonical home for ADRs
- ADR-2605172000 — kotoba substrate
- ADR-2605172100 — Payments on-chain only
- ADR-2605181100 — MST encrypted records + Signal key wrap
- ADR-2605192100 — Mission Charter
- ADR-2605192115 — Non-profit / donation-only / no-ads
- ADR-2605192130 — 10% Tithe redistribution
- ADR-2605192145 — Public Fund architecture
- ADR-2605192200 — Charter Compliance Rider v2.0
- ADR-2605192245 — Global Land Sovereignty (waqf-equivalent)
- ADR-2605192300 — Council 5-of-7 Safe
- ADR-2605215000 — Inference Murakumo-only
- ADR-2605261000 — Labor Liberation Transition Mechanism (L0..L6)
- ADR-2605262130 — Kotoba storage substrate unification
- ADR-2605262700 — chigiri legal procedure substrate R0 (cross-actor)
- ADR-2605262800 — Public-data legal corpus ingestion (informs accounting reasoning recipes)
- `/CHARTER-RIDER.md` §2 — 8 prohibited categories
- `20-actors/chigiri/` — gap-closure sibling actor (R0 scaffold pattern reference)
