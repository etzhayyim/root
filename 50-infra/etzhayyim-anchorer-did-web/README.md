# etzhayyim-anchorer-did-web

Cloudflare Worker that serves the **DID Document for `did:web:anchorer.etzhayyim.com`** at the spec-required resolution endpoint:

```
https://anchorer.etzhayyim.com/.well-known/did.json
```

## What this DID identifies

The off-chain actor that:

1. Lists `com.etzhayyim.substrate.ipfsPin` records from `pds.etzhayyim.com`.
2. Filters out roots that already have a matching `com.etzhayyim.substrate.l2Anchor` under this DID's repo.
3. For each unanchored `rootCid`, calls `EtzhayyimAnchor.anchor(rootHash, ipfsCid, batchSize)` on Base L2 via a funded EOA.
4. Emits `com.etzhayyim.substrate.l2Anchor` receipts under this DID linking `rootCid` ↔ `txHash` ↔ `blockNumber` ↔ `ipfsPinUri`.

Runtime: [`50-infra/anchor-cron/`](../anchor-cron/) (substrate mode, `src/index-substrate.ts`) — Stage 5b of [ADR-2605171800](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md).

## Why a separate DID

- The anchorer's job is to commit content-addressed roots to a public L2; its on-chain footprint is the EOA address baked into each `Anchored` event. The DID separates the off-chain receipt log (l2Anchor records under this repo) from the on-chain footprint, so multiple anchorers can co-exist with distinct DIDs while all anchoring against the same `EtzhayyimAnchor` contract.
- A third party can audit anchor lag (ipfsPin → l2Anchor gap) by listing both collections.
- Service entry routes resolvers to `pds.etzhayyim.com` where the receipts live.

## Files

| File | Purpose |
|---|---|
| `did.json` | The DID Document. Declares `id`, `alsoKnownAs`, `service[AtprotoPersonalDataServer]`. |
| `src/worker.ts` | Worker fetch handler. Serves did.json on GET/HEAD; 405 / 404 otherwise. |
| `wrangler.toml` | Route binding `anchorer.etzhayyim.com/.well-known/did.json`. |
| `package.json` | wrangler + types. |
| `tsconfig.json` | `resolveJsonModule` for the did.json import. |

## Deploy

```bash
cd 50-infra/etzhayyim-anchorer-did-web
npm install      # first-time only
wrangler deploy
```

Verify:

```bash
curl -i https://anchorer.etzhayyim.com/.well-known/did.json | head -5
curl https://dev.uniresolver.io/1.0/identifiers/did:web:anchorer.etzhayyim.com
```

## DNS

`anchorer.etzhayyim.com` requires an AAAA record on the `etzhayyim.com` zone. Pattern follows [`50-infra/etzhayyim-did-web/`](../etzhayyim-did-web/), [`50-infra/etzhayyim-projector-did-web/`](../etzhayyim-projector-did-web/), and [`50-infra/etzhayyim-pinner-did-web/`](../etzhayyim-pinner-did-web/).

## EOA + on-chain footprint

The anchorer's EOA (signer key in the `anchor-cron` substrate-mode env) is distinct from the DID. Anchor receipts encode both:

| Field | Where |
|---|---|
| `anchorer` (`0x...` EOA) | On-chain in `EtzhayyimAnchor.anchors[rootHash].anchorer` + `l2Anchor.anchorer` AT Record field |
| `did:web:anchorer.etzhayyim.com` | Repo identifier of every emitted `l2Anchor` AT Record |

Off-chain attestation links the two; rotation policy is operator-managed.
