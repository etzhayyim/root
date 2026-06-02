# etzhayyim-projector-did-web

Cloudflare Worker that serves the **DID Document for `did:web:projector.etzhayyim.com`** at the spec-required resolution endpoint:

```
https://projector.etzhayyim.com/.well-known/did.json
```

## What this DID identifies

The off-chain actor that:

1. Subscribes to the PDS firehose (`com.atproto.sync.subscribeRepos` on `pds.etzhayyim.com`).
2. Projects each commit into a per-collection AT-Protocol MST shard (`@atproto/repo`).
3. Flushes CAR files at the configured boundary (`<dataDir>/<shardKey>/<rootCid>.car`).
4. Emits `com.etzhayyim.substrate.shardSnapshot` AT Records under this DID with `phase: 2`, `rootCid`, and `snapshotCid`.

Runtime: [`50-infra/mst-projector/`](../mst-projector/) — Stage 3 of [ADR-2605171800](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md).

## Why a separate DID

- The mst-projector is a distinct actor from the PDS host (`did:web:pds.etzhayyim.com`) and from end-user adherents. Its records carry a public trail of which projector emitted which shard, so replication-by-replay across multiple projectors can converge on identical `rootCid`s and any third party can audit.
- Service entry routes resolvers to `pds.etzhayyim.com` — that's where the actor's records actually live; the projector subdomain only hosts the DID Doc.

## Files

| File | Purpose |
|---|---|
| `did.json` | The DID Document. Declares `id`, `alsoKnownAs`, `service[AtprotoPersonalDataServer]`. |
| `src/worker.ts` | Worker fetch handler. Serves did.json on GET/HEAD; 405 / 404 otherwise. |
| `wrangler.toml` | Route binding `projector.etzhayyim.com/.well-known/did.json`. |
| `package.json` | wrangler + types. |
| `tsconfig.json` | `resolveJsonModule` for the did.json import. |

## did.json (v1)

Minimal AT-Protocol DID Doc. `verificationMethod` is empty — the actor signs nothing locally; record creates land at `pds.etzhayyim.com` and are signed by the PDS at the TLS + DID-binding layer.

Future: add `verificationMethod` entries if the projector is ever extended to publish externally-signed receipts (e.g., a peer-projector federation handshake).

## Deploy

```bash
cd 50-infra/etzhayyim-projector-did-web
npm install      # first-time only
wrangler deploy
```

After deploy:

```bash
curl -i https://projector.etzhayyim.com/.well-known/did.json | head -5
# HTTP/2 200
# content-type: application/did+json; charset=utf-8

curl https://dev.uniresolver.io/1.0/identifiers/did:web:projector.etzhayyim.com
# Universal Resolver returns the DID Document
```

## DNS

`projector.etzhayyim.com` requires an AAAA record on the `etzhayyim.com` zone. The Worker route binding takes over the `/.well-known/did.json` path; other paths return 404 (intentional — the projector runtime is internal to the Mac mini fleet and exposes nothing via HTTPS).

Pattern follows [`50-infra/etzhayyim-did-web/`](../etzhayyim-did-web/) (the root DID Worker for `did:web:etzhayyim.com`).
