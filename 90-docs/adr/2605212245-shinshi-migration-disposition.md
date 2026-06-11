---
id: adr-2605212245-shinshi-migration-disposition
title: "ADR-2605212245: shinshi app migration disposition (etzhayyim → etzhayyim)"
status: proposed
doc_type: adr
topic: shinshi-migration
authoritative: true
last_verified: 2026-05-21
priority: 4.0
axis: governance
weight: 0.50
priority_note: "P5_DEFER resolution for etzhayyim-project-shinshi"
authoritative_for:
  - migration-disposition-shinshi
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192400-etzhayyim-eros-gore-council-judging
related: []
supersedes: []
superseded_by: []
---

# ADR-2605212245: shinshi app migration disposition (etzhayyim → etzhayyim)

**Status**: proposed
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

# Context

`etzhayyim-project-shinshi` (137 files) is the etzhayyim NSFW content platform
(`shinshi.etzhayyim.com`) implementing wRPC stream-native reactive pipeline with
path-based DID identity, age-gated (18+), 247 models × 5 scenes = 1,235 images,
self-labeled `nsfw` / `nudity` / `sexual`.

Charter Rider v2.0 has two competing pulls on this app:

**Pro-migration pulls**:

- ADR-2605192100 §1.13 + ADR-2605192400 establish **Eros 許容** (産霊 / 雅歌 /
  Tree of Life の生命創出). 合意ある成人性表現 is constitutionally protected.
- Path-based DID + age verification + content self-labeling are exactly the
  substrate-aligned controls etzhayyim expects.

**Anti-migration pulls**:

- The repo contains `260228-ad-strategy-trafficstars-exoclick.md` — an
  explicit ad-monetization strategy targeting ExoClick / TrafficStars
  ad networks. This is a direct §2(c) SURVEILLANCE CAPITALISM violation
  (ad-tech DSP/SSP integration) and a direct §2(h) WELLBECOMING
  SUBORDINATION violation (engagement-optimized addictive design pattern
  characteristic of NSFW-tube monetization).
- The substrate boundary table prohibits "第三者広告 / AdSense / Meta Pixel /
  アフィリエイト / GA4 広告連携". ExoClick/TrafficStars are precisely the
  prohibited category.
- etzhayyim-project-pornhub (already in P0_EXCLUDE) and etzhayyim-project-exoclick
  (also P0_EXCLUDE) are the sibling apps in the etzhayyim ad-tech NSFW funnel.
  Migrating shinshi without removing its monetization layer would re-introduce
  the prohibited revenue model that P0 already rejected.

The Charter does not prohibit consensual adult content per se; it prohibits
**the ad-supported revenue model + addictive engagement design** that is the
de-facto operating mode of `shinshi.etzhayyim.com`.

# Decision

**Reclassify `etzhayyim-project-shinshi` from DEFER to EXCLUDE.** Do not migrate
to `etzhayyim-root/60-apps/`.

Rationale: the constitutional violation is in the **revenue model and
engagement design**, not in the Eros content itself. Migrating the codebase
without those layers would require removing >50% of the implementation
(the monetization + recommendation + retention loops are the load-bearing
architecture), at which point a clean-room rewrite under etzhayyim is more
appropriate than a code-port.

If etzhayyim later commissions an Eros-permitted content platform
(consistent with ADR-2605192400 §1.13), it MUST be designed natively as:

- Donation-only revenue (no ad networks; no engagement-optimized recommendations)
- SBT-gated access (Adherent SBT + age proof, no anonymous monetized eyeballs)
- did:web:etzhayyim.com identity (no third-party DID broker)
- Wellbecoming-aligned consumption metrics (session-length caps, no
  infinite-scroll, no streak/loyalty addictive patterns)

That future app would be a NEW design under a NEW ADR, not a port of shinshi.

# Consequences

- DEFER count decrements from 2 → 0.
- EXCLUDE count increments from 30 → 31.
- The future Eros-permitted platform (if commissioned) gets a clean-slate
  ADR rather than inheriting shinshi's compromised architecture.
- etzhayyim-side `shinshi.etzhayyim.com` deployment continues to operate under etzhayyim
  governance (out of etzhayyim's jurisdiction).

# Alternatives Considered

1. **ALIGN as-is.** Rejected: directly violates §2(c) + §2(h).
2. **TRANSFORM with monetization layer removed.** Rejected: removing the
   monetization + recommendation engine eliminates >50% of the codebase;
   a clean-room rewrite is cheaper and avoids inheriting addictive-design
   data models in the MST schema.
3. **Keep as DEFER pending architectural review.** Rejected: the §2(c)
   violation is unambiguous from the ad-strategy file present in the repo;
   further deferral is not productive.

# References

- ADR-2605192100 §1.13 (Eros 許容 constitutional invariant)
- ADR-2605192200 (Charter Rider v2.0 §2(c) + §2(h))
- ADR-2605192400 (Eros allowed / Gore prohibited)
- Source: `etzhayyim-root/60-apps/etzhayyim-project-shinshi/260228-ad-strategy-trafficstars-exoclick.md`
- Source: `etzhayyim-root/60-apps/etzhayyim-project-shinshi/CLAUDE.md`
- Sibling P0_EXCLUDE: etzhayyim-project-pornhub, etzhayyim-project-exoclick
