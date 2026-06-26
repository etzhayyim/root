---
id: adr-2606042330-entity-as-actor-society-wide-social-mirror-graph
title: "ADR-2606042330: entity-as-actor — society-wide entity socialization via keyless mirror-actors"
status: accepted
doc_type: adr
topic: entity-as-actor-social-mirror-graph
authoritative: true
last_verified: 2026-06-06
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - "1 entity = 1 actor: every public/power entity datafied by a knowledge-graph actor resolves its own did:web actor"
  - keyless mirror-actor model (no-server-key) + namespaced generated handle registries
  - entity social timeline = kotoba Datom as-of history projected as app.bsky.feed.post
  - searchActors / getProfile at society scale across all entity namespaces + unispsc unification
depends_on:
  - "2606013800"
  - "2605241800"
  - "2605231525"
  - "2605231902"
  - "2605262130"
  - "2605312345"
  - "2605215000"
  - "2605192200"
  - "2605171300"
related:
  - "2606021600"
  - "2606022000"
  - "2606032000"
  - "2606011800"
  - "2606012600"
  - "2606041827"
supersedes: []
superseded_by: []
---

# ADR-2606042330: entity-as-actor — society-wide entity socialization via keyless mirror-actors

**Status**: proposed
**Date**: 2026-06-04
**Deciders**: Jun Kawasaki

# Context

The question *「`https://etzhayyim.com/search` にまだ 12 actor しかない。全世界の行政・法人組織・
不動産・ウェブサイトなどの actor が登録されているはずだが、どうなっている?」* exposes a real gap
between the **expectation** (society-wide entities each present as an actor) and the **current
design** (a handful of knowledge-graph actors that hold the world's entities only as internal
kotoba Datom records).

## Two mismatches in the current state

**(A) Most designed actors are R0, un-deployed.** The Status table in `CLAUDE.md` lists 50+
Tier-B / knowledge-graph actors, but only **9 glyphed named actors** are actually registered in
`50-infra/etzhayyim-did-web/src/registry/infra-actors.ts` (watatsuna · watari · tsumugi · kanae ·
kabuto · kanjo · ooyake · tsuzuri · todoke). Plus seeded profiles, `/search` surfaces ~12. The
rest exist as ADR + manifest + cells + lexicon in the repo but resolve no DID.

**(B) Category confusion: governments / companies / craft are *entities*, not *actors*.** Under
the current design a single KG actor datafies many real-world entities **into the kotoba Datom log
as entities**, never as separate actors. The user's mental model — *1 real-world entity = 1 actor* —
is **not** what ships. The entity census (seed data already in the repo) is large:

| KG actor | entity kind | seed count | id shape |
|---|---|---|---|
| ooyake 公 | government units (58 registry files) | **7,108** | `gov.afg.adm1.af-bal` |
| kabuto 兜 | public companies | **1,720** | `org.corp.tw.tsmc` |
| tsumugi 紡ぎ | power-law organisms | 19 | `org.corp.jp.7203` (∈ corp space) |
| kanjo 勘定 | disclosure filers | ~5 (84 filings) | `org.corp.*` |
| watatsuna 綿津綱 | submarine cables + stations | 36 | `cable.jupiter` |
| watari 渡り | ships + aircraft | 13 | `craft.vessel.imo9811000` |
| (existing) unispsc | UNSPSC commodity agents | **18,342** | `c70000000` |

So ~11,000 new entity-actor candidates exist **today** from bounded `:representative` seed alone;
full society scale (millions) sits behind live-ingest gates (G7).

## The precedent that already solves "actor at scale"

The UNSPSC organism wave (ADR-2605171300) **already implements `1 entity = 1 actor` at scale** and
is the template this ADR generalizes:

- `50-infra/etzhayyim-did-web/src/registry/unispsc-handles.gen.ts` (18,352 lines) is a **generated**
  `Set<handle>` + `UNISPSC_TOTAL_COUNT`. The Worker never enumerates 18k entries in code.
- A **handle SHAPE** regex (`/^c\d{6,12}$/`) lets `isKnownHandle()` validate membership without a
  per-actor source file or a per-actor subdomain Worker (ADR-2605241800 §Phase A).
- Each handle resolves a **keyless** `did:web:etzhayyim.com:actor:<handle>` with
  `verificationMethod: []` — a **mirror of the on-chain ERC725 key, never server-minted**
  (ADR-2605231525 no-server-key; ADR-2606013800 D2 three-tier fail-open resolution).
