# ADR-2605213000: Phases F / G / H / I closure — Phase E reference stack fully equipped

**Status**: ACTIVE
**Supersedes**: amends ADR-2605210000 + ADR-2605211000 + ADR-2605212000
**Date**: 2026-05-21
**Decider**: Claude Opus 4.7 + ~30 Haiku 4.5 parallel agents (autonomous /loop)

## Context

Following ADR-2605210000 Phase E completion (25 kotoba actors, 27 with pre-existing inclusive of open-isco + tsukuru), four execution-layer phases completed in the same session:

- **Phase F** — CF Worker XRPC adapters (25/25) + PDS session auth (`@etzhayyim/sdk-auth`)
- **Phase G** — mst-projector Phase 3 reference impl (in-memory + production LanceDB/DuckDB/HF embedding adapters)
- **Phase H** — Cross-actor integration tests demonstrating 25-actor mesh composition
- **Phase I** — CI workflows (vitest × 25 + tsc × 5 SDK + wrangler-validate) + runtime input validators (`@etzhayyim/lexicon-to-zod`)

## Decision: structural completeness declared

All code-only deliverables from Phase E through Phase I are merged to `main`. The reference stack is end-to-end equipped:

```
   Lexicon JSON SSoT (208 namespaces)
              │
              ↓ lexicon-to-openapi   ↓ lexicon-to-zod
              │                       │
   OpenAPI 3.0 (208)            Zod runtime validator
              │                       │
              └────────────┬──────────┘
                           ↓
   CF Worker XRPC adapter (25 actors, sdk-auth wired)
                           │  e.write() / e.read()
                           ↓
   @etzhayyim/sdk — Etzhayyim class — atproto PDS
                           │
                           ↓ kotoba reference impl (27 actors)
                           │
                           ↓ commit firehose
                           │
   mst-projector (in-memory ⇄ LanceDB+DuckDB+HF embedding)
                           │
                           ↓ com.etzhayyim.projector.* records
                           │
   clients read indexed views via standard e.read()
```

## Phase summary

### Phase F — Worker XRPC + auth (PRs #153-#208)

- 25 worker scaffolds at `60-apps/etzhayyim-project-<actor>/xrpc-adapter/`
- `@etzhayyim/sdk-auth`: `createAuthedEtzhayyim` + `extractBearerToken` + `refreshPdsSession`
- All 25 workers accept `Authorization: Bearer <jwt>` header or fall back to env `PDS_ACCESS_JWT`
- 300+ XRPC endpoints exposed

### Phase G — mst-projector Phase 3 (PRs #210, #213, #222)

**In-memory baseline** (zero deps):
- `InMemoryTextIndex` / `InMemoryAttributeIndex` / `InMemoryAggregateIndex`
- `InMemoryProjector` (alias `MstProjector`) with `processCommit` + 3 query methods
- 13 Vitest tests

**Production adapters** (deploy-time installed):
- `LanceDbTextIndex` via `@lancedb/lancedb`
- `DuckDbAttributeIndex` + `DuckDbAggregateIndex` via `duckdb-async`
- `HuggingFaceEmbedding` via HF Inference API
- `LocalTransformersEmbedding` via `@xenova/transformers` ONNX
- All dynamic imports + `peerDependenciesMeta` optional

**Firehose subscriber** — `PollingFirehose` (test substrate); production swaps WebSocket `com.atproto.sync.subscribeRepos`.

**Materializer** — writes outputs back as `com.etzhayyim.projector.aggregate` / `textSearch` records.

### Phase H — Cross-actor integration (PR #220)

| File | Demonstrates |
|---|---|
| `bonsai-vascular.test.ts` | koke → hakkou → ki absorb/synthesize/bloom/ring |
| `authority-chain.test.ts` | hanrei + houki + houbun composition |
| `sbom-blast-radius.test.ts` | ipaddress + sbom CVE pipeline + blast-radius |
| `otakiage-lifecycle.test.ts` | state machine all 3 paths |
| `mst-projector-end-to-end.test.ts` | kiyo → projector ingest → 3 query types |

### Phase I — CI + validators (PRs #221, #223)

- `.github/workflows/test.yml` — vitest × 25 + tsc × 5 SDK + integration
- `.github/workflows/wrangler-validate.yml` — `wrangler deploy --dry-run` × 25 gated on `deploy-preview` label
- `@etzhayyim/lexicon-to-zod` — `buildValidatorMap` + `validateInput` + CLI
- open-banking `transfer` integrates Zod safeParse + 400 on validation failure

## Quantitative snapshot

| Layer | Coverage |
|---|---|
| kotoba actors | 27/27 (100%) |
| Worker XRPC + sdk-auth | 25/25 (100%) |
| Vitest tests | 24/25 active (96%) |
| Cross-actor integration | 5 scenarios |
| OpenAPI 3.0 specs | 208 namespaces |
| mst-projector backends | in-memory + LanceDB + DuckDB + 2 embedders |
| CI workflows | 3 |
| Runtime validators | Zod generator + open-banking demo |
| ADRs this session | 4 active |
| Session PR count (etz) | ~123 (#100-#223) |
| Session PR count (vendor) | 2 |
| TypeScript new code | ~37,000 lines |

## Remaining operator-gated work

1. `wrangler deploy` × 25 (CF account) per ADR-2605211000 4-tier priority
2. `pnpm install` LanceDB / DuckDB / @xenova/transformers on projector pod
3. WebSocket `com.atproto.sync.subscribeRepos` client (replace PollingFirehose)
4. CF Workers secrets: `PDS_ACCESS_JWT` + `PDS_REFRESH_JWT` × 25
5. CF DNS records `<actor>.etzhayyim.com` × 25

## Lessons learned

1. **Parallel haiku scales well for repetitive scaffold work** — 4-6 agents × ~3-15 min per batch.
2. **Verify `mergedAt` not agent claims** — early agents collided on PR #146 with false-merge claims. Always `gh pr view <N> --json mergedAt` non-null assertion.
3. **Git-lock contention forces sequential cleanup** — 5+ agents on one local clone caused some to abandon mid-flight. Final cleanup must be sequential.
4. **Squash-merge can collapse parallel PRs** — observed #170 sdk-auth + mst-projector squashed together. Cosmetic only; files all land.
5. **`peerDependenciesMeta` optional** is right for the projector — in-memory ships, LanceDB/DuckDB graduate at deploy time without forcing heavy native deps on all consumers.

## Related

- [ADR-2605203000](/90-docs/adr/2605203000-kotoba-write-target-options.md) — Phase E foundation
- [ADR-2605210000](/90-docs/adr/2605210000-phase-e-reference-impl-completion.md) — Phase E completion
- [ADR-2605211000](/90-docs/adr/2605211000-worker-xrpc-adapter-deploy-runbook.md) — deploy runbook
- [ADR-2605212000](/90-docs/adr/2605212000-mst-projector-phase3-indexed-views.md) — mst-projector Phase 3
- [ADR-2605172000](/90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md) — kotoba substrate
- [ADR-2605172400](/90-docs/adr/2605172400-etzhayyim-vendor-three-axis-split-rule.md) — vendor/etz boundary
