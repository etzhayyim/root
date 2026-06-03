---
id: adr-2605191358-yoro-murakumo-rw-free-rewrite-map
title: "ADR-2605191358: yoro / murakumo RW-free rewrite — per-path migration map"
status: proposed
doc_type: adr
topic: yoro-murakumo-rw-free-rewrite
authoritative: true
last_verified: 2026-05-19
priority: 8.0
axis: architecture
weight: 0.80
priority_note: "Concretizes ADR-2605172000 (RW-free hard rule) for the two largest remaining RW-dependent apps in etzhayyim/root. Without this map yoro/murakumo migration stages 3-5 cannot proceed."
authoritative_for:
  - per-path rewrite map for yoro UI (kagami-store + 12 RW Async MVs)
  - per-path rewrite map for murakumo cluster (goose recipes / LiteLLM / vertex_inference_job)
  - per-path rewrite map for CF Worker murakumo (Kysely + Hyperdrive)
  - rewrite ordering and `@etzhayyim/sdk` adoption gate
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605171900-yoro-migration-to-etzhayyim
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - 2605191346-etzhayyim-vultr-free-murakumo-control-plane
related:
  - ADR-2605172100 (substrate client imports — `@etzhayyim/sdk` only)
  - ADR-2605182312 (murakumo-gemma4 local bring-up)
  - 60-apps/etzhayyim-project-open-isco/rw-free/ (first reference impl)
supersedes: []
superseded_by: []
---

# ADR-2605191358: yoro / murakumo RW-free rewrite — per-path migration map

**Status**: proposed
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

ADR-2605171900 (yoro migration) copied yoro code to `etzhayyim/root/60-apps/etzhayyim-project-yoro/` at stages 1–2 (code + DNS placeholder). Stages 3–5 (AppView deployment, legacy redirect, vendor cleanup) are blocked because the copied code still depends on RisingWave via `atproto.etzhayyim.com PDS + Hyperdrive → RisingWave`, violating ADR-2605172000.

Grep evidence (`60-apps/etzhayyim-project-yoro/CLAUDE.md`, 2026-05-19) — 14 RW touchpoints retained verbatim from upstream:

- `kagami-store.svelte.ts` (`query()` / `loadLabel()` / `federatedQuery()` / `listAvailableLabels()` — all backed by RW via Hyperdrive)
- 12 RisingWave Async MVs feeding event-driven dashboards
- `searchActors` → `vertex_app` + `vertex_repo_record` RW direct
- Read path `PDS → pipethroughAppView → yoro AppView → HYPERDRIVE → RisingWave`
- Write path `PDS XRPC → graph SQL path → RisingWave Stream Load → MV refresh`

Murakumo has two distinct RW dependencies:

1. **`60-apps/etzhayyim-project-murakumo/`** (vendor-only, not yet migrated) — goose recipes INSERT into RW via `/Users/judah/.etzhayyim/rw-url`; LiteLLM `vertex_inference_job` row writes; ansible distributes PG URL.
2. **`50-infra/cloudflare/workers/murakumo/`** (vendor-only, not yet migrated) — `createKyselyDb(HYPERDRIVE)` + direct `vertex_inference_job` SQL inside Worker handlers.

Additional vendor-only assets:

- `50-infra/multicluster/murakumo-vke/placement-contract.yaml` — places `risingwave` service in topology
- `50-infra/vultr/yoro-actors-raw/templates/yoro-social-post.json` — `postgres:16-alpine` container

Per ADR-2605191346, none of the above may target Vultr VKE either. Per ADR-2605172000, none may carry RW dependency. The migration is therefore a **substrate rewrite**, not a `mv`.

# Decision

The five RW-dependent paths above are rewritten against AT MST + IPFS + Base L2, accessed exclusively via `@etzhayyim/sdk`. Lexicons (`00-contracts/lexicons/com/etzhayyim/{yoro,murakumo}/`) are already migrated and retained unchanged — the wire format is stable; only the durable storage substrate swaps.

## Path-level rewrite map

### yoro UI (`60-apps/etzhayyim-project-yoro/`)

