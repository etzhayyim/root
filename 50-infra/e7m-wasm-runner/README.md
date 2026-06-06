# @etzhayyim/e7m-wasm-runner

Kotoba-premise WASM-actor **deploy + run** — Cloudflare-free. Per
[ADR-2606015200](../../90-docs/adr/2606015200-wasm-actor-runtime-round-2.md) (run)
and [ADR-2606064600](../../90-docs/adr/2606064600-e7m-kotoba-premise-ipfs-deploy.md)
(deploy).

A WASM actor is just a content-addressed `.wasm` on IPFS. Its **CID is the only
trust anchor** — every fetch is re-verified against it before execution, no server
key ([ADR-2605231525](../../90-docs/adr/2605231525-no-server-key.md)). The apex
Cloudflare Worker's `/ipfs/<cid>` is one optional gateway, not a dependency.

```
.wasm ──deploy──▶ IPFS (bytes) + kotoba Datom log (binding) ──run──▶ verify CID ──▶ execute
```

## Deploy (`deploy.mjs`)

```
node deploy.mjs --file actor.wasm --actor tsumugi \
  [--pin kubo|pinner|none] [--kubo http://127.0.0.1:5001] \
  [--pinner-dir /data/mst-projector] [--graph com.etzhayyim.tsumugi] \
  [--kotoba http://127.0.0.1:8077] [--out actor.deploy.json]

# write the kotoba binding (operator-gated; omit the token for a dry run):
KOTOBA_TOKEN=<at-session-jwt> node deploy.mjs --file actor.wasm --actor tsumugi --pin kubo
```

Pipeline: **content-address** (`wasmcar.mjs` → raw `bafkrei…` single-block, or
dag-pb `bafybei…` multi-block CAR) → **pin to IPFS** → **register** the
`actor/wasm-cid` binding in the canonical Datom log → emit a gateway-independent
`*.deploy.json` manifest (carries the `EtzhayyimWasmComponent` did.json service
hint).

| `--pin`    | what it does                                                                                  |
|------------|-----------------------------------------------------------------------------------------------|
| `kubo`     | POST the CAR to a local/LAN kubo node (`/api/v0/dag/import`); assert the root == our CID.      |
| `pinner`   | drop `<dataDir>/<urlenc(shardKey)>/<cid>.car` for the [ipfs-pinner](../ipfs-pinner/) daemon.   |
| `none`     | compute CID + manifest only (CI / dry run).                                                    |

Without `KOTOBA_TOKEN` the kotoba leg is a **dry run** (no-server-key): the
manifest shows the binding it *would* append.

## Run (`runner.mjs`, `serve.mjs`)

```
node runner.mjs --cid bafkrei…                  # fetch from IPFS (kubo-local first), verify, run
node runner.mjs --did did:web:etzhayyim.com:actor:tsumugi --kotoba http://127.0.0.1:8077
E7M_IPFS_GATEWAYS=http://127.0.0.1:8080,https://ipfs.io node runner.mjs --cid bafkrei…
node serve.mjs --port 8787                       # GET /xrpc/com.etzhayyim.actor.run?actor=<did|handle>
```

Gateways are **kubo-local-first by default** (not Cloudflare); override with
`E7M_IPFS_GATEWAYS` or `--gateways`. `--did` resolution is **kotoba-first** when
`--kotoba`/`KOTOBA_URL` is set (reads `actor/wasm-cid` straight from the Datom
log), with did.json as fallback.

## Modules

| file                  | role                                                                       |
|-----------------------|----------------------------------------------------------------------------|
| `wasmcar.mjs`         | CAR/CID **encoder** — inverse of `etzhayyim-did-web/src/{cid,car}.ts`.      |
| `deploy.mjs`          | deploy orchestrator + CLI (`e7m-wasm-deploy`).                              |
| `kotoba-register.mjs` | `kg.ingest_batch` body (WasmActorImage + `actor/wasm-cid` binding) + POST.  |
| `runner.mjs`          | resolve → CID/CAR-verify → run; gateway-agnostic, kotoba-first DID resolve. |
| `serve.mjs`           | HTTP XRPC serving surface (T2 donated-mesh node).                           |

## Test

```
npm test     # node --experimental-strip-types --test tests/*.test.mjs  (19/19)
```

## Honest R0

Single-block raw CIDs are byte-identical to `ipfs add --cid-version=1
--raw-leaves`. Multi-block dag-pb CIDs are a *flat* DAG (raw leaves under one
root) — internally consistent and kubo-round-trippable, not claimed bit-identical
to `ipfs add` for deep DAGs (most edge actors are single-block). Live kubo pinning
and kotoba writes are operator-gated. No libp2p transport yet (HTTP + IPFS
gateway).
