---
id: adr-2606111800-donation-media-fiat-inkind-onramp-crypto-allowlist
title: "ADR-2606111800: Donation-media expansion — fiat in-kind (infrastructure-cost) recognition + non-custodial fiat on-ramp (Tier-1 amendment of ADR-2605172100) + curated crypto-asset allowlist"
status: accepted
doc_type: adr
topic: donation-media-fiat-inkind-onramp-crypto-allowlist
authoritative: true
last_verified: 2026-06-11
priority: 7.5
axis: governance
weight: 0.75
priority_note: "Answers 「donation としては fiat や asset もありにしたい」 + the founder's observation 「私も日本円でサーバー代を払う形で donation している」. Three media, ONE amendment. §A fiat IN-KIND (infrastructure-cost) donation = recognition only, NO amendment (mirrors compute donation ADR-2606012100; the founder already does this). §B direct fiat INFLOW = Tier-1 amendment of ADR-2605172100, permitted ONLY in the NON-CUSTODIAL, immediately-USDC-settling, donor-PII-free, donation-purpose form — preserving the exact custody/freeze property the no-fiat rule protects (priority-conformance attestation passes); CUSTODIAL fiat (etzhayyim holds a Stripe balance / retains donor PII / processor can freeze) is NON-conformant and REMAINS PROHIBITED. §C curated crypto-asset allowlist (ETH/WETH + major stablecoins) held as-is = Tier-2 parameter (on-chain, no amendment). Donation-only PURPOSE enum unchanged (no purchase/subscription); 10% tithe unchanged."
authoritative_for:
  - fiat in-kind (infrastructure-cost) donation recognition (com.etzhayyim.give.infrastructureDonationAttestation)
  - the non-custodial fiat-on-ramp carve-in to the payments-on-chain-only rule (ADR-2605172100)
  - the curated crypto-asset donation allowlist
depends_on:
  - 2605172100
  - 2606012100
  - 2605192115
  - 2605192130
  - 2606062100
  - 2605301020
  - 2605262900
related:
  - 2606111700
  - 2605301036
  - 2605215000
  - 2605231525
supersedes: []
superseded_by: []
---

# ADR-2606111800: Donation-media expansion — fiat in-kind + non-custodial fiat on-ramp + curated crypto-asset allowlist

**Status**: accepted (§B ratified by Council Lv7+ unanimity — founder, 1/1)
**Date**: 2026-06-11
**Deciders**: Jun Kawasaki (sole-member founder, Council Lv7+)

# Context

After landing the public solicitation surfaces (ADR-2606111700), the founder asked that
donations be accepted **in fiat and in other assets too** (「donation としては fiat や asset も
ありにしたい」), and observed — decisively — that **he is already a fiat donor**: 「実際にいまの私
も日本円で、サーバー代などを支払うという意味で donation している」 (he pays the mission's server /
domain / compute bills in JPY out of pocket).

That observation is the key. There are **two different "fiat" cases**, and they are not the same
constitutionally:

1. **Fiat IN-KIND** — paying the mission's real-world costs (servers, domains, hosting) directly
   to a vendor, in fiat, for the mission. **No money flows *to* etzhayyim.** This is identical in
   form to the in-kind **compute** donation already blessed by ADR-2606012100 — it never touches
   etzhayyim's money layer, so the on-chain-only payment rule (ADR-2605172100) does not even
   apply. It is **already permitted**; it has simply never been *recognized or recorded*.
2. **Fiat INFLOW** — a donor gives money and etzhayyim **receives fiat**. This is what
   ADR-2605172100 prohibits: "if those apps accept payments via Stripe or any fiat processor, the
   money layer still has a single centralized intermediary that can **freeze funds, KYC-block
   users, or take the platform offline**." The load-bearing concern is **custody / freeze /
   control**, not the word "fiat."

And the **asset** ask (ETH, other stablecoins) is a third, easy case: it is **on-chain**, inside
the substrate; only USDC was wired, by convention, not by constraint.