- `getProfile` / `searchActors` proxy to the registry upstream.

The plumbing to turn 7,108 gov-units and 1,720 companies into resolvable actors therefore needs
**no new invention** — only generalization of the `.gen.ts` + handle-shape + resolver pattern to a
small set of new entity namespaces, plus a **social timeline projection** so the actors are not
inert profiles but living, followable presences.

## The constitutional forcing function

"atproto に登録して social 化" has exactly one charter-clean shape, and the charter **forces** it:

- You **cannot mint a signing key and post AS** the Japanese government or Toyota — that is
  **impersonation** and violates ooyake's standing invariant *「never the government, never an
  official channel」* (ADR-2606021600) and the force/transparency posture. A real per-entity atproto
  PDS repo would also need a per-entity private key, which ADR-2605231525 prohibits the server from
  holding.
- Therefore every entity-actor is an **observational mirror** — keyless, clearly labelled
  *「etzhayyim observational mirror of X」*, whose "voice" is **etzhayyim's record of public facts
  about X**, never X speaking. This is precisely ooyake / kabuto / watatsuna / watari's existing
  *mirror, not target-list, not channel* posture, now given a per-entity social surface.
- **Person-entities are structurally excluded** (watari G4 no-person; nusa `:thc-class` precedent):
  the operator/subject of an entity-actor is a public organ or a public legal person, never a
  natural person, private vehicle, private vessel, or private residence.

# Decision

Introduce the **entity-as-actor** layer: every public/power entity that a knowledge-graph actor
datafies into the kotoba Datom log **also** resolves its own **keyless mirror-actor** on the
etzhayyim did:web + atproto substrate, with a social profile and a Datom-history timeline. Zero
invariant amendments.

## D1 — Handle namespace + canonical DID

Each entity id maps to a single-label handle by dot→hyphen substitution, carrying a namespace
prefix so the Worker can shape-validate without enumeration:

| namespace | handle shape | from id | example handle |
|---|---|---|---|
| `gov` | `^gov-[a-z0-9-]+$` | `:gov.unit/id` | `gov-afg-adm1-af-bal` |
| `corp` | `^corp-[a-z0-9-]+$` | `:company/id` / `:organism/id` / kanjo filer (all `org.corp.*`) | `corp-tw-tsmc` |
| `cable` | `^cable-[a-z0-9-]+$` | `:cable/id` | `cable-jupiter` |
| `station` | `^station-[a-z0-9-]+$` | `:station/id` | `station-maruyama` |
| `craft` | `^craft-[a-z0-9-]+$` | `:craft/id` | `craft-vessel-imo9811000` |

- Canonical DID: `did:web:etzhayyim.com:actor:<handle>` (ADR-2606013800), keyless
  (`verificationMethod: []`), content-addressable did.json CID advertised per ADR-2606015400.
- `corp` deliberately **unifies kabuto + tsumugi + kanjo** — they already share the `org.corp.*` id
  space, so one company = one `corp-*` actor whose facts are woven from all three KG actors (supply
  edges from kabuto, 縁/karma from tsumugi, 決算 from kanjo). This is the entity-graph the user asked
  for: a single social presence per real-world organization.
- unispsc's existing `c\d{6,12}` handles are **folded into the same registry mechanism** (a 6th
  namespace, `unspsc`-shaped) so `/search` searches commodities and entities through one path.

## D2 — Generated per-namespace handle registries

A new build step (`70-tools/scripts/entity-actors/gen-entity-handles.mjs`, stdlib/node-only) reads
each KG actor's seed/merged EDN, extracts entity ids, and emits
`50-infra/etzhayyim-did-web/src/registry/entity-handles.<ns>.gen.ts` — each a
`Set<handle>` + `<NS>_TOTAL_COUNT` + `<NS>_GENERATED_AT`, mirroring `unispsc-handles.gen.ts`
exactly. The Worker imports these and extends `isKnownHandle()` / the namespaced-shape table. No
per-actor file, no per-actor Worker (ADR-2605241800 §Phase A preserved). `no-git-lfs`: the `.gen.ts`
are source-committed (text), the underlying EDN seeds stay in DataLad→IPFS where already large
(tsumugi G8 pattern).

## D3 — Profile view = kotoba entity record (mirror-labelled)

