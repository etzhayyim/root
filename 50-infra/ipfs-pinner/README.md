# ipfs-pinner

**Stage 4 module of [ADR-2605171800](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md).** Pins MST CAR shards (emitted by mst-projector) to IPFS so any client can fetch them by CID without trusting our infrastructure.

## What it does

```
com.etzhayyim.apps.substrate.mstRoot records (PDS firehose)
       │
       ▼
ipfs-pinner ──▶ read CAR from local mst-projector data volume
       │   ──▶ POST to pinning provider (Pinata / Web3.Storage / Filecoin)
       │   ──▶ verify pinned (GET /ipfs/<cid>)
       │   ──▶ emit com.etzhayyim.apps.substrate.ipfsPin record
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
| **kotobase** | kotoba-native PSA | CAR-on-B2 off-site (durable), per-account quota | **religious-corp durable remote pin** (recommended) |
| **Pinata** | $20/mo for 1 GB pinned | as long as you pay | low-latency, fast pin |
| **Web3.Storage** | free tier 5 GB | as long as service exists | bulk pin without billing |
| **Filecoin (via Storacha)** | per-GB-month | deal-bound (1-2 years), renewable | long-term archive |
| **Self-hosted Kubo** | infra cost | you decide | full control |

Default (Phase 1 dev): Kubo only (no API key, self-hosted, fits the
religious-corp ethos). Production must override with `ETZ_PINNER_PROVIDERS=kubo,kotobase`
(or similar dual-pin) to satisfy the replication-factor ≥ 2 invariant.

### kotobase — the kotoba-native durable remote pin

[`kotobase.net`](https://kotobase.net) (`did:web:kotobase.net`, gftd infra, built on
`etzhayyim/kotoba`) is a content-addressed pin & hosting service exposing the **standard
IPFS Pinning Service API** (`POST {base}/pins`). It is the religious-corp-aligned durable
remote target to pair with local Kubo: Kubo provides the blocks, kotobase fetches the
root CID and archives the commit's blocks off-site as one CAR on Backblaze B2
(CAR-on-B2, ADR-2606042100), and content is retrievable from any IPFS gateway incl.
`https://ipfs.gftd.ai/ipfs/<cid>`.

The pinner pins **by CID** — `mst-projector` names each CAR `<rootCid>.car`, so the root
CID is the filename stem (no CAR parse), submitted to `/pins` and verified against the
returned `PinStatus`.

**Auth — no platform key is held** (the credential is minted in the member/operator's own
runtime and presented), exactly one of:
- `ETZ_KOTOBASE_JWT` → `Authorization: Bearer <jwt>` (gftd-AUTHN JWT, `sub` = tenant DID);
- `ETZ_KOTOBASE_CACAO` (base64-cbor) + `ETZ_KOTOBASE_DID` → `Authorization: CACAO <b64>` +
  `x-kotoba-did`. The CACAO must grant `kotobase:pin` over the tenant DID — the **same
  self-signed-CACAO leash** mechanism ibuki uses for its kotoba write capability
  (ADR-2606111400), here scoped to pinning rather than `datom:transact`.

Enable with `ETZ_PINNER_PROVIDERS=kubo,kotobase`. Native `ipfs` tooling can use the same
service directly: `ipfs pin remote service add kotobase https://kotobase.net <JWT>`.

## Status

**Phase 1 (Kubo-only working)** —
- ✅ `com.etzhayyim.substrate.ipfsPin` lexicon (`00-contracts/lexicons/com/etzhayyim/substrate/ipfsPin.json`)
- ✅ Kubo provider: real `/api/v0/dag/import` + `/api/v0/pin/add` round-trip
- ✅ `buildPinRecord` + `emitPinRecord` (AtpAgent, mirrors mst-projector emit pattern)
- ✅ `discoverCars` + `pinOne` + polling loop over the shared mst-projector data volume
- ✅ Tests: 21/21 (`pnpm test`, node:test under tsx)
- ✅ **kotobase provider** (`POST /pins` PSA round-trip; Bearer JWT or self-signed CACAO; gftd gateway in the receipt)
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
│   │   ├── kubo.ts          # working: dag/import + pin/add
│   │   └── kotobase.ts      # working: kotobase.net PSA POST /pins (Bearer JWT | CACAO)
│   ├── kubo.test.ts    # node:test — kubo HTTP round-trip with mocked fetch
│   ├── kotobase.test.ts # node:test — PSA round-trip + auth/CID internals with mocked fetch
│   ├── emit.ts         # buildPinRecord + emitPinRecord (AtpAgent)
│   └── emit.test.ts    # node:test — record shape + required-field invariants
└── Dockerfile
```

## Configuration

| env | default | purpose |
|---|---|---|
| `ETZ_PINNER_PROVIDERS` | `kubo` | comma-separated provider list (production: `kubo,kotobase` or similar) |
| `ETZ_PINNER_MIN_PROVIDERS` | `min(providers, 2)` | replication factor floor; pinOne errors if fewer providers confirmed |
| `ETZ_KOTOBASE_URL` | `https://kotobase.net` | kotobase PSA base (clients append `/pins`) |
| `ETZ_KOTOBASE_JWT` | — | gftd-AUTHN JWT (`Authorization: Bearer`); `sub` = tenant DID |
| `ETZ_KOTOBASE_CACAO` + `ETZ_KOTOBASE_DID` | — | self-signed CACAO (base64-cbor) granting `kotobase:pin` + tenant DID (alt to JWT) |
| `ETZ_KOTOBASE_GATEWAY` | `https://ipfs.gftd.ai` | gateway base reported in the pin receipt |
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