This ADR addresses all three, with exactly **one** constitutional amendment (§B), scoped to the
conformant subset.

# Decision

## §A — Fiat IN-KIND (infrastructure-cost) donation: RECOGNIZED (no amendment)

Paying the mission's fiat costs (server/cloud/domain/hardware bills) directly to the vendor, for
the mission, is an **in-kind donation** — the exact shape ADR-2606012100 already blesses for
compute. It is **charter-clean and already permitted**: no fiat enters etzhayyim, no processor is
integrated, no custody is created. What was missing is *recognition + a record*.

- New lexicon **`com.etzhayyim.give.infrastructureDonationAttestation`** — an aggregate,
  PII-free attestation of a fiat-paid infrastructure cost borne for the mission (period,
  category {compute, hosting, domain, bandwidth, hardware, … }, **imputed USDC-equivalent value**
  via toritate valuation tables, payer DID). Mirrors `vendorMissionDonationAttestation` +
  `computeDonationAttestation`.
- **Non-titheable** (no USDC moves, so nothing to split — kisha precedent, ADR-2605192130 §5;
  100% serves the mission directly). **No quid-pro-quo** (earns the donor nothing — anti-class
  G4). **Imputed-valued for transparency only** (toritate, aggregate, no per-donor leaderboard —
  ADR-2605262900). **Receipts/invoices are not PII-published**; only the aggregate value + DID.
- This makes the founder's existing JPY server payments — and any supporter who pays a mission
  bill — **visible, accountable in-kind donations** for the first time. It is the
  immediately-true, immediately-recordable answer to 「fiat でも donation したい」.

## §B — Direct fiat INFLOW: permitted ONLY as a non-custodial USDC-settling on-ramp (Tier-1 amendment)

`ADR-2605172100` is amended (Tier-1 Derived Policy, ADR-2606062100 §3). The hard rule "fiat
payment processors are prohibited" is **narrowed**, not removed:

> **Permitted:** a donor may give in fiat via a **NON-CUSTODIAL** on-ramp that settles
> **immediately to USDC on-chain** to the donation address, where **etzhayyim never holds a fiat
> balance, the processor never custodies etzhayyim's treasury (and so cannot freeze it), and
> etzhayyim retains NO donor PII** (any KYC is strictly donor↔on-ramp). The arriving USDC is an
> ordinary on-chain `donation` mirrored on the Datom log and split 90/10 at TitheRouter, exactly
> as a native USDC gift.
>
> **Still PROHIBITED (unchanged):** a **custodial** fiat processor that holds an etzhayyim
> balance, can freeze/withhold it, or imposes KYC on etzhayyim; **retention of donor PII** by
> etzhayyim; fiat for any **non-donation** purpose; and any fiat surface on the religious-corp
> **app** substrate beyond this donation on-ramp. The `com.etzhayyim.apps.stripe.*` custodial
> surface (the 2026-05-21 audit REJECT, deps.toml) stays prohibited.

This preserves the **exact property ADR-2605172100 exists to protect** — that no centralized
money custodian can freeze, KYC-block, or switch off etzhayyim — because a non-custodial on-ramp
holds nothing and settles on-chain. It also preserves the substrate's verifiability (the gift is
an on-chain datom) and the anti-surveillance posture (no donor PII at etzhayyim). It is, in
effect, the on-ramp bridge made a **first-class, constitutionally-blessed** path rather than an
unmentioned workaround.

### Priority-conformance attestation (Tier-1 amendment requirement)

