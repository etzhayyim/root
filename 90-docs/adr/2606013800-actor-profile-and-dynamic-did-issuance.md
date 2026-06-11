---
id: adr-2606013800-actor-profile-and-dynamic-did-issuance
title: "ADR-2606013800: Actor profile schema + dynamic did.json issuance from kotoba"
status: accepted
doc_type: adr
topic: actor-profile-and-dynamic-did-issuance
authoritative: true
last_verified: 2026-06-01
priority: 6.0
axis: architecture
weight: 0.62
priority_note: "Closes the 'profile not found' gap for kotoba-native actors and demotes the hardcoded DID registry to a fallback."
authoritative_for:
  - actor-profile-schema
  - dynamic-did-web-issuance
  - actor-getprofile-resolution
depends_on:
  - 2605212030
  - 2605241800
  - 2605231525
  - 2605312345
  - 2605262130
related:
  - 2606011800
  - 2606012600
  - 2606013200
  - 2606012100
supersedes: []
superseded_by: []
---

# ADR-2606013800: Actor profile schema + dynamic did.json issuance from kotoba

**Status**: accepted
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

Two defects surfaced when trying to view a Tier-B actor (tsumugi 紡ぎ) on the live site:

1. **`https://etzhayyim.com/profile/did:web:etzhayyim.com:actor:tsumugi` → "profile not found".**
   The apex Worker does not serve `/profile/...`; it reverse-proxies to the yoro
   AppView, whose `/profile/[handle]` route resolves a **handle** against the PDS
   (`app.bsky.actor.getProfile`). A raw actor DID is not a PDS repo, and tsumugi is
   a **kotoba-native** actor that deliberately has **no atproto profile record**
   ("emits kotoba EDN directly into the Datom log", per ADR-2606011800). So nothing
   resolved.

2. **`did.json` was hardcoded, not issued from canonical state.**
   `/actor/<handle>/did.json` was built in the CF Worker from a hand-authored
   TypeScript registry (`infra-actors.ts`). New actors required editing that file
   and redeploying the Worker; the kotoba Datom log — declared first-class canonical
   state by ADR-2605312345 — was not the source.

The fix must respect four constitutional invariants:

- **Datom log = SSoT** (ADR-2605312345). Profile/identity state lives in kotoba, not
  Kotoba/Datomic / PDS-SQL (the legacy `getProfile` path is being retired anyway —
  b94484a5d routed reads through the apex substrate).
- **No server-held private key** (ADR-2605231525). The Worker must not sign DID
  documents or mint keys. did:web's trust root is TLS; `verificationMethod` is a
  **mirror** of the on-chain ERC725 key, populated only when chain wiring lands.
- **did:web resolution must stay live.** Identity is load-bearing; resolution can
  never go dark because kotoba/KV is unreachable.
- **Murakumo-only / cookie-free** (ADR-2605215000, Charter Rider §2(c)). No new
  commercial endpoints, no trackers.

# Decision

## D1 — Actor profile is a single kotoba record, SSoT for BOTH did.json and the profile view

New schema `00-contracts/schemas/actor-profile.kotoba.edn` defines one `:actor/*`
entity per actor in the public `actors-v1` graph, keyed by `:actor/handle`
(`:db.unique/identity`, idempotent upsert). It carries the union of DID-doc fields
(`:actor/service` → `service[]`, `:actor/vm` → `verificationMethod[]`, mirror-only)
and profile-view fields (`display-name-*`, `description`, `avatar`, `performer-type`,
`ui-type`, `glyph`, `kind`, `status`, `tier`, `adr`, `primary-schema`). Seed for the
10 registered actors lives in `actor-profile-seed.kotoba.edn`.

This record is the **single source** rendered into the DID Document *and* the
`app.bsky.actor.getProfile` view, so the two can never drift.

## D2 — Dynamic did.json issuance: 3-tier, fail-open

The apex Worker resolves an `ActorRecord` (`resolveActorRecord`) in order:

1. **CF KV** (`actor:<handle>`) — materialized from kotoba by the publisher; fast,
   origin-independent.
2. **kotoba pull** (`KOTOBA_ENDPOINT` → `com.etzhayyim.apps.kotobase.kg.entity`) — first-class
   canonical state; best-effort, result cached back into KV.
3. **compiled `INFRA_ACTORS`** — last-resort fallback so did:web never goes dark.

