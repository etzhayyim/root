# ipfs-pinner

**Stage 4 module of [ADR-2605171800](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md).** Pins MST CAR shards (emitted by mst-projector) to IPFS so any client can fetch them by CID without trusting our infrastructure.

## What it does

```
ai.gftd.apps.substrate.mstRoot records (PDS firehose)
       │
       ▼
ipfs-pinner ──▶ read CAR from local mst-projector data volume
       │   ──▶ POST to pinning provider (Pinata / Web3.Storage / Filecoin)
       │   ──▶ verify pinned (GET /ipfs/<cid>)
       │   ──▶ emit ai.gftd.apps.substrate.ipfsPin record
       ▼
public IPFS network
```

## Why a separate pinner

mst-projector produces CAR files but doesn't pin them. Separating concerns:

- **mst-projector** = pure projection logic, no external network deps beyond PDS.
- **ipfs-pinner** = takes CARs, pushes to IPFS providers, records receipts.
- A third party can run their own pinner against the same CAR set with the same providers; receipts are publicly verifiable.

## Provider selection

| Provider | Cost | Persistence | Use case |
|---|---|---|---|
| **Pinata** | $20/mo for 1 GB pinned | as long as you pay | low-latency, fast pin |
| **Web3.Storage** | free tier 5 GB | as long as service exists | bulk pin without billing |
| **Filecoin (via Storacha)** | per-GB-month | deal-bound (1-2 years), renewable | long-term archive |
| **Self-hosted Kubo** | infra cost | you decide | full control |

Default: dual-pin to Pinata (hot) + Filecoin via Storacha (cold). Configurable via `ETZ_PINNER_PROVIDERS`.

## Status

**Scaffold v0.0.0**. Stubs only.

## Layout

```
ipfs-pinner/
├── README.md
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts        # CLI / service entry
│   ├── providers/
│   │   ├── pinata.ts
│   │   ├── web3storage.ts
│   │   ├── filecoin.ts
│   │   └── kubo.ts
│   └── emit.ts         # writes ai.gftd.apps.substrate.ipfsPin AT records
└── Dockerfile
```

## Configuration

| env | default | purpose |
|---|---|---|
| `ETZ_PINNER_PROVIDERS` | `pinata,filecoin` | comma-separated provider list |
| `ETZ_PINATA_JWT` | (none, required if pinata enabled) | Pinata API JWT |
| `ETZ_WEB3STORAGE_TOKEN` | (none, required if web3storage enabled) | Web3.Storage token |
| `ETZ_STORACHA_DID` | (none, required if filecoin enabled) | Storacha account DID |
| `ETZ_KUBO_API` | `http://127.0.0.1:5001` | local Kubo API |
| `ETZ_PINNER_DATA_DIR` | `/data/mst-projector` | shared volume with mst-projector |
| `ETZ_PINNER_DID` | `did:web:pinner.etzhayyim.com` | own DID for emitted records |

## Operational guarantees

- **Replication factor**: each CAR is pinned to at least 2 distinct providers before the `ipfsPin` record is emitted.
- **Verification**: post-pin GET from a separate gateway confirms the CID is fetchable.
- **Retry**: failed pins go to a retry queue with exponential backoff. After 5 failures, alert via paymaster solvency channel.

## See also

- [ADR-2605171800 § Stage 4](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md)
- `../mst-projector/` — upstream
- `../anchor-cron/` — downstream
