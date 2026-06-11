---
id: adr-2606064600-e7m-kotoba-premise-ipfs-deploy
title: "ADR-2606064600: e7m kotoba-premise IPFS deploy (Cloudflare-free WASM-actor deploy)"
status: proposed
doc_type: adr
topic: e7m-kotoba-premise-ipfs-deploy
authoritative: true
last_verified: 2026-06-06
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "Closes the deploy-side Cloudflare dependency; the run side was already IPFS/CID-native."
authoritative_for:
  - e7m-wasm-actor-deploy
depends_on:
  - 2606014500
  - 2606014600
  - 2606015200
  - 2606015400
  - 2606036000
  - 2605262130
  - 2605312345
  - 2605231525
related:
  - 2605171800
  - 2606013800
  - 2606015600
supersedes: []
superseded_by: []
---

# ADR-2606064600: e7m kotoba-premise IPFS deploy (Cloudflare-free WASM-actor deploy)

**Status**: proposed
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki

# Context

The WASM-actor **run** path is already kotoba/IPFS-premise and trustless: a
content-addressed `.wasm` on IPFS, fetched from any gateway, re-verified against
its CID before execution, no server key (ADR-2606014500 / 14600 / 15200 / 15400,
ADR-2605231525). The apex Cloudflare Worker's `/ipfs/<cid>` is *one* trustless
gateway, not a dependency of execution.

The **deploy** path, however, was still Cloudflare-premise. The only deploy
tooling that existed —

- `70-tools/etzhayyim-cli/deploy.go` → Docker build → push → **Cloudflare
  Containers** + `wrangler.jsonc` + `wrangler deploy` + R2 static upload, and
- `70-tools/e7m-cli/src/commands/actor.ts deploy` → `npx wrangler deploy`

— both terminate at Cloudflare. There was **no command** that takes a built
`.wasm`, content-addresses it, pins it to IPFS, and registers the binding in the
canonical kotoba Datom log. Actor CIDs were hand-authored into `INFRA_ACTORS`
(`wasmCid` field) and advertised by the Worker; deploying a new actor meant a
code edit + a Worker redeploy. The bytes lived on IPFS but the *deploy act* did
not — it lived in `wrangler`.

This is the asymmetry this ADR closes: make deploy as Cloudflare-free as run.

# Decision

Add a **kotoba-premise deploy** to `50-infra/e7m-wasm-runner/` — the mirror image
of the runner that already lives there. The pipeline is:

```
.wasm bytes
  → buildCar()          content-address (CAR + CID)
  → pin to IPFS         kubo /dag/import (live) OR drop a CAR for ipfs-pinner
  → registerInKotoba()  append the handle→CID binding to the canonical Datom log
  → <name>.deploy.json  gateway-independent manifest; run via ANY IPFS gateway
```

No Cloudflare, no Docker, no wrangler, no R2 in the path.

## 1. Content-address — `wasmcar.mjs` (the missing *write* half)

The runtime already had the *read* half: `cid.ts` (raw single-block CID verify)
and `car.ts` (multi-block dag-pb CAR verify + reassemble). `wasmcar.mjs` is the
minimal inverse — no IPFS/dag-cbor/protobuf library imported, so encoder and
verifier stay lockstep. Two layouts, picked by size, mirroring the two read
tiers:

- **single block** (≤ 256 KiB chunk): raw codec (`0x55`) → `bafkrei…` CID. This
  is **byte-identical to `ipfs add --cid-version=1 --raw-leaves`** and verifiable
  by `cid.ts::verifyRawCid` (the T1 browser-local tier). *Empirically*: the
  committed `kanae-core.wasm` (23,868 B) → `bafkreielhr6l5jy7ml5l62ncyva34lhjw52q2onwxwy6ubep4wqxjyjnie`,
  equal to `cidV1Raw(bytes)`, and the emitted CAR reassembles to the exact bytes
  via `verifyCarToBytes`.
- **multi block** (> chunk): raw leaves + one dag-pb (`0x70`) UnixFS-File root →
  `bafybei…` CID, verifiable by `car.ts::verifyCarToBytes` (the T2 mesh tier).
  *Empirically*: a 600 KB buffer → 3 leaves + 1 root, round-trips to the original.

## 2. Pin to IPFS — three Cloudflare-free modes

`deploy.mjs --pin <mode>`:

- **`kubo`** — POST the CAR to a local/LAN kubo node (`/api/v0/dag/import?pin-roots=true`),
  assert the imported root equals our CID. The religious-corp default node
  (no API key, no centralized service; ADR-2605171800 Stage 4).
- **`pinner`** — drop the CAR where the existing **ipfs-pinner** daemon discovers
  it: `<dataDir>/<encodeURIComponent(shardKey)>/<cid>.car` (the exact layout
  `discoverCars` walks). The daemon then pins to ≥2 providers (replication-factor
  invariant) and emits its `com.etzhayyim.substrate.ipfsPin` record. Offline drop,
  no live call at deploy time.
- **`none`** — compute + manifest only (CI, dry runs, air-gapped CID computation).

## 3. Register the binding — `kotoba-register.mjs` (the canonical Datom log)

Where the Cloudflare path mutated a Worker registry / wrangler config, the kotoba
path **appends a Datom** (ADR-2605312345: the Datom log is first-class canonical
state). Two `kg.ingest_batch` entities, shapes matching the wasm-sbom generator
(ADR-2606036000) so the existing purl↔CVE / SBOM joins compose:

1. `WasmActorImage` `id=<cid>` — the immutable image (codec, byteSize, blockCount,
   `wasm/ipfsUri`, agentDid, deployedAt).
