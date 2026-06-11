---
id: adr-2605202800-tsukuru-etzhayyim-business-model-change
title: "ADR-2605202800: tsukuru full move to etzhayyim — business model change (Stripe Issuing → ERC-4337 + USDC)"
status: proposed
doc_type: adr
topic: tsukuru-etzhayyim-business-model-change
authoritative: true
last_verified: 2026-05-20
priority: 7.0
axis: organization
weight: 0.70
priority_note: "Multi-phase business-model-change migration. Phase 1 (spec/lexicon/BPMN scaffold + plan) lands with this ADR. Phase 2-5 (payment rewrite + factory DID migration + DNS cutover + vendor deprecation) deferred to follow-up ADRs."
authoritative_for:
  - tsukuru B2B factory-direct ordering on etzhayyim substrate
  - Stripe Issuing → ERC-4337 + USDC payment migration plan
  - Kotoba/Datomic Hyperdrive → PDS XRPC + IPFS storage migration plan
  - 460+ factory DID migration plan (etzhayyim → etzhayyim)
depends_on:
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605171900-yoro-migration-to-etzhayyim
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
related:
  - adr-2605202300-maps-etzhayyim-consumer-migration
  - adr-2605202400-gtfs-rt-vendor-mirror
supersedes: []
superseded_by: []
---

# ADR-2605202800: tsukuru full move to etzhayyim — business model change

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

`tsukuru.etzhayyim.com` is the vendor B2B factory-direct ordering platform —
460+ manufacturer DIDs across 30+ countries, BTO/MTO/CTO production
orders, EUV lithography + CNT manufacturing flows, supplier exchange
package normalization, trade compliance + HS classification. Current
implementation:

- **Persistence**: `createKyselyDb()` (Kotoba/Datomic Hyperdrive direct
  write, T2 Domain per ADR-0036)
- **Payment**: `payment.method = "stripe_issuing"` — Stripe Issuing
  virtual cards for factory disbursement, cross-actor invoke
  `did:web:stripe.etzhayyim.com cancelCard`
- **Runtime**: `runtime = "k8s-langserver"` with bpmn-dispatcher +
  kotodama.worker_api on Vultr VKE
- **Identity**: `did:web:tsukuru.etzhayyim.com` controller + path-based DIDs
  for industry sections (ISIC A-U) + manufacturer registry path DIDs
- **Storage**: `graph = "kotoba"` (vertex_tsukuru_*)

Per **ADR-2605172400** 3-axis OR-test, tsukuru as-is is structurally
**vendor-bound** (all 3 axes hit): operator product liability + factory
master custody + Stripe fiat settlement. This was the same pattern
caught for ohanashi / joucho / kagami / sense earlier in the
2026-05-20 migration sweep.

User direction 2026-05-20: "tsukuru も etzhayyim に移行、統合" with
explicit override interpretation = **business model change to satisfy
3-axis clean for etzhayyim deployment**, not catalog SPLIT.

This ADR records the multi-phase plan to make tsukuru substrate-clean.

# Decision

**Migrate tsukuru to etzhayyim/root via business model change.** The
etzhayyim deploy of tsukuru runs RW-free (PDS + IPFS) and on-chain-only
(ERC-4337 + USDC), satisfying ADR-2605172000 and ADR-2605172100.

Multi-phase rollout to avoid breaking the 460+ manufacturer production
workload. Vendor `tsukuru.etzhayyim.com` runs in parallel with etzhayyim
implementation until factory migration completes.

## Phase 1 — scaffold + plan (THIS ADR + sibling vendor PR)

Land:
- This ADR (proposed status)
- `etzhayyim-root/60-apps/etzhayyim-project-tsukuru/` scaffold:
  - CLAUDE.md (sed-transformed from vendor)
  - PROJECT.jsonld, OWNERS, kotodama.toml
  - scripts/register-isic-industry-actors.mjs
  - appview/tsukuru-tsukr8u0/{package.json, vitest.config.ts}
  - appview/tsukuru-tsukr8u0/src/README.md — Phase 2 placeholder
    (does NOT carry over Stripe + RW src/app.ts)
- `etzhayyim-root/20-actors/tsukuru/{actor-manifest.jsonld, CLAUDE.md}`
  (21 ISIC industry path-based actors)
- vendor `deps.toml [[migrations]]` entry
  `tranche-f-tsukuru-etzhayyim-fullmove-2026-05-20` with full plan +
  blocked-by list

Note: lexicons (9 sub-dirs) and BPMN (10+ files) for tsukuru already
present in etzhayyim/root from Phase 3 wave 5 — only the 60-apps
project dir + actor-manifest needed scaffolding.

## Phase 2 — payment + persistence rewrite (NEW etzhayyim-side PR)

