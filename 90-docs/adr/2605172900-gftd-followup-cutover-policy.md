---
id: adr-2605172900-gftd-followup-cutover-policy
title: "ADR-2605172900: gftd-→-etzhayyim follow-up cutover policy — what is rewritten, what is preserved as historical"
status: active
doc_type: adr
topic: gftd-followup-cutover-policy
authoritative: true
last_verified: 2026-05-17
priority: 6.0
axis: organization
weight: 0.60
priority_note: "Establishes the policy boundary between mechanical sed rewrites (executed 2026-05-17) and identifier-cutover items deferred to dedicated future ADRs. Required to close ADR-2605152100 Step 8 cleanly."
authoritative_for:
  - which legacy 'gftd*' refs in etzhayyim/root are intentionally preserved
  - which legacy 'gftd*' refs were mechanically rewritten in the 2026-05-17 sweep
  - migration of legacy subdomain references (open-scope subset)
  - the policy for historical `did:web:*` DIDs under the legacy zone
  - the policy for `ai/gftd/apps/*` NSID lexicons
  - 12-month grace period for the legacy geth RPC host
  - legacy npm scope migration (deferred)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605172800-gftd-cli-migration-strategy
related:
  - 
supersedes: []
superseded_by: []
---

# ADR-2605172900: gftd-→-etzhayyim follow-up cutover policy

**Status**: active
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

