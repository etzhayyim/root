# Migration TODO

**Status**: 🔄 TRANSFORM — seed copied 2026-05-21, codemod pending.

**Codemod required**: RisingWave/Postgres -> kotoba Datomic EDN

## Substrate-boundary checks (per CLAUDE.md)

This seed was copied verbatim from `etzhayyim-root/60-apps/etzhayyim-project-hrse`.
The following constitutional invariants are likely violated and MUST be
remediated before this app can be considered etzhayyim-aligned:

- [ ] Replace any `@atproto/api`, `viem`, raw IPFS client, `@noble/ciphers`,
      `@signalapp/libsignal-client` imports with `@etzhayyim/sdk`.
- [ ] Strip RisingWave / Postgres / Kysely / centralized DB code — migrate to
      kotoba Datomic EDN EAVT records.
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
detected violation line. Remediation must replace these imports with the
substrate-aligned equivalents listed at the top of this file.

Detected violations:

```
  none remaining for direct AT Protocol client imports; server-client uses @etzhayyim/sdk/atproto
```

---

## Stripe → USDC codemod (2026-05-23)

<!-- stripe-usdc-codemod-closure:2605231830 -->

**Status (Stripe layer)**: ✅ verified — only JSDoc comment mentions in `appview/external-hrse/src/lib/clerk-subscription.ts` (no active Stripe SDK calls). Comment language can be updated in a future docs sweep; no behavioural change required.

_Verified by manual review 2026-05-23._

---

## RW → MST substrate codemod (2026-05-23)

<!-- rw-mst-codemod-progress:2605231930 -->

**Status**: 🟡 partial — annotated; runtime migration pending.

### Applied

- 4 operational scripts annotated with `// CHARTER-VIOLATION §substrate` at the
  `import postgres from "postgres"` line so the lint catches them:
  - `appview/external-hrse/scripts/migrate-data.ts`
  - `appview/external-hrse/scripts/run-migrations.ts`
  - `appview/external-hrse/scripts/seed-master-data.ts`
  - `appview/external-hrse/scripts/verify-seed-data.ts`

These are one-shot operational scripts (data migration + verification), not
runtime worker code. They are kept in place because the underlying Postgres
schema they target will exist until hrse adopts the MST PDS write path.

### Remaining

- Adopt `_etzhayyim_substrate.py`-style seam (or its TypeScript equivalent
  against `@etzhayyim/sdk`) for the four scripts so they can be re-run
  against MST + IPFS once hrse cuts over.
- `appview/external-hrse/src/lib/clerk-subscription.ts` — Stripe references
  in JSDoc only; no runtime change needed.

_Closed (Stage 1) by manual codemod 2026-05-23._