`resolveActorRecord` (ADR-2606013800, KV → kotoba → compiled) is extended with an **entity tier**:
for a namespaced entity handle, it pulls the entity's kotoba record (`kg.entity`) and maps it to an
`ActorRecord` whose:

- `displayName` = the entity's public name + the namespace glyph;
- `description` **must** begin with the mirror disclaimer (`observation-only`, never the entity
  itself) — enforced by construction in the mapper, not by convention;
- `performer-type` = `:organization` | `:system` (never `:person`);
- `verificationMethod: []` (no-server-key);
- service[] points at the **owning KG actor's** xrpc/wasm surface (the mirror is rendered by the KG
  actor that maintains it, not a new per-entity server).

## D4 — Social timeline = Datom as-of history → app.bsky.feed.post

The "social" half reuses the **feed-post membrane + feed-discover L1 projection** (ADR-2605231902,
preserved unchanged) rather than inventing a feed store:

- Each material change to an entity's Datom history (`as-of` transaction: a new 決算 filing, a cable
  fault bulletin, a gov-unit procedure/address change, a craft chokepoint transit, a supply-edge
  rewiring) projects to one **`app.bsky.feed.post`** authored by that entity-actor's DID.
- The post body is **Murakumo-narrated** (ADR-2605215000 sole inference SSoT) from the Datom delta,
  aggregate-first and `:representative`-honest; the post `createdAt` = the Datom `as-of` instant.
- **非終末論**: append-only; there is no "final state" post and no mutable overwritten timeline — the
  timeline *is* the entity's `as-of` trajectory (Wellbecoming framing, ADR-2605312345).
- Follows/feeds let a member subscribe to e.g. "every Malacca-chokepoint craft transit" or "Toyota's
  disclosure + supply + 縁 stream" as one civic-accountability timeline.

## D5 — searchActors / getProfile at society scale

`app.bsky.actor.searchActors` (`com.etzhayyim.yoro.actor.searchActors`) and `getProfile` resolve
across **all** namespaces + unispsc through the unified registry. `/search` and `/actors` paginate
(the registry is a `Set`, counts come from `<NS>_TOTAL_COUNT`); the HTML index shows per-namespace
totals (e.g. "gov 7,108 · corp 1,720 · …") so the page honestly reports scale instead of a silent
12.

## D6 — Lexicon

New `com.etzhayyim.mirror.*` lexicon family under `00-contracts/lexicons/com/etzhayyim/mirror/`:
`mirrorActor` (entity-actor record; `const performerType ∈ {organization,system}`, `const
isMirror=true`, `const serverHeldKey=false`, `personSubject` **unrepresentable**), `mirrorPost`
(the Datom-delta → feed-post envelope; `const narrator="murakumo"`). These sit beside, and reuse,
`com.etzhayyim.actor.*` (ADR-2606013800) and the `app.bsky.feed.post` membrane.

## D7 — Gates (charter-enforced by construction)

- **G1 mirror-only / no-impersonation** — every entity-actor is `isMirror=true`; description carries
  the observation-only disclaimer; the server never holds a key to post *as* the entity. Posts are
  etzhayyim's record of public facts, never the entity's own speech.
- **G2 public/power-entity-only** — subject is a public organ or public legal person. `gov` =
  ooyake's public gov-units; `corp` = listed/public companies; `craft` operator = a company org id,
  never a person; private vessels/jets/residences excluded (watari G4, tsumugi G1).
- **G3 person-excluded by construction** — `performerType` cannot be `:person`; `personSubject`
  field does not exist in the lexicon (nusa `:thc-class` / watari no-person precedent).
- **G4 not-a-target-list** — aggregate-first, resilience/accountability framing inherited from each
  source KG actor (watatsuna/watari G2, tsumugi G1); a social presence for accountability, not a
  dossier for interdiction.
- **G5 no-server-key** — `verificationMethod: []`, `serverHeldKey=false`; any future per-entity key
  is an on-chain ERC725 mirror, never server-minted (ADR-2605231525).
- **G6 Murakumo-only** — all post narration via the Murakumo fleet (ADR-2605215000).
- **G7 sourcing-honesty** — `:representative` seed clearly flagged; `<NS>_TOTAL_COUNT` reports the
  registered (not the claimed-global) count; freshness-tail for stale entities (watari G5).
