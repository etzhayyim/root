---
id: adr-2606037200-open-kyber-kotoba-datomic-erp-isic-industry-packs-productivity-suite
title: "ADR-2606037200: open-kyber as kotoba-Datomic ERP — ISIC industry packs + productivity suite"
status: active
doc_type: adr
topic: open-kyber-kotoba-datomic-erp
authoritative: true
last_verified: 2026-06-07
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "Promotes open-kyber from APQC reference ERP to the canonical kotoba-Datomic enterprise substrate; foundation for ISIC-complete industry coverage."
authoritative_for:
  - open-kyber-kotoba-datomic-state
  - isic-industry-pack-model
  - kyber-productivity-suite-integration
depends_on:
  - "2605262130"  # kotoba storage substrate unification (no RisingWave)
  - "2605312345"  # kotoba Datom = first-class canonical state
  - "2605181100"  # kotoba E2E encrypted-record envelope (Tier-3 PII)
  - "0025"        # kyber APQC/BPMN/OCEL projector consolidation
  - "2606014500"  # one Worker, many WASM actors (R3: ERP-as-WASM-actor)
  - "2606015400"  # mesh-runner serving + IPFS-based DID (e7m-wasm-runner)
related:
  - "2606032000"  # kanjō (external public-company financials) — sibling reckoning vocab
  - "2606012100"  # okaimono provisioning commons (UNSPSC catalog ties to inventory)
  - "2606032100"  # labor-liberation robotics wave (ISIC/ISCO/UNSPSC ranking)
supersedes:
  - "0025"        # D1 supersedes the ADR-0025 RisingWave read path (kqe-over-Datom-log)
superseded_by: []
---

# ADR-2606037200: open-kyber as kotoba-Datomic ERP — ISIC industry packs + productivity suite

**Status**: active — the `kotoba` reference layer is landed and verified (R1/R2, 113 tests
green incl. the drive file-tree core, `tsc` clean as of 2026-06-06). The **ERP Worker
Kysely/Hyperdrive cutover is now done in source** (`etzhayyim-wasm-kyber-erp-kyb3rerp/src/app.ts`
routes all 28 commands through the kotoba functions via `createXrpcBridge`; zero
`createKyselyDb`/`HYPERDRIVE` references; worker `app.ts` type-checks clean against the package
sources). **R3 (the code moves too) landed as a PoC**: the ERP is also compiled to a
content-addressed **`kotoba-node` WASM actor** (`wasm/kyber-erp-core/`, Rust, exports
`run(ctx-cbor)` + imports `kotoba:kais/{kqe,auth}`, `wasm-tools validate` ✓) that writes ERP
state straight into the Datom log via `kqe` — no CF Worker, no XRPC, no PDS hop. CID
`bafkreigdcmd54zval3z7xwmvmq5tgbsu6rpbxx4gtyhswxhvvfkaltaomi` (raw single-block, 119 KB),
registered as `did:web:etzhayyim.com:actor:kyber` in `infra-actors.ts` (wasmCid). Remaining: the
operator **deploy** of the Worker build, the full 28-command Rust parity, and pin/publish of the
actor bytes — all Council + operator gated. See Consequences § "Open tasks" and
`WORKER-AS-WASM-ACTOR-MIGRATION.md`.
**Date**: 2026-06-03 (status updated 2026-06-07)
**Deciders**: Jun Kawasaki

# Context

open-kyber (brand **Kyber**, `60-apps/etzhayyim-project-open-kyber/`) is the Apache-2.0,
APQC-PCF-aligned open-source ERP. As shipped under ADR-0025 it consolidates a 13-WASM mess
into one ERP Worker + one APQC/BPMN/OCEL projector, with the read path defined as
`PDS createRecord → onCommit → RisingWave streaming MV → getApqcCoverage`. Three gaps:

