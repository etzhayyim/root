# anchor-cron

**Stage 5b of [ADR-2605171800](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md).** The off-chain scheduled job that walks the checkpointer sidecar's pending-anchor list and submits each MST root to [EtzhayyimAnchor](../l2-anchor-contract/) on Base L2, then records the receipts back into the sidecar's index.

## What it does

```
checkpointer sidecar (in lg-uhl-right-neural Pod)
   ├─ #commitMst writes index row (rootCid, ipfsCid, ...)
   ├─ #pinSoon stamps ipfs_pinned_at when Stage 3 completes
   └─ index row sits with anchor_tx_hash == null
                              │
                              ▼ Unix-socket IPC
anchor-cron CronJob (every 15 minutes):
   1. anchor_pending  →  list of rows
   2. for each:
        rootHash = sha256(mst_root_cid as UTF-8 bytes)
        EtzhayyimAnchor.anchor(rootHash, ipfsCid bytes, batchSize) via viem
        wait for N confirmations
   3. anchor_commit(rows + tx hashes)  →  sidecar stamps the index
```

## Why batched

- Base L2 charges ~$0.001 per tx. Anchoring every individual record is fine cost-wise (~$1/day for the projected fleet) but wasteful.
- The sidecar's `#pinSoon` already coalesces at the IPFS pin layer; cron just batches the L2 submissions.
- If projection volume spikes (e.g., bulk seed of 18k unispsc_agents), anchor-cron pulls up to `ETZ_ANCHOR_BATCH_MAX` roots in one cron tick and serializes them as separate sequential txs.

## Status

- **Sidecar mode (v0.1.0)**: sidecarClient.ts + pending.ts + submit.ts + cron.ts + index.ts all real. Local-anvil-validated against `0x5fbdb2315678afecb367f032d93f642f64180aa3`. Base sepolia / mainnet pending an `EtzhayyimAnchor` deploy to those chains.
- **Substrate mode (Phase 1)**: pendingFromPds.ts + commitToPds.ts + cron-substrate.ts + index-substrate.ts + `com.etzhayyim.substrate.l2Anchor` lexicon. End-to-end mocked-PDS coverage in tests; production deploy gated on the same `EtzhayyimAnchor` deploy + an ipfs-pinner producing real `ipfsPin` records.
- **Tests**: 45/45 (vitest, sidecar 30 + substrate 15).

## Layout

```
anchor-cron/
├── README.md
├── package.json
├── tsconfig.json
├── Dockerfile             # K8s CronJob image (multi-stage build)
├── k8s/cronjob.yaml       # CronJob + ServiceAccount manifest
└── src/
    ├── index.ts             # sidecar-mode cron entry (cell-checkpoint anchors)
    ├── index-substrate.ts   # substrate-mode cron entry (firehose-driven anchors)
    ├── cron.ts              # sidecar runTick orchestrator
    ├── cron-substrate.ts    # substrate runTickSubstrate orchestrator
    ├── sidecarClient.ts     # msgpack + Unix-socket framing for the checkpointer wire protocol
    ├── pending.ts           # sidecar mode — anchor_pending → PendingRoot[] with rootHash computed
    ├── pendingFromPds.ts    # substrate mode — list ipfsPin records, filter unanchored
    ├── commitToPds.ts       # substrate mode — emit com.etzhayyim.substrate.l2Anchor receipts
    └── submit.ts            # viem walletClient.writeContract → EtzhayyimAnchor.anchor() (shared)
```

## Substrate mode (firehose-driven, Phase 1)

Closes the substrate pipeline `mst-projector → ipfs-pinner → anchor-cron`. Reads
`com.etzhayyim.substrate.ipfsPin` records from a PDS, anchors each unique
`rootCid` to EtzhayyimAnchor, and writes `com.etzhayyim.substrate.l2Anchor`
receipts back. Sidecar mode (cell-checkpoint anchors) is unaffected.

| substrate-mode env | default | purpose |
|---|---|---|
| `ETZ_ANCHOR_PDS_URL` | `https://pds.etzhayyim.com` | PDS for reads + writes |
| `ETZ_ANCHOR_PDS_SESSION` / `ETZ_ANCHOR_PDS_AUTH` | — | resumable session OR handle+password |
| `ETZ_ANCHOR_PINNER_REPO` | (required) | DID hosting `ipfsPin` records |
| `ETZ_ANCHOR_ANCHORER_REPO` | (required) | DID under which `l2Anchor` records are written |
| `ETZ_ANCHOR_CHAIN_ID` | `8453` | EIP-155 chain id (Base mainnet / 84532 sepolia) |

