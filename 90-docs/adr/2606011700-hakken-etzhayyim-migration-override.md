---
id: adr-2606011700-hakken-etzhayyim-migration-override
title: "ADR-2606011700: hakken product-discovery ingest → etzhayyim (override of vendor-keep ADR-2606011400)"
status: proposed
doc_type: adr
topic: hakken-etzhayyim-migration-override
authoritative: true
last_verified: 2026-06-01
priority: 7.0
axis: organization
weight: 0.70
priority_note: "User-directed move (2026-06-01) of hakken's product-discovery ingest front to etzhayyim, overriding the same-day vendor-keep verdict of vendor ADR-2606011400 (Consensys pattern). Phase 1 (scaffold + ingest-core rw-free + lexicons + this ADR) lands now. Phase 2 (pipeline rehome) and Phase 3 (fulfillment via etzhayyim consent capability) deferred."
authoritative_for:
  - hakken product-discovery ingest on the etzhayyim RW-free substrate
  - com.etzhayyim.apps.hakken.* record namespace
  - the etzhayyim/etzhayyim boundary for hakken (ingest front vs fulfillment tail)
depends_on:
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
  - adr-2605202800-tsukuru-etzhayyim-business-model-change
overrides:
  - vendor ADR-2606011400 (Consensys pattern) — vendor-keep verdict for hakken
---

# ADR-2606011700: hakken product-discovery ingest → etzhayyim (override of vendor-keep ADR-2606011400)

## Status

Proposed (2026-06-01). User-directed.

## Context

`hakken` (発見, vendor `hakken.etzhayyim.com`, nanoid `h4kk3n0x`) is an AI-First OEM
product-discovery × D2C pipeline (vendor ADR-2605270000): it scans branded-product price
gaps, searches OEM/supplier candidates on AliExpress / Alibaba / 1688, scores them, routes
SKUs through a 3-phase lifecycle (dropship → import → OEM), and registers them for D2C sale.

Under the vendor 3-axis split rule (ADR-2605172400) hakken was **vendor-confirmed**:

| Axis | Evidence | Verdict |
|---|---|---|
| Liability | resale / small-lot import operator duty | HIT |
| Custody | supplier master + marketplace order data | HIT |
| Settlement | `okaimono_register` Stripe product creation, `import_order` marketplace payment | HIT |

The same-day vendor ADR-2606011400 (Consensys pattern) reaffirmed this: the **consumer-facing
product layer defaults to the etzhayyim front**, while **regulated functions (merchant-of-record,
fiat settlement, fulfillment, PII custody) stay etzhayyim functions** consumed via consent capability.

The user directed (2026-06-01): *"etzhayyim/root に移行してください"* for the company/product
ingest actors (hakken + tsukuru). This ADR records the hakken half.

## Decision

Move hakken's **product-discovery ingest front** to etzhayyim, splitting it from the regulated
fulfillment tail exactly as ADR-2606011400 prescribes — but landing the product-front code in
etzhayyim/root rather than leaving it vendor-side.

1. **Ingest front → etzhayyim.** `trend_scan`, `gap_analysis`, `supplier_search`,
   `quality_eval`, and the **ingest write path** (branded products + supplier candidates →
   kotoba product KG) move to `hakken.etzhayyim.com`. These are on-chain-clean: the facts are
   public OSINT-grade product/supplier data, no payment, no private custody.