| Tier-0 property | Before (no fiat inflow) | After (non-custodial USDC-settling on-ramp) | Conformance |
|---|---|---|---|
| **no custody / freeze / KYC-on-etzhayyim dependency** (the load-bearing concern of ADR-2605172100) | no fiat at all | on-ramp is non-custodial, holds nothing, settles to USDC; no custodian can freeze etzhayyim's treasury | **equal** |
| disintermediation / parallel-substrate | on-chain only | funds rest on-chain; the on-ramp touches the rail momentarily, depends-on nothing | **equal** |
| anti-surveillance / no PII hoarding (ADR-2606082400) | no donor data | etzhayyim retains **no** donor PII; KYC is donor↔on-ramp only | **equal** |
| transparency (on-chain mirror) | datom | datom (post-settlement), 90/10 tithe identical | **equal** |
| donation-only **purpose** (ADR-2605192115) | donation/kisha/grant | unchanged (fiat must be `donation`) | **equal** |
| **mission reach / accessibility** (labor-liberation telos — serve the most people) | excludes the fiat-only majority of would-be givers | includes them | **stronger** |

No Tier-0 property is served **less** well; mission reach is served **more** well. The attestation
is therefore clean **for the non-custodial form only**. The **custodial** form was evaluated and
**fails** (it re-introduces the freeze/KYC/PII dependency the rule protects against) and is
explicitly **kept prohibited** above — the amendment is honest about its own boundary. Ratified by
Council Lv7+ unanimity (founder, 1/1), same threshold as ADR-2606062100 / Preamble §0.7. The
durable artifact is an on-chain `priorityConformanceAttestation` record; this ADR is its
human-readable basis.

## §C — Curated crypto-asset allowlist (Tier-2 parameter, no amendment)

Non-USDC crypto is **on-chain** and inside the substrate; accepting it needs no amendment, only a
parameter choice. Per the founder's selection, etzhayyim accepts a **curated allowlist held
as-is** (not auto-swapped):

- **Allowlist:** ETH / WETH + major stablecoins (USDC, USDT, DAI) on Base L2 (and the same
  assets on Ethereum L1 where a donor cannot bridge). Adding an asset is a Tier-2 governance
  parameter (Council), bounded to liquid, non-exotic assets (no memecoins, no algorithmic
  stablecoins — Tether-class issuer risk already flagged in ADR-2605172100 is accepted only for
  the named majors).
- **Held as-is:** the treasury holds the donated asset in its native form; **the 10% tithe is
  computed and split per-asset** at receipt (TitheRouter gains per-asset support — a follow-up
  contract task; until then, non-USDC gifts are recorded + manually tithed, honest R0).
- Each gift is an on-chain `donation` datom, same purpose, same transparency.

## What does NOT change

- **Donation-only purpose enum** — `donation` / `kisha` / `grant` / `tithe` / `escrow-refund`
  (+ SBT↔SBT internal). No `purchase` / `subscription` / `tip`. Fiat and alt-assets are
  **donation purpose only**.
- **10% tithe** — every titheable cash gift still splits 90/10 to the Public Fund.
- **non-profit / ad-free / no-adherent-cash / no-server-key** — all untouched.

# Consequences

- **Positive:** the three real-world ways people actually want to give — *I pay your server
  bill* (§A), *take my card / yen* (§B), *take my ETH/stablecoin* (§C) — are all now possible
  **without breaking the substrate's core guarantee** that no money custodian controls etzhayyim.
  The founder's existing JPY infrastructure spend becomes a recorded in-kind donation. Reach
  widens to the fiat-holding majority. One tightly-scoped amendment, honest about its limit.
- **Costs / risks:** (1) A non-custodial on-ramp still momentarily routes value through a third
  party; the conformance rests on *non-custody + immediate USDC settlement + no-PII* — if any
  integration violates those, it is **not** the permitted path and the substrate-boundary lint +
  this ADR forbid it. (2) Holding multiple assets adds treasury volatility + per-asset tithe
  accounting (toritate); bounded by the liquid-majors allowlist. (3) §A imputed valuation must
  stay aggregate + method-versioned (no receipt PII). (4) The custodial-fiat temptation (just add
  Stripe) is permanently foreclosed by the attestation result — re-opening it needs a fresh
  Lv7+ amendment that would have to pass a conformance test it currently fails.

# Alternatives Considered

