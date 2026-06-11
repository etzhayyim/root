# ADR-2605210000: Phase E rw-free reference impl scaffold complete (25 actors)

**Status**: ACTIVE
**Supersedes**: none (extends ADR-2605203000 with completion milestone)
**Date**: 2026-05-21
**Decider**: Claude Opus 4.7 + 5 Haiku 4.5 parallel agents (autonomous /loop)

## Context

[ADR-2605203000](/90-docs/adr/2605203000-rw-free-write-target-options.md) defined the Option B PDS XRPC pattern (`@etzhayyim/sdk e.write()`) replacing vendor's `createKyselyDb` direct-write pattern, per the [ADR-2605172000](/90-docs/adr/2605172000-etzhayyim-rw-free-substrate.md) RW-free substrate mandate.

This ADR records the **scaffold-layer completion** of that migration — every actor in `etzhayyim/root/60-apps/` that has lexicons under `00-contracts/lexicons/com/etzhayyim/<actor>/` now has a `rw-free/` reference implementation.

## Decision

The Phase E reference impl scaffold layer is **structurally complete** at 25 actors. No more lexicons exist without a corresponding rw-free TypeScript module.

The next operator phase target is **execution-layer**: wiring rw-free packages to live CF Workers + LangServer pods + deploying.

## Actor coverage matrix

| Actor | Coverage | Lexicons | Commands | Notes |
|---|---|---|---|---|
| open-isco | seed pattern | — | 4 | Original reference (ADR-2605172000 seed) |
| tsukuru | 46/46 | — | 46 | Pre-existing (Phase 2 escrow_intent + lawfirm P1) |
| hanrei | 31/31 | — | 31 | Legal case corpus (jurisdiction/court/case/law/source/gazette/digest/hunt/stats/collect tiers) |
| ipaddress | 37/37 | — | 37 | RIR/NIR/ASN/Prefix/Provider/IP/Scan/Search/Topology/Geo/Abuse/Collect/List/Analyze/Peering tiers |
| sbom | 17 / canonical 4/4 | 4 | 17 | Artifact→Component→CVE→VulnMatch→PatchPolicy→PatchAction→Recall |
| kiyo | 12/12 | 12 | 12 | Research archive (paper/review/citation/stats) |
| ki | 4/4 | 4 | 4 | Bonsai vascular (absorb→synthesize→bloom→ring) |
| otakiage | 13 / canonical 10/10 | 10 | 13 | Reuse/ritual state machine + certificate + matsuri |
| houki | 9 / canonical 8/8 | 8 | 9 | Private authority (corporate legal docs) |
| open-banking | 5/5 | 5 | 5 | Double-entry ledger |
| open-denki | 12/12 | 12 | 12 | Smart grid (IEC 61968/61970) |
| koke | 4/4 | 4 | 4 | Bonsai fixation tier |
| hakkou | 3 / canonical 2/2 | 2 | 3 | Bonsai fermentation tier |
| isbn | 4/4 | 4 | 4 | ISO 2108 book registry |
| gtin | 3/3 | 4 | 3 | GS1 product registry |
| houbun | 12/12 | 8 | 12 | Global statute/treaty corpus (3-layer DID) |
| isin | 11/11 | 11 | 11 | ISO 6166 security registry |
| dns | 6/6 | 7 | 6 | Domain transfer (Squarespace→Cloudflare) |
| ndc | 3 / canonical 1/1 | 1 | 3 | US FDA NDC + WHO ATC drug registry |
| ocel | 3/3 | 1 | 3 | Object-Centric Event Log |
| houshi | 3/3 | 3 | 3 | Spore dispersal & dormancy |
| anime | 10/10 | 10 | 10 | Title/season/episode/schedule/review |
| manga | 12/12 | 12 | 12 | Title/chapter/tag/reading/Narou ingest |
| gameka | 9/9 | 9 | 9 | Game gen+publish lifecycle |
| bpmn | 13/13 | 13 | 13 | Process engine (deploy/start/signal/cancel) |
| narou | 11/11 | 11 | 11 | Web novel platform |
| yoro | 23/23 | 23 | 23 | Federated social feed + actor + graph + feed |

**Total**: 25 actor rw-free packages, ~315 commands, 161 vendor lexicons covered.

## Trinity groupings

The 25 actors form three thematic trinities:

### Bonsai vascular trio (biology metaphor)
`koke (fixation)` → `hakkou (ferment)` → `ki (absorb → synthesize → bloom → ring)`

### Authority chain trio (compliance composition per 90-docs/260323-authority-chain-compliance-design.md)
`hanrei (case law)` + `houki (private corporate)` + `houbun (statute/treaty)`

### ISO standards trio (content-addressed identifier registries)
`isbn (ISO 2108)` + `gtin (GS1)` + `isin (ISO 6166)`

