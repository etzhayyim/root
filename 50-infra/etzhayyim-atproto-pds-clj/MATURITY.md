# etzhayyim atproto PDS — maturity scorecard

Independent clj+kotoba Personal Data Server (`did:web:atproto.etzhayyim.com`),
breaking the gftd.ai dependency. Updated by the maturity `/loop`.

## R-level: R1 (storage + sync surface complete; relay registration pending)

| Capability | Status | Evidence |
|---|---|---|
| Independent identity (no gftd) | ✅ | `describeServer` did=`did:web:atproto.etzhayyim.com`, domains=`etzhayyim.com` |
| Resident deploy (self-healing) | ✅ | LaunchDaemon on `asher` (RunAtLoad+KeepAlive), live |
| `com.atproto.repo.*` (CRUD) | ✅ | create/get/put/delete/listRecords/describeRepo |
| **Durable storage** (restart-safe) | ✅ | `DurableStore` append-only EDN journal + replay; verified write→restart→present |
| **DAG-CBOR** (deterministic) | ✅ | validated vs canonical IPLD vector `cid({})==bafyrei…y6swua` |
| **CIDv1** (dag-cbor/sha2-256) | ✅ | `cid-of-bytes`, base32 |
| **MST** (atproto layering) | ✅ | 2-zero-bits/level reference algorithm |
| **Signed commit** (Ed25519) | ✅ | `sig` over dag-cbor commit; sign/verify tested |
| **CAR v1** serialization | ✅ | header `{roots,version}` + length-prefixed blocks |
| Signing key stable + published | ✅ | `PDS_SIGNING_KEY_FILE`; did.json `#atproto` Multikey `z6Mk…` |
| **sync read surface** | ✅ | getRepo / getRecord / getBlocks / getLatestCommit / getRepoStatus / listRepos |
| **`subscribeRepos` firehose** | ✅ | websocket; binary `#commit` frame (CAR + ops) on connect; verified live (opcode 2, header `a26174`) |
| **blob store** | ✅ | `repo.uploadBlob` (CIDv1 raw `bafkrei…`) / `sync.getBlob` (CID-verified) / `sync.listBlobs`; verified live |
| **relay-verification chain** | ✅ | a relay reconstructs the key from the did.json multibase + verifies the commit `sig` (test; tampered fails) |
| Public-hostname cutover | ⏳ operator | `cloudflared tunnel login` → `atproto.etzhayyim.com` |
| Relay registration | ⏳ operator | `requestCrawl` to a relay after cutover |

## Tests

`bb test` — 12 deftests / 48 assertions green: independent-identity, http-layer,
durable-store-survives-restart, dag-cbor-is-spec-correct, federation-sync-surface
(getRepo/getRecord/getBlocks/getRepoStatus + 404), signing-key-published-and-stable,
commit-signature-roundtrips, firehose-frame-wellformed, relay-verification-chain
(multibase→key→verify + tamper-fails), blob-store-roundtrips.

## Next maturity steps (loop)

1. wire `uploadBlob`/`getBlob` into the live record path (blob ref validation on
   createRecord; `getBlob` auth) + a `listBlobs`-since cursor.
2. `com.atproto.repo.applyWrites` (batch) + `com.atproto.repo.importRepo` (CAR in).
3. an HTTP-level firehose integration test (connect → parse the `#commit` body's
   CAR → confirm the record block is present).
