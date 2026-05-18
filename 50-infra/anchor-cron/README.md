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

**v0.1.0 implemented**. sidecarClient.ts + pending.ts + submit.ts + index.ts all real. Local-anvil-validated against `0x5fbdb2315678afecb367f032d93f642f64180aa3`. Base sepolia / mainnet pending an `EtzhayyimAnchor` deploy to those chains.

## Layout

```
anchor-cron/
├── README.md
├── package.json
├── tsconfig.json
├── Dockerfile             # K8s CronJob image (multi-stage build)
├── k8s/cronjob.yaml       # CronJob + ServiceAccount manifest
└── src/
    ├── index.ts           # cron entry — runs one tick
    ├── sidecarClient.ts   # msgpack + Unix-socket framing for the checkpointer wire protocol
    ├── pending.ts         # anchor_pending → PendingRoot[] with rootHash computed
    └── submit.ts          # viem walletClient.writeContract → EtzhayyimAnchor.anchor()
```

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