1. **Substrate drift.** The canonical-state rule for the whole monorepo is now the **kotoba
   Datom log** (ADR-2605262130 + 2605312345): RisingWave / Postgres / Kysely / Hyperdrive
   are prohibited as canonical or projection stores. open-kyber's RisingWave read path and
   the `createKyselyDb(env.HYPERDRIVE)` calls in `src/app.ts` are out of compliance, and the
   app's own code comments admit the read paths "currently return empty envelopes" since the
   SQL layer was deprecated 2026-04-13. The `kotoba/` reference module had begun the
   migration but only covered 3 collections (account, integrationBinding, employee).

2. **No industry coverage.** The ERP is generic. The founder directive of 2026-06-03 is
   *"ISIC のすべての産業にそれぞれ対応した ERP"* — an ERP tailored to every industry. The
   monorepo already holds the full ISIC Rev.4 classification (428 classes + 21 sections A–U,
   `60-apps/etzhayyim-project-open-isic/`), but nothing connects it to the ERP.

3. **No suite integration.** The directive also names *mailer, drive, docs, sheets* (a
   Google-Workspace-shaped productivity layer) to be "連携、統合" with the ERP. The Svelte
   SPA already scaffolds Mailer / Drive / Calendar / Organizer views, but there is no data
   model binding them to business records, and no kotoba-native definition of what a "drive
   file" or a "doc" even is on this substrate.

# Decision

Promote open-kyber to a **kotoba-Datomic ERP** and give it two first-class extensions —
**ISIC industry packs** and a **kotoba-native productivity suite** — all on the Datom log.

## D1 — Canonical state is the kotoba Datom log (supersedes the ADR-0025 read path)

A new EAVT vocabulary, **`00-contracts/schemas/erp-ontology.kotoba.edn`** (`erp-ontology`,
graph `kyber-erp-v1`), is the single SSoT for every ERP record. The 8 core modules map to
Datom kinds:

| Module | APQC L1 | Datom kinds |
|---|---|---|
| Accounting | 9.0 | `:account` `:journal-entry` `:journal-line` |
| AP/AR | 9.0 | `:invoice` |
| HR | 7.0 | `:employee` (PII pointer only — see D4) |
| Procurement | 4.0 | `:purchase-order` |
| Inventory | 5.0 | `:inventory-item` |
| Sales | 3.0 | `:sales-order` |
| Asset | 10.0 | `:fixed-asset` `:depreciation-run` |
| Governance | 11.0 | `:policy-control` `:risk-issue` |

The ERP Worker keeps its existing XRPC surface (`com.etzhayyim.apps.kyber.*`), but writes
**assert Datoms** and reads are **kqe arrangements** (EAVT/AEVT/AVET/VAET) directly over the
canonical log. MST = ingress/interop wire, IPFS = block backend, Base L2 = trust anchor.
**No RisingWave, no Kysely, no Hyperdrive** in any religious-corp ERP path. The kyb3proj
APQC projector keeps working: the L1 binding moves from a SQL label to the Datom attribute
`:apqc/l1`, and `getApqcCoverage` is recomputed from the `:modules` map in the ontology.

## D2 — Accounting is Datomic-accounting (非終末論)

An ERP is an accumulation of facts, never a mutable "current state" that overwrites the past.
This is exactly Datomic semantics and the reason kotoba is the right substrate:

- A journal entry is a header (`:journal-entry`) + balanced lines (`:journal-line`,
  `SUM(debit)=SUM(credit)`); a **reversal asserts a contra entry** (`:acct.je/reverses`),
  never an in-place edit.
- A depreciation run is a **new periodic fact** (`:depreciation-run`), accumulating, not
  overwriting.
- The books are read **as-of** any date via the Datom log's transaction time. This realizes
  the Charter's 非終末論 invariant (ADR-2605192100 §1.15): there is no "final" ledger state.

## D3 — ISIC industry packs (the "all industries" coverage model)

Rather than fork 428 ERPs, ship **one base + a pack overlay per industry**, defined in
**`60-apps/etzhayyim-project-open-kyber/industry-packs/isic-packs.kotoba.edn`**:

