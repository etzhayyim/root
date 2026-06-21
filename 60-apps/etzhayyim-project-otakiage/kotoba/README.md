# otakiage kotoba

Phase E Option B reference implementation of otakiage (reuse + ritual platform) on the etzhayyim substrate.

Per [ADR-2605081700](../../../90-docs/adr/2605081700-otakiage-reuse-ritual-platform.md) + [ADR-2605203000](../../../90-docs/adr/2605203000-kotoba-write-target-options.md), otakiage migrates from vendor's `createKyselyDb` pattern (RW direct write) to **Option B** — PDS XRPC writes via `@etzhayyim/sdk e.write()`.

Coverage: **10 of 10 (100%) canonical** + 3 transition helpers = **13 total commands**.

| Tier | Commands | Slice |
|---|---|---|
| Item | submitItem, getItem, listItems | 1 |
| State transitions | requestReuse, handover, expire, requestRitual, ritualize | 2 |
| Certificate + Matsuri + Coverage + AgentChat | issueCertificate, anchorCertificate, scheduleMatsuri, coverage, agentChat | **3** |

All 10 canonical otakiage lexicons now have kotoba reference impl. Wire-up
to a Worker / LangServer pod XRPC handler is the next operator task per
ADR-2605203000.

## Item state machine (per ADR-2605081700)

```
submitted
  ↓ (auto, TTL 30d)
reuse_open
  ├→ handed_over           (terminal, T1 social derive)
  └→ reuse_expired
        └→ ritual_pending  (mode=reuse_then_ritual のみ)
              └→ ritualized (terminal, certificate URI 発行)
```

Item modes:
- `reuse_only` — try reuse only; expire if not handed over
- `ritual_only` — skip reuse_open, go directly to ritual_pending
- `reuse_then_ritual` — try reuse first, fall back to ritual on expiry

## Authority-chain DIDs (per otakiage CLAUDE.md)

```
did:web:otakiage.etzhayyim.com                          — controller
did:web:otakiage.etzhayyim.com:reuse                    — handover broker
did:web:otakiage.etzhayyim.com:ritual                   — ceremony actor
did:web:otakiage.etzhayyim.com:matsuri                  — seasonal organizer
did:web:otakiage.etzhayyim.com:item:{itemId-slug}       — this slice (Item)
did:web:otakiage.etzhayyim.com:certificate:{certId-slug} — Certificate (future)
did:web:otakiage.etzhayyim.com:matsuri:{matsuriId-slug}  — Matsuri (future)
```

## Pattern translation (Option B)

| Vendor (`otakiage.etzhayyim.com`) | etzhayyim (this PR) |
|---|---|
| `const db = createKyselyDb();` | `import type { Etzhayyim } from "@etzhayyim/sdk"` |
| `db.insertInto("vertex_otakiage_item").values({...}).execute()` | `e.write({ collection: "com.etzhayyim.otakiage.item", record, rkey })` |
| `db.selectFrom("vertex_otakiage_item").where("id","=",i).execute()` | `e.read({ collection, rkey: \`item-${idSlug(i)}\` })` |

## Usage

```ts
import { Etzhayyim } from "@etzhayyim/sdk";
import { submitItem } from "@etzhayyim/otakiage-kotoba";

const e = new Etzhayyim({
  did: "did:web:otakiage.etzhayyim.com",
  pdsUrl: "https://pds.etzhayyim.com",
  l2RpcUrl: "https://mainnet.base.org",
});

// Submit (auto-transitions to reuse_open with 30d TTL)
const r = await submitItem(e, {
  itemId: "item-2026-0001",
  ownerDid: "did:plc:abc...",
  title: "古い本棚",
  description: "状態良好、要組立",
  category: "furniture",
  mode: "reuse_then_ritual",
  locationHint: "東京都世田谷区",
});
// → { status: "registered", itemUri: "at://...", itemStatus: "reuse_open",
//     reuseDeadlineAt: "+30d" }
```

## Why Option B for otakiage

Per ADR-2605203000 Phase E decision matrix:
- **Catalog**: item lifecycle records + certificate issuance + matsuri events
- **Write cadence**: per-submission (low rate) + per-state-transition (low rate)
- **Query pattern**: status filter (kanban) + locationHint proximity + ownerDid filter

Option A (vendor RW mirror) rejected — ADR-2605172000 mandates kotoba.

## Sibling reference impls

| Actor | Coverage | Status |
|---|---|---|
| hanrei | 31/31 (100%) | complete |
| ipaddress | 37/37 (100%) | complete |
| sbom | 17/N (canonical 4/4) | canonical complete |
| kiyo | 12/12 (100%) | complete |
| ki | 4/4 (100%) | complete |
| **otakiage** | **3/10** | active |
