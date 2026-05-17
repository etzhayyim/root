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
  - which 'gftd*' refs in etzhayyim/root are intentionally preserved
  - which 'gftd*' refs were mechanically rewritten in the 2026-05-17 sweep
  - migration of 'gftd.ai' subdomain references (open-scope subset)
  - the policy for `did:web:X.gftd.ai` historical DIDs
  - the policy for `ai.gftd.apps.*` NSID lexicons
  - 12-month grace period for `geth.gftd.ai`
  - `@gftdcojp/` npm scope migration (deferred)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605172800-gftd-cli-migration-strategy
related:
  - https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605152100-etzhayyim-github-org-boundary.md
supersedes: []
superseded_by: []
---

# ADR-2605172900: gftd-→-etzhayyim follow-up cutover policy

**Status**: active
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

ADR-2605152100 (vendor) established the etzhayyim ⇄ gftd source-control
boundary on 2026-05-15. Step 8 of that ADR ("gftdcojp 側 open scope
cleanup") was functionally completed across multiple subsequent commits
during the 2026-05-17 migration session (murakumo-kubelet, comfyui mac
mini fleet, 27 k8s langservers, bpmn-timers scope-split, 5 70-tools
open dirs, 30 60-apps stubs, 70-tools/gftd Go CLI, 70-tools/gftd-py
Python port, scripts + config + ingress-nginx-dispatcher).

After Step 8, **5120 files** in etzhayyim/root still contain `gftd.ai`
or `gftdcojp` substring references (down from 7054 pre-sweep). This is
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

Adopt the following classification + policy for all `gftd.ai`,
`gftdcojp`, and `gftd.co.jp` references in `etzhayyim/root`.

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
| `60-apps/*/PROJECT.jsonld` + `60-apps/*/magatama.jsonld` (~33 files) | Per-project canonical identity (DID + handle + nanoid). The DID `did:web:X.gftd.ai` is the historical identifier under which an app's atproto records were authored; rewriting the DID without a proper PLC migration (ADR-0014) orphans the records. |
| Any file where a `did:web:X.gftd.ai` appears as a stable identifier | DIDs are historical commitments. Migration requires `did:plc` switch + DID document rotation, not text replacement. |

**Total Class A: ~10,019 files** (the dominant share of remaining
`gftd*` refs).

## Class B — INTENTIONAL CROSS-REPO REFERENCES (preserve)

References that document the boundary between this monorepo and the
vendor monorepo. These must remain pointing at vendor.

| Path / pattern | Why preserved |
|---|---|
| `CLAUDE.md` root | Identity section: `Vendor: Gftd Japan株式会社 (did:web:gftd.co.jp)`, cross-repo URL pointer |
| `README.md` root | Boundary ADR link + vendor monorepo SSoT URL |
| `deps.toml` root | `boundary_adr` URL, `github_org_vendor_monorepo` setting, `seed_source` URL, `legacy_domain = "geth.gftd.ai"` (grace), `did = "did:web:gftd.co.jp"` (vendor DID) |
| `lefthook.yml` root | Cross-repo URL pointer for hook reference set |
| `90-docs/adr/*.md` (12 files) | ADRs cross-reference vendor ADRs by full URL (Shannon-Optimal, MCP-as-Cell-Membrane, Bonsai Cultivar, etc.). Required by ADR-2605170900 placement policy. |

**Total Class B: ~17 files** (small, mostly the four root config files +
ADR cross-references).

## Class C — MECHANICAL CUTOVER COMPLETED (executed 2026-05-17 sweep)

The 2026-05-17 mechanical sweep rewrote the following in active code +
config files:

```
gftd.ai                         → etzhayyim.com   (broad)
ghcr.io/gftdcojp/               → ghcr.io/etzhayyim/
github.com/gftdcojp/at-client   → github.com/etzhayyim/root/10-protocol/at-client
github.com/gftdcojp/signal-client → github.com/etzhayyim/root/10-protocol/signal-client
github.com/gftdcojp/wproto      → github.com/etzhayyim/root/10-protocol/wproto
github.com/gftdcojp/magatama-go → github.com/etzhayyim/root/20-actors/magatama-go
github.com/gftdcojp/nats-jetstream-kv-resp        → github.com/etzhayyim/root/50-infra/nats-jetstream-kv-resp
github.com/gftdcojp/nats-jetstream-objectstore-s3 → github.com/etzhayyim/root/50-infra/nats-jetstream-objectstore-s3
github.com/gftdcojp/nats-tiered-storage           → github.com/etzhayyim/root/50-infra/nats-tiered-storage
github.com/gftdcojp/spin-tinygo-flight            → github.com/etzhayyim/root/50-infra/spin-tinygo-flight
github.com/gftdcojp/sveltejs-adapter-wasm         → github.com/etzhayyim/root/50-infra/sveltejs-adapter-wasm
github.com/gftdcojp/tonbo                         → github.com/etzhayyim/root/50-infra/tonbo
github.com/gftdcojp/cdn                           → github.com/etzhayyim/root/70-tools/cdn
github.com/gftdcojp/yata                          → github.com/etzhayyim/root/50-infra/yata
/Users/junkawasaki/github/ai-gftd-apps-gftdcojp   → /Users/junkawasaki/github/etzhayyim-root   (local absolute paths)
ai-gftd-apps-gftdcojp                              → etzhayyim/root   (in path-style refs)
```

**Restored (false positives caught + reverted in same commit)**:

- `gftdcojp/etzhayyim/root` (broken intermediate from over-eager
  ai-gftd-apps-gftdcojp rewrite) → `gftdcojp/ai-gftd-apps-gftdcojp`
  (correct vendor monorepo name)
- `geth.etzhayyim.com` → `geth.gftd.ai` (12-month grace per deps.toml
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

### D.1 — `@gftdcojp/` npm scope

| File pattern | Count | Status |
|---|---|---|
| `**/.npmrc` with `@gftdcojp:registry=https://npm.pkg.github.com` | ~5 | preserved |
| `**/package.json` with `"name": "@gftdcojp/..."` | ~20 | preserved |
| TypeDoc / generated docs HTML mentioning `@gftdcojp/...` | ~10 | preserved |
| Code imports `from '@gftdcojp/...'` | ~50 | preserved |

**Why deferred**: `@gftdcojp/` is the npm.pkg.github.com scope for
published TypeScript / Rust packages. A scope rename requires:

1. Create `@etzhayyim` npm org (or use GitHub Packages with new scope)
2. Republish every package under new scope
3. Update consumer dependencies (in lockfiles, package.json, code
   imports)
4. Set up redirects / deprecations on old `@gftdcojp/*` packages
5. Coordinate with external consumers (if any have these packages
   declared)

This is a coordinated rollout, not a sed. **Dedicated follow-up ADR**
(to be authored when rename is undertaken).

### D.2 — `ai.gftd.apps.*` NSID lexicons (active code references)

Even after sweeping `gftd.ai` → `etzhayyim.com`, NSIDs like
`ai.gftd.apps.openIsic.classifyEntity` remain in active code that
invokes XRPC methods. Approximately ~200 files outside the Class A
lexicon files themselves.

**Why deferred**: NSIDs are protocol identifiers; renaming them
requires:

1. Author new lexicon JSON under `ai.etzhayyim.apps.X.Y` namespace
2. Deploy new XRPC endpoints alongside legacy `ai.gftd.apps.*` endpoints
3. Grace period where both NSIDs resolve to the same handler
4. Update clients to new NSIDs
5. Retire `ai.gftd.apps.*` after telemetry shows zero usage

This is a protocol-level coordination, not a string replacement.
**Future ADR** when NSID cutover is undertaken.

### D.3 — `did:web:X.gftd.ai` DIDs (where they appear as identifiers, not test data)

Most `did:web:X.gftd.ai` references in etzhayyim/root are in Class A
(JSON-LD, lexicons, BPMN, seed migrations). A subset appears in active
code (e.g., DID resolution test fixtures, default actor configs).

**Why deferred**: DIDs are stable cryptographic identifiers. Rewriting
`did:web:X.gftd.ai` → `did:web:X.etzhayyim.com` requires:

1. Provision the new DID at `https://X.etzhayyim.com/.well-known/did.json`
2. Update the DID document `alsoKnownAs` to chain the new and old DIDs
3. Re-sign or re-author atproto records to use the new DID
4. (Optional) Migrate to `did:plc:` per ADR-0014 (vendor) for portable DIDs
5. Retire `did:web:X.gftd.ai` resolution after migration

Coordinated per-DID rollout. **Per-actor follow-up ADRs** (e.g., the
`yoro` actor's DID migration is captured in ADR-2605171900). When a new
actor migrates from `did:web:X.gftd.ai` to `did:web:X.etzhayyim.com`,
its own ADR documents the rotation.

## Class E — VENDOR-SCOPE SUBDOMAINS THAT INCIDENTALLY GOT REWRITTEN

The mechanical sweep rewrote ALL `*.gftd.ai` subdomains to
`*.etzhayyim.com`. Some of these subdomains map to apps that stay
vendor (`mangaka.gftd.ai`, `kenkyusha.gftd.ai`, `lawfirm.gftd.ai`,
`flight-offer.gftd.ai`, etc.). Where these appear in:

- Test fixtures and mock data — acceptable to leave rewritten (they're
  mock URLs that don't need to resolve)
- Active code that actually invokes those vendor subdomains — the
  reference is now broken and should be re-rewritten BACK to vendor
  domain

A scan after the sweep identified ~10 mangaka refs + ~4 kenkyusha refs.
These need per-app inspection. **Acceptable churn**: if a future deploy
of any of these references hits a 404 / DNS-NXDOMAIN at
`X.etzhayyim.com`, it's an indicator to inspect and either:

1. Restore the vendor URL `X.gftd.ai` (vendor canonical), OR
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

- **Some test fixtures may have wrong domain refs** (`mangaka.etzhayyim.com`
  in test data that should have stayed `mangaka.gftd.ai`). Discovered
  on first deploy / test run; not blocking until then.
- **Class A is a large pool (~10,019 files)** that will eventually need
  NSID cutover work. Estimated effort: 2-3 dedicated sessions per
  identifier family (NSIDs, BPMN process IDs, DIDs).
- **No automated lefthook rule** enforces "no new `gftd.ai` refs in
  newly authored code" yet. The CLAUDE.md prose rule is the only
  guardrail. Adding a `lefthook` hook `no-gftd-refs-outside-classA` is
  a follow-up.

## Migration / rollout

This ADR is the **classification + policy**. Concrete cutover work for
D.1 / D.2 / D.3 is captured by dedicated follow-up ADRs at the time
each cutover is undertaken.

- [x] **Class C — mechanical sweep** (this session: 1934 files
      rewritten in commits 8d90e691, 44a3d85d, 3b83b9f0, bpmn-timers
      etc. across the 2026-05-17 session)
- [x] **Class A + B documentation** (this ADR — establishes the
      preservation policy)
- [ ] **Class D.1 — npm scope rename ADR** (`@gftdcojp/` → `@etzhayyim/`)
- [ ] **Class D.2 — NSID cutover ADR** (`ai.gftd.apps.*` → `ai.etzhayyim.apps.*`)
- [ ] **Class D.3 — DID cutover** (per-actor follow-ups; first instance
      is ADR-2605171900 for `yoro`)
- [ ] **Lefthook rule** `no-gftd-refs-in-newly-authored-code` (CI
      guardrail enforcing the CLAUDE.md prose rule)

# Alternatives Considered

## A. Defer all sweeping until each cutover is dedicated

Don't touch any `gftd.ai` refs in the 2026-05-17 session; only do
per-cutover ADRs (D.1, D.2, D.3).

却下理由: 1934 files of mechanical rewrites are low-risk and
high-clarity wins. Leaving them as drift makes the codebase visibly
inconsistent ("why does this file say `gftd.ai` when our domain is
`etzhayyim.com`?"). Mechanical sweep + classify-the-rest is faster
than per-cutover discipline for cleanly mechanical items.

## B. Sweep everything blanket — including NSIDs / DIDs / lexicons

Rewrite all `gftd.ai` references regardless of context.

却下理由: lexicon NSIDs, BPMN process IDs, alembic seed hashes are
identifiers, not domain names. Rewriting them silently breaks
verification (record authorship, migration replay, lexicon
compatibility). Class A exclusion is non-negotiable.

## C. Do nothing — let drift accumulate

Leave the 7054 file refs as-is, document the boundary in CLAUDE.md
only.

却下理由: drift compounds. The Go module paths in particular block
`go build` for downstream consumers (they wouldn't find the `gftd-*`
modules at the vendor path either, since we've stubbed them). Module
path correctness is a build-time requirement, not aesthetic preference.

# References

- ADR-2605152100 (vendor) — etzhayyim GitHub Org Boundary
- ADR-2605170900 (this repo) — etzhayyim/root as canonical ADR home
- ADR-2605172800 (this repo) — 70-tools/gftd CLI migration strategy
- ADR-2605171900 (this repo) — yoro migration (example of D.3 per-actor
  DID cutover)
- ADR-0014 (vendor) — self-hosted did:plc migration (Phase 5)
- `CLAUDE.md` (root, this repo) — operating entity identity, follow-up
  cutover phrasing
- `deps.toml` (root, this repo) — `[platform.geth_legacy]` 12-month
  grace period for `geth.gftd.ai`
- 2026-05-17 session commits implementing this policy:
  - `8d90e691` murakumo + comfyui migration
  - `44a3d85d` 27 k8s langservers
  - `3b83b9f0` 5 70-tools open dirs
  - `dc45e314` bpmn-timers scope-split + k8s deep sweep
  - `83cdda57` 70-tools/gftd Go CLI
  - `1cafabb9` 70-tools/gftd-py
  - `c5617342` config + scripts + ingress
  - `bc726d2e` mechanical Class C sweep (1934 files)