2. `actor.<handle>` (graph `actors-v1`) with claim **`actor/wasm-cid=<cid>`** —
   the mutable binding the apex did.json reader already consumes (`kotoba.ts` →
   `EtzhayyimWasmComponent` service endpoint, ADR-2606013800). Deploying a new
   actor version is now an append, not a Worker redeploy.

**No-server-key** (ADR-2605231525): a write to the canonical log requires an
operator AT-session token. Without `KOTOBA_TOKEN` the registration is a **dry run**
returning the body it *would* post — the same convention every `kotoba/deploy.sh`
uses. The deploy process never holds a platform key.

## 4. Run is now Cloudflare-free by default — `runner.mjs`

`fetchVerified` previously defaulted its gateway to `https://etzhayyim.com` (the
apex Worker). It now defaults to a **kubo-local-first** ordered gateway list
(`http://127.0.0.1:8080`, then public trustless gateways `ipfs.io` / `dweb.link`),
overridable with `E7M_IPFS_GATEWAYS`, and tries each in order. The apex is no
longer special — pass it explicitly if you want it. `didToCid` gains a
**kotoba-first** resolution path: given `KOTOBA_URL` it reads the `actor/wasm-cid`
binding straight from the Datom log (`kg.entity`), with did.json as fallback. The
CID remains the only trust anchor in every path.

# Consequences

- **Deploy no longer depends on Cloudflare/Docker/wrangler/R2.** A donated mesh
  node (e7m) or a developer laptop with a kubo node can deploy and serve an actor;
  `https://etzhayyim.com` becomes an optional public gateway, removable without
  breaking deploy or run.
- **A new actor / new actor version is an IPFS pin + a Datom append**, not a code
  edit to `INFRA_ACTORS` + a Worker redeploy. The hand-authored `wasmCid` fields
  become a compiled fallback over the live kotoba binding (matching the existing
  3-tier `resolveActorRecord`: KV → kotoba → compiled).
- **SBOM/CVE chain composes for free** — the `WasmActorImage` entity is the same
  shape `wasm_sbom_gen.py` emits, so a deploy can carry (or be joined to) its
  CycloneDX SBOM and the existing `purl_vuln_match.py`.
- **19/19 tests green** in `50-infra/e7m-wasm-runner/` (4 prior + 15 new):
  CAR/CID encode↔verify round-trips (raw + dag-pb, chunk boundary, determinism),
  the ingest-body binding shape, the operator-token gate, the pinner CAR drop, an
  injected-kubo import, and the Cloudflare-free run loop (a deployed CID served by
  an injected gateway re-verifies + runs; gateway fallback; kotoba-first
  `didToCid`). End-to-end CLI verified against `kanae-core.wasm`.

## Honest R0 scope

- The **single-block raw** path is byte-identical to `ipfs add --raw-leaves`. The
  **multi-block dag-pb** path is a *flat* DAG (raw leaves under one root); it is
  internally consistent (our encoder ≡ our verifier ≡ kubo round-trip) and
  equivalent to `ipfs add` only while leaf-count fits a single UnixFS fan-out
  (no intermediate parent layer). It is **not** claimed bit-identical to
  `ipfs add` for deep DAGs. Most edge actors are single-block (T1).
- Live `kubo` pinning and the kotoba write are **operator-gated** (a running node
  + `KOTOBA_TOKEN`); the default is dry-run / offline CAR-drop.
- This adds a deploy *path*; it does not migrate the existing hand-authored
  `INFRA_ACTORS.wasmCid` entries (they remain the compiled fallback). Promoting
  kotoba to the live source for an actor is flipping `KOTOBA_ENDPOINT` on, per
  ADR-2606013800 — out of scope here.
- No libp2p transport — serving stays over the `serve.mjs` HTTP XRPC surface and
  any IPFS gateway (the libp2p `/x/etzhayyim/xrpc/1.0` wrap remains future work
  per ADR-2606015400).

# Alternatives Considered

- **Keep wrangler, add an IPFS step** — rejected; leaves Cloudflare on the deploy
  critical path, which is exactly the dependency the ask removes.
- **Pin via Pinata/web3.storage API directly from deploy** — rejected as the
  default; those are centralized + keyed. The ipfs-pinner already brokers them
  behind the religious-corp replication-factor invariant, so deploy drops a CAR
  and lets the daemon fan out. (Both remain reachable through the pinner.)
- **Use a full IPFS library (`@helia`/`ipfs-unixfs`) to build the CAR** — rejected
  for R0; a ~150-line encoder that is the literal inverse of the committed
  `car.ts` reader keeps the two provably lockstep, has zero dependencies, and runs
  unchanged under the Worker bundler and `node --experimental-strip-types`.
- **Store the binding only in did.json (Worker)** — rejected; that is the
  Cloudflare dependency. The Datom log is canonical state (ADR-2605312345); the
  Worker did.json mirrors it.

# References

- `50-infra/e7m-wasm-runner/` — `wasmcar.mjs`, `deploy.mjs`, `kotoba-register.mjs`,
  `runner.mjs` (gateway-agnostic + kotoba-first `didToCid`), `tests/`, `README.md`
- `50-infra/etzhayyim-did-web/src/cid.ts` + `car.ts` — the read half this inverts
- `50-infra/ipfs-pinner/` — the CAR-discovery + replication daemon (`pin=pinner`)
- ADR-2606014500 / 14600 / 15200 / 15400 — one-Worker-many-WASM, gateway, mesh runner
- ADR-2606036000 — wasm-sbom (ingest body shape reused)
- ADR-2605262130 / 2605312345 — kotoba canonical Datom log
- ADR-2605231525 — no-server-key
- ADR-2606013800 — actor record / did.json `actor/wasm-cid` resolution
