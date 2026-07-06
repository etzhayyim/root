# etzhayyim-project-amnesty — Legal-Person Debt Restructuring Actor

Sibling actor to [yobel](../etzhayyim-project-yobel/) — handles **legal-person** debt restructuring (sovereign / corporate / multilateral / partnership). What yobel rejects under DMN R14 (natural-person-only invariant), amnesty accepts.

**Design SSoT**: [`90-docs/adr/2605202000-etzhayyim-amnesty-legal-person-debt-actor.md`](../../90-docs/adr/2605202000-etzhayyim-amnesty-legal-person-debt-actor.md)

## Identity & Boundary

| 項目 | 値 |
|---|---|
| Operating entity | **etzhayyim** (3-axis split clean) |
| DID | `did:web:amnesty.etzhayyim.com` (primary) |
| License | Apache-2.0 + Charter Compliance Rider v2.0 |
| Charter alignment | Mission §1 の **institutional dimension** — macro-scale labor coercion via sovereign + corporate debt overhang |
| Substrate | AT MST + IPFS + Base L2 (kotoba) + optional UN/UNCITRAL registry mirror |
| Settlement | USDC on Base L2 + on-chain restructuring instruments (haircut / rescheduling / equity swap / nature swap) |
| Ratification gate | Council Lv9 chair × 3 + Five-Bootstrap consultation (higher than yobel's Lv6+ × 3 / Lv9 × 1 — legal-person debt has macro impact) |
| Quorum | 80% (yobel's baseline 50% +30% for institutional scale) |

## Symmetric pair with yobel

```
              debtor entity type
                     │
       ┌─────────────┴─────────────┐
       │                           │
 natural_person              legal_person
       │                           │
       ▼                           ▼
  ┌─────────┐                 ┌─────────┐
  │ yobel   │                 │ amnesty │
  │  R14    │←─────── A14 ──→ │         │
  │  pass   │     deferTo     │  pass   │
  └─────────┘                 └─────────┘
```

Both actors enforce mutual deferral: yobel R14 returns `deferToAmnesty=true` for legal-person debtors; amnesty A14 returns `deferToYobel=true` for natural-person debtors. Caller routes accordingly.

## Status

**proposed / pre-seed (Phase 1).** ADR + 8 lexicons + project marker only. Subsequent phases (cells / Solidity / web3 / governance) deferred per ADR-2605202000 §Phase plan.

## Rite Catalog

| Rite | 適用 | Consent threshold (permille) | 史的事例 |
|---|---|---|---|
| `sovereign_multilateral` | 国家 vs 多国/多機関 creditor coalition | 750 (≥ 75%) | HIPC 1996+, Argentina 2005 |
| `sovereign_bilateral` | 二国間 sovereign rescheduling | 500 (≥ 50%) | Paris Club bilateral cases |
| `corporate_chapter_11` | US Ch11 / 会社更生 / UK scheme of arrangement | 667 (≥ 2/3, matching 11 USC §1126(c)) | Lehman, Enron post-confirmation, GM |
| `corporate_workout` | out-of-court informal restructuring | 900 (≥ 90% — high bar to bind dissenters out-of-court) | 私的整理ガイドライン (Japan), London Approach |
| `debt_for_nature_swap` | sovereign debt cancellation ↔ conservation commitment | 600 (≥ 60% creditor + NGO accreditation) | Bolivia 1987, Belize 2021, Seychelles 2018 |

## NSID

- Canonical (kuniUmi precedent と整合): `com.etzhayyim.apps.etzhayyim.amnesty.*`
- Vendor transitional alias: `org.etzhayyim.amnesty.*` (post-cutover, vendor-side mirror)

Path: `00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/amnesty/{declareRestructuring,enrollCreditorClass,enrollDebtor,verifyEligibility,voteOnPlan,recordSettlement,listRestructurings,getRestructuring}.json`

## Cluster Integration

```
amnesty.etzhayyim.com (legal-person, voluntary multi-creditor)
 ├─ defers natural-person → yobel.etzhayyim.com (symmetric pair; natural-person formal procedure then resolves via native saisei per ADR-2607061800)
 ├─ represented   → vendor:lawfirm.etzhayyim.com (sovereign counsel, corporate counsel, court filings)
 ├─ falls back    → vendor:bankruptcy.gftd.ai (formal Ch11 / 会社更生 / scheme for the LEGAL-PERSON case only — when voluntary multi-creditor consent fails; still vendor-side, out of ADR-2607061800's natural-person-only scope, and still not backed by real vendor code as of that ADR's survey)
 ├─ eligibility   ← council SBT registry (Lv1+ proposers, Lv9 chair × 3 for ratification)
 ├─ ratification  ← Council Lv9 × 3 + Five-Bootstrap consultation
 ├─ settlement    → ERC725 Smart Wallet + Base L2 USDC + on-chain restructuring instruments
 ├─ audit         → AT MST + IPFS append-only + optional UN/UNCITRAL registry mirror
 └─ publication   → app.bsky.feed.post (#sovereign-debt / #chapter11 / #debt-restructuring / #amnesty)
```

## Invariants (NON-NEGOTIABLE)

- **Legal-person debtor only.** `enrollDebtor.debtorEntityType` enum excludes `natural_person` (single negative — `natural_person` MUST defer to yobel). DMN A14 cell-level gate cross-checks resolved CouncilSBT entityType
- **Multi-creditor consent threshold.** Per-rite-type threshold (≥ 50% / 2/3 / 75% / 90% / 60%) MUST be met before any settlement. EVM-level enforcement deferred to Phase 5 Solidity contracts
- **Voluntary opt-in (creditor side).** No creditor can be force-bound. Out-of-court rites require near-unanimity (90%). Court-supervised rites (`corporate_chapter_11`) follow §1126(c) heuristic + court confirmation
- **No fiat / no Stripe.** USDC on Base L2 only
- **No claim to override secular law.** When voluntary restructuring fails, fallback to formal legal procedure — for the legal-person case that remains vendor:bankruptcy.gftd.ai (unbuilt as of ADR-2607061800's survey); the natural-person case never reaches amnesty (deferred to yobel at DMN A14) and resolves via native `saisei` instead. amnesty is voluntary doctrinal witness + on-chain neutral settlement infrastructure, NOT a court substitute
- **Council Lv9 chair × 3 ratification.** Same severity as Mission Charter amendments (legal-person debt restructuring has macro impact on Charter §1 mission). Higher bar than yobel's Lv6+ × 3
- **Charter Rider §2 compliance review.** Sovereign debtor passing through §2(a) military-state filter, corporate debtor through §2(b) speculative-finance + §2(c-h) filters
- **Tax advice delegated.** Per-jurisdiction restructuring tax treatment (e.g. cancellation-of-debt income, §382 ownership change limits) is vendor:lawfirm.etzhayyim.com's domain. amnesty does not opine

## Deferred phases

| Phase | Deliverable |
|---|---|
| 2 | Actor scaffold — BPMN + DMN tables (eligibility-by-rite-type / cross-creditor-threshold / per-jurisdiction-court-coordination) + 6 cell READMEs |
| 3 | S1 Python cells (declaration / creditor_class_enrollment / debtor_enrollment / vote_collection / settlement_execution / audit_witness) |
| 4 | S2 ports + pytests + orchestrator + sample HIPC-Zambia or Chapter11-Acme fixture |
| 5 | Solidity contracts (3 — AmnestyRestructuringRegistry + AmnestyVoteRegistry + AmnestySettlementRegistry). More complex than yobel's 2 because legal-person flow has voting + settlement as distinct phases |
| 6 | Web3 ports + EIP-712 typed-data for creditor class consent + integration tests |
| 7 | Council ratification proposal + Base L2 deployment runbook |

## See also

- [yobel](../etzhayyim-project-yobel/) — natural-person sibling actor
- [ADR-2605202000](../../90-docs/adr/2605202000-etzhayyim-amnesty-legal-person-debt-actor.md) — design SSoT
- [ADR-2605201800](../../90-docs/adr/2605201800-etzhayyim-yobel-debt-release-actor.md) — yobel ADR (natural-person scope basis)
- [ADR-2607061800](../../90-docs/adr/2607061800-saisei-self-filing-debt-relief-actor.md) — saisei (native natural-person formal procedure fallback, reached via yobel's deferral, not directly by amnesty)
- vendor:bankruptcy.gftd.ai — mandatory legal procedure fallback for the LEGAL-PERSON case only (unbuilt as of ADR-2607061800's survey — still an open gap, out of that ADR's natural-person-only scope)
- vendor:lawfirm.etzhayyim.com — sovereign / corporate counsel delegation target