- **21 section packs** (`pack/A` … `pack/U`) covering all of ISIC Rev.4, each declaring an
  additive overlay: `:pack/modules-emphasis`, `:pack/doc-types`, `:pack/uom` (units of
  measure), `:pack/coa-ext` (chart-of-accounts extensions), `:pack/compliance` (sector
  control frameworks), `:pack/kpis`, and `:pack/actor-link` (the etzhayyim Tier-B actor
  whose domain the section is — e.g. `pack/A` → sanae/mitsuho/suki, `pack/C29` → sarutahiko).
- A first wave of **8 division packs** (`pack/A01`, `pack/A03`, `pack/C10`, `pack/C21`,
  `pack/C29`, `pack/K64`, `pack/K65`, `pack/Q86`) refining sections that are too coarse
  (farming vs fishing; food vs pharma vs autos; banking vs insurance). More land incrementally.
- **Resolution**: a tenant declares `:erp.tenant/isic-codes`; the loader maps each code's
  2-digit division to a section via `:section-ranges` (mirroring open-isic
  `sectionForDivision`), tries the most-specific division/class pack first, and writes the
  resolved set to `:erp.tenant/active-packs`. Overlays **compose** (division wins on CoA
  conflicts). Records created thereafter carry `:erp/isic-pack` for per-industry coverage and
  compliance reporting.

This makes "ISIC のすべての産業にそれぞれ対応した ERP" tractable and maintainable: 100% section
coverage on day one, progressively deeper division/class tailoring over time.

## D4 — Tier-3 PII never becomes a plaintext Datom

HR salary / personal contact stay in the `com.etzhayyim.encrypted.record` envelope
(ADR-2605181100). The `:employee` Datom carries only non-PII facets (department, position,
employment type) plus a **pointer** (`:hr.employee/pii-cid` + `:pii-recipients`). The
substrate never sees cleartext salary. This preserves the existing `kotoba` E2E split.

## D5 — kotoba-native productivity suite (mailer / drive / docs / sheets / calendar)

The suite is modeled as first-class ERP objects on the Datom log, **not** as external SaaS:

- **mailer** — a `:mail` Datom routed over **openmail Postage** (ADR Postage.sol); body is a
  CID block (E2E-sealed for confidential mail). NOT Gmail/外部メールプロバイダ.
- **drive** — a content-addressed file/folder tree; bytes are **IPFS CIDs**, the Datom is
  metadata; each save is a new revision (as-of history = version history).
- **docs / sheets** — content-addressed document/grid blocks with `:rev` revision history;
  a sheet can `:suite.sheet/bound` to live ERP entities (a trial-balance sheet bound to
  accounts).
- **calendar** — pure `:calendar-event` Datoms (no external CalDAV), linkable to ERP records.

Every suite object can `:links` to any business record, so the integration is bidirectional:
an invoice cites a drive file; a sales order attaches a docs quote; an HR review schedules a
calendar event. Integrations are registered in the `:integration` catalog with
`:erp.integration/transport ∈ {:openmail :ipfs :datom :xrpc}` — **never** a fiat or
third-party-ad transport (Charter Rider §2, substrate boundary).

## D6 — Maturity / coverage roadmap

- **R0 (this ADR)** — `erp-ontology` EAVT vocab + 21 section packs + 8 division packs +
  suite vocabulary, validated (EDN balance, section A–U coverage). Design SSoT.