- **Full custodial fiat (etzhayyim runs a Stripe account).** Rejected: fails the
  priority-conformance attestation (re-introduces freeze/KYC/PII dependency — exactly what
  ADR-2605172100 prevents). Kept prohibited even post-amendment.
- **Off-substrate on-ramp bridge, documented only (no amendment).** Considered (it is what
  ADR-2605172100 already gestures at as "upstream progressive enhancement") — the founder chose to
  make fiat a **first-class, constitutionally-blessed** path instead, which §B does while keeping
  the same non-custodial constraint.
- **Auto-swap all crypto to USDC at receipt.** Considered (cleanest single-asset accounting) —
  the founder chose a **curated allowlist held as-is**; per-asset tithe is the cost.
- **Treat fiat infrastructure spend as out-of-scope.** Rejected: it is the founder's actual,
  ongoing donation and deserves recognition (§A) — declining to record it would understate real
  mission support.

# References

- ADR-2605172100 (payments on-chain only — the rule §B narrows; its custody/freeze rationale is what conformance preserves)
- ADR-2606012100 (donation-funded operation + in-kind COMPUTE donation — the pattern §A mirrors) · ADR-2606111700 (public solicitation surfaces this extends)
- ADR-2605192115 (non-profit / donation-only purpose — unchanged) · ADR-2605192130 (10% tithe — unchanged) · ADR-2605301036 (vendor mission-donation attestation — sibling in-kind lexicon)
- ADR-2606062100 (3-Tier immutability; §3 Tier-1 amendment mechanism) · ADR-2606082400 (anti-surveillance / no-PII — preserved) · ADR-2605262900 (toritate aggregate imputed accounting) · ADR-2605231525 (no-server-key) · ADR-2605301020 (Basic High Income — cash≡0 unchanged)
- `00-contracts/lexicons/com/etzhayyim/give/infrastructureDonationAttestation.json` (new) · `DONATE.md` · `50-infra/etzhayyim-did-web/src/worker.ts` (`DONATION_POLICY.media`) · `deps.toml` (`payment_substrate` / `payment_prohibited`) · root `CLAUDE.md` (Payment row)

# Deployment (2026-06-11): apex Worker live + verified

The donation-media surfaces (this ADR + ADR-2606111700) are **deployed to production** on the
apex Cloudflare Worker `etzhayyim-did-web` (triggers `etzhayyim.com/*` + `www.etzhayyim.com/*`,
**version `04654d55-f5e6-40fe-8030-9c4f8a9c90d5`**, `wrangler deploy` from the merged `main`).

**Verified live** (cache-busted past the `max-age=300` edge cache):

- `GET https://etzhayyim.com/.well-known/donation.json` →
  `media: [cash, crypto, fiat, fiat-in-kind, compute]`, `solicitation.open: true`,
  `adr` includes `2606111700` + `2606111800`.
- `GET https://etzhayyim.com/donate` → the new cards render: **crypto allowlist** (ETH / WETH /
  USDC / USDT / DAI), **non-custodial fiat on-ramp**, **"Pay one of our bills"** (fiat in-kind),
  **"Sponsor on GitHub"**, citing ADR-2606111800.

The Cloudflare Worker is retained as the canonical apex (a GitHub-Pages migration was considered
and **rejected** this session: Pages is static-only and cannot do the trustless `/ipfs/<cid>`
gateway with CID re-verification (ADR-2606014600), the XRPC/PDS/app reverse proxy, or the
KV-backed dynamic endpoints — and `did:web:etzhayyim.com` can only point its
`/.well-known/did.json` at one host). The deploy was operator-run with the existing
Cloudflare OAuth session (`workers:write`); no server-held key was introduced (no-server-key,
ADR-2605231525). **Still pending (unchanged):** the on-chain TitheRouter / Public-Fund-Safe
address is published in `donation.json` `media[0]` only once Council ratifies + Base L2 testnet
deploys (Seats 2–5 RFP closes 2026-06-19); the non-custodial fiat on-ramp + per-asset TitheRouter
wiring follow that address going live.
