# anchor-cron

**Stage 5b of [ADR-2605171800](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md).** The off-chain scheduled job that collects MST root + IPFS pin receipts and submits them as batched `anchor()` calls to [EtzhayyimAnchor](../l2-anchor-contract/) on Base L2.

## What it does

```
ai.gftd.apps.substrate.mstRoot   ┐
+ ai.gftd.apps.substrate.ipfsPin │ (firehose subscribe)
                                 ▼
anchor-cron (every 60s, or when ≥ 100 pending) ───▶
   1. read pending (rootCid, ipfsCid, batchSize) from PDS
   2. compute rootHash = sha256(ipfsCid bytes)
   3. EtzhayyimAnchor.anchor(rootHash, ipfsCid, batchSize) via viem walletClient
   4. wait for 3 confirmations
   5. emit ai.gftd.apps.substrate.anchored record (txHash, blockNumber, rootHash)
   6. mark pending as done
```

## Why batched

- Base L2 charges ~$0.001 per tx. Anchoring every individual record is fine cost-wise (~$1/day for the projected fleet) but wasteful.
- The mst-projector already batches at the shard level (flush every 1000 records or 60s). Each batched mstRoot becomes one anchor() call.
- If projection volume spikes (e.g., bulk seed of 18k unispsc_agents), anchor-cron pulls multiple roots in one cron tick and serializes them as separate sequential txs.

## Status

**Scaffold v0.0.0**. Stubs only.

## Layout

```
anchor-cron/
├── README.md
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts        # cron entry — runs the tick
│   ├── pending.ts      # read pending mstRoot + ipfsPin records from PDS
│   ├── submit.ts       # viem walletClient.writeContract to EtzhayyimAnchor
│   └── emit.ts         # write ai.gftd.apps.substrate.anchored receipt records
└── Dockerfile          # K8s CronJob image
```

## Configuration

| env | default | purpose |
|---|---|---|
| `ETZ_ANCHOR_CONTRACT` | (none, required) | deployed EtzhayyimAnchor address |
| `ETZ_ANCHOR_RPC_URL` | `https://mainnet.base.org` | Base L2 RPC |
| `ETZ_ANCHOR_DID` | `did:web:anchor.etzhayyim.com` | own DID for receipt records |
| `ETZ_ANCHOR_SIGNER_KEY` | (none, required) | private key for the anchorer EOA (or Smart Account session key) |
| `ETZ_ANCHOR_CONFIRMATIONS` | `3` | block confirmations before emit |
| `ETZ_ANCHOR_BATCH_MAX` | `10` | max pending roots per tick |

## Solvency

Per ADR-2605172100, the etzhayyim Paymaster operates from a similar account and uses the same fee-skim mechanism. The anchor-cron's signing account is separately funded — typically by:

1. Initial seed (10-100 USD worth of ETH on Base)
2. Top-up cron (separate) from the paymaster's fee skim account
3. Alert when balance < 7 days of operation

## See also

- [ADR-2605171800 § Stage 5](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md)
- `../l2-anchor-contract/` — the on-chain target
- `../etzhayyim-paymaster/` — gas sponsorship for user-side payments (related but separate)
