---
id: adr-2606111700-public-sponsor-donation-solicitation-surfaces
title: "ADR-2606111700: Public sponsor / donation solicitation surfaces — GitHub Sponsor button (custom-only) + DONATE.md + README + active /donate CTA"
status: accepted
doc_type: adr
topic: public-sponsor-donation-solicitation-surfaces
authoritative: true
last_verified: 2026-06-11
priority: 5.0
axis: governance
weight: 0.5
priority_note: "Answers 「etzhayyim でも sponsor, donation を募集して」. Adds the PUBLIC-FACING solicitation surfaces the repo lacked (no FUNDING.yml, no DONATE.md, no README support section) on TOP of the already-live /donate + /.well-known/donation.json declaration (ADR-2606012100). Charter-clean by construction: the GitHub Sponsor button uses custom-only URLs pointing at the on-chain donate page (NO fiat Sponsor rails — Stripe/Patreon/etc are prohibited, ADR-2605172100); solicitation is benefit-free (no quid-pro-quo tiers/leaderboards, G4); NO on-chain address is fabricated (the live donation.json stays the single SoT). ZERO invariant amendments — purely additive public-proof + 募集 copy."
authoritative_for:
  - the public sponsor/donation solicitation surfaces (.github/FUNDING.yml + DONATE.md + README support section + /donate CTA)
  - the FUNDING.yml charter-clean rule (custom-only, no fiat Sponsor rails)
depends_on:
  - 2606012100
  - 2605192115
  - 2605192130
  - 2605172100
related:
  - 2605192100
  - 2605215000
  - 2605301020
  - 2605301036
  - 2605262900
supersedes: []
superseded_by: []
---

# ADR-2606111700: Public sponsor / donation solicitation surfaces

**Status**: accepted (founder; additive, zero invariant amendments)
**Date**: 2026-06-11
**Deciders**: Jun Kawasaki

# Context