| Old (RW-backed)                            | New (`@etzhayyim/sdk`)                                                  |
|---|---|
| `kagami-store.query(label, filter, limit)` | `e.read({ collection, filter })` → MST collection traverse              |
| `kagami-store.loadLabel(label)`            | `e.list({ collection })` (lazy page)                                    |
| `kagami-store.federatedQuery(label, …)`    | Lexicon NSID federation via `e.federated({ host, collection, filter })` |
| `kagami-store.listAvailableLabels()`       | `e.collections()` (MST root index)                                      |
| 12 RW Async MVs                            | Client-side reducer over MST subtree (CRDT-style; cached in `localStorage` / `IndexedDB`) — no server-side MV. Heavy aggregates → background `mst-projector` (`50-infra/mst-projector/`) emits CID-pinned snapshots referenced from MST. |
| `searchActors(query, opts)`                | `e.search({ collection: 'app.bsky.actor.profile', q })` — query rewriter against MST keys; full-text via IPFS CID-pinned inverted index built by `mst-projector` (lazy) |
| Read path Hyperdrive → RW                  | PDS XRPC → MST → client reducer (no Hyperdrive)                         |
| Write path RW Stream Load + MV refresh     | `e.write({ collection, record, blobs })` → PDS commit → IPFS pin → L2 anchor (batched, `anchor-cron`) |
| RW operator JWT                            | `did:web:etzhayyim.com` + WebAuthn passkey, DID-bound (ADR-2605172000 §SDK) |
| Server-side plaintext RW query             | Private records → `com.etzhayyim.encrypted.*` envelope (ADR-2605181100); public records → plaintext MST |

### murakumo cluster (`60-apps/etzhayyim-project-murakumo/` — pending migration)

| Old (RW-backed)                                        | New (`@etzhayyim/sdk`)                                                |
|---|---|
| goose recipe INSERT into `com.etzhayyim.yoro.platformDigest` | `e.write({ collection: 'com.etzhayyim.yoro.platformDigest', record })`      |
| LiteLLM `vertex_inference_job` row write               | `e.write({ collection: 'com.etzhayyim.murakumo.inferenceJob', record })`; status updates as new records (event-sourced; no UPDATE) |
| `vertex_repo_commit` MV                                | `mst-projector` derives commit log → CID-pinned JSON; referenced by MST record |
| RW PG URL `/Users/judah/.etzhayyim/rw-url`                  | Removed. No PG URL in secrets store.                                  |
| ansible PG URL distribution                            | ansible distributes `@etzhayyim/sdk` config (PDS URL + DID + paymaster address) only |
| persona-cron RW direct INSERT                          | persona-cron → `e.write(…)` → PDS commit; L2 anchor on next batch     |

### CF Worker murakumo (`50-infra/cloudflare/workers/murakumo/` — pending migration)

| Old (Kysely + Hyperdrive)                                       | New                                                                |
|---|---|
| `import { createKyselyDb } from '@etzhayyim/magatama-host-sdk'`      | `import { Etzhayyim } from '@etzhayyim/sdk'`                       |
| `createKyselyDb(env.HYPERDRIVE)` + raw SQL                      | `new Etzhayyim({ pdsUrl, did, … })`; no Hyperdrive binding         |
| `INSERT INTO vertex_inference_job …`                            | `e.write({ collection: 'com.etzhayyim.murakumo.inferenceJob', record })` |
| `SELECT … FROM vertex_inference_job WHERE error IS NULL …`      | `e.read({ collection, filter })` (key-prefix MST traverse)         |
| Hyperdrive `env.HYPERDRIVE` Worker binding                      | Removed from `wrangler.jsonc`                                      |
| FLUSH / RW-specific SQL semantics                               | Idempotent record creation (collection NSID + rkey scheme)         |

### multicluster murakumo-vke (`50-infra/multicluster/murakumo-vke/`)

Per ADR-2605191346 §Substrate hard rule, `etzhayyim/*` workloads run on **Murakumo Mac-mini fleet** only. The Vultr VKE placement contract is **retired** rather than rewritten:

- `placement-contract.yaml`: drop `risingwave` from the service list. No replacement service is provisioned on the Mac-mini fleet — RW-free rewrite eliminates the need.
- `topology.yaml` / `karmada-pull-mode-runbook.md`: archive under `50-infra/_archive/vultr/multicluster/` for audit trail; no etzhayyim deploy uses them.

### vultr yoro-actors-raw (`50-infra/vultr/yoro-actors-raw/`)

`templates/yoro-social-post.json` requires `postgres:16-alpine` for a per-actor scratch DB. Replacement:

- Remove the Postgres container from the template.
- Per-actor scratch state lives in the actor's local IndexedDB / SQLite-WASM and is checkpointed to MST via `e.write({ collection: 'com.etzhayyim.yoro.actorRunState', record })`.

If the actor genuinely needs SQL semantics (joins, aggregates), it runs **DuckDB-WASM** over CID-pinned Parquet snapshots emitted by `mst-projector` — read-only, no shared mutable state.

## Adoption gate

No yoro / murakumo PR merges into `etzhayyim/root/main` unless it passes the substrate hard rule check (ADR-2605172100):

