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
`publish-actor-records.mjs --put-kv`, and `wrangler deploy`.

For the kotoba pull tier, set `KOTOBA_ENDPOINT` in `wrangler.toml` to the etzhayyim
kotoba read surface, then `node scripts/publish-actor-records.mjs --ingest-kotoba`.

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
npm test                                   # did-web: car + erc725 (node:test)
node 50-infra/e7m-wasm-runner/ ; npm test  # runner
(cd 20-actors/ameno && npm test)           # ameno: loader + panel
```
