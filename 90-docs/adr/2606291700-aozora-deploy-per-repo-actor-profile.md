---
id: adr-2606291700-aozora-deploy-per-repo-actor-profile
title: "ADR-2606291700: aozora deploy — per-repo actor profile deployment to the PDS"
status: proposed
doc_type: adr
topic: aozora-deploy
authoritative: true
last_verified: 2026-06-29
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - bb aozora:deploy task
  - etzhayyim.aozora-deploy namespace
  - actor-profile-seed.kotoba.edn generation
depends_on:
  - adr-2606013800
  - adr-2606231200
  - adr-2606242330
related:
  - adr-2606281500
supersedes: []
superseded_by: []
---

# ADR-2606291700: aozora deploy — per-repo actor profile deployment to the PDS

**Status**: proposed
**Date**: 2026-06-29
**Deciders**: Jun Kawasaki

# Context

Each `com-etzhayyim-*` repo is an independent actor with its own kotoba-rad
sovereign identity (`:rad/aozora {:pds :collection}`). The `actor:publish`
pipeline (ADR-2606231200) produces the identity, but its step 5 (`step-aozora`)
was **planned-only** — it emitted a command string and never executed the PDS
write. The actor profile record (`<collection>.profile`, `rkey=self`) never
landed on the aozora PDS.

Additionally, the `actor-profile-seed.kotoba.edn` (SSoT, ADR-2606013800) only
covered 41 of 168 `com-etzhayyim-*` repos. The remaining 127 had no
`did:web:etzhayyim.com:actor:<handle>` entry, so the apex Worker could not
resolve them.

The gap: **there was no `aozora deploy` command** that takes a single repo's
manifest + genesis and writes its profile to the PDS. Each repo should be
deployable independently, tied to its kototama (radical identity), not via a
central generator script.

# Decision

## 1. `bb aozora:deploy <name>` — per-repo PDS profile deployment

New `bb` task backed by `etzhayyim.aozora-deploy` (clj/bb, per the repo
operational-code rule). For each actor:

1. **Read manifest** from `20-actors/<name>/` (monorepo) or
   `../../etzhayyim/com-etzhayyim-<name>/` (published repo) — both
   `manifest.jsonld` and `actor-manifest.jsonld` supported.
2. **Derive genesis** via `manifest->genesis` (ADR-2606231200) — yields
   `:rad/aozora {:pds :collection}` + `:rad/did-web`.
3. **Build profile record body** — `{"$type" "<coll>.profile",
   "displayName", "description", "createdAt", ...}` mirroring the apex Worker's
   `profile.json`.
4. **Call `etzhayyim.pds.client/create-record!`** against the genesis `:pds`
   with `rkey=self` (idempotent — re-deploy overwrites, no duplicates).
5. **no-server-key**: optionally present a member CACAO leash (`LEASH` env) so
   the write is attributed to a consenting member; absent → unattributed
   (fail-open back-compat). The actor's own sealed key (PDS-side actorkeys
   registry) signs the commit — never this tool.

```
bb aozora:deploy chie              # dry-run
bb aozora:deploy chie --apply      # execute PDS write
LEASH=<cacao> bb aozora:deploy chie --apply  # member-attributed
```

## 2. `step-aozora` now executes (not just plans)

`actor_publish.cljc` step 5 transitions from planned-only to executed when
`--apply` is passed. It calls `aozora-deploy/deploy-one` with the genesis
`:pds` + `LEASH` env. The dry-run path still prints the planned command.

## 3. Seed generation: `gen-missing-actor-profiles.clj`

A bb script (`50-infra/etzhayyim-did-web/scripts/`) that reads each missing
repo's `manifest.jsonld` and generates EDN entries for
`actor-profile-seed.kotoba.edn`. Ran once to add 132 entries (41 → 173
handles, 4 duplicates removed). The script is idempotent — re-running produces
no new entries for already-registered handles.

## 4. Static `did.json` + `profile.json` materialization

`publish-actor-records.mjs` + `gen-kotoba-actor-blocks.mjs` materialize 173
actors × 2 files (`public/actor/<handle>/{did.json,profile.json}`), CF-served
(worker-independent). Actor-resolver tests relaxed from `== 28` to `>= 28`.

## 5. bb classpath includes PDS source

`bb.edn :paths` now includes `50-infra/etzhayyim-atproto-pds-clj/src` so
`etzhayyim.pds.client` is resolvable from `aozora-deploy` and `actor-publish`.

# Consequences

- **Per-repo deploy**: each `com-etzhayyim-*` repo can deploy its own actor
  profile to the PDS independently. No central batch script needed for ongoing
  operation (the seed generator was a one-time bootstrap).
- **`actor:publish` is now end-to-end**: the 5-step pipeline actually writes
  the profile to the PDS on `--apply`, instead of stopping at step 4.
- **173 actors resolvable**: the apex Worker + static files now cover all
  `com-etzhayyim-*` repos, not just 41.
- **no-server-key preserved**: the deploy tool never holds a signing key. The
  PDS signs with the actor's sealed key; the member leash attributes the write.
- **Idempotent**: `rkey=self` means re-deploy overwrites the same profile —
  no duplicates, safe to re-run.
- **PDS must be running** for `--apply` to succeed. Dry-run works offline.

# Alternatives Considered

1. **Keep `step-aozora` planned-only, execute out-of-band** — rejected: the
   whole point of `actor:publish` is to be a one-command pipeline. Leaving
   step 5 as a manual out-of-band step defeats the purpose and is a known gap
   (the survey confirmed nobody runs the planned command).

2. **Use the apex Worker KV path instead of the PDS** — rejected: the Worker
   KV (`publish-actor-records.mjs --put-kv`) serves `did.json` + `getProfile`
   for the apex domain, but the aozora PDS/AppView boundary (`aozora.app`,
   app-aozora) is the canonical record store per ADR-2606242330. Actor profiles
   should live on the PDS (where `createRecord` writes EAVT datoms), not just
   in Worker KV (which is a read-optimization cache).

3. **Batch-deploy all actors at once** — rejected: per-repo deploy is the
   design. Each repo has its own release cadence, its own kotoba-rad identity,
   and its own member leash. A batch tool would couple them unnecessarily.

4. **Write the generator as `.mjs` (JS)** — rejected: the repo rule mandates
   clj/bb for new operational tooling. The generator was initially written as
   `.mjs` and rewritten as `.clj` to comply.

# References

- ADR-2606013800 (Actor profile + dynamic did.json)
- ADR-2606231200 (actor:publish pipeline)
- ADR-2606242330 (app-aozora / aozora.app canonical PDS/AppView boundary)
- ADR-2606281500 (actor autonomous publication — 種をまく doctrine)
- `50-infra/etzhayyim-atproto-pds-clj/src/etzhayyim/pds/client.clj` (PDS client)
- `70-tools/src/etzhayyim/aozora_deploy.cljc` (deploy namespace)
- `70-tools/src/etzhayyim/actor_publish.cljc` (step-aozora execution)
- `50-infra/etzhayyim-did-web/scripts/gen-missing-actor-profiles.clj` (seed generator)
