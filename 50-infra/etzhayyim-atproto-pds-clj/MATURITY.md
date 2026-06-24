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
| **`com.atproto.repo.importRepo`** | ✅ | parse CAR → walk MST → ingest records; verified live (getRepo→importRepo roundtrip, 3 records) |
| **account + session auth** | ✅ | `createAccount` (PBKDF2) / `createSession` / `getSession` / `refreshSession` / `deleteSession` (HS256 JWT, `exp` expiry); opt-in write-auth gate (`PDS_REQUIRE_AUTH`) **scoped: session `sub` must own the repo** (401 no-session / 403 wrong-repo); verified live |
| **blob-ref integrity** | ✅ | a record referencing an absent blob is rejected (400); verified live (absent→400, real→200) |
| **identity / error envelopes** | ✅ | `resolveHandle` account-backed (registered did wins, else did:web); `describeRepo` handle/didDoc/recordCount; consistent 400/404/501 `error` envelopes; verified live |
| Signing key stable + published | ✅ | `PDS_SIGNING_KEY_FILE`; did.json `#atproto` Multikey `z6Mk…` |
| **sync read surface** | ✅ | getRepo / getRecord / getBlocks / getLatestCommit / getRepoStatus / listRepos |
| **`subscribeRepos` firehose** | ✅ | websocket; binary `#commit` frame (CAR + ops) on connect; verified live (opcode 2, header `a26174`) |
| **blob store** | ✅ | `repo.uploadBlob` (CIDv1 raw `bafkrei…`) / `sync.getBlob` (CID-verified) / `sync.listBlobs`; verified live |
| **relay-verification chain** | ✅ | relay parses the served getRepo CAR → decodes the commit → verifies `sig` from the did.json key (test; tampered fails) |
| Public-hostname cutover | ⏳ operator | `cloudflared tunnel login` → `atproto.etzhayyim.com` |
| Relay registration | ⏳ operator | `requestCrawl` to a relay after cutover |

## Tests

`bb test` — 19 deftests / 70 assertions green: independent-identity, http-layer,
durable-store-survives-restart, dag-cbor-is-spec-correct, dag-cbor-and-car-roundtrip,
federation-sync-surface (getRepo/getRecord/getBlocks/getRepoStatus + 404),
signing-key-published-and-stable, commit-signature-roundtrips,
relay-verification-chain, relay-verifies-from-served-car (parse real CAR → verify),
firehose-frame-wellformed, firehose-frame-carries-the-repo (decode #commit → CAR),
apply-writes-batch, import-repo-roundtrips (export→import 12 records),
account-and-session-auth, jwt-expiry, write-auth-gate (401 / 200 own-repo / 403 other-repo),
blob-ref-validation (400 absent blob), firehose-websocket-integration (real WS over a
socket → #commit frame → CAR), resolve-handle-account-backed, error-paths (400/404/501
envelopes), blob-store-roundtrips.

## Next maturity steps (loop)

1. `listRecords` `reverse` + `rkeyStart`/`rkeyEnd` cursor (full param surface).
2. record value sanity on write (reject non-map / missing `$type`) + a per-collection
   record count in `describeRepo`.
3. a conformance smoke against the `@atproto` CAR/commit shapes where feasible offline.