The founder asked etzhayyim to **actively solicit sponsors / donations** (「etzhayyim でも
sponsor, donation を募集して」), prompted by reviewing how a comparable project is funded
(`666ghj/MiroFish` — backed by corporate incubation + user-borne paid SaaS, the *opposite* of
etzhayyim's donation-only model).

**Pre-state (verified):** etzhayyim already has the *declaration* layer — the apex Cloudflare
Worker serves a live `GET /donate` page and `GET /.well-known/donation.json` machine policy
(ADR-2606012100), the `@etzhayyim/sdk` `donate()` surface exists, and the `TitheRouter` /
`PublicFundGovernance` contracts are written + tested. **What was missing was the public
*solicitation* layer**: there is **no `.github/FUNDING.yml`** (so the repo shows no "Sponsor"
button), **no root `DONATE.md`**, and **no support section in `README.md`**. The declaration is
passive; nothing invites a visitor to give.

Two hard constraints shape any solution:

1. **Fiat donation rails are constitutionally prohibited.** GitHub Sponsors (Stripe-backed),
   Patreon, Open Collective, Ko-fi, Liberapay all route money through fiat processors
   (Stripe/PayPal/Square …), which `deps.toml` `payment_prohibited` + ADR-2605172100 forbid.
   etzhayyim accepts value **only** as USDC on Base L2 (via `TitheRouter`, 90/10 tithe split) or
   as in-kind compute (Murakumo mesh).
2. **No live on-chain donation address exists yet.** The `TitheRouter` / Public-Fund-Safe
   addresses are undeployed (Base L2 testnet pending Bootstrap-Council ratification; Seats 2–5
   RFP closes 2026-06-19). Any solicitation **must not fabricate an address**.

And one doctrinal constraint: **a donation must earn the donor nothing** — no perks, tiers,
priority, governance weight, or recognition leaderboard (anti-class invariant, ADR-2606012100
§G4). So the solicitation cannot use the usual "sponsor tier" pattern.

# Decision

Add the **public solicitation surfaces**, all additive, all charter-clean:

## 1. GitHub Sponsor button — `.github/FUNDING.yml` (custom-only)

Create `.github/FUNDING.yml` using **only the `custom:` field**, pointing at
`https://etzhayyim.com/donate` and `…/.well-known/donation.json`. **Every fiat platform key
(`github`, `patreon`, `open_collective`, `ko_fi`, `liberapay`, `tidelift`) is left blank, with a
comment naming why** (fiat processors prohibited). This gives the repo a real "Sponsor" button
that routes to the on-chain donation surface instead of a fiat rail.

## 2. Root `DONATE.md` — the how-to-give / 募集 document

A public solicitation doc: the donation-only model, the two media (USDC cash via `TitheRouter`
90/10; in-kind compute ameno/e7m/kotoba), the benefit-free rule stated up front, the
why-no-GitHub-Sponsors rationale, and an **honest "address pending" notice** that names the live
`donation.json` as the single source of truth for the address when it lands (no address printed
in `DONATE.md` — one place only, so it can never drift).

## 3. `README.md` support section + active `/donate` CTA

A short **Support etzhayyim — 寄付 / sponsor** section in `README.md` (links to `DONATE.md`,
`/donate`, `donation.json`, FUNDING.yml). The apex Worker's `donation.json` gains a
`solicitation` block (`open: true`, `callToAction`, `grantsBenefit: false`, `tiers: "none"`,
`leaderboard: "none"`, sponsor-button + address-status notes) and the `/donate` HTML gains a
benefit-free **"Sponsor on GitHub"** card + an explicit "a gift earns you nothing" line. The page
stays cookie-free, script-free, tracker-free.

## Charter-clean by construction

- **No fiat rail** (FUNDING custom-only → on-chain `/donate`; ADR-2605172100).
- **Benefit-free** — no tiers, no leaderboard, no quid-pro-quo (G4). Soliciting for etzhayyim's
  own religious activity is **案内, not advertising** (ADR-2605192115 §1.2).
- **No fabricated address** — the live `donation.json` remains the single SoT; surfaces say
  "pending" until Council + testnet.
- **10% tithe unchanged** — every cash `donation` still auto-splits 90/10 at `TitheRouter`.
- **No invariant amendment** — purely additive public-proof + solicitation copy.

# Consequences

- **Positive:** etzhayyim now *invites* support, not merely declares a policy — a Sponsor button
  on the repo, a clear how-to-give doc, a README ask, and an active (still honest, still
  benefit-free) call-to-action on the live page. The custom-only FUNDING.yml is a reusable
  pattern: any future etzhayyim repo gets a charter-clean Sponsor button by copying it.
- **Costs / risks:** (1) GitHub renders the `custom` Sponsor button but a user expecting fiat
  "Sponsor" may be briefly surprised to land on an on-chain page — mitigated by the page's plain
  explanation. (2) Until the address is live, money-giving is "pending" — the compute-donation
  path (ameno/e7m/kotoba) is the immediately-actionable ask, and the address gap closes when the
  Council ratifies + testnet deploys (tracked, ADR-2606012100). (3) Solicitation must never drift
  into perks/tiers — encoded structurally (`grantsBenefit:false`, `tiers:"none"` in the policy)
  and called out in `DONATE.md` + FUNDING.yml comments.

# Alternatives Considered

- **Enable GitHub Sponsors / Patreon / Open Collective.** Rejected: fiat processors are
  constitutionally prohibited (ADR-2605172100 / 2605192115). The whole point of the on-chain
  substrate is to route around them.
- **Sponsor tiers with perks / a donor wall.** Rejected: a quid-pro-quo violates the anti-class
  gift invariant (G4) and a per-donor leaderboard forms exactly the class the charter forbids.
- **Print a donation address now to look "live".** Rejected: no address is deployed; fabricating
  one would be dishonest and dangerous (funds to a wrong/again-changing address). The live
  `donation.json` is the single SoT and says "pending" truthfully.
- **Do nothing (the /donate page already exists).** Rejected: that is the *declaration*, not the
  *solicitation* the founder asked for; a repo with no Sponsor button and no README ask does not
  invite support.

# References

- ADR-2606012100 (donation-funded operation + compute-node donation — the live `/donate` + `donation.json` this builds on)
- ADR-2605192115 (non-profit / donation-only / no-ads — §1.2 案内 ≠ advertising) · ADR-2605192130 (10% tithe → Public Fund)
- ADR-2605172100 (payments on-chain only; Stripe/PayPal/fiat processors prohibited)
- ADR-2605192100 (Mission Charter — non_profit_only / donation_only constants) · ADR-2605215000 (Murakumo-only inference) · ADR-2605262900 (toritate — aggregate-only imputed accounting, no per-donor leaderboard)
- `.github/FUNDING.yml` · `DONATE.md` · `README.md` (Support section) · `50-infra/etzhayyim-did-web/src/worker.ts` (`DONATION_POLICY.solicitation` + `/donate` CTA)
- contrast: `github.com/666ghj/MiroFish` (corporate-incubation + user-borne paid Zep Cloud / LLM API — the funding model etzhayyim inverts)
