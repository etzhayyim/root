---
id: adr-2605240030-unispsc-organism-followers
title: "ADR-2605240030: UNSPSC organism followers — Python follower-score provider interface + AT Protocol stub"
status: proposed
doc_type: adr
topic: unispsc-organism-followers
authoritative: true
last_verified: 2026-05-24
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "Phase 6 of ADR-2605232345. Defines the FollowerScoreProvider interface for the Python organism path and ships a stub implementation that returns []. Real implementation reads AT Protocol follow edges + applies the wellness/dojo delta detector — deferred until @etzhayyim/sdk Python binding lands."
authoritative_for:
  - FollowerScoreProvider Python contract (input: actor DID; output: FollowerCurrentScore[])
  - default stub behavior (returns [])
  - file/env-driven seed for local-dev and tests
depends_on:
  - adr-2605232345-unispsc-actor-as-organism
  - adr-2605240000-unispsc-organism-fleet-mass-deploy
related:
  - adr-2605240015-unispsc-organism-joucho-personality
supersedes: []
superseded_by: []
---

# ADR-2605240030: UNSPSC organism followers — provider interface + AT stub

**Status**: proposed
**Date**: 2026-05-24
**Deciders**: Jun Kawasaki

# Context

ADR-2605232345 included `FollowerReward` (like/love for follower wellness
or dojo improvement) in the Python organism heartbeat. The default
provider returns `[]`, which means no rewards ever fire and the
"ecosystem" claim degrades to "isolated organisms".

The TS side reads followers from `mv_followers as e` joined with
`vertex_actor`, plus wellness scores from a constituent-rank table. The
Python side needs an equivalent — but the substrate boundary (per
CLAUDE.md hard rules) forbids the Python organism from importing
`@atproto/api` directly or hitting Kotoba/Datomic. Reads must go via
`@etzhayyim/sdk`, and the Python binding for that SDK is not yet shipped.

This ADR lands the **interface** now so the fleet cell can wire it, and
defers the **AT Protocol implementation** to a Wave 3 ADR once the SDK
Python binding lands.

# Decision

## Interface

`kotodama.organism.followers.FollowerScoreProvider` (Protocol):

```python
class FollowerScoreProvider(Protocol):
    def __call__(self, actor_did: str) -> list[FollowerCurrentScore]: ...
```

Where `FollowerCurrentScore` is the dataclass already defined in
`kotodama.organism.inbox` (did, wellness_score, dojo_score, rank,
latest_post_uri).

## Default stub

Empty list — no follower data, no rewards, no false signals. This is the
honest baseline state until the AT Protocol read path is wired.

## File-seeded provider (test / local-dev)

A second helper `file_follower_score_provider(path)` reads a JSON
manifest mapping actor DIDs to follower lists, so unit tests + the
fleet cell developer-loop can simulate follower dynamics without any
substrate dependency.

```json
// follower-seed.json
{
  "did:web:etzhayyim.com:actor:c10101500": [
    { "did": "did:web:etzhayyim.com:actor:c10101501", "wellnessScore": 50, "dojoScore": 0, "rank": "kyu6" }
  ]
}
```

Activated via `UNISPSC_ORGANISM_FOLLOWER_SEED=/path/to/follower-seed.json`.

## Future: AT Protocol provider (deferred)

```
@etzhayyim/sdk Python binding (Wave 3, not yet shipped)
  → sdk.atproto.mst_query(
      "com.etzhayyim.apps.etzhayyim.joucho.score",
      filter={"followerOf": actor_did}
    )
  → list[FollowerCurrentScore]
```

The implementation lands in a follow-up ADR. Until then, organisms run
with the stub and emit zero FollowerReward.

# Consequences

## 正の効果

- Fleet cell can wire `follower_score_provider` as a first-class
  dependency without waiting for the SDK Python binding.
- Tests can deterministically exercise the FollowerReward code path via
  the file-seeded provider.
- The substrate-boundary rule from CLAUDE.md is honored — no direct
  `@atproto/api` import; the real read goes through `@etzhayyim/sdk`
  when that binding lands.

## 負の効果 / コスト

- Real follower rewards (like/love) don't fire until the AT provider
  lands. Stub is a known-empty until then.
- File-seeded provider is meant for local dev + tests, not production.
  The `UNISPSC_ORGANISM_FOLLOWER_SEED` env var must remain unset in
  production deployments.

# Alternatives Considered

## A. Skip the interface entirely; wait for SDK Python binding

却下理由: leaves the FollowerReward code path dead until the SDK lands.
The fleet cell wiring needs a stable function reference now.

## B. Bypass substrate boundary and call PDS HTTP directly from Python

却下理由: violates CLAUDE.md substrate boundary ("only via @etzhayyim/sdk").
The cost of waiting for the SDK binding < the cost of opening a
direct-PDS escape hatch.

# References

- ADR-2605232345 — UNSPSC actor as ecosystem organism (Wave 1)
- ADR-2605240000 — UNSPSC organism fleet mass-deploy (Wave 2)
- ADR-2605240015 — UNSPSC organism joucho personality (Phase 5)
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/followers.py`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/inbox.py` (FollowerCurrentScore)