- **R1 (landed 2026-06-03)** — `kotoba/` TS layer: kotoba-Datom-native modules for all 8
  core kinds + suite + ISIC loader. Shipped: exact-decimal `money.ts` (BigInt fixed-point);
  `accounting.ts` (double-entry GL, trial balance, 非終末論 `reverseJournalEntry`);
  `assets.ts` (fixed asset + exact straight-line depreciation, accumulating runs);
  `erp-modules.ts` (invoice / purchase-order / inventory / sales-order / policy-control /
  risk-issue); `suite.ts` (mailer over Postage / drive on IPFS / docs / sheets / calendar);
  `isic-packs.ts` (`resolvePacks` over 21 sections A–U + 8 division packs); `tenant.ts`
  (`registerTenant` declares ISIC codes → resolves + PERSISTS `:erp.tenant/active-packs`,
  upsert re-resolves on pivot — closes the ISIC story end-to-end); `coverage-all.ts`
  (`erpCoverage` rolls up every module + suite and reports active APQC L1 — the kqe
  replacement for the RisingWave `getApqcCoverage` MV). **7 test files, 39 tests green;
  `tsc --noEmit` clean.** kotoba reference layer COMPLETE.
- **R2 (keystone landed 2026-06-03)** — `xrpc-bridge.ts` (`createXrpcBridge`) adapts the
  kotodama-host-sdk AT-repo `XrpcClient` (`sdk.pds`) to the `Etzhayyim` read/write surface,
  letting the ERP Worker DELETE its `createKyselyDb(env.HYPERDRIVE)` read paths and route
  every command through the tested kotoba functions. Verified by driving the real kotoba
  functions through a mock XrpcClient (8 test files, 43 tests green). The actual `app.ts`
  edits (per-handler swap + Kysely removal) are an operator step — the worker package has no
  build/typecheck harness in-repo — captured as a precise runbook in
  `60-apps/etzhayyim-project-open-kyber/R2-WORKER-WIRING.md` (cmd→kotoba mapping table,
  new suite/tenant/ISIC commands, kyb3proj coverage from `erpCoverage`/`:apqc/l1`,
  verification + acceptance steps).