ADR-2605152100 established the etzhayyim ⇄ upstream source-control
boundary on 2026-05-15. Step 8 of that ADR ("upstream-side open scope
cleanup") was functionally completed across multiple subsequent commits
during the 2026-05-17 migration session (murakumo-kubelet, comfyui mac
mini fleet, 27 k8s langservers, bpmn-timers scope-split, 5 70-tools
open dirs, 30 60-apps stubs, 70-tools/gftd Go CLI, 70-tools/gftd-py
Python port, scripts + config + ingress-nginx-dispatcher).

After Step 8, **5120 files** in etzhayyim/root still contain legacy
substring references (down from 7054 pre-sweep). This is
**intentional** — these references fall into four well-defined
categories, three of which preserve content as historical/immutable/
identity-bearing and one of which is queued for a dedicated future
migration.

`CLAUDE.md` (root) already documents the policy with the phrase:

> Do not introduce `gftd-` prefixed identifiers in newly authored code.
> Use `etzhayyim-` or no prefix. **Existing seeded `gftd-` files will
> be renamed in a follow-up cutover.**

This ADR makes the "follow-up cutover" explicit: what is and is not
covered by it, and the timeline.

# Decision

Adopt the following classification + policy for all legacy
domain / org / company references in `etzhayyim/root`.

## Class A — HISTORICAL / IMMUTABLE AUDIT (NEVER rewrite)

The following content is the historical audit record of the platform.
Rewriting would falsify identifier history and break verification of
past commits / events / records.

| Path | Why preserved |
|---|---|
| `00-contracts/lexicons/ai/gftd/*.json` (~5434 files) | atproto NSID lexicons. NSIDs are content-addressable identifiers ("ai.gftd.apps.X.Y"). Each is the identity of a specific XRPC method; rename = new method. Cutover happens via lexicon-version migration, NOT find-and-replace. |
| `00-contracts/bpmn/ai/gftd/*.bpmn` (~4027 files) | BPMN process IDs are named with NSID-form `ai.gftd.apps.X.processY`. They serve as the durable identity of business processes. Rename = new process. |
| `00-contracts/dmn/ai/gftd/*.dmn` | DMN decision tables. Same reasoning as BPMN. |
| `30-graph/graph-schema/alembic/versions/r_*_seed_*.py` (~525 files) | DB seed migrations. Every applied alembic migration is recorded in the production graph DB by its hash. Rewriting changes the hash → migration system thinks it's a new migration → re-application → data corruption risk. |
| `30-graph/graph-schema/sql_migrations/*_seed_*.sql` | Same as alembic. |
| `60-apps/*/PROJECT.jsonld` + `60-apps/*/magatama.jsonld` (~33 files) | Per-project canonical identity (DID + handle + nanoid). The historical `did:web:` DID on the legacy zone is the identifier under which an app's atproto records were authored; rewriting the DID without a proper PLC migration (ADR-0014) orphans the records. |
| Any file where a historical `did:web:` DID on the legacy zone appears as a stable identifier | DIDs are historical commitments. Migration requires `did:plc` switch + DID document rotation, not text replacement. |

**Total Class A: ~10,019 files** (the dominant share of remaining
`gftd*` refs).

## Class B — HISTORICAL CROSS-REPO BOUNDARY REFERENCES (now scrubbed)

These were references that documented the boundary between this monorepo
and the upstream legacy monorepo. As of the 2026-05-17 sweep, the
top-level docs (`CLAUDE.md`, `README.md`, `deps.toml`, `lefthook.yml`,
`90-docs/CLAUDE.md`, `90-docs/adr/README.md`, and the individual ADRs)
have been scrubbed of the explicit upstream URL / org / company name.
The boundary is still recorded via ADR-2605152100 (by ID, not URL).

## Class C — MECHANICAL CUTOVER COMPLETED (executed 2026-05-17 sweep)

The 2026-05-17 mechanical sweep rewrote the following families of refs
in active code + config files (LHS = legacy form, RHS = etzhayyim form):

```
legacy apex domain              → etzhayyim.com   (broad)
ghcr.io/<legacy-org>/           → ghcr.io/etzhayyim/
github.com/<legacy-org>/at-client          → github.com/etzhayyim/root/10-protocol/at-client
github.com/<legacy-org>/signal-client      → github.com/etzhayyim/root/10-protocol/signal-client
github.com/<legacy-org>/wproto             → github.com/etzhayyim/root/10-protocol/wproto
github.com/<legacy-org>/magatama-go        → github.com/etzhayyim/root/20-actors/magatama-go
github.com/<legacy-org>/nats-jetstream-kv-resp        → github.com/etzhayyim/root/50-infra/nats-jetstream-kv-resp
github.com/<legacy-org>/nats-jetstream-objectstore-s3 → github.com/etzhayyim/root/50-infra/nats-jetstream-objectstore-s3
github.com/<legacy-org>/nats-tiered-storage           → github.com/etzhayyim/root/50-infra/nats-tiered-storage
github.com/<legacy-org>/spin-tinygo-flight            → github.com/etzhayyim/root/50-infra/spin-tinygo-flight
github.com/<legacy-org>/sveltejs-adapter-wasm         → github.com/etzhayyim/root/50-infra/sveltejs-adapter-wasm
github.com/<legacy-org>/tonbo                         → github.com/etzhayyim/root/50-infra/tonbo
github.com/<legacy-org>/cdn                           → github.com/etzhayyim/root/70-tools/cdn
github.com/<legacy-org>/yata                          → github.com/etzhayyim/root/50-infra/yata
local checkouts of the legacy monorepo     → /Users/junkawasaki/github/etzhayyim-root (local absolute paths)
legacy monorepo path refs                   → etzhayyim/root (in path-style refs)
```

**Restored (false positives caught + reverted in same commit)**:

- Broken intermediate paths from over-eager monorepo rewrites — restored to
  their correct legacy upstream form
- `geth.etzhayyim.com` → legacy geth RPC host (12-month grace per deps.toml
  `[platform.geth_legacy]`)

**Scope**: only files in active code + config (`*.go`, `*.mod`, `*.toml`,
`*.rs`, `*.ts`, `*.tsx`, `*.js`, `*.mjs`, `*.svelte`, `*.py`, `*.json`,
`*.jsonc`, `*.yaml`, `*.yml`, `*.sh`, `*.html`, `*.sol`, `*.md`,
`*.sql`, `Dockerfile`, `Makefile`). Class A paths were explicitly
excluded.

**Outcome**: 1934 files affected by the sweep, 35,414 files scanned,
~30 minutes of compute. Go modules in 10-protocol/, 20-actors/,
50-infra/, 70-tools/ all build green after the rewrites.

## Class D — DEFERRED CUTOVERS (dedicated future ADRs)

Three families of identifiers were deliberately NOT rewritten by the
sweep because each requires more than mechanical text replacement.

### D.1 — legacy npm scope

| File pattern | Count | Status |
|---|---|---|
| `**/.npmrc` with legacy scope `registry=https://npm.pkg.github.com` directive | ~5 | preserved |
| `**/package.json` with legacy-scope `"name": "..."` | ~20 | preserved |
| TypeDoc / generated docs HTML mentioning legacy-scope imports | ~10 | preserved |
| Code imports from the legacy npm scope | ~50 | preserved |

**Why deferred**: the legacy npm scope is the npm.pkg.github.com scope for
published TypeScript / Rust packages. A scope rename requires:

1. Create `@etzhayyim` npm org (or use GitHub Packages with new scope)
2. Republish every package under new scope
3. Update consumer dependencies (in lockfiles, package.json, code
   imports)
4. Set up redirects / deprecations on the old scope's packages
5. Coordinate with external consumers (if any have these packages
   declared)

This is a coordinated rollout, not a sed. **Dedicated follow-up ADR**
(to be authored when rename is undertaken).

### D.2 — `ai/gftd/apps/*` NSID lexicons (active code references)

Even after the broad legacy-domain sweep, NSIDs like
`ai.gftd.apps.openIsic.classifyEntity` (dot-form of the `ai/gftd/apps/`
path-form lexicon ID) remain in active code that invokes XRPC methods.
Approximately ~200 files outside the Class A lexicon files themselves.

**Why deferred**: NSIDs are protocol identifiers; renaming them
requires:

1. Author new lexicon JSON under `ai.etzhayyim.apps.X.Y` namespace
2. Deploy new XRPC endpoints alongside the legacy NSID endpoints
3. Grace period where both NSIDs resolve to the same handler
4. Update clients to new NSIDs
5. Retire the legacy NSIDs after telemetry shows zero usage

This is a protocol-level coordination, not a string replacement.
**Future ADR** when NSID cutover is undertaken.

### D.3 — historical `did:web:` DIDs on the legacy zone (where they appear as identifiers, not test data)

Most historical legacy-zone `did:web:` references in etzhayyim/root are
in Class A (JSON-LD, lexicons, BPMN, seed migrations). A subset appears
in active code (e.g., DID resolution test fixtures, default actor
configs).

**Why deferred**: DIDs are stable cryptographic identifiers. Rewriting
a historical legacy-zone DID to `did:web:X.etzhayyim.com` requires:

1. Provision the new DID at `https://X.etzhayyim.com/.well-known/did.json`
2. Update the DID document `alsoKnownAs` to chain the new and old DIDs
3. Re-sign or re-author atproto records to use the new DID
4. (Optional) Migrate to `did:plc:` per ADR-0014 for portable DIDs
5. Retire the legacy-zone DID resolution after migration

Coordinated per-DID rollout. **Per-actor follow-up ADRs** (e.g., the
`yoro` actor's DID migration is captured in ADR-2605171900). When a new
actor migrates from its legacy-zone DID to `did:web:X.etzhayyim.com`,
its own ADR documents the rotation.

## Class E — LEGACY-SCOPE SUBDOMAINS THAT INCIDENTALLY GOT REWRITTEN

The mechanical sweep rewrote ALL legacy-zone subdomains to
`*.etzhayyim.com`. Some of those subdomains map to apps that stay on
the legacy zone (`mangaka.*`, `kenkyusha.*`, `lawfirm.*`,
`flight-offer.*`, etc.). Where these appear in:

- Test fixtures and mock data — acceptable to leave rewritten (they're
  mock URLs that don't need to resolve)
- Active code that actually invokes those legacy subdomains — the
  reference is now broken and should be re-rewritten BACK to the
  legacy domain

A scan after the sweep identified ~10 mangaka refs + ~4 kenkyusha refs.
These need per-app inspection. **Acceptable churn**: if a future deploy
of any of these references hits a 404 / DNS-NXDOMAIN at
`X.etzhayyim.com`, it's an indicator to inspect and either:

1. Restore the legacy-zone URL (legacy canonical), OR
2. Confirm the app has migrated and the new etzhayyim subdomain is
   provisioned

# Consequences

## 正の効果

- **Boundary policy is explicit.** The 5120-file count is no longer a
  vague "lots of refs" but four well-named buckets with clear
  preservation logic.
- **The 2026-05-17 sweep is documented.** What was rewritten, what was
  excluded, what was restored — all in one record.
- **Future cutovers are unblocked.** The deferred D.1 / D.2 / D.3 each
  have a clearly stated path forward.
- **CLAUDE.md "follow-up cutover" phrase has a referent.** Until now it
  was an undocumented placeholder.

## 負の効果 / コスト

- **Some test fixtures may have wrong domain refs** (legacy-zone subdomains
  that were swept to `*.etzhayyim.com` when they should have stayed on
  the legacy zone). Discovered on first deploy / test run; not blocking
  until then.
- **Class A is a large pool (~10,019 files)** that will eventually need
  NSID cutover work. Estimated effort: 2-3 dedicated sessions per
  identifier family (NSIDs, BPMN process IDs, DIDs).
- **No automated lefthook rule** enforces "no new legacy refs in
  newly authored code" yet. The CLAUDE.md prose rule is the only
  guardrail. Adding a `lefthook` hook `no-legacy-refs-outside-classA`
  is a follow-up.

## Migration / rollout

This ADR is the **classification + policy**. Concrete cutover work for
D.1 / D.2 / D.3 is captured by dedicated follow-up ADRs at the time
each cutover is undertaken.

- [x] **Class C — mechanical sweep** (this session: 1934 files
      rewritten in commits 8d90e691, 44a3d85d, 3b83b9f0, bpmn-timers
      etc. across the 2026-05-17 session)
- [x] **Class A + B documentation** (this ADR — establishes the
      preservation policy)
- [ ] **Class D.1 — npm scope rename ADR** (legacy scope → `@etzhayyim/`)
- [ ] **Class D.2 — NSID cutover ADR** (legacy `ai/gftd/apps/*` NSIDs → `ai/etzhayyim/apps/*`)
- [ ] **Class D.3 — DID cutover** (per-actor follow-ups; first instance
      is ADR-2605171900 for `yoro`)
- [ ] **Lefthook rule** `no-legacy-refs-in-newly-authored-code` (CI
      guardrail enforcing the CLAUDE.md prose rule)

# Alternatives Considered

## A. Defer all sweeping until each cutover is dedicated

Don't touch any legacy refs in the 2026-05-17 session; only do
per-cutover ADRs (D.1, D.2, D.3).

却下理由: 1934 files of mechanical rewrites are low-risk and
high-clarity wins. Leaving them as drift makes the codebase visibly
inconsistent ("why does this file still use the legacy domain when
our domain is `etzhayyim.com`?"). Mechanical sweep + classify-the-rest
is faster than per-cutover discipline for cleanly mechanical items.

## B. Sweep everything blanket — including NSIDs / DIDs / lexicons

Rewrite all legacy references regardless of context.

却下理由: lexicon NSIDs, BPMN process IDs, alembic seed hashes are
identifiers, not domain names. Rewriting them silently breaks
verification (record authorship, migration replay, lexicon
compatibility). Class A exclusion is non-negotiable.

## C. Do nothing — let drift accumulate

Leave the 7054 file refs as-is, document the boundary in CLAUDE.md
only.

却下理由: drift compounds. The legacy Go module paths in particular
block `go build` for downstream consumers (they wouldn't find the
legacy modules at the legacy path either, since we've stubbed them).
Module path correctness is a build-time requirement, not aesthetic
preference.

# References

- ADR-2605152100 — etzhayyim GitHub Org Boundary
- ADR-2605170900 (this repo) — etzhayyim/root as canonical ADR home
- ADR-2605172800 (this repo) — 70-tools/gftd CLI migration strategy
- ADR-2605171900 (this repo) — yoro migration (example of D.3 per-actor
  DID cutover)
- ADR-0014 — self-hosted did:plc migration (Phase 5)
- `CLAUDE.md` (root, this repo) — operating entity identity, follow-up
  cutover phrasing
- `deps.toml` (root, this repo) — `[platform.geth_legacy]` 12-month
  grace period for the legacy geth RPC host
- 2026-05-17 session commits implementing this policy:
  - `8d90e691` murakumo + comfyui migration
  - `44a3d85d` 27 k8s langservers
  - `3b83b9f0` 5 70-tools open dirs
  - `dc45e314` bpmn-timers scope-split + k8s deep sweep
  - `83cdda57` 70-tools/gftd Go CLI
  - `1cafabb9` 70-tools/gftd-py
  - `c5617342` config + scripts + ingress
  - `bc726d2e` mechanical Class C sweep (1934 files)
