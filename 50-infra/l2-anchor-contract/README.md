# l2-anchor-contract

**Stage 5a of [ADR-2605171800](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md).** Solidity smart contract on Base L2 that accepts MST root anchoring. Immutable append-only log of `(rootCid, ipfsCid, blockNumber, anchorerDid)` tuples — the public, censorship-resistant record of "etzhayyim's state at time T".

## What it does

```
anchor-cron ───▶ EtzhayyimAnchor.anchor(rootHash, ipfsCid, batchSize)
                 │
                 ├─ emit Anchored(rootHash, ipfsCid, blockNumber, sender)
                 └─ store in mapping(rootHash => AnchorEntry)
                              ▲
                              │
                  any reader ─┘  via getAnchor(rootHash) or events filter
```

## Why on-chain

- **Tamper-evidence**: once anchored, the rootHash cannot be removed or changed.
- **Public timestamping**: the Base block number is the authoritative "when was this state real".
- **Third-party verifiability**: any client with Base RPC can query Anchor events without trusting our PDS or IPFS pinning.
- **Cheap on Base**: ~$0.001 per anchor tx. With batch anchoring (one root per 1000 records or 60s), total cost ≈ $1/day for the full open-* fleet at projected scale.

## Why immutable, no updates

The contract has **no admin function**. No `setAdmin`, no `pause`, no `upgrade`. Once deployed, the only operation is `anchor(...)`. This is the trust assumption: the contract code itself is the only governance.

Rationale:
- An "admin" function would re-introduce the centralized intermediary that ADR-2605172000 + 2605172100 explicitly eliminate.
- If the contract logic needs to change, deploy a new contract; the SDK's `anchorContract` config points to the active one. Old anchors remain valid on the old contract; new anchors land on the new.

## Status

**Scaffold v0.0.0**. Solidity source + Foundry config. Not yet deployed.

## Layout

```
l2-anchor-contract/
├── README.md
├── foundry.toml
├── src/
│   └── EtzhayyimAnchor.sol
├── test/
│   └── EtzhayyimAnchor.t.sol
├── script/
│   └── Deploy.s.sol
└── .gitignore
```

## Deployment

```bash
# Foundry must be installed: https://book.getfoundry.sh/getting-started/installation
forge install
forge build
forge test

# Deploy to Base Sepolia (testnet first)
forge script script/Deploy.s.sol:Deploy \
  --rpc-url $BASE_SEPOLIA_RPC \
  --broadcast \
  --private-key $DEPLOYER_PRIVATE_KEY \
  --verify --etherscan-api-key $BASESCAN_KEY

# Mainnet deploy after testnet validation
forge script script/Deploy.s.sol:Deploy \
  --rpc-url https://mainnet.base.org \
  --broadcast \
  --private-key $DEPLOYER_PRIVATE_KEY \
  --verify --etherscan-api-key $BASESCAN_KEY
```

After deploy, update [`deps.toml [platform.operating_entity].anchorContract`] with the deployed address.

## See also

- [ADR-2605171800](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md) — pipeline
- [ADR-2605172000](../../90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md) — substrate
- `../anchor-cron/` — the off-chain caller
- Base docs — https://docs.base.org/
- Foundry book — https://book.getfoundry.sh/
