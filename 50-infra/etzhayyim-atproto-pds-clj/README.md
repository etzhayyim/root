# etzhayyim-atproto-pds-clj

> **Status: `canonical` (record layer) — per ADR-2606242330** (PDS consolidation).
> The single canonical PDS *record/translation layer* for `pds.etzhayyim.com`:
> clj/bb over the kotoba Datom log. The XRPC surface eventually moves to
> kotoba-server (ADR-2606015002 D2); the Bun PDS pod (`50-infra/k8s/atproto-pds`)
> stays `bridge-only` until this reaches server/repo/identity parity. AppView = aozora.

An **independent** atproto Personal Data Server for `atproto.etzhayyim.com`,
written in **Clojure** (babashka) on the **kotoba Datom log**. It exists to break
the current dependency where `atproto.etzhayyim.com` is a byte-identical alias of
the gftd.ai PDS worker (`did:web:atproto.gftd.ai`, RisingWave/Hyperdrive backend,
TypeScript). This server reuses **none** of that code and points at **no**
`*.gftd.ai` endpoint.

## Identity (independent)
- DID: `did:web:atproto.etzhayyim.com`
- `availableUserDomains`: `["etzhayyim.com"]`
- AppView / Chat: `bsky.etzhayyim.com` / `chat.etzhayyim.com`
- Contact / policy: `support@etzhayyim.com`, `etzhayyim.com/{privacy,terms}`

## Substrate
Records are appended to the **kotoba Datom log** (content-addressed EAVT,
ADR-2605262130 / ADR-2605312345) — not a managed SQL DB. Each write emits datoms
keyed by the at-uri `at://<did>/<collection>/<rkey>`; the repo state is the
materialization of the append-only log.

- `KOTOBA_URL` set  → records persist to the live kotoba engine (`store.clj` `KotobaStore`).
- `KOTOBA_URL` unset → in-process datom log (`MemStore`) — local/dev + tests only.

## Layout
| path | role |
|---|---|
| `src/etzhayyim/pds/config.clj` | identity + endpoints (all etzhayyim, env-overridable) |
| `src/etzhayyim/pds/datom.clj`  | vendored kotoba Datom-log + tiny datalog `q` |
| `src/etzhayyim/pds/util.clj`   | TID rkeys, base32, content CID, timestamps |
| `src/etzhayyim/pds/store.clj`  | `PdsStore` protocol + `MemStore` / `KotobaStore` |
| `src/etzhayyim/pds/xrpc.clj`   | `com.atproto.*` method handlers |
| `src/etzhayyim/pds/server.clj` | http-kit router + `-main` |
| `did.json`                     | static `did:web:atproto.etzhayyim.com` document |
| `Dockerfile` / `deploy/`       | babashka image + k8s pod + cloudflared + RUNBOOK |

## Run / test locally
```bash
bb test            # 4 tests / 23 assertions
PORT=9911 bb serve
curl localhost:9911/xrpc/com.atproto.server.describeServer
curl -X POST localhost:9911/xrpc/com.atproto.repo.createRecord -H content-type:application/json \
  -d '{"repo":"atproto.etzhayyim.com","collection":"app.bsky.feed.post","record":{"text":"shalom"}}'
```

## Implemented XRPC methods
`server.describeServer`, `server.createSession` (minimal), `identity.resolveHandle`,
`repo.createRecord`, `repo.putRecord`, `repo.getRecord`, `repo.deleteRecord`,
`repo.listRecords`, `repo.describeRepo`, plus `/.well-known/did.json` and `/health`.

## Deliberately staged (NOT yet implemented — needed for public federation)
This is a functional, independent PDS for first-party etzhayyim records. It is
**not yet** a federation-complete Bluesky PDS. Follow-ups, in order:
1. **Signed MST commits** — real Merkle Search Tree + repo `commit` signed by the
   PDS key; `com.atproto.sync.*` (getRepo/getLatestCommit/subscribeRepos/getBlocks).
2. **Spec-exact CIDv1** — dag-cbor multihash CIDs (today: sha-256 content hash for
   intra-PDS addressing only).
3. **Auth** — real JWT/OAuth session issuance + DPoP (today: minimal session stub).
4. **Account lifecycle** — `createAccount`, handle registry, `uploadBlob` + blob store.
5. **Verify `KotobaStore` wire** against the live kotoba engine at cutover.

See `deploy/RUNBOOK.md` for the deploy + DNS cutover (credential-gated).
