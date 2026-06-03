# Migration TODO

**Status**: 🔄 TRANSFORM — seed copied 2026-05-21, codemod pending.

**Codemod required**: RisingWave/Postgres → AT MST + IPFS

## Substrate-boundary checks (per CLAUDE.md)

This seed was copied verbatim from `etzhayyim-root/60-apps/ai-gftd-project-yatabase`.
The following constitutional invariants are likely violated and MUST be
remediated before this app can be considered etzhayyim-aligned:

- [ ] Replace any `@atproto/api`, `viem`, raw IPFS client, `@noble/ciphers`,
      `@signalapp/libsignal-client` imports with `@etzhayyim/sdk`.
- [ ] Strip RisingWave / Postgres / Kysely / centralized DB code — migrate to
      AT Protocol MST + IPFS + Base L2 anchor.
- [ ] Strip Stripe / PayPal / Square / fiat processors — migrate to USDC on
      Base L2 + ERC-4337 + `etzhayyim-tithe-router` (10% auto-split to
      Public Fund).
- [ ] Remove third-party advertising / AdSense / Meta Pixel / GA4 ad-linkage.
      Only internal-promo for etzhayyim's own religious activity is allowed.
- [ ] Verify identity flow uses did:web:etzhayyim.com + did:plc + WebAuthn
      passkey + Adherent SBT. Remove server-issued JWTs without DID binding.
- [ ] Reclassify payment purposes to: donation / kisha / grant / tithe /
      escrow-refund (external) OR internal-purchase / internal-subscription /
      internal-promo (SBT↔SBT carve-out).
- [ ] Audit against Charter Rider v2.0 §2(a)-(h).

## Reference

- Constitution wave ADRs: ADR-2605192100 / 2605192115 / 2605192130 / 2605192200
- Substrate boundary table: `/CLAUDE.md` § "Substrate boundary"
- Charter Rider: `/CHARTER-RIDER.md`

---

## Codemod scan results (applied 2026-05-21)

Automated annotation pass added `// CHARTER-VIOLATION` comments above each
detected violation line. The imports themselves were NOT removed (would break
the build). Remediation must replace these imports with the substrate-aligned
equivalents listed at the top of this file.

Detected violations:

```
  RW/Kysely/Prisma: /Users/junkawasaki/github/etzhayyim-root/60-apps/ai-gftd-project-yatabase/src/schema-describe.ts:64
```

---

## Post-verification gap patch (2026-05-21)

Additional violations detected in re-scan:

```
  - 60-apps/ai-gftd-project-yatabase/lg/lg_yatabase/graphs/marketing.py
  - 60-apps/ai-gftd-project-yatabase/lg/lg_yatabase/templates.py
  - 60-apps/ai-gftd-project-yatabase/lg/tests/test_marketing_sales_nodes.py
  - 60-apps/ai-gftd-project-yatabase/src/schema-describe.ts
```

Lines annotated with `CHARTER-VIOLATION §substrate` comments.

---

## Stripe → USDC codemod (2026-05-23)

<!-- stripe-usdc-codemod-closure:2605231730 -->

**Status (Stripe layer)**: ✅ codemod applied (substrate code).
**Status (overall)**: 🔄 RW→MST layer still pending (see schema-describe.ts).

### Applied changes

| File | Change |
|---|---|
| `src/billing-stripe.ts` | **deleted** — replaced by `src/billing.ts` |
| `src/billing.ts` | **new** — dead Stripe code stripped (createStripeCheckoutSession / verifyStripeSignature / kvGetStripeCustomerId / stripePriceForPlan removed), `STRIPE_*` env vars dropped, `stripeSubscriptionId`/`stripeCustomerId` params dropped, handlers return Charter Rider §2 403/410 responses |
| `src/donate.ts` | **rewritten** — wired to `@etzhayyim/sdk` `donate()` (v0.1 EOA path), stub txHash removed. Returns 503 `SignerUnconfigured` when `YATA_DONATE_PRIVATE_KEY` is absent. |
| `src/app.ts` | import path updated (`./billing-stripe` → `./billing`); legacy `/webhook/stripe` + `/auth/v1/portal` route comments now flag deprecation; `/auth/v1/whoami` no longer reads `stripeCustomerId` from KV (always `null` + `canOpenPortal: false`) |
| `src/landing.ts` | feature card "Stripe Live billing (US)" → "USDC donations on Base L2"; upgrade copy now points to POST /api/donate |
| `svelte/src/lib/api.ts` | `auth.upgrade()` / `auth.stripePortal()` removed; replaced by `auth.downgradeToFree()` + new `donate.submit()` namespace + `DonationPurpose` enum |
| `svelte/src/routes/studio/billing/+page.svelte` | "Upgrade to Developer — $33/mo" / "Manage subscription" buttons replaced by USDC donation form (amount + purpose + memo) hitting `donate.submit()` |
| `package.json` | added `@etzhayyim/sdk: workspace:*` to `dependencies` |

### Remaining (documentation rewrites — non-blocking)

These files still contain "Stripe" references that describe legacy endpoints
in user-facing documentation. The active code paths are unchanged by these
strings, so they were not rewritten in this codemod:

- `src/openapi.ts` — `/auth/v1/upgrade` / `/auth/v1/portal` / `/webhook/stripe` paths
  still documented as Stripe surfaces; add `deprecated: true` flag + describe
  /api/donate replacement.
- `src/docs.ts` — "Upgrade" + "Customer Portal" sections need rewrite.
- `src/changelog.ts` / `src/quickstart.ts` / `src/terms.ts` / `src/privacy.ts` /
  `src/data-rights.ts` / `src/seo.ts` / `src/studio.ts` / `src/invoice.ts` /
  `src/email-outbox.ts` / `src/plan-quota.ts` — string-level mentions only.
- `lg/lg_yatabase/graphs/bmc_iteration.py` — BMC iteration template; review.
- `svelte/README.md` — README rewrite for new USDC flow.

### Remaining (RW→MST layer)

The substrate-boundary RW violations called out in the post-verification gap
patch above (`schema-describe.ts`, `marketing.py`, `templates.py`,
`test_marketing_sales_nodes.py`) are out of scope for the Stripe→USDC
codemod. They will be addressed in a follow-up RW→MST sweep.

### Pre-deploy checklist

- [ ] Configure `YATA_DONATE_PRIVATE_KEY` (Worker secret, EOA on Base L2).
- [ ] Configure `YATA_DONATE_TREASURY` (Base L2 Safe address).
- [ ] Run `pnpm typecheck` from `60-apps/ai-gftd-project-yatabase`.
- [ ] Run `pnpm studio:build` to verify Svelte page compiles.
- [ ] Run the customer-journey smoke (`70-tools/scripts/yatabase-customer-journey.mjs`) — note steps 7/8 (Stripe webhook + post-checkout) will now respond 410; update smoke script.
- [ ] Update OpenAPI spec + docs strings (above).

_Closed by manual codemod 2026-05-23._