Entry: `tsx src/index-substrate.ts` (or build + run `dist/index-substrate.js`).

## Configuration

| env | default | purpose |
|---|---|---|
| `ETZ_ANCHOR_CONTRACT` | (required) | deployed EtzhayyimAnchor address |
| `ETZ_ANCHOR_RPC_URL` | `https://mainnet.base.org` | Base L2 RPC |
| `ETZ_ANCHOR_SIGNER_KEY` | (required) | 0x-hex 32-byte private key for the anchorer EOA |
| `ETZ_ANCHOR_SOCKET` | `/run/etzhayyim/checkpointer.sock` | sidecar Unix socket |
| `ETZ_ANCHOR_CELL_DIDS` | (required) | CSV of cell DIDs to anchor |
| `ETZ_ANCHOR_CONFIRMATIONS` | `3` | block confirmations before commit |
| `ETZ_ANCHOR_BATCH_MAX` | `10` | max pending roots per tick |
| `ETZ_ANCHOR_WARN_BALANCE_WEI` | `0` (off) | signer-balance floor (wei). Each tick reads the signer's balance and emits a single-line stderr warning (`[anchor-cron] solvency: signer=0x.. balanceWei=.. warnBelowWei=.. action=top-up-required`) when the balance dips below this floor. Anchoring continues — the warning is so operators top up BEFORE the EOA runs dry. |

## Deploy to Base sepolia

```bash
# 1. Deploy the contract.
cd 50-infra/l2-anchor-contract
forge script script/Deploy.s.sol \
  --rpc-url https://sepolia.base.org \
  --broadcast \
  --private-key $ETZ_DEPLOYER_KEY

# 2. Record the address.
#    Edit deps.toml [platform.l2.anchor_contract] address_testnet = "0x...".

# 3. Create the signer secret.
kubectl -n mitama-udf create secret generic anchor-cron-signer \
  --from-literal=key=0x<32-byte-hex>

# 4. Build + push the image.
docker build -f 50-infra/anchor-cron/Dockerfile \
  -t ghcr.io/etzhayyim/anchor-cron:$(git rev-parse --short HEAD) .
docker push ghcr.io/etzhayyim/anchor-cron:$(git rev-parse --short HEAD)

# 5. Apply the CronJob (after editing the env to point at the new address).
kubectl apply -f 50-infra/anchor-cron/k8s/cronjob.yaml

# 6. Flip on Stage 4 inside the sidecar — uncomment ETZ_ANCHOR_CHAIN_ID
#    in 50-infra/k8s/lg-uhl-right-neural/deployment.yaml (value: "84532"),
#    then `kubectl apply` it.
```

## Local-anvil smoke

```bash
anvil --chain-id 260425  # (or use the running geth-private)
forge script 50-infra/l2-anchor-contract/script/Deploy.s.sol \
  --rpc-url http://localhost:8545 \
  --broadcast \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

ETZ_ANCHOR_CONTRACT=0x5fbdb2315678afecb367f032d93f642f64180aa3 \
ETZ_ANCHOR_RPC_URL=http://localhost:8545 \
ETZ_ANCHOR_SIGNER_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
ETZ_ANCHOR_SOCKET=/tmp/etz-sidecar-test/checkpointer.sock \
ETZ_ANCHOR_CELL_DIDS=did:test:integration \
node dist/index.js
```

## Solvency

Per ADR-2605172100, the etzhayyim Paymaster operates from a similar account and uses a fee-skim mechanism. The anchor-cron's signing account is separately funded — typically by:

1. Initial seed (10-100 USD worth of ETH on Base)
2. Top-up cron (separate) from the paymaster's fee skim account
3. Alert when balance < 7 days of operation

## See also

- [ADR-2605171800 § Stage 5](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md)
- `../l2-anchor-contract/` — the on-chain target
- `../etzhayyim-paymaster/` — gas sponsorship for user-side payments (related but separate)