- **Maturity deepening (landed 2026-06-03)** — `seed.ts` (`seedChartOfAccounts` seeds the
  base 25-account IFRS chart PLUS the tenant's ISIC pack `coa-ext` accounts, so a
  manufacturer's ledger ships with Raw Materials/WIP/Finished Goods and a bank's with
  Loans/Reserves — the concrete "industry-tailored ERP" behaviour); `posting.ts`
  (`postInvoice` recognizes an AP/AR invoice as a balanced double-entry journal —
  Dr AR/Cr Revenue+Tax for receivables, Dr Expense+Tax/Cr AP for payables — and links the
  invoice to its JE, tying AP/AR to the GL); `contra-asset` account type added; ISIC
  division packs expanded 8→15 (C26/F41/H49/H50/I55/J62/P85). EDN section/division packs
  kept in sync (21 sections + 15 division packs). Further deepening: `decliningBalanceSchedule`
  + `runDepreciation` method dispatch (straight-line / double-declining, final-period
  true-up to salvage); `order-to-cash.ts` (`invoiceSalesOrder`: SO → AR invoice + link +
  status); `statements.ts` (`balanceSheet` + `incomeStatement` generated from CoA +
  trial balance, asserting Assets = Liabilities + Equity + Net Income). The full
  order-to-cash spine — Sales Order → Invoice → Journal Entry → Trial Balance → Balance
  Sheet / Income Statement — runs end to end on the Datom log. Then `purchase-to-pay.ts`
  (`receivePurchaseOrder` + `billPurchaseOrder`: PO → receipt → AP invoice + link, the
  procurement mirror) and `close.ts` (`closePeriod`: posts the closing entry zeroing the
  P&L accounts and carrying net income/loss to Retained Earnings — after close the income
  statement reads zero, equity holds the result, books stay balanced; non-終末論, the
  original postings are preserved). Both order-to-cash AND purchase-to-pay spines plus
  period close now run end to end on the Datom log. Then `cashflow.ts` (`cashFlowStatement`,
  direct method — classifies cash movements into operating/investing/financing and asserts
  net change equals the cash ledger movement, completing the financial THREE statements
  BS+PL+CF) and `budget.ts` (`setBudget` + `budgetVarianceReport` — per-account/period
  budget Datoms vs trial-balance actuals). The accounting core — double-entry GL, both
  AP/AR spines, depreciation (SL+DB), period close, BS/PL/CF, budgeting — is complete on
  the Datom log. Then `inventory-ledger.ts` (`receiveStock`/`issueStock`/`stockLedger`/
  `stockValuation`: a perpetual stock ledger with MOVING-AVERAGE cost — each movement an
  immutable Datom carrying the running qty + weighted-average; issues value COGS at the
  current average) + exact `mulMoney`/`divMoneyBy` decimal ops. Then `fx.ts` (multi-currency:
  `setFxRate`/`getFxRate` rate table with inverse-pair resolution, exact `convert`,
  `invoiceTotalsInBase` consolidating multi-currency AR/AP into one base currency and
  flagging unconvertible currencies). Then `payment.ts` (`recordPayment`: settles an open
  invoice against cash and posts it — Dr Cash/Cr AR for receivables, Dr AP/Cr Cash for
  payables — with partial-payment status tracking open→partial→paid and overpayment
  rejection, closing the SO/PO → invoice → JE → payment → cash cycle). Then the productivity
  suite gained real function: `sheets-eval.ts` (`evaluateGrid` — an exact-decimal spreadsheet
  engine: cell refs A1, ranges A1:B3, the four operators with precedence + parens, and
  SUM/AVG/MIN/MAX/COUNT, with #CYCLE/#DIV/0/#PARSE error cells) + `sheets-erp.ts`
  (`buildTrialBalanceGrid` renders the live trial balance as a worksheet whose footer SUM()
  formulas are COMPUTED by the engine over real ledger Datoms — the concrete suite↔ERP
  連携・統合). Then `party.ts` (customer/supplier master with credit limits) + `aging.ts`
  (`arAging`/`apAging` bucket open invoices by days-past-due current/1-30/31-60/61-90/90+
  netting paid amounts; `creditCheck` sums a customer's AR exposure vs their limit so an
  order can be blocked before breaching it). Then `tax.ts` (tax-code registry + `taxReport`:
  rolls invoice tax into OUTPUT tax 仮受 / INPUT tax 仮払, net payable = output − input, broken
  down by tax code and currency — the 消費税/VAT 申告 helper, non-adjudicating). Then
  `recurrence.ts` (`expandRRule` — calendar RRULE expansion FREQ/INTERVAL/COUNT/UNTIL for
  recurring suite events) + a consolidating `kotoba/README.md` indexing the full ~30-module
  surface. Finally `asset-register.ts` (`assetRegister`: cost → accumulated depreciation →
  net book value roll-forward) + a full **end-to-end integration test** that onboards a
  manufacturer (ISIC 2910 → pack C/C29 + industry CoA), runs a quarter (moving-average
  inventory, PO→bill, credit-checked SO→invoice→post→payment, depreciation, tax), produces
  TB/IS/BS/CF (all balanced) and closes the period — proving every module composes on the
  one Datom log. **20 test files, 89 tests green; `tsc --noEmit` clean.**

The open-kyber kotoba reference is now a feature-complete kotoba-Datomic ERP: the full
accounting cycle (GL → AP/AR → payment → close → BS/PL/CF), inventory (moving-average),
multi-currency, tax, budgeting, aging/credit, ISIC industry packs (21 sections + 15
divisions), a functional productivity suite (sheets formula engine + calendar RRULE), and
the worker-wiring bridge — all on the Datom log, verified end to end. A read-only
`audit.ts` (`ledgerAudit`) sweeps the five accounting invariants (entries balance, no orphan
account refs, trial balance balances, no over-applied invoices, reversal integrity) — the
non-mutating toritate/danjo audit ethos applied to the ERP itself. Finally `docs-md.ts`
(`parseMarkdown`: heading outline + nested tree + extracted links + word count + TOC,
fenced-code-aware) gives the docs suite object real function — so all four named suite apps
now compute, not just store: **mailer** routes over Postage, **drive** versions IPFS files,
**docs** structures Markdown, **sheets** evaluates formulas (+ calendar expands RRULEs).
**22 test files, 96 tests green; `tsc --noEmit` clean.**

Finally the canonical Datom vocabulary was brought back in sync with the matured code:
`erp-ontology.kotoba.edn` → **v0.2.0** adds the post-R0 attribute families `:pay.payment/*`
(payment application), `:tax.code/*` (VAT/消費税), `:party/*` (customer/supplier + credit
limit), `:budget.line/*`, `:fx.rate/*`, `:inv.move/*` (moving-average stock ledger) + the
invoice settlement fields, with the `:erp/kind` enum and `:modules` coverage map extended to
match. The documented SSoT now describes the full ERP surface (EDN balance-validated). ISIC
tailoring was then deepened with `DIVISION_COA_EXT` — division-level chart-of-accounts
extensions that compose on top of the section ext (pharma C21 GMP batch costing, banking
K64 interbank book + customer deposits, insurance K65 unearned-premium reserve, health Q86
claims receivable, …), so a tenant's ledger is tailored to its precise ISIC division, not
just its section. **23 test files, 100 tests green; `tsc --noEmit` clean.**
- **R3 (PoC landed 2026-06-06; live deploy gated)** — the ERP CODE also moves onto the
  substrate: `wasm/kyber-erp-core/` compiles the ERP to a content-addressed `kotoba-node` WASM
  actor (Rust, `run(ctx-cbor)` over a `{method,args}` envelope, `kqe`+`auth` host imports) that
  the kotoba host / `e7m-wasm-runner` stores on IPFS by CID and runs, writing state straight to
  the Datom log. PoC commands: `createAccount` / `seedChartOfAccounts` / `createJournalEntry`
  (exact i128-micros double-entry) / `getTrialBalance` + `coverage` (best-effort `kqe.query`) /
  `ping`. CID `bafkreigdcmd54zval3z7xwmvmq5tgbsu6rpbxx4gtyhswxhvvfkaltaomi`; advertised as
  `did:web:etzhayyim.com:actor:kyber`. Design in `WORKER-AS-WASM-ACTOR-MIGRATION.md`. Still
  gated: live multi-tenant deployment, the full 28-command Rust parity + verified read path,
  openmail Postage send, USDC/TitheRouter settlement of intra-suite value flows, and pin/publish
  of the actor bytes. Operator + Council gated.

# Consequences

**Positive**
- Brings open-kyber into substrate compliance: one canonical store, no RisingWave/SQL.
- Accounting gains real audit history (as-of) for free — the substrate *is* the audit log.
- ISIC section coverage is complete on day one; tailoring deepens without forking.
- The suite is confidentiality-correct by construction (E2E mail, sealed CIDs) and ad-free.
- Cross-links the ERP to the Tier-B actor mesh (each industry pack names its actor).

**Negative / honest limits**
- The `kotoba` reference layer is landed (R1/R2); the **deployed ERP Worker is not yet
  migrated** — its `createKyselyDb(env.HYPERDRIVE)` read paths and empty-envelope stubs
  persist until the R2 cutover runbook is executed (see Open tasks).
- Pack overlays are `:representative` starting points, not a chartered-accountant's sector
  chart of accounts; division/class depth is incremental.
- Docs/sheets are content-addressed blocks with revision history, **not** a real-time
  collaborative CRDT editor yet (that is a later round).
- The suite cores are **TypeScript** (`kotoba/src/`), running in the ameno/Svelte SPA. They
  are not yet content-addressed py/WASM edge actors; that runtime migration is designed in
  `SUITE-PY-WASM-MIGRATION.md` (T1-raw-CID browser vs T2-dag-pb mesh tiering) but unbuilt.
- No external-SaaS import path (by design) — tenants migrating from Google Workspace get the
  kotoba-native model, not a Gmail/Drive bridge.

**Open tasks**
- **[compliance, ADR-2605262130] — DONE in source (2026-06-06)** `R2-WORKER-WIRING.md` executed:
  the Worker `src/app.ts` no longer references `createKyselyDb`/`HYPERDRIVE` and routes every
  XRPC handler (all 28, incl. billing rewritten as kotoba records) through the tested `kotoba`
  functions via `createXrpcBridge`. `app.ts` type-checks clean against the package sources.
  **Remaining = operator deploy only**: `e7m actor build .` + `e7m actor deploy .` + the
  createAccount→createJournalEntry→getTrialBalance→dashboard smoke (the worker package has no
  in-repo build/typecheck harness, so the bundle+deploy happen where that toolchain exists).
  New suite/tenant/ISIC commands stay deferred (need lexicon authoring + codegen, runbook Step 3).
- **[suite]** Mailer has no openmail Postage *send* path yet (R3-gated); drive gained a real
  file-tree core (`drive-tree.ts`, 2026-06-06) but a collaborative CRDT editor for docs/sheets
  is still a later round.
- **[runtime]** Adopt `SUITE-PY-WASM-MIGRATION.md` to turn the suite cores into CID-addressed
  py/WASM actors (start with `recurrence`, finish with the exact-decimal `sheets-eval`).
- **[runtime, ADR-2606014500] — PoC DONE (2026-06-06), parity + publish gated** The ERP Worker
  itself now has a content-addressed `kotoba-node` WASM-actor form (`wasm/kyber-erp-core/`, CID
  `bafkreigdcmd54z…`, registered as `did:web:etzhayyim.com:actor:kyber`). Remaining: port the
  full 28-command kotoba surface to Rust (TS Vitest vectors are the conformance oracle), wire
  the verified kotoba Datalog read path (`list*`/`getTrialBalance`/`erpCoverage`), the encrypted
  HR E2E host surface, the CBOR `InvokeContext`→`{method,args}` host adapter, then pin the bytes
  + Council/operator-gated deploy. The CF Worker (`kyb3rerp`) stays the live path until then.
  Plan: `WORKER-AS-WASM-ACTOR-MIGRATION.md`.

# Alternatives Considered

1. **Keep RisingWave projection, add ISIC as SQL views.** Rejected: violates ADR-2605262130
   (no RisingWave) and 2605312345 (Datom is canonical). The whole point is substrate unity.
2. **Fork one ERP per ISIC class (428 apps).** Rejected: unmaintainable, defeats the single
   APQC-aligned core, and explodes the deploy surface. Base + composable packs is the
   standard ERP "industry vertical" pattern done content-addressably.
3. **Integrate real Google Workspace (Gmail/Drive/Docs APIs).** Rejected: external SaaS +
   third-party data egress + ad-ecosystem coupling violate the substrate boundary and Charter
   Rider §2. openmail Postage + IPFS + Datom blocks give the same surface, kotoba-native.

# References

- `00-contracts/schemas/erp-ontology.kotoba.edn` — the ERP EAVT vocabulary (this ADR)
- `60-apps/etzhayyim-project-open-kyber/industry-packs/isic-packs.kotoba.edn` — 21+8 packs
- `60-apps/etzhayyim-project-open-kyber/kotoba/` — kotoba-native TS implementation (R1+)
- `60-apps/etzhayyim-project-open-kyber/wasm/kyber-erp-core/` — ERP-as-WASM-actor PoC (R3)
- `60-apps/etzhayyim-project-open-kyber/WORKER-AS-WASM-ACTOR-MIGRATION.md` — R3 migration design
- ADR-2605262130 — kotoba storage substrate unification (no RisingWave)
- ADR-2605312345 — kotoba Datom = first-class canonical state
- ADR-2605181100 — kotoba E2E encrypted-record envelope (Tier-3 PII)
- ADR-0025 — kyber APQC/BPMN/OCEL projector consolidation (read path superseded by D1)
- `60-apps/etzhayyim-project-open-isic/kotoba/src/types.ts` — `sectionForDivision` (mirrored)
