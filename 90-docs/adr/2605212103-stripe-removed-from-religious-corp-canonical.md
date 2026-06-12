---
id: adr-2605212103-stripe-removed-from-religious-corp-canonical
renumbered_from: "2605212100"
title: "ADR-2605212103: Stripe URL + stripePost removed from etzhayyim canonical repo (open-kyber) — Charter Rider §1.3 compliance"
status: proposed
doc_type: adr
topic: stripe-removal-religious-corp-canonical
authoritative: true
last_verified: 2026-05-21
priority: 7.0
axis: governance
weight: 0.70
priority_note: "Charter Rider §1.3 forbids fiat payment processors on the religious-corp canonical substrate. The Stripe code in 60-apps/etzhayyim-project-open-kyber/ erp/src/app.ts shipped before the rider landed and was flagged as a violation by the Phase 4 yorishiro migration survey (ADR-2605211900). This ADR replaces the Stripe call sites with a no-op stub that keeps types intact and documents the downstream-fork patch contract."
authoritative_for:
  - open-kyber Stripe integration policy in canonical etzhayyim repo
  - downstream commercial fork patch contract for billing
depends_on:
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605211900-etzhayyim-yorishiro-external-actor-bridge
related:
  - 60-apps/etzhayyim-project-open-kyber/etzhayyim-wasm-kyber-erp-kyb3rerp/src/app.ts
  - 70-tools/scripts/yorishiro/survey.mjs
supersedes: []
superseded_by: []
---

# ADR-2605212103: Stripe URL + stripePost removed from etzhayyim canonical repo (open-kyber) — Charter Rider §1.3 compliance

**Status**: proposed
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

# Context

The yorishiro migration survey (ADR-2605211900 Phase 4,
`70-tools/scripts/yorishiro/survey.mjs`) bucketed every direct external
`fetch` callsite in the monorepo against three rules:

1. `matched` — host covered by an existing yorishiro → migrate
2. `unmatched` — host has no yorishiro yet → author one
3. `violation` — host is a forbidden category per Charter Rider §2 +
   ADR-2605192115 §1.3 → **do NOT yorishiro-wrap; remove entirely**

Exactly one finding landed in the `violation` bucket:

```
60-apps/etzhayyim-project-open-kyber/etzhayyim-wasm-kyber-erp-kyb3rerp/src/app.ts:620
  URL    : https://api.stripe.com/v1/${path}
  reason : ADR-2605192115 §1.3 — fiat payment processors are forbidden
```

The Stripe integration predates the Charter Rider v2.0 wave (ADR-2605192200,
2026-05-19) and the §1.3 narrowing (ADR-2605192115, 2026-05-19). At
authoring time, `kyber.etzhayyim.com` (the etzhayyim commercial tenancy of the
open-kyber codebase) was operated as a paid ERP. Post-Charter, this is
no longer compatible with the canonical religious-corp repo.

Two call sites use it:

| Site | Purpose | Stripe API |
|---|---|---|
| `cmdProvisionTenant` | Create a Stripe customer when a tenant signs up on a non-free plan | `POST /v1/customers` |
| `cmdReportUsageToStripe` | Report monthly usage events to a Stripe meter | `POST /v1/billing/meter_events` |

# Decision

The canonical `etzhayyim/root` repo MUST NOT contain the literal
`api.stripe.com` URL or a working `stripePost` implementation. The
type signature `stripePost(path, params, stripeKey)` is preserved as
a no-op stub so the existing call sites typecheck without further
edits and so the open-kyber module still builds:

```ts
async function stripePost(
  _path, _params, _stripeKey
): Promise<{ ok: boolean; id?: string; errorMessage?: string }> {
  return {
    ok: false,
    errorMessage:
      "Stripe disabled in canonical etzhayyim repo (Charter Rider §1.3). " +
      "Patch your downstream commercial fork to re-implement stripePost.",
  };
}
```

The two call sites (`cmdProvisionTenant` / `cmdReportUsageToStripe`)
already handle `ok=false` paths: provisioning continues with an empty
`stripeCustomerId`, and usage reporting accumulates skips/errors. No
behaviour-affecting edits are needed at the call sites.

## Downstream fork contract

A commercial fork that wants Stripe back patches a single function in
its own tree:

```ts
// In a downstream branch / private overlay only:
async function stripePost(path, params, stripeKey) {
  const body = new URLSearchParams(params).toString();
  const res = await fetch(`https://api.stripe.com/v1/${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${stripeKey}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
  });
  // … (the implementation that lived in the canonical repo prior to this ADR)
}
```

The downstream fork's CI runs without `no-external-purchase-purpose`
+ without the yorishiro survey gate, since it operates under a
different (for-profit) constitutional regime.

## Why a stub instead of full removal

Two reasons to keep the function signature:

1. **Type safety**: deleting `stripePost` would force matching deletion of
   both call sites and their `stripeCustomerId` plumbing. That's a
   wide refactor that crosses the open-kyber ERP's data model
   (`vertex_kyber_billing_tenant.stripe_customer_id` column). The stub
   keeps the canonical repo's `tsc --noEmit` clean.
2. **Migration ergonomics**: a downstream fork patches one function;
   they don't have to re-thread Stripe through the codebase.

# Consequences

## Positive

- `yorishiro audit` + `no-external-purchase-purpose` lefthook hook now
  pass on the open-kyber tree (the survey's `violation=1` finding clears).
- The canonical repo no longer contains a literal call to `api.stripe.com`,
  matching the religious-corp's substrate-edge invariants.
- The downstream commercial fork contract is documented and minimal
  (one function patch).

## Negative

- `kyber.etzhayyim.com` (the deployed commercial tenancy) will not collect
  customers / report usage to Stripe until the downstream fork patches
  `stripePost` back in. This is the expected outcome — the deployed
  instance operates under etzhayyim's commercial license, not under
  the religious-corp Charter Rider.
- A future contributor might re-add Stripe (or another payment
  processor) at a different call site. The `no-external-purchase-purpose`
  hook + the `survey.mjs` `CHARTER_VIOLATION_HOSTS` map catch the URL
  but not other payment processors. Periodic Charter audits remain
  necessary.

# Alternatives Considered

## ALT-1: keep the Stripe code, gate by env var

Already the existing behaviour (`if (stripeKey && planId !== "free")`).
The URL is still in source and the survey still flags it. Doesn't
satisfy Charter compliance.

## ALT-2: delete `stripePost` entirely; remove both call sites + DB columns

Cleanest but invasive — requires schema migration for the
`vertex_kyber_billing_tenant` table. Deferred to a later refactor
PR; for now the stub keeps the surface area minimal.

## ALT-3: move `stripePost` to a separate file gated by an env-var build flag

Adds build-config complexity without removing the URL from canonical
source.

# References

- ADR-2605192115 (SBT↔SBT internal carveout — §1.3 forbids subscription / purchase / tip on external)
- ADR-2605192200 (Charter Rider v2.0 — §2 prohibited categories)
- ADR-2605211900 (yorishiro external-actor bridge — Phase 4 survey identified this finding)
- `70-tools/scripts/yorishiro/survey.mjs` (the Phase 4 audit tool)
- `60-apps/etzhayyim-project-open-kyber/etzhayyim-wasm-kyber-erp-kyb3rerp/src/app.ts` (Stripe call sites)
