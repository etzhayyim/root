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
| **DAG-CBOR decoder + CAR parser** | ✅ | inverse codec; encode↔decode + build↔parse roundtrips tested |
| `com.atproto.repo.applyWrites` | ✅ | batch create/update/delete in one call; verified live |
| Signing key stable + published | ✅ | `PDS_SIGNING_KEY_FILE`; did.json `#atproto` Multikey `z6Mk…` |
| **sync read surface** | ✅ | getRepo / getRecord / getBlocks / getLatestCommit / getRepoStatus / listRepos |
| **`subscribeRepos` firehose** | ✅ | websocket; binary `#commit` frame (CAR + ops) on connect; verified live (opcode 2, header `a26174`) |
| **blob store** | ✅ | `repo.uploadBlob` (CIDv1 raw `bafkrei…`) / `sync.getBlob` (CID-verified) / `sync.listBlobs`; verified live |
| **relay-verification chain** | ✅ | relay parses the served getRepo CAR → decodes the commit → verifies `sig` from the did.json key (test; tampered fails) |
| Public-hostname cutover | ⏳ operator | `cloudflared tunnel login` → `atproto.etzhayyim.com` |
| Relay registration | ⏳ operator | `requestCrawl` to a relay after cutover |

## Tests

`bb test` — 16 deftests / 59 assertions green: independent-identity, http-layer,
durable-store-survives-restart, dag-cbor-is-spec-correct, dag-cbor-and-car-roundtrip,
federation-sync-surface (getRepo/getRecord/getBlocks/getRepoStatus + 404),
signing-key-published-and-stable, commit-signature-roundtrips,
relay-verification-chain, relay-verifies-from-served-car (parse real CAR → verify),
firehose-frame-wellformed, firehose-frame-carries-the-repo (decode #commit → CAR),
apply-writes-batch, blob-store-roundtrips.

## Next maturity steps (loop)

1. `com.atproto.repo.importRepo` — parse an incoming CAR, walk the MST, ingest the
   records (uses the new decoder + parser).
2. blob ref validation on createRecord/applyWrites (verify `{$type:blob}` link
   bytes resolve in the blob store) + a `listBlobs`-since cursor.
3. an HTTP-socket firehose integration test (connect → read the binary frame off
   the wire → parse the `#commit` body's CAR → confirm the record block).