Rewrite the appview src/app.ts for etzhayyim substrate:

### 2.1 — replace `createKyselyDb()` writes with PDS XRPC

Current vendor pattern:
```ts
const db = createKyselyDb();
await db.insertInto('vertex_tsukuru_production_order').values({ ... }).execute();
```

Etzhayyim pattern:
```ts
await sdk.pds.comAtprotoRepoCreateRecord(
  'ai.etzhayyim.apps.tsukuru.productionOrder',
  { ... }
);
```

Read path:
- Hot: etzhayyim `mst-projector` (`50-infra/mst-projector/`) → fixed-
  shape views
- Cold: PDS firehose + IPFS CAR archives

### 2.2 — replace Stripe Issuing with ERC-4337 + USDC

Current vendor:
```ts
payment: { method: "stripe_issuing", stripeCardId: "isc_xyz" }
await kotodama.Invoke("did:web:stripe.etzhayyim.com", "cancelCard", { cardId });
```

Etzhayyim:
```ts
import { pay } from "@etzhayyim/sdk";
await pay({
  to: factoryWallet, // ERC-4337 smart wallet
  amount: { value: "10000", currency: "USDC" }, // 10,000 USDC
  chain: "base",
  meta: { productionOrderId, tsukuruRfqUri },
});
// → @etzhayyim/sdk handles UserOperation construction via
//   etzhayyim-paymaster + Base L2 USDC transfer
```

Factory disbursement: factories provide ERC-4337 smart-wallet addresses
during Phase 4 migration (instead of W-8BEN + bank info as currently).
`etzhayyim-paymaster` pays gas on factory behalf.

Cancellation / dispute: ERC-4337 has no `cancelCard` analog. Replace
with **escrow pattern**: USDC held in `ai.etzhayyim.apps.payment.escrowOpened`
state, released on `qualityInspection.passed`, refundable to buyer
within dispute window. Reference: `00-contracts/lexicons/com/etzhayyim/apps/
payment/{sent,streamStarted,escrowOpened,split}.json` (already in
etzhayyim/root from Phase 3 wave 4).

### 2.3 — rewrite cross-actor invokes

Current Stripe invoke calls become:
- `cancelCard` → escrow release/refund via @etzhayyim/sdk
- `chargeCustomer` → escrow open via @etzhayyim/sdk pay()

## Phase 3 — etzhayyim deploy

- DNS: `AAAA tsukuru.etzhayyim.com → 100::` (CF Worker route placeholder
  per ADR-2605172300 platform.dns pattern)
- Build + deploy `@etzhayyim/tsukuru` Worker on etzhayyim CF account
- Smoke: `curl https://tsukuru.etzhayyim.com/health` = 200
- Lexicon NSID rename: `com.etzhayyim.apps.tsukuru.*` → `ai.etzhayyim.apps.tsukuru.*`
  (lexicon files already exist in etzhayyim under `com/etzhayyim/apps/tsukuru/`
  per Phase 3 wave 5; rename collection NSIDs at this Phase 3 step)

## Phase 4 — factory DID migration (operator + factory consent)

460+ manufacturer DIDs currently at `did:web:tsukuru.etzhayyim.com:manufacturer:{slug}`.

For each factory:
1. Notify factory of platform migration (etzhayyim non-profit operator,
   USDC settlement, ERC-4337 smart wallet onboarding)
2. Factory provides ERC-4337 smart wallet address (or platform helps
   set one up via etzhayyim-paymaster)
3. Mint `tsukuru.etzhayyim.com:manufacturer:{slug}` DID on etzhayyim PDS
4. Mirror manufacturer registry record from vendor to etzhayyim
5. Forward future RFQs to new DID
6. Sunset old `tsukuru.etzhayyim.com:manufacturer:{slug}` after first successful
   etzhayyim-side order

Estimated timeline: 460 factories × ~1 day onboarding = 6 month rolling
migration. Factories with no etzhayyim engagement after 6 months get
sunset notice.

## Phase 5 — DNS cutover + vendor deprecation

