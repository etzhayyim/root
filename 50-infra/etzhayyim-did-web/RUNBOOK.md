# etzhayyim-did-web — operator runbook

Operator-gated enablement for the apex Worker. Code is shipped + tested; these
steps require Cloudflare / chain credentials and so are run by an operator. Per
ADR-2606013800 / 2606014500 / 2606014600 / 2606015200.

## 1. Promote did.json/getProfile to the KV (then kotoba) source

By default the Worker serves the **compiled `INFRA_ACTORS` fallback** (identical
output to KV/kotoba — same `toDidDoc`/`toGetProfileView` mappers). To make the
kotoba `actors-v1` graph the live source:

```bash
cd 50-infra/etzhayyim-did-web
wrangler login                 # Cloudflare auth
npm run enable-kv              # creates ACTOR_KV, publishes records, deploys
```

`enable-kv` runs `wrangler kv namespace create ACTOR_KV`, appends the
`[[kv_namespaces]]` binding to `wrangler.toml`, runs
`publish-actor-records.cljs --put-kv`, and `wrangler deploy`.

For the kotoba pull tier, set `KOTOBA_ENDPOINT` in `wrangler.toml` to the etzhayyim
kotoba read surface, then `npx nbb scripts/publish-actor-records.cljs --ingest-kotoba`.

## 2. First-party trustless IPFS gateway

The `/ipfs/<cid>` gateway verifies bytes against the CID (raw direct, dag-pb via
CAR) regardless of upstream, so any gateway is safe. To serve etzhayyim-pinned
content, set in `wrangler.toml [vars]`:

```toml
IPFS_GATEWAYS = "https://<etzhayyim-kotoba-or-ipfs-pin>/ipfs/{cid}"
```

(Default, empty, uses dweb.link + ipfs.io.)

## 3. On-chain ERC725 verificationMethod

Once `EtzhayyimAuthz` is deployed to Base (ADR-2605212030 Phase B), set in
`wrangler.toml [vars]`:

```toml
AUTHZ_CONTRACT_ADDRESS = "0x…"
BASE_RPC_URL = "https://…base-rpc…"
CHAIN_ID = "8453"           # Base mainnet (or 84532 Sepolia)
```

The Worker then reads `resolveDwebHandle(keccak256("<handle>.etzhayyim.com"))` and
mirrors the active key into each actor's `verificationMethod` (never minted
server-side — ADR-2605231525). Until then it stays `[]` (TLS trust holds).

## 4. T2 mesh execution (donated node)

A donated kotoba/e7m node runs large (dag-pb) componentize-py actors:

```bash
node 50-infra/e7m-wasm-runner/runner.mjs --did did:web:etzhayyim.com:actor:watatsuna
```

It resolves → CAR-verifies → jco-runs the component. Exposing the result over
libp2p `/x/etzhayyim/xrpc/1.0` is the remaining transport wiring.

## Tests

```bash
npm run test:cljs                          # bb: did-web router / CLJC ownership (incl. /organism)
npm test                                   # did-web: car + erc725 (node:test)
node 50-infra/e7m-wasm-runner/ ; npm test  # runner
(cd 20-actors/ameno && npm test)           # ameno: loader + panel
```

The CLJC-owned public surfaces currently include `/`, `/organism`,
`/system-dynamics`, and `/actor/<handle>/system-dynamics`, all rendered without
`sh` wrappers in the bb test path.

`/organism` is rendered by cljs/Hiccup in `cljs/src/did_web/core.cljs`. The
standalone `public/organism/index.html` entrypoint has been retired; keep the
JSON snapshots under `public/organism/*.json` current instead of editing a
separate HTML file.

## kotoba browser-publish (member-signed feed)

The feed/profile reads + post/like/reply writes run in the browser kotoba-wasm
node; signed blocks are published to this Worker. Operational notes:

- **Always `wrangler deploy` after `wrangler secret put`.** `secret put` can
  redeploy a *stale* bundle, which silently reverts the local publish routes
  (`/xrpc/com.etzhayyim.apps.kotoba.block.{put,has}`, `.root`) to the kotoba
  upstream proxy (403). A fresh `wrangler deploy` from source restores them.
- **`KOTOBA_ATTEST_KEY`** (Worker secret, base64 32 bytes): the oversight key
  that AES-GCM-encrypts the raw client IP in the suppressable edit-attestation
  log (`kattest:<graph>:<root>`). Mirrored in macOS Keychain
  (`security find-generic-password -a KOTOBA_ATTEST_KEY -s etzhayyim -w`). Absent
  → only a salted hash + /24 prefix are stored (pseudonymous). IP is NEVER put
  in the immutable IPFS blocks (erasable by deleting the KV attestation).
- **`KOTOBA_ROOT`** Durable Object = the authoritative published head per graph
  (atomic CAS). Migration tag `v1`. To regenerate the genesis blocks/root:
  `./scripts/build-kotoba-wasm.sh && node scripts/gen-kotoba-blocks.mjs`.
- Block/root serving: genesis blocks are static (`public/kotoba/blocks/<cid>`);
  post-genesis blocks come from KV via the Worker fallback. Re-publishing only
  sends the delta (`block.has`).
