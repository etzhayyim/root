# etzhayyim-atproto-pds-clj

> **Status: `canonical` (record layer) — per ADR-2606242330** (PDS consolidation).
> The single canonical PDS for `atproto.etzhayyim.com`: clj/bb over the kotoba
> Datom log, with a from-scratch atproto repo/federation codec. AppView = aozora.

An **independent** atproto Personal Data Server for `atproto.etzhayyim.com`,
written in **Clojure** (babashka). It breaks the dependency where
`atproto.etzhayyim.com` was a byte-identical alias of the gftd.ai PDS worker
(`did:web:atproto.gftd.ai`, RisingWave/TypeScript). This server reuses **none** of
that code, points at **no** `*.gftd.ai` endpoint, and implements the atproto repo
format (DAG-CBOR / CIDv1 / MST / signed commit / CAR) **from scratch — no SDK**.

## Identity (independent)
- DID: `did:web:atproto.etzhayyim.com`; `availableUserDomains`: `["etzhayyim.com"]`
- AppView / Chat: `bsky.etzhayyim.com` / `chat.etzhayyim.com`
- The did:web document publishes the repo signing key as an atproto `Multikey`
  (`#atproto`, `z6Mk…`), so a relay can verify the repo commit `sig`.

## Storage (pick one, via env)
Records are an append-only **kotoba Datom log** (content-addressed EAVT,
ADR-2605262130 / 2605312345); repo state is the materialization of the log.
- `KOTOBA_URL`        → persist to the live kotoba engine (`store.clj` `KotobaStore`).
- `PDS_STORE_PATH`    → **durable on-disk** EDN journal, replayed on boot (`DurableStore`) — survives restart, no external service.
- neither             → in-process `MemStore` (ephemeral; local/dev + tests).

Blobs (opaque bytes) are content-addressed under `PDS_BLOB_DIR` (CIDv1 raw).
Accounts (handle → did + PBKDF2 password) live in `PDS_ACCOUNTS_FILE`. The commit
signing key is persisted (present-only) at `PDS_SIGNING_KEY_FILE`.

## Layout
| path | role |
|---|---|
| `src/etzhayyim/pds/config.clj`  | identity + endpoints + env config |
| `src/etzhayyim/pds/datom.clj`   | vendored kotoba Datom-log + tiny datalog `q` |
| `src/etzhayyim/pds/util.clj`    | TID rkeys, base32, content CID, timestamps |
| `src/etzhayyim/pds/store.clj`   | `PdsStore` protocol + `MemStore` / `DurableStore` / `KotobaStore` |
| `src/etzhayyim/pds/repo.clj`    | **DAG-CBOR (en/decoder) + CIDv1 + MST + Ed25519 signed commit + CAR (read/write) + did:key multibase** |
| `src/etzhayyim/pds/blob.clj`    | content-addressed blob store + blob-ref validation |
| `src/etzhayyim/pds/account.clj` | account store (PBKDF2) + HS256 session JWTs |
| `src/etzhayyim/pds/xrpc.clj`    | `com.atproto.*` JSON method handlers |
| `src/etzhayyim/pds/server.clj`  | http-kit router (REST + websocket firehose) + `-main` |
| `deploy/resident/`              | LaunchDaemon + cloudflared config + RUNBOOK |

## Run / test
```bash
bb test                                        # 28 deftests / 106 assertions
PORT=9911 PDS_STORE_PATH=./repo.edn bb serve
curl localhost:9911/xrpc/com.atproto.server.describeServer
curl -X POST localhost:9911/xrpc/com.atproto.repo.createRecord -H content-type:application/json \
  -d '{"repo":"atproto.etzhayyim.com","collection":"app.bsky.feed.post","record":{"$type":"app.bsky.feed.post","text":"shalom"}}'
curl localhost:9911/xrpc/com.atproto.sync.getRepo?did=did:web:atproto.etzhayyim.com -o repo.car
```
Resident deploy (self-healing LaunchDaemon on a fleet node) + the public-hostname
cutover: see `deploy/resident/RUNBOOK.md`.

## XRPC surface
- **identity**: `resolveHandle` (account-backed), `/.well-known/did.json`, `/health`
- **server**: `describeServer`, `createAccount`, `createSession`, `getSession`,
  `refreshSession`, `deleteSession`
- **repo**: `createRecord`, `putRecord` (record `$type` required), `getRecord`,
  `deleteRecord`, `listRecords` (`reverse` / `rkeyStart` / `rkeyEnd` / `cursor`),
  `describeRepo` (per-collection counts), `applyWrites` (batch), `uploadBlob`,
  `importRepo` (CAR in → MST walk), `listMissingBlobs`
- **sync (federation)**: `getRepo` (→ CAR), `getRecord`, `getBlocks`,
  `getLatestCommit`, `getRepoStatus`, `listRepos`, `getBlob`, `listBlobs`,
  `subscribeRepos` (websocket firehose — binary `#commit` frame)

Optional auth: set `PDS_REQUIRE_AUTH` to require a session Bearer on writes, scoped
so the session `sub` must own the target repo (401 / 403 otherwise).

## Conformance + what remains
The codec is verified against the canonical IPLD vector
(`cid({}) == bafyrei…y6swua`) and round-trips (encode↔decode, CAR build↔parse,
export↔import, sign↔verify, relay-verifies-from-the-served-CAR). See `MATURITY.md`
for the full scorecard. Remaining for **public** federation:
1. **Public-hostname cutover** — point `atproto.etzhayyim.com` at this PDS
   (`cloudflared tunnel login`, operator-only). RUNBOOK §2.
2. **Relay registration** — `requestCrawl` to a relay after the cutover.
3. **Incremental sync** — `getRepo` `since` once a persistent commit log exists.