- **G8 outward-gated** — the registry, profiles, and projection logic ship now; **live publication
  of entity-actor posts to the atproto firehose, and live full-universe entity ingest, are Council +
  operator gated** (the same G7/G11 posture as every KG actor). R0 = generate, resolve, dry-run.
- **G9 no-git-lfs / PII-clean** — `.gen.ts` text-committed; entity data in DataLad→IPFS; no natural-
  person PII (follows from G3).

## D8 — Non-goals

- **N1** NOT real per-entity atproto PDS repos / NOT posting as the entity (impersonation; G1).
- **N2** NOT a real-estate registry of private properties — land remains the LandRegistry/LANDS.md
  4-layer trust (ADR-2605192245); only *public* land/works entities may mirror, never private
  residences.
- **N3** NOT "one actor per website" — websites are crawled content in the kotoba CC web-search
  (ADR-2606012300), not minted as person-or-private actors; only a website's *public operating
  organization* mirrors as a `corp` entity.
- **N4** NOT surveillance / pattern-of-life / target-list (G4).
- **N5** NOT a new state store — state stays the kotoba Datom log (ADR-2605262130/2605312345); no
  Kotoba/Datomic/SQL.

# Update — landed + LIVE (2026-06-06)

Status flipped **proposed → accepted**: the design shipped and is verified in production.

**Registry + resolution**

- `gen-entity-handles.mjs` → 5 `entity-handles.<ns>.gen.ts` (gov 7,106 + corp 1,733 + cable 14 +
  station 22 + craft 13 = **8,888** keyless mirror handles); `corp` unifies kabuto+tsumugi+kanjo over
  `org.corp.*`.
- `entity-actors.ts` resolves each `did:web:etzhayyim.com:actor:<ns>-<…>` as a keyless record
  (`verificationMethod:[]`, G5) + `searchEntityActors` offset-cursor pagination `{records, nextOffset,
  total}`.