## Substrate boundary preserved (ADR-2605172000)

All 25 actors comply with the RW-free substrate mandate:
- No `createKyselyDb()` calls — replaced with `e.write({ collection, record, rkey })`
- No `env.HYPERDRIVE` bindings — purely PDS-resident
- No fiat payment processors — substrate boundary respects open-banking ledger metadata only; on-chain settlement (USDC on Base L2) lives outside the rw-free package per ADR-2605172400 3-axis OR-test
- IPFS-backed blobs (kiyo / otakiage / houki) store CIDv1 only — no inline binary
- Vault zero-knowledge invariant (dns authCode) enforced via `signal:v1:` prefix validation

## Pattern invariants

Every rw-free package follows the same shape:

```
60-apps/etzhayyim-project-<actor>/rw-free/
├── package.json         — @etzhayyim/<actor>-rw-free, workspace dep on @etzhayyim/sdk
├── README.md            — coverage table + DID hierarchy + usage example
└── src/
    ├── types.ts         — record types + Input/Output + slug/DID/rkey helpers + DID_PREFIX const
    ├── <tier>.ts        — functions per tier (max 5 src files per actor)
    └── index.ts         — barrel
```

Function shape:

```ts
import type { Etzhayyim } from "@etzhayyim/sdk";

export async function registerX(e: Etzhayyim, input: RegisterXInput): Promise<RegisterXOutput> {
  if (/* validation */) return { status: "rejected", error: "..." };
  const rkey = xRkey(input.id);
  const existing = await e.read<XRecord>({ collection: X_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) return { status: "alreadyExists", ... };
  const record: XRecord = { did: xDid(input.id), ...input, createdAt: new Date().toISOString() };
  const receipt = await e.write({ collection: X_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", xUri: receipt.uri, did: record.did };
}
```

Idempotency = rkey-direct read before write. AT Lexicon no-float restriction = integer fields (`*Permille` for 0-1.0 values × 1000).

## Next phase: execution-layer

Three operator workstreams open in priority order:

### 1. CF Worker XRPC adapter wiring (CRITICAL)

Each rw-free package needs a CF Worker that:
- Imports the rw-free functions
- Exposes them as XRPC handlers at `https://<actor>.etzhayyim.com/xrpc/<NSID>`
- Authenticates via PDS session
- Logs to Cloudflare Logpush

Recommended starter actor: **open-banking** (smallest surface, 5 commands, financial — high value test).

### 2. mst-projector Phase 3 indexed views

Per ADR-2605203000 §"Phase 3", post-fetch filters (e.g., `hanrei.searchDecisions`, `ipaddress.searchProviders`, `kiyo.searchPapers`) are O(N) full-collection scans. Phase 3 mst-projector pushes these to indexed materialized views server-side (O(log N) or O(1)).

Reference impl `truncated:boolean` flags in all aggregation outputs already make the projector dependency honest.

### 3. Deploy & smoke test

Per root CLAUDE.md deploy checklist:
1. Deploy check: `/_app/meta` or `/health` 応答 + build exit 0
2. Sanity check: 全 XRPC endpoint 実行 (Write→`{did|status}`, Read→`{...}` or `{error:"not found"}`, List→`{..., offset, limit}`)
3. Regression check: PDS profile / subscribeRepos collections / 連携 app onCommit

## Migration efficiency note

The final 8 actors (haiku batch 1+2) were ported by 8 parallel **Haiku 4.5** agents in two batches, while the first 17 were ported sequentially by **Opus 4.7**:

- Sequential Opus: ~17 actors × ~3-5 min/actor ≈ 50-85 min total
- Parallel Haiku batch 1 (5 actors): ~3 min wall-clock for 35 lexicons
- Parallel Haiku batch 2 (3 actors): ~4 min wall-clock for 47 lexicons

Lesson learned: agent self-reports must be verified via `gh pr view <N> --json mergedAt` returning non-null. Two early haiku agents (anime + gameka) raced for PR #146 — one claimed merge falsely. Subsequent agents were instructed to verify before claiming success.

## Related

- [ADR-2605203000](/90-docs/adr/2605203000-rw-free-write-target-options.md) — Phase E write-target options (foundation)
- [ADR-2605172000](/90-docs/adr/2605172000-etzhayyim-rw-free-substrate.md) — RW-free substrate (substrate mandate)
- [ADR-2605172400](/90-docs/adr/2605172400-etzhayyim-vendor-three-axis-split-rule.md) — 3-axis OR-test (vendor/etzhayyim boundary)
- [ADR-2605152100](/90-docs/adr/2605152100-etzhayyim-github-org-boundary.md) — GitHub org split (this repo's scope)
- `90-docs/260323-authority-chain-compliance-design.md` — Authority chain composition
