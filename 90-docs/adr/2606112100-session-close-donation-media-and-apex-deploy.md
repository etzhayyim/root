---
id: adr-2606112100-session-close-donation-media-and-apex-deploy
title: "ADR-2606112100: Session close (2026-06-11) — donation solicitation + media expansion (fiat/asset) shipped & apex Worker deployed live"
status: accepted
doc_type: adr
topic: session-close-donation-media-and-apex-deploy
authoritative: false
last_verified: 2026-06-11
priority: 4.0
axis: governance
weight: 0.4
priority_note: "Session-close index for the 2026-06-11 donation arc: public solicitation surfaces (ADR-2606111700) + donation-media expansion fiat/asset (ADR-2606111800, incl. a Tier-1 amendment) merged to main and DEPLOYED LIVE on the apex Worker (version 04654d55, verified). Also records the same session's hakoniwa 箱庭 actor (ADR-2606111400/2606111500) landing. Non-authoritative narrative; the per-topic ADRs remain authoritative."
authoritative_for: []
depends_on:
  - 2606111700
  - 2606111800
  - 2606111400
  - 2606111500
related:
  - 2606012100
  - 2605172100
  - 2606014600
  - 2605231525
supersedes: []
superseded_by: []
---

# ADR-2606112100: Session close (2026-06-11) — donation media shipped + apex deployed

**Status**: accepted (session-close narrative; non-authoritative)
**Date**: 2026-06-11
**Deciders**: Jun Kawasaki

# Context

Closing record for the 2026-06-11 session. It began from a question about `666ghj/MiroFish`
(how it is built + funded) and ended with etzhayyim's donation surfaces expanded and **deployed
live**. The per-topic ADRs are authoritative; this is the index + the deploy receipt.

# What landed (all merged to `main`)

## Donation arc (the session's tail — the "募集 / fiat や asset / deploy" thread)

1. **Public solicitation surfaces — ADR-2606111700** (PR #1608). The repo gained a *solicitation*
   layer on top of the live *declaration*: `.github/FUNDING.yml` (a Sponsor button using
   `custom:`-only URLs → the on-chain `/donate`, **no fiat rails**), root `DONATE.md`, a README
   "Support" section, and a benefit-free `/donate` CTA + `DONATION_POLICY.solicitation` block.
   Zero invariant amendments; benefit-free (anti-class G4); no fabricated address.
2. **Donation-media expansion — ADR-2606111800** (PR #1609). Three media, one amendment:
   **§A fiat IN-KIND** (paying the mission's fiat infra bills direct to the vendor — the founder's
   actual ongoing JPY server-cost donation — recognized via
   `com.etzhayyim.give.infrastructureDonationAttestation`; no amendment); **§B** a **Tier-1
   amendment** of ADR-2605172100 permitting fiat inflow **only** as a non-custodial,
   immediately-USDC-settling, donor-PII-free, donation-purpose on-ramp (priority-conformance
   attestation passes; **custodial fiat stays prohibited**, honestly); **§C** a curated crypto
   allowlist (ETH/WETH + USDC/USDT/DAI) held as-is, per-asset tithe. Donation-purpose enum + 10%
   tithe + non-profit/ad-free/no-server-key unchanged.
3. **Apex deploy (this close).** ADR-2606111700 + 2606111800 surfaces **deployed live** on the
   `etzhayyim-did-web` Worker (version `04654d55`), verified: `donation.json` →
   `media: [cash, crypto, fiat, fiat-in-kind, compute]` + `solicitation.open: true`; `/donate`
   shows the new cards. A GitHub-Pages migration was considered and **rejected** (Pages cannot do
   the trustless `/ipfs/<cid>` gateway (ADR-2606014600), the XRPC/app proxy, or dynamic
   KV/DID endpoints; the apex domain resolves did:web from one host only). The Worker is retained
   as canonical apex; no server-held key introduced (ADR-2605231525).

## hakoniwa arc (the session's head — the MiroFish answer)

4. **hakoniwa 箱庭 — ADR-2606111400 (charter carve-in) + ADR-2606111500 (actor)** (PR #1601).
   The charter-clean inversion of a MiroFish-class swarm-prediction engine: a contained box of
   **fictional latent personas** producing a **distribution** (never a point), feeding mitooshi.
   Authorized by a charter consolidation onto two axes (reciprocity + subject-reality):
   *simulating fictional agents ≠ surveilling real people*. Reached **R1** in-session — autonomous
   heartbeat → kotoba Datom log, founder-signed social emission, **real Wikidata public-entity
   ingest** (persons P31=Q5 dropped at ingest, G1), and the **live LLM-persona swarm** (Murakumo,
   kernel fallback). 30 network-free tests green.

# Consequences

- **Live outcome:** etzhayyim now *invites* support across five media (USDC, curated crypto,
  non-custodial fiat on-ramp, fiat in-kind, compute) on a deployed apex — and the founder's
  existing JPY infrastructure spend is, for the first time, a recordable in-kind donation.
- **Honest boundaries preserved:** custodial fiat remains prohibited (failed conformance); the
  on-chain donate address is still pending Council + Base L2 testnet (published only in the live
  `donation.json` when ready, Seats 2–5 RFP closes 2026-06-19); the non-custodial on-ramp + the
  per-asset TitheRouter wiring follow that address going live.
- **Worktrees:** all session branches merged + cleaned; only sibling-agent worktrees remain.

# Open / next (all gated or follow-up)

- On-chain TitheRouter / Public-Fund-Safe deploy (Council + Base L2 testnet) → publishes the
  donate address; then wire the non-custodial fiat on-ramp + per-asset tithe.
- hakoniwa: scope-expansion of the bounded Wikidata ingest + external AT-Proto firehose relay
  (operator transport) stay Council/operator-gated.

# References

- ADR-2606111700 (solicitation surfaces) · ADR-2606111800 (donation-media expansion + deploy addendum)
- ADR-2606111400 (charter synthetic-persona carve-in) · ADR-2606111500 (hakoniwa actor)
- ADR-2606012100 (donation-funded operation) · ADR-2605172100 (payments on-chain only — §B narrows it) · ADR-2606014600 (trustless IPFS gateway — why Pages can't replace the Worker) · ADR-2605231525 (no-server-key)