1. No direct import of `@atproto/api`, `viem`, `kysely`, `@etzhayyim/magatama-host-sdk`, `pg`, `postgres`, `@signalapp/libsignal-client`, `@noble/ciphers` from app code.
2. Only `@etzhayyim/sdk` and `@etzhayyim/sdk/encrypted` may appear as substrate-client imports.
3. CI grep gate (future `lefthook` hook, see §Consequences): `grep -rE 'risingwave|hyperdrive|kysely|createKyselyDb' 60-apps/ etzhayyim-project-yoro 60-apps/ etzhayyim-project-murakumo 50-infra/cloudflare/workers/murakumo` returns empty.

## Ordering

The rewrite proceeds in this order to minimize churn:

1. **`@etzhayyim/sdk`** API surface freeze for the verbs used above (`read`, `write`, `list`, `search`, `federated`, `collections`). Verify against `open-isco/rw-free/` reference impl.
2. **CF Worker murakumo** rewrite — smallest scope, least UI coupling. Demonstrates SDK adoption.
3. **murakumo cluster** rewrite — goose recipes + LiteLLM. Confirms event-sourced inference-job pattern.
4. **yoro UI kagami-store** rewrite — largest scope; depends on `mst-projector` shipping CID-pinned aggregates.
5. **`mst-projector`** materializes the heavy aggregates that previously lived as RW MVs.
6. **Vultr archive sweep** — multicluster + yoro-actors-raw Postgres removed; legacy Vultr dirs move to `50-infra/_archive/vultr/`.

# Consequences

**Positive**:

- yoro / murakumo become verifiable from any client with internet access, no privileged RW operator. Matches ADR-2605172000's definition of "open".
- Vultr exit (ADR-2605191346) is unblocked for these two apps.
- Stages 3–5 of ADR-2605171900 (yoro migration) can resume.

**Negative / costs**:

- Heavy aggregates (12 MVs) lose RW's streaming-MV ergonomics. Replaced by `mst-projector` batch projection (latency: seconds → minutes for derived views). Acceptable for the social-feed / inference-job use cases; not acceptable for sub-second analytics — those move to client-side reducers over the relevant MST subtree.
- Event-sourced `vertex_inference_job` (no UPDATE) requires record-versioning at the lexicon level — append-only with `parent_uri` reference. Lexicons need a small extension.
- CI grep gate must be added to `lefthook.yml` and `.github/workflows/`. Currently `lefthook.yml` only enforces trailing-ws + EOF (per root CLAUDE.md §Future Work).

**Required follow-ups**:

- Lefthook hook `lint-rw-free-imports` — fail on any import in the prohibited set from app code.
- `@etzhayyim/sdk` `search()` / `federated()` API design (currently only `write`/`read`/`list` are in the reference impl).
- `mst-projector` snapshot scheme — Parquet vs JSON-Lines; pinning policy.
- L2 anchor batch cadence for high-volume inference-job records (anchor-cron tuning).

# Alternatives Considered

**A. Keep RW for yoro/murakumo, deploy on a separately-funded RW cluster.**
Rejected. Violates ADR-2605172000 hard rule. Reduces yoro/murakumo to "open license, closed substrate" — the failure mode ADR-2605172000 was created to prevent.

**B. Backend XRPC proxy: app remains RW-aware, calls a backend that owns RW.**
Rejected as substrate. Only allowed pattern (per CLAUDE.md §Substrate boundary) is *progressive enhancement*: open app operates without it, and the backend is consent-capability-gated for fiat/paid features only. Not for the core data path of yoro/murakumo.

**C. Partial migration: rewrite write path, keep read path on RW.**
Rejected. Half-state leaves RW operator in the trust path for any audit/verify scenario. Either both paths are RW-free or neither is.

**D. CRDT (Automerge/Yjs) as durable layer instead of MST.**
Rejected. MST is the AT Protocol canonical state and already integrates with PDS + IPFS + L2 anchor pipeline (ADR-2605171800). Adding a parallel CRDT layer doubles client complexity without verifiability gain. CRDT-style reducers run *over* MST events client-side; the durable layer remains MST.

# References

- ADR-2605170900 (etzhayyim/root canonical home for open ADRs)
- ADR-2605171900 (yoro migration to etzhayyim — Stages 1–5)
- ADR-2605172000 (etzhayyim RW-free substrate — hard rule)
- ADR-2605181100 (etzhayyim encrypted records — `com.etzhayyim.encrypted.*`)
- ADR-2605191346 (Vultr-free + Murakumo Mac-mini Tier-1 fleet)
- ADR-2605171800 (LangGraph Pregel → MST → IPFS → L2 anchor pipeline)
- `60-apps/etzhayyim-project-open-isco/rw-free/` (first RW-free reference impl)
- `20-actors/etzhayyim-sdk/README.md` (SDK API surface + hard rules)
- `50-infra/mst-projector/` (MST → CID-pinned snapshot projector)
- `50-infra/anchor-cron/` (Base L2 batched anchor)
