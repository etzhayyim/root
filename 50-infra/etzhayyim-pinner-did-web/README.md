# etzhayyim-pinner-did-web

Cloudflare Worker that serves the **DID Document for `did:web:pinner.etzhayyim.com`** at the spec-required resolution endpoint:

```
https://pinner.etzhayyim.com/.well-known/did.json
```

## What this DID identifies

The off-chain actor that:

1. Reads CAR files written by `mst-projector` to a shared data volume (`<dataDir>/<shardKey>/<rootCid>.car`).
2. Pins each new CAR to ≥1 IPFS providers (default: Kubo; production: Kubo + Filecoin via Storacha).
3. Verifies the provider's returned CID equals the filename-encoded `rootCid`.
4. Emits `com.etzhayyim.substrate.ipfsPin` AT Records under this DID with `rootCid`, `carCid`, `providers[]`, and `pinnedAt`.

Runtime: [`50-infra/ipfs-pinner/`](../ipfs-pinner/) — Stage 4 of [ADR-2605171800](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md).

## Why a separate DID

- The pinner publishes a public receipt trail; a third party can verify replication by enumerating ipfsPin records under this DID and re-pulling each `carCid` from any IPFS gateway. Distinct DID keeps that audit log from getting tangled with projector / anchorer / adherent records.
- Service entry routes resolvers to `pds.etzhayyim.com` where the records actually live.

## Files

| File | Purpose |
|---|---|
| `did.json` | The DID Document. Declares `id`, `alsoKnownAs`, `service[AtprotoPersonalDataServer]`. |
| `src/worker.ts` | Worker fetch handler. Serves did.json on GET/HEAD; 405 / 404 otherwise. |
| `wrangler.toml` | Route binding `pinner.etzhayyim.com/.well-known/did.json`. |
| `package.json` | wrangler + types. |
| `tsconfig.json` | `resolveJsonModule` for the did.json import. |

## Deploy

```bash
cd 50-infra/etzhayyim-pinner-did-web
npm install      # first-time only
wrangler deploy
```

Verify:

```bash
curl -i https://pinner.etzhayyim.com/.well-known/did.json | head -5
curl https://dev.uniresolver.io/1.0/identifiers/did:web:pinner.etzhayyim.com
```

## DNS

`pinner.etzhayyim.com` requires an AAAA record on the `etzhayyim.com` zone. Pattern follows [`50-infra/etzhayyim-did-web/`](../etzhayyim-did-web/) and [`50-infra/etzhayyim-projector-did-web/`](../etzhayyim-projector-did-web/).
