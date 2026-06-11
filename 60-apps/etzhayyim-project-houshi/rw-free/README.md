# houshi rw-free

Phase E Option B reference implementation of houshi (方子 / spore dispersal, dormancy) on the etzhayyim substrate.

Per [ADR-2605203000](../../../90-docs/adr/2605203000-rw-free-write-target-options.md), houshi migrates from vendor's `createKyselyDb` pattern (RW direct write via dispatcher proxy) to **Option B** — PDS XRPC writes via `@etzhayyim/sdk e.write()`.

Coverage: **3 of 3 (100%)** canonical houshi lexicons ported.

| Tier | Commands | Slice |
|---|---|---|
| Sporulation | storeSpore, listSpores, germinate | **3** |

## Bonsai biology mapping

```
dormancy      →  storeSpore   →  SporeRecord    (artifact in custody chain)
query         →  listSpores   →  SporeQuery     (enumerate by custodian/origin)
revival       →  germinate    →  GerminateRecord (revive dormant → kobo agent)
```

## Architectural note

Houshi is the spore dispersal and dormancy system. A spore is a serialized kobo agent snapshot (CBOR-encoded state blob + revival key hint + custody chain). Spores are stored in PDS records and queried by custodian or origin agent DID. Germination is the revival process — client-side revivalKey validation + pod-side kobo spawning (per ADR-2605111200).

All three procedures use the same Option B `e.write()` and `e.read()` API pattern.

## Authority-chain DIDs

```
did:web:houshi.etzhayyim.com                         — controller
did:web:houshi.etzhayyim.com:spore:{sporeId-slug}   — SporeRecord
did:web:houshi.etzhayyim.com:germinate:{sporeId}    — GerminateRecord
```

## Usage

```ts
import { Etzhayyim } from "@etzhayyim/sdk";
import { storeSpore, listSpores, germinate } from "@etzhayyim/houshi-rw-free";

const e = new Etzhayyim({
  did: "did:web:houshi.etzhayyim.com",
  pdsUrl: "https://pds.etzhayyim.com",
  l2RpcUrl: "https://mainnet.base.org",
});

// Stage 1: store a spore
const store = await storeSpore(e, {
  sporeVertexId: "spore-2026-kobo-001",
  custodianDid: "did:web:kobo.etzhayyim.com",
  originAgentDid: "did:web:origin.etzhayyim.com",
  quorumN: 2,
  blobCbor: "base64-encoded-cbor-snapshot",
  revivalKeyHint: "sha256-digest-of-revival-key",
});

// Stage 2: list spores in custody
const list = await listSpores(e, {
  custodianDid: "did:web:kobo.etzhayyim.com",
  includeGerminated: false,
  limit: 20,
});
// → spores[], total count, pagination

// Stage 3: germinate (revive)
const germ = await germinate(e, {
  sporeVertexId: "spore-2026-kobo-001",
  revivalKey: "client-validated-key",
  newAgentDid: "did:web:revived-kobo.etzhayyim.com",
});
// → agentVertexId, germinatedAt, prionsRestored count
```

## Collections

| Collection | Record type | Rkey pattern |
|---|---|---|
| `com.etzhayyim.houshi.spore` | SporeRecord | `spore-{sporeId-slug}` |
| `com.etzhayyim.houshi.germinate` | GerminateRecord | `germinate-{sporeId-slug}` |

## Why Option B for houshi

Per ADR-2605203000 Phase E decision matrix:
- **Catalog**: kobo agent snapshots + revival metadata (private state, not federated)
- **Write cadence**: per-germination-cycle (triggered by agent lifecycle events)
- **Query pattern**: custodian/origin filters + pagination (list operations)

Option A (vendor RW mirror) rejected — ADR-2605172000 mandates rw-free.

## What this package IS / ISN'T

**IS**:
- Reference impl of all 3 canonical houshi lexicons on Option B (PDS XRPC).
- Spore storage + custody chain + germination revival flow.
- Client-side revivalKey validation boilerplate.

**ISN'T**:
- A deployed Worker (scaffold-only).
- Actual kobo agent bytecode serialization — blob_cbor is opaque to houshi.
- Quorum consensus logic — this is just the record layer.

## Related

- [ADR-2605203000](../../../90-docs/adr/2605203000-rw-free-write-target-options.md) — Phase E write-target options
- [ADR-2605111200](../../../90-docs/adr/2605111200-cf-worker-edge-only-no-rw-connection.md) — CF Worker edge-only
- [ki rw-free](../../etzhayyim-project-ki/rw-free/) — Option B reference (4/4 ✓)
- [hanrei rw-free](../../etzhayyim-project-hanrei/rw-free/) — Option B reference (31/31 ✓)