- **43 Tier-B named actors registered** via `tier-b-actors.gen.ts` (regenerated by `bb gen:tier-b-actors`
  — `etzhayyim.gen-tier-b-actors`, the clj/bb port of the retired `gen-tier-b-actors.mjs`; scans
  `manifest.jsonld` for `tier=="Tier-B"` not already in `INFRA_ACTORS`, falling back to `manifest.edn`
  (Gen-3 kotoba-native) as the jsonld-deletion wave removes each actor's jsonld); `infra-actors.ts` renamed its
  hand-authored export to `HAND_AUTHORED_ACTORS` and now exports
  `INFRA_ACTORS = { ...TIER_B_ACTORS, ...HAND_AUTHORED_ACTORS }`. Total resolvable ≈ **8,947**.

**Three fixes that made `/search` honest (12 → society scale)**

1. `searchActors` short-circuit in `worker.ts` (entity matches + best-effort PDS merge).
2. **`getSuggestions` also short-circuited** — default `/search` browse calls `getSuggestions`, not
   `searchActors`; without this the page stayed at ~62.
3. **yoro service-worker (`kotoba-sw.js`) backfill defeated** — the in-browser kotoba node intercepted
   `searchActors` and set `merged.totalActors = merged.actors.length` (~62). Fixed by prepending the
   compiled named/infra actors on `offset===0` so the SW finds nothing missing and passes the response
   through; `totalActors` now reports `ENTITY_TOTAL_COUNT + namedActors.length`.

**Per-profile 500 fixed**

- `yoro .../profile/[handle]/+page.svelte`: the actor-DID branch called `getAuthorProfile` against the
  PDS (`atproto.etzhayyim.com`), which 405'd on GET → threw inside `Promise.all` → SvelteKit 500.
  Replaced with a guarded **relative `/xrpc/app.bsky.actor.getProfile`** fetch against the apex
  (`.catch(()=>null)` + a record-derived fallback object), so a miss degrades gracefully instead of
  500-ing. `kotodama-yoro` deployed (version `92d5aa2c`).
- A complementary `etzhayyim-xrpc-proxy` apex-routing change (`tryApexActorProfile`) is committed but
  **not deployed** — its deploy is blocked by a cross-account service binding
  (`etzhayyim-pds-2603241700`), and the yoro-side fix already resolves the 500, so it is redundant.

**SDK clean-build restored** — `@etzhayyim/sdk/src/index.ts` had `export * as kotoba-datomic` (invalid
identifier, leftover from rename cutover `96186ef915`); renamed to `kotobaDatomic` (the
`@etzhayyim/sdk/kotoba-datomic` package-exports subpath is unaffected). `tsc --noEmit` exit 0.

**Verified live (2026-06-06)**

- `https://etzhayyim.com/actor/himawari/profile.json` → **HTTP 200**
- `https://etzhayyim.com/profile/did:web:etzhayyim.com:actor:himawari` → **HTTP 200** (no longer 500)
- `/search` reports society scale (8,888 entities + 18,342 unspsc + named/service).

**Count without GROUP-BY rescan** — `actor-count-mv.kotoba.edn` + `emit_ingest_batch.mjs` reference the
kotoba `MvRegistry::maintain` incremental tally (assert/retract deltas net the per-namespace count);
`ENTITY_TOTAL_COUNT` is the compiled constant, no per-request aggregate scan.

Tests green: 7/7 (TS) + 5/5 (py); gen deterministic; zero invariant amendments.

# Consequences

**Positive**

- `/search` honestly reflects scale: ~29,000 actors (7,108 gov + 1,720 corp + craft/cable/station +
  18,342 unspsc) from seed alone, growing with gated live ingest — answering the user's question
  directly.
- One real-world organization = one `corp` social presence weaving kabuto + tsumugi + kanjo facts:
  the unified entity graph the user wants.
- The Datom-history-as-timeline makes the substrate's append-only `as-of` model *visible and
  followable* — civic accountability as a social feed, fully on-chain-anchored, Murakumo-narrated,
  non-eschatological.
- Reuses three shipped mechanisms wholesale (unispsc handle registry, ADR-2606013800 resolver,
  ADR-2605231902 feed membrane); minimal new surface; zero invariant amendments.

**Negative / risks**

- **Mirror-vs-impersonation is a perception risk**: a casual viewer may read an entity-actor as the
  entity's official account. Mitigated by the mandatory by-construction disclaimer (G1) + `isMirror`
  flag + verificationMethod:[] (no verifiable authorship by the entity). Must be visible in the
  yoro AgentProfile UI, not just the record.
- **Scale of generated files**: per-namespace `.gen.ts` could total tens of thousands of lines (as
  unispsc already does). Acceptable (text, source-committed); regeneration is deterministic.
- **Surveillance-adjacent optics** even with G2/G3/G4 — society-wide entity socialization invites the
  "are you building a panopticon?" critique. The charter answer (public-power-only, aggregate-first,
  accountability-not-interdiction, person-excluded, on-chain-transparent) must be stated on the
  `/search` and `/actors` pages, not just in this ADR.

# Alternatives Considered

1. **Full atproto PDS repo per entity (real account that posts).** Rejected: requires a per-entity
   private key (no-server-key violation, ADR-2605231525) and means posting *as* the entity
   (impersonation; ooyake "never the official channel"). Legally and constitutionally impossible for
   third-party entities.
2. **Keep entities KG-internal (status quo).** Rejected: does not "socialize" entities — they remain
   invisible rows inside 6 KG actors; `/search` stays at 12 and the user's expectation is unmet.
3. **One actor per KG actor, entities as sub-resources only.** Rejected: this *is* the status quo's
   shape; it cannot give a per-entity profile/timeline/follow, which is the explicit ask.
4. **Mint handles only for entities with rich data; skip the long tail.** Rejected as the default but
   adopted as a *honesty knob*: `<NS>_TOTAL_COUNT` reports exactly what is registered, and thin
   entities still resolve a minimal mirror profile (no fabricated coverage, G7); we do not silently
   truncate.

# References

- ADR-2606013800 — actor profile + dynamic did.json (resolver this generalizes)
- ADR-2605241800 — agentURI 5-layer / one-Worker-many-actors (Phase A no-per-actor-Worker)
- ADR-2605231525 — no-server-key invariant
- ADR-2605231902 — feed-post membrane + feed-discover L1 projection (timeline reuse)
- ADR-2605262130 / 2605312345 — kotoba Datom log = first-class canonical state
- ADR-2605215000 — Murakumo-only inference
- ADR-2605171300 — UNSPSC 18,345-agent wave (the scale precedent)
- ADR-2606021600 (ooyake) / 2606022000 (kabuto) / 2606032000 (kanjo) / 2606011800 (tsumugi) /
  2606012600 (watatsuna) / 2606041827 (watari) — source KG actors whose entities are mirrored
- ADR-2605192200 — Charter Rider (license + compliance posture)