`/actor/<handle>/did.json` maps the resolved record through the pure `toDidDoc()`
mapper. `verificationMethod` is whatever `:actor/vm` carries (empty today → empty
array; the doc still validates and trust falls back to TLS — **no key is minted**).
Free-form member/council handles (not registered actors) keep the legacy
`buildPerActorDidDoc` scaffold path.

## D3 — Actor profile resolution through the apex registry

- New REST surface `GET /actor/<handle>/profile.json` → `toGetProfileView(record)`.
- XRPC short-circuit: `app.bsky.actor.getProfile` / `com.etzhayyim.actor.getProfile`
  for a **registered actor** (DID form `did:web:etzhayyim.com:actor:*`, or a bare
  handle that is a known actor) is served from the actor registry **before** the
  substrate/PDS alias routing. Human-member profiles are never hijacked (the
  short-circuit is gated on the actor being known).
- yoro SSR `getProfile()` resolves registered-actor DIDs via the apex registry first,
  with the PDS path preserved as fallback (additive; cannot regress human members).
  This makes `/profile/did:web:etzhayyim.com:actor:tsumugi` render via `AgentProfile`.

## D4 — Publisher

`scripts/publish-actor-records.mjs` parses the canonical seed EDN and materializes,
per actor, the `record.json` / `did.json` / `profile.json`; `--put-kv` pushes records
to KV, `--ingest-kotoba` POSTs `kg.ingest_batch` (operator-gated). `toDidDoc` /
`toGetProfileView` are mirrored between the publisher (JS) and the Worker (TS) so KV,
kotoba, and compiled fallback all render identically.

# Consequences

- The kotoba `actors-v1` graph becomes the live source of truth for actor identity +
  profile; `infra-actors.ts` is demoted to a typed compiled fallback (kept, not
  deleted — it is the identity-live backstop).
- did:web resolution is now dynamic but **fail-open**: KV miss → kotoba → compiled,
  so it cannot go dark.
- tsumugi (and every kotoba-native actor) gets a resolvable profile WITHOUT a PDS
  repo, preserving the "kotoba-native, no atproto record" property.
- No server key is introduced; `verificationMethod` stays empty until the on-chain
  ERC725 mirror lands (ADR-2605212030 Phase B).
- **HONEST R0**: KV namespace + a reachable `KOTOBA_ENDPOINT` are operator-gated
  (kotoba has no public read surface yet — Murakumo-mesh-internal). Until enabled the
  Worker serves the compiled fallback through the SAME mappers, so behaviour is
  identical; KV merely promotes kotoba to live source. `kg.entity` response shape is
  consumed defensively (best-effort). Live kotoba ingest of the seed is operator-gated.
  yoro change is in the (deprecated-but-live) appview copy; only that copy exists.

# Alternatives Considered

- **Give tsumugi a real PDS repo + `app.bsky.actor.profile` record.** Rejected: breaks
  the kotoba-native invariant and re-introduces a PDS/Kotoba/Datomic dependency for actor
  state that ADR-2605312345 + b94484a5d are removing.
- **Worker signs the DID document / holds a key.** Rejected: violates ADR-2605231525.
  did:web does not require a signed document — TLS is the trust root.
- **Keep the hardcoded registry as SSoT.** Rejected: contradicts ADR-2605312345 and
  forces a Worker redeploy per actor.
- **Worker pulls kotoba on every resolution (no KV).** Rejected: couples did:web
  liveness to kotoba uptime. KV snapshot + compiled fallback decouples them.

# References

- `00-contracts/schemas/actor-profile.kotoba.edn` — schema (SSoT)
- `00-contracts/schemas/actor-profile-seed.kotoba.edn` — seed for 10 actors
- `50-infra/etzhayyim-did-web/src/registry/actor-profiles.ts` — ActorRecord + mappers
- `50-infra/etzhayyim-did-web/src/kotoba.ts` — kotoba pull path
- `50-infra/etzhayyim-did-web/scripts/publish-actor-records.mjs` — publisher
- ADR-2605212030 (hybrid did:web + did:erc725), ADR-2605241800 (single did-web Worker,
  libp2p service), ADR-2605231525 (no-server-key), ADR-2605312345 (Datom = canonical
  state), ADR-2605262130 (kotoba substrate), ADR-2606011800 (tsumugi, kotoba-native)
