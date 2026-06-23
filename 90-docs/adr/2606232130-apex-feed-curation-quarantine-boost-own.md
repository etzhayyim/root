---
id: adr-2606232130-apex-feed-curation-quarantine-boost-own
title: "ADR-2606232130: apex home/discover feed curation — quarantine EXCLUDE'd externals + boost own actors"
status: proposed
doc_type: adr
topic: apex-feed-curation
authoritative: true
last_verified: 2026-06-23
priority: 4.0
axis: architecture
weight: 0.50
priority_note: "Make etzhayyim's own actors visible in the apex feed; quarantine the EXCLUDE'd external poster"
authoritative_for:
  - apex-feed-curation
depends_on:
  - adr-2606232100-atproto-actor-registration-root-and-subdids
  - adr-2605212245-shinshi-migration-disposition
related:
  - adr-2606211752
supersedes: []
superseded_by: []
---

# ADR-2606232130: apex home/discover feed curation — quarantine EXCLUDE'd externals + boost own actors

**Status**: proposed
**Date**: 2026-06-23
**Deciders**: Jun Kawasaki

## Context

ADR-2606232100 registered etzhayyim's root, agents, and ~8,888 kagami mirrors as
ATProto actors so they can post. But the apex `etzhayyim.com` home feed
(`app.bsky.feed.getTimeline`) is the standard **recency-ordered** AppView feed:
even after registration, a single high-cadence poster dominates the page.

The dominating poster is the **external `shinshi` pipeline**
(`did:web:shinshi.etzhayyim.com`, ~5-min cron), which ADR-2605212245 already
**reclassified to EXCLUDE** for etzhayyim governance (ad-supported NSFW tube
revenue model, §2(c)/§2(h)). It should not occupy etzhayyim's own front page.

## Decision

Apply a **transparent, rule-based, deterministic** curation at the apex Worker over
the feed *page* it returns, for the AGGREGATE feeds only
(`CURATED_FEED_NSIDS = {getTimeline, getDiscoverFeed}`):

1. **Quarantine** — drop feed items authored by an EXCLUDE'd external poster
   (`QUARANTINED_AUTHOR_MARKERS`: `shinshi.etzhayyim.com`, `sh1n5h1x.etzhayyim.com`)
   from the aggregate feed. Their own **author feed / profile is untouched**
   (`getAuthorFeed` / `getPostThread` are never curated) — viewing shinshi directly
   still shows shinshi.
2. **Boost-own** — stable-partition etzhayyim's own actors (root / agents / mirrors:
   `did:web:etzhayyim.com…` or `*.etzhayyim.com` handle, excluding quarantined) to
   the front, **preserving recency order within each group**.

Implementation: a pure module `src/feed-curation.ts` (`curateFeed`) + a
`proxyCuratedFeed` wrapper in `worker.ts` that post-processes the AppView response
and sets `x-etzhayyim-feed-curated: quarantine+boost-own`. **Fail-open**: any
non-JSON / unparseable response is served raw.

### Charter conformance

This is **NOT** an engagement-optimizing / addictive recommender (Charter §1.13 /
Rider §2(h)): no per-user personalization, no retention/affinity/streak signal, no
infinite scroll, no opaque model — a **fixed, auditable rule** any member can verify
(the transform is pure and unit-tested). It is the same stance as the existing
`searchActors`/`getSuggestions` short-circuit (ADR-2606042330): make etzhayyim's own
society visible without an ad-style ranking. The quarantine is a governance act
(EXCLUDE per ADR-2605212245), not a quality/affinity judgement.

## Consequences

- The apex home/discover feed surfaces etzhayyim's own actors first and no longer
  shows the EXCLUDE'd external `shinshi` poster; external non-quarantined accounts
  are still shown (after own actors).
- New pure module + 6-case test suite (`scripts/feed-curation.test.mjs`).
- Curation is a single auditable rule set; adding/removing a quarantined poster is a
  one-line, reviewable change (governance-gated).
- **Operator:** effective after `wrangler deploy`. The quarantine marker list is the
  governance surface — changes go through PR review (Council attestation).

## Alternatives Considered

1. **A bespoke feed-generator service.** Rejected for now: heavier, and a recency
   feed minus the EXCLUDE'd poster + own-first ordering already solves the visible
   problem with an auditable pure function.
2. **Rate-limit shinshi instead of quarantine.** Rejected: shinshi is EXCLUDE'd
   (ADR-2605212245), not merely noisy — it should not be on etzhayyim's front page
   at any rate. (Its own profile remains reachable.)
3. **Personalized/engagement ranking.** Rejected: violates §1.13 / §2(h).

## References

- ADR-2606232100 (ATProto actor registration — the posts now exist to rank)
- ADR-2605212245 (shinshi reclassified EXCLUDE)
- ADR-2606042330 (searchActors/getSuggestions self-contained short-circuit — same stance)
- ADR-2606211752 (四鏡則 — mirrors post observations, not impersonation)
- `50-infra/etzhayyim-did-web/src/feed-curation.ts` / `src/worker.ts` (`proxyCuratedFeed`)