2. **Fulfillment tail stays a etzhayyim function.** `okaimono_register` (Ph1 dropship) + Stripe
   product creation, `import_order` (Ph2 Alibaba small-lot), and `tsukuru_order` (Ph3 OEM)
   HIT the Settlement + Custody axes. They remain etzhayyim functions consumed via consent
   capability. etzhayyim hakken takes no payment and is not merchant-of-record. (tsukuru
   itself is separately etzhayyim-migrated per ADR-2605202800; its on-chain escrow-intent is
   a later option for hakken's OEM route.)

3. **RW-free + on-chain.** Persistence is `@etzhayyim/sdk` `e.write()` → PDS XRPC createRecord
   → MST + IPFS + Base L2 anchor. No RisingWave. Mirrors tsukuru rw-free (ADR-2605202800
   Phase 2). Vendor floats are integer-encoded (`weightG` = kg×1000, `ratingMilli` = rating×1000)
   per the AT-Lexicon no-float rule.

4. **NSID namespace = `com.etzhayyim.apps.hakken.*`** (operator-directed, reverse-DNS of
   etzhayyim.com). hakken had no legacy etzhayyim lexicon (vendor wrote kotoba datoms directly), so
   the namespace is native. **Note:** the established record-NSID authority elsewhere in
   etzhayyim/root is `com.etzhayyim.*` (consent / council / encrypted / esign), with
   `com.etzhayyim.*` otherwise reserved for launchd/system labels. `com.etzhayyim.*` was chosen
   here by explicit operator direction; if the org standardises record NSIDs on `com.etzhayyim.*`,
   hakken should follow in a later sweep (lexicons + write-path collections + magatama
   `nsidPrefixes`).

## Override

This ADR **overrides the hakken-specific vendor-keep verdict of vendor ADR-2606011400**. The
*structure* of 2606011400 is preserved (product front → etzhayyim, regulated tail → etzhayyim
function); only the placement of the product-front code changes from vendor-side to
etzhayyim/root. The liability invariant is unchanged: etzhayyim is neither merchant-of-record
nor settlement counterparty; etzhayyim remains both for any hakken-originated sale.

## Consequences

- **Phase 1 (this commit):** scaffold (`PROJECT.jsonld`, `magatama.jsonld`, `OWNERS`,
  `CLAUDE.md`) + 4 lexicons (`ingestProduct`, `ingestSupplierCandidate`, `listProducts`,
  `listSupplierCandidates`) + `rw-free/` ingest reference (`types.ts`, `ingest.ts`). Vendor
  `hakken.etzhayyim.com` unchanged.
- **Phase 2 (planned):** rehome the LangGraph discovery nodes to the etzhayyim Murakumo fleet,
  writing through the rw-free ingest surface. kotoba product KG only; no RW.
- **Phase 3 (deferred):** fulfillment via etzhayyim consent capability; optional on-chain
  escrow-intent OEM route reusing tsukuru's Phase 2 pattern.
- **Phase 4 (planned):** vendor discovery-node sunset once etzhayyim ingest is stable.
- **Lexicon bundle:** `10-protocol/lexicons-bundle/src/lexicons.gen.json` regenerated
  (`node scripts/build-bundle.mjs`) so the 4 `com.etzhayyim.apps.hakken.*` lexicons resolve;
  without this the PDS validator hangs with `Lexicon not found`. The PDS typed registry
  (`gen-pds-lexicon-registry.mjs`) + Worker redeploy is a **Phase 2 deploy prerequisite**
  (no etzhayyim deploy happens in this commit; vendor is unchanged).
- **This PR is hakken-only.** `main` independently migrated tsukuru to `com.etzhayyim.apps.tsukuru.*`
  (~86 files, part of a repo-wide `com.etzhayyim.apps.*` standard — 15,758 occurrences vs 0 for
  `com.etzhayyim.*`). Per operator direction (2026-06-01), tsukuru will be converted to
  `com.etzhayyim.apps.tsukuru.*` to match hakken, **but in a separate follow-up PR** because it
  overrides merged work across 86 files including cross-app refs (aidesk / hc), graph migrations,
  and four generated registries (`lexicons.gen.json` / `_manifest.json` / `apps.openapi.json` /
  `docs.json`) that must be regenerated. Bundling it here would make this PR unreviewable. hakken
  is left at `com.etzhayyim.*` in this PR; the tsukuru sweep follows.
- **Payment namespace stays shared.** hakken takes no payment, so writes no payment records. The
  shared payment/escrow authority (`payment.escrowOpened/escrowRefunded/sent/split/stream`,
  read by treasury / tithe) is owned by a different actor and is NOT part of the hakken or
  tsukuru namespace decision — it follows whatever the payment authority standardises on
  (currently `com.etzhayyim.apps.payment.*` on main).
- **Open:** the `com.etzhayyim.*` vs `com.etzhayyim.*` record-NSID convention (see Decision §4)
  needs an org-level ruling. The operator chose `com.etzhayyim.*` for hakken/tsukuru with full
  knowledge that the repo standard is `com.etzhayyim.*`; this divergence is deliberate and
  documented, to be revisited at org-level standardisation.

## Status update (2026-06-02 — session close)

All migration PRs merged to `etzhayyim/root` main:

- **#697 (merged)** — Phase 1 contract surface: scaffold + 4 `com.etzhayyim.apps.hakken.*`
  lexicons + rw-free ingest reference.
- **#724 (merged)** — **actual LangGraph pipeline code moved from vendor, VERBATIM** (no
  refactor): `lg/lg_hakken/` = `graph.py`, `state.py`, `edn.py`, `kotoba.py`,
  `kotoba_datomic.py`, and the 11 nodes (`trend_scan`, `gap_analysis`, `supplier_search`,
  `quality_eval`, `phase_router`, `okaimono_dropship`, `import_order`, `tsukuru_order`,
  `okaimono_register`, `social_announce`, `phase_promotion`) + `pyproject.toml` / `uv.lock` /
  `wasm/agent.py`. Byte-identical to vendor HEAD (excl `.venv`/`__pycache__`).
- **#718 (merged)** — tsukuru converted to `com.etzhayyim.apps.tsukuru.*` (ADR-2606020000).

**Code state:** the moved pipeline is **un-refactored by design** — it still references vendor
`kotoba`/RisingWave/Stripe and `com.etzhayyim.*` NSIDs. Per operator direction the refactor
(RW → kotoba/PDS, Stripe tail → etzhayyim consent capability, `com.etzhayyim.*` → `com.etzhayyim.*`,
wiring the pipeline to the rw-free ingest surface) happens **on the etzhayyim side** and is the
remaining Phase 2/3 work. Vendor `hakken.etzhayyim.com` is unchanged (Phase 4 sunset still pending,
after etzhayyim deploy proves stable).

**Backlog:** the company/product ingest-actor *code move* is complete (hakken contract +
pipeline, tsukuru namespace, okaimono already resident). Remaining items — etzhayyim-side
refactor, LangGraph pod rehome/deploy, vendor sunset — are operator/infra tasks, not further
code moves.

## References

- Vendor ADR-2606011400 — Consensys pattern (product front / infra back) [overridden for hakken placement]
- Vendor ADR-2605270000 — hakken OEM product-discovery BMC-lean (origin design)
- ADR-2605202800 — tsukuru full move to etzhayyim (business-model-change; sibling ingest actor)
- ADR-2605172000 — etzhayyim RW-free substrate
- ADR-2605172400 — etzhayyim 3-axis split rule
