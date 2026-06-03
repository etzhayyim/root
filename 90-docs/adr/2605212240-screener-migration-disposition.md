---
id: adr-2605212240-screener-migration-disposition
title: "ADR-2605212240: screener app migration disposition (etzhayyim → etzhayyim)"
status: proposed
doc_type: adr
topic: screener-migration
authoritative: true
last_verified: 2026-05-21
priority: 3.0
axis: governance
weight: 0.30
priority_note: "P5_DEFER resolution for etzhayyim-project-screener"
authoritative_for:
  - migration-disposition-screener
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related: []
supersedes: []
superseded_by: []
---

# ADR-2605212240: screener app migration disposition (etzhayyim → etzhayyim)

**Status**: proposed
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

# Context

`etzhayyim-project-screener` (65 files, Next.js + v0.dev scaffold) was flagged as
DEFER during the 2026-05-21 P5_REVIEW pass because the bare name "screener"
admits two readings under Charter Rider v2.0 §2:

1. **Financial screener** — equity / commodities / token screening that
   facilitates speculative finance (§2(b) risk: price arbitrage signal generation).
2. **Sanctions screener** — KYC / AML / OFAC-list screening that supports
   compliance and humanitarian (e.g. crypto-asset-freeze) workflows.

Inspection of the source repository (`etzhayyim-root/60-apps/etzhayyim-project-screener/README.md`
and PROJECT.jsonld) confirms reading (2):

> "Sanctions screening service" — deployed as `v0-sanctions-screening-service`
> on Vercel under the etzhayyim org.

Sibling apps `etzhayyim-project-sanctions` and `etzhayyim-project-crypto-asset-freeze`
have already been migrated under the P3_SUBSTRATE batch (see migration log
2026-05-21) as Charter-aligned compliance tooling.

# Decision

**Reclassify `etzhayyim-project-screener` from DEFER to ALIGN.** Migrate to
`etzhayyim-root/60-apps/etzhayyim-project-screener/` using the standard
`rsync + NOTICE` flow established for the P5_ALIGN batch.

Constraints carried forward:

- The migrated app MUST NOT add §2(b) speculative-finance features. If the
  Vercel-deployed scope later expands beyond sanctions/KYC screening, a new
  ADR is required.
- The v0.dev / Vercel deployment pipeline is **out of scope** for the
  etzhayyim substrate. The migrated copy is a code-archive seed only; any
  re-deployment must use etzhayyim's CF Workers + did:web identity flow.

# Consequences

- Migrated app count increments from 184 → 185.
- DEFER count decrements from 2 → 1 (only `shinshi` remains).
- No new substrate-boundary violation introduced (Next.js + Tailwind only;
  no Stripe / RisingWave / @atproto/api direct imports detected at scan).

# Alternatives Considered

1. **Keep as DEFER.** Rejected: scope is unambiguous after README review.
2. **EXCLUDE as §2(b) speculative finance.** Rejected: README explicitly
   identifies sanctions screening, which is the opposite of speculation.
3. **TRANSFORM with codemod.** Rejected: no codemod target detected
   (no Stripe / RW / ad-pixel imports in scan).

# References

- ADR-2605192100 (Charter §2(b) speculative finance definition)
- ADR-2605192200 (Charter Rider v2.0)
- `_working_p5_decisions.md` (P5_REVIEW 255 アプリ 個別移行判断)
- Source: `etzhayyim-root/60-apps/etzhayyim-project-screener/README.md`
