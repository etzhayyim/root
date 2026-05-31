# ipfs-pinner

**Stage 4 module of [ADR-2605171800](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md).** Pins MST CAR shards (emitted by mst-projector) to IPFS so any client can fetch them by CID without trusting our infrastructure.

## What it does

```
app.etzhayyim.apps.substrate.mstRoot records (PDS firehose)
       │
       ▼
ipfs-pinner ──▶ read CAR from local mst-projector data volume
       │   ──▶ POST to pinning provider (Pinata / Web3.Storage / Filecoin)
       │   ──▶ verify pinned (GET /ipfs/<cid>)
       │   ──▶ emit app.etzhayyim.apps.substrate.ipfsPin record
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

Default (Phase 1 dev): Kubo only (no API key, self-hosted, fits the
religious-corp ethos). Production must override with `ETZ_PINNER_PROVIDERS=kubo,filecoin`
(or similar dual-pin) to satisfy the replication-factor ≥ 2 invariant.

## Status

**Phase 1 (Kubo-only working)** —
- ✅ `app.etzhayyim.substrate.ipfsPin` lexicon (`00-contracts/lexicons/app/etzhayyim/substrate/ipfsPin.json`)
- ✅ Kubo provider: real `/api/v0/dag/import` + `/api/v0/pin/add` round-trip
- ✅ `buildPinRecord` + `emitPinRecord` (AtpAgent, mirrors mst-projector emit pattern)
- ✅ `discoverCars` + `pinOne` + polling loop over the shared mst-projector data volume
- ✅ Tests: 12/12 (`pnpm test`, node:test under tsx)
- ⏳ Pinata / Web3.Storage / Filecoin (via Storacha) providers — stubs remain throw-on-call

The producer side (mst-projector Phase 2) emits CAR files named by their AT-Protocol MST root CID; the pinner verifies the provider's returned CID equals the filename-encoded `rootCid` before emitting the pin record. CID mismatch is fatal.

## Layout

```
ipfs-pinner/
├── README.md
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts        # CLI / service entry + discoverCars + pinOne + pollLoop
│   ├── index.test.ts   # node:test — discoverCars walking shared volume
│   ├── providers/
│   │   ├── pinata.ts        # stub (TODO)
│   │   ├── web3storage.ts   # stub (TODO)
│   │   ├── filecoin.ts      # stub (TODO)
│   │   └── kubo.ts          # working: dag/import + pin/add
│   ├── kubo.test.ts    # node:test — kubo HTTP round-trip with mocked fetch
│   ├── emit.ts         # buildPinRecord + emitPinRecord (AtpAgent)
│   └── emit.test.ts    # node:test — record shape + required-field invariants
└── Dockerfile
```

## Configuration

| env | default | purpose |
|---|---|---|
| `ETZ_PINNER_PROVIDERS` | `kubo` | comma-separated provider list (production: `kubo,filecoin` or similar) |
| `ETZ_PINNER_MIN_PROVIDERS` | `min(providers, 2)` | replication factor floor; pinOne errors if fewer providers confirmed |
| `ETZ_PINNER_PDS_URL` | `https://pds.etzhayyim.com` | PDS where the pinner authenticates + writes pin records |
| `ETZ_PINNER_PDS_SESSION` | — | JSON `{did,handle,accessJwt,refreshJwt}` (preferred) |
| `ETZ_PINNER_PDS_AUTH` | — | JSON `{handle,password}` (fallback) |
| `ETZ_PINNER_POLL_MS` | `10000` | dataDir polling interval |
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