After ≥80% factory migration + ≥1 month etzhayyim-side production
proven:
- Add `routing-gateway/src/worker.ts` branch: `label === 'tsukuru'`
  → 301 to `tsukuru.etzhayyim.com` (yoro Stage 4 pattern, PR #1315)
- Stripe Issuing wind-down — settle outstanding cards, cancel program
- vendor `60-apps/etzhayyim-project-tsukuru/` → `[MOVED]` stub
- vendor CF Worker delete: `tsukuru-tsukr8u0`

## Phase 6 — long-tail cleanup

- Remaining < 20% factories that didn't migrate: courtesy sunset or
  legacy wrap-up
- Vendor Kotoba/Datomic `vertex_tsukuru_*` tables: keep as historical
  read-only mirror for 1 year (compliance / audit reference)
- Lexicon dual-schema retire (vendor NSID `com.etzhayyim.apps.tsukuru.*`
  removal)

# Consequences

## 正の効果

- **3-axis clean satisfied**: Liability redistributed to factories
  (KYC on factory side, not platform operator), Custody on PDS +
  IPFS (no centralized DB), Settlement on Base L2 (no Stripe fiat).
- **Open ecosystem**: 460+ factories become etzhayyim-native and can
  serve other etzhayyim-side apps without re-onboarding.
- **Lower cost**: USDC on Base L2 has dramatically lower fees than
  Stripe Issuing (no 3% + $0.30 per transaction).
- **Censorship resistance**: factory payments don't depend on Stripe
  approval / risk team.

## 負の効果 / コスト

- **Massive rewrite**: 460+ factory DID migrations + payment system
  swap + persistence layer swap = multi-quarter project.
- **Factory consent risk**: some factories may refuse ERC-4337
  onboarding (KYC concerns, regulatory in their jurisdiction, no crypto
  experience). Could lose ~20% of supplier network.
- **Trade compliance regression**: existing Stripe + KYC infrastructure
  has US OFAC + EU sanctions screening built in. ERC-4337 + USDC has
  weaker built-in screening — need separate sanctions check via
  `sanctions-screening` actor (which stays vendor per ADR-2605172400).
- **Customer (buyer) flow**: buyers must hold USDC and sign ERC-4337
  UserOperations. Higher friction than credit card payment. May need
  vendor-side `okaimono.etzhayyim.com` Stripe-frontend that bridges to
  etzhayyim USDC behind the scenes (acceptable per ADR-2605172400
  vendor → etzhayyim consent-capability pattern).
- **Dispute resolution complexity**: ERC-4337 lacks Stripe-style
  charge-back. Escrow pattern handles common cases but adversarial
  disputes need ADR.

## Migration plan

### Immediate (this PR pair)
- [x] etzhayyim/root scaffold (60-apps + 20-actors + ADR)
- [x] vendor deps.toml entry with full plan

### Near-term (next session work)
- [ ] Phase 2.1: PDS XRPC reimpl of writes (per-collection PRs)
- [ ] Phase 2.2: @etzhayyim/sdk pay() integration + escrow pattern
- [ ] Phase 2.3: cross-actor invoke rewrites

### Medium-term (1-3 months)
- [ ] Phase 3: tsukuru.etzhayyim.com deploy
- [ ] Phase 4 start: factory consent + onboarding outreach

### Long-term (6-12 months)
- [ ] Phase 4 complete: 460 factory migrations
- [ ] Phase 5: DNS cutover + vendor stub
- [ ] Phase 6: long-tail cleanup

# Alternatives Considered

## A. C-group SPLIT pattern (lexicon etzhayyim, production vendor)

Apply same pattern as dougaka / animeka / manga: keep production
src/app.ts vendor (with Stripe + RW), only move lexicons.

却下理由: user explicitly directed "移行、統合" (migrate + integrate),
implying full move not split. Also tsukuru's open-economy potential
(global factory network) benefits more from etzhayyim's substrate
than vendor's centralized SaaS shape.

## B. Vendor confirmed + no move

Accept 3-axis HIT result (same as ohanashi / joucho / kagami / sense)
and record vendor-confirmed entry.

却下理由: user override.

## C. New tsukuru-v2 on etzhayyim, leave v1 vendor

Build `tsukuru-v2.etzhayyim.com` as greenfield etzhayyim-native and
let factories choose to migrate or not.

却下理由: complexity (two parallel platforms forever), brand
confusion. Phased rollout (this ADR) is the same outcome with
clearer migration arc.

# References

- ADR-2605172000 — etzhayyim RW-free substrate (Phase 2.1 driver)
- ADR-2605172100 — payments on-chain only (Phase 2.2 driver)
- ADR-2605172400 — 3-axis split rule (this ADR overrides vendor-default verdict)
- ADR-2605171900 — yoro AppView migration (reference pattern for Stage 3-5)
- ADR-2605172300 — etzhayyim DNS scaffolding
- `@etzhayyim/sdk` `pay()` reference: `etzhayyim-root/20-actors/etzhayyim-sdk/`
- `etzhayyim-paymaster` ERC-4337 reference: `etzhayyim-root/50-infra/etzhayyim-paymaster/`
- vendor deps.toml `tranche-f-tsukuru-etzhayyim-fullmove-2026-05-20`
- Seed Data: `00-contracts/catalogs/com/etzhayyim/tsukuru/manufacturer-catalog.v1.json` (465 companies)
