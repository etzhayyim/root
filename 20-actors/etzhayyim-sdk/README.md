# @etzhayyim/sdk

RW-free substrate SDK for `etzhayyim/root` open religious-corp apps. Per **[ADR-2605172000](../../90-docs/adr/2605172000-etzhayyim-rw-free-substrate.md)**, apps under `etzhayyim/root` MUST NOT depend on RisingWave or any centralized off-chain database. This SDK wraps the primary substrate — **AT Protocol MST + IPFS + Base L2 anchor** — as one ergonomic API.

> **Status**: scaffold v0.0.0. All implementations are TODO stubs. Reference implementation lands when the first open-* app (`open-isco` candidate) ports to the SDK.

## What it replaces

| Old (RisingWave-backed) | New (SDK call) |
|---|---|
| `INSERT INTO vertex_<actor>_<kind>` | `e.write({ collection, record, blobs? })` |
| `SELECT ... WHERE` | `e.read({ collection, prefix?, cursor?, limit? })` |
| streaming materialized view | `e.subscribe({ collections })` AsyncGenerator over PDS firehose |
| tamper-evidence / audit log | `e.verify(uri)` returns Merkle proof + on-chain anchor tx |
| large blob in RW row | `WriteOpts.blobs` Map → SDK pins to IPFS, embeds CID in record |

## Quick start (target API, scaffold only)

```typescript
import { Etzhayyim } from "@etzhayyim/sdk";

const e = new Etzhayyim({
  did: "did:web:etzhayyim.com",
  pdsUrl: "https://pds.etzhayyim.com",
  ipfsGateway: "https://ipfs.etzhayyim.com",
  ipfsApiUrl: "https://ipfs-api.etzhayyim.com",
  l2RpcUrl: "https://mainnet.base.org",
  anchorContract: "0xANCHOR_ETZHAYYIM",
  signer: passkeyDidSigner,  // WebAuthn → DID-bound
});

// Write — pins blob to IPFS, then createRecord on PDS, then schedules
// MST root for next L2 anchor batch.
const receipt = await e.write({
  collection: "ai.gftd.apps.openIsco.occupation",
  record: {
    code: "2511",
    name: "Software Developer",
    major: "2",
    handbookRef: { $type: "blob" },  // SDK fills with IPFS CID
  },
  blobs: new Map([["handbookRef", handbookPdf]]),
});
// → { uri, cid, blobCids, pendingAnchor }

// Read — MST traversal, optional blob fetch.
const { records, cursor } = await e.read<Occupation>({
  collection: "ai.gftd.apps.openIsco.occupation",
  prefix: "2",   // major code prefix
  limit: 50,
});

// Verify — third-party Merkle proof against L2 anchor.
const proof = await e.verify(receipt.uri);
// → { included, anchoredAt: { txHash, blockNumber, rootCid }, merklePath }

// Subscribe — replaces streaming MV.
for await (const ev of e.subscribe<Occupation>({
  collections: ["ai.gftd.apps.openIsco.occupation"],
})) {
  console.log(ev.op, ev.uri, ev.value);
}
```

## Module layout

```
src/
├── index.ts    # Etzhayyim class, public types, re-exports
├── pds.ts      # AT Protocol PDS write/read helpers
├── ipfs.ts     # IPFS pin/fetch helpers
└── l2.ts       # Base L2 anchor contract helpers
```

Apps MUST import from `@etzhayyim/sdk` only. Direct imports of `@atproto/api`, IPFS client libraries, or `viem` from app code are prohibited (the SDK is the only seam where substrate clients are imported).

## Hard rules (enforced by ADR-2605172000 + future CI hook)

- **No `risingwave` / `kysely` / `pg` / `postgres` imports** anywhere under `etzhayyim/root/60-apps/` or `etzhayyim/root/20-actors/` (excluding this SDK itself).
- **No SQL strings** (`SELECT`, `INSERT`, `CREATE TABLE`, `mv_`, `vertex_`) outside SQL-migration test fixtures.
- **No central DB credentials** in app code or env. Identity is DID; signing is WebAuthn or operator-held private key.

## Dependencies

- `@atproto/api` — PDS write/read, firehose subscribe
- `viem` — Base L2 RPC + contract interaction
- IPFS HTTP API client TBD (`ipfs-http-client` or `helia`; chosen during reference impl)

## Versioning

Current: `0.0.0` (scaffold). API surface is **not yet stable** — every method throws "not yet implemented". The first stable cut (`0.1.0`) lands together with the first reference-impl app migration.

## See also

- [ADR-2605172000](../../90-docs/adr/2605172000-etzhayyim-rw-free-substrate.md) — substrate hard rule + per-app migration patterns
- [ADR-2605171800](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md) — pipeline this SDK packages
- [ADR-2605170900](../../90-docs/adr/2605170900-etzhayyim-root-adr-canonical-home.md) — etzhayyim/root canonical home rule

## License

Apache 2.0
