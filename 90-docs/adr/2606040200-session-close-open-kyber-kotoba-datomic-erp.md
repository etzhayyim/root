---
id: adr-2606040200-session-close-open-kyber-kotoba-datomic-erp
title: "ADR-2606040200: Session close (loop) — open-kyber kotoba-Datomic ERP reference complete"
status: active
doc_type: adr
topic: open-kyber-kotoba-datomic-erp
authoritative: false
last_verified: 2026-06-04
priority: 3.0
axis: process
weight: 0.30
priority_note: "Documentation-only session close registering ADR-2606037200's /loop delivery."
authoritative_for: []
depends_on:
  - "2606037200"
related:
  - "2605262130"
  - "2605312345"
supersedes: []
superseded_by: []
---

# ADR-2606040200: Session close (loop) — open-kyber kotoba-Datomic ERP reference complete

**Status**: active
**Date**: 2026-06-04
**Deciders**: Jun Kawasaki

# Context

A `/loop` (dynamic, self-paced) was run to answer the founder question
*「今の open kyber は erp として設計・管理・統合されているか」* and the directive that
followed: *「これを kotoba datomic として coverage・成熟度を向上して、ISIC のすべての産業に
それぞれ対応した erp に、mailer/drive/docs/sheets なども連携・統合」*.

At the start, open-kyber was an APQC-aligned ERP whose deployed worker used a RisingWave
projection read path (ADR-0025) — out of compliance with the canonical-state rule (kotoba
Datom log, ADR-2605262130 + 2605312345) and with no ISIC tailoring and no functional suite.

This ADR is the **documentation-only session close**. The authoritative design is
**ADR-2606037200**.

# Decision

Deliver, over 22 self-paced loop iterations, a complete **kotoba-Datomic ERP reference**
implementation for open-kyber, plus the canonical schema and the worker-migration runbook —
all monorepo-side, with honest scoping of what is reference vs. live.

## Shipped (all under `60-apps/etzhayyim-project-open-kyber/` + `00-contracts/schemas/`)

1. **Canonical schema** — `00-contracts/schemas/erp-ontology.kotoba.edn` **v0.2.0** (EAVT
   vocabulary, kept in sync with the code: payment / tax / party / budget / fx / stock-move
   families + invoice settlement fields) + `industry-packs/isic-packs.kotoba.edn` (21 ISIC
   section packs A–U + 15 division packs). Both EDN balance-validated.

2. **`rw-free/` TS reference** — **33 source modules · 23 test files · 100 tests green ·
   `tsc --noEmit` clean**:
   - Accounting core: double-entry GL + trial balance + non-終末論 reversal; ISIC-pack-aware
     chart-of-accounts seeding; invoice posting; **payment application** (settle vs cash);
     **period close** (P&L → retained earnings).
   - Reporting: **Balance Sheet + Income Statement + Cash-Flow statement** (the financial
     three); AR/AP **aging** + **credit-limit** check; **consumption-tax/VAT** report;
     **budget-vs-actual**; all-module coverage rollup; **ledger-integrity audit**.
   - Inventory: perpetual **moving-average cost** stock ledger + valuation.
   - Assets: register + **straight-line and declining-balance** depreciation.
   - Multi-currency **FX** (rate table + conversion + base-currency consolidation).
   - Masters & tenancy: party master (credit limits) + tenant ISIC-pack activation.
   - **Productivity suite** (functional, not just stored): mailer (openmail Postage), drive
     (versioned IPFS), **docs** (Markdown outline/TOC), **sheets** (exact-decimal formula
     engine + a live trial-balance worksheet), calendar (RRULE expansion).
   - **`createXrpcBridge`** — the HostSDK→Etzhayyim worker-wiring keystone — plus a full
     **end-to-end integration test** (manufacturer onboarding → a quarter of operations →
     balanced TB/IS/BS/CF → period close).

3. **Docs** — ADR-2606037200; `R2-WORKER-WIRING.md` (the worker-migration runbook); refreshed
   app `README.md` / `CLAUDE.md`; this session-close + deps.toml + ADR-README registration.

# Consequences

- open-kyber now has a feature-complete, self-auditing, end-to-end-verified kotoba-Datomic
  ERP reference, with ISIC tailoring to the division level and a functional suite. The
  canonical Datom vocabulary (the repo's SSoT) describes the full surface.
- The deployed ERP Worker is **not yet migrated**: its read path still serves the ADR-0025
  empty-envelope stubs until R2 is applied per the runbook.

# Honest limits

- `rw-free` is the **reference implementation**; it is verified in its own vitest harness
  (workspace `@etzhayyim/sdk-mock`), not against the live substrate.
- **R2 (worker `app.ts` wiring + Kysely removal) is operator-gated and un-verifiable in-repo**
  — the worker package has no build/typecheck harness here — which is exactly why it was
  captured as a runbook rather than blind-edited.
- ISIC pack overlays are `:representative` starting points, not a chartered-accountant's
  sector chart of accounts.
- Not committed at session close (working tree). The `/loop` was stopped because the work is
  complete and the surface saturated; further iterations were low-value.

# Alternatives Considered

- **Blind-edit the deployed worker `app.ts`** (1142 lines, 9+ Kysely sites) — rejected: no
  in-repo build/typecheck harness means the change couldn't be verified, violating the
  report-faithfully principle. Captured as a runbook instead.
- **Stop earlier** — the loop kept adding verified, in-harness value (each iteration tests
  green) until genuine saturation; stopped at that point.

# References

- ADR-2606037200 — open-kyber as kotoba-Datomic ERP (authoritative design)
- `60-apps/etzhayyim-project-open-kyber/rw-free/README.md` — module index
- `60-apps/etzhayyim-project-open-kyber/R2-WORKER-WIRING.md` — worker migration runbook
- `00-contracts/schemas/erp-ontology.kotoba.edn` v0.2.0 — canonical EAVT vocabulary
- ADR-2605262130 / 2605312345 — kotoba Datom = canonical state (no RisingWave)
