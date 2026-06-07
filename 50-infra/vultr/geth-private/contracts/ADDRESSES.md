# etzhayyim private chain — Phase 2-A deployed contracts

| Field | Value |
|---|---|
| Chain ID | 260425 |
| Native token | `neth` (symbol `NETH`, 18 decimals); base unit `wu`. Pure UI/wallet metadata — Solidity unit literal `1 ether` (= 10^18) is unchanged and continues to be used in code (e.g. `minBond = 1 ether` in ClaimStakeEscrow = 1 GCC, since GCC has 18 decimals) |
| RPC (in-cluster) | `http://geth-private.geth-private.svc.cluster.local:8545` |
| Deploy block | `0x4c6` (1222) |
| Deployer | `0xaFed0Cb7633EDBd26aA52658e71528309F562501` (sealer) |
| Compiler | solc 0.8.23, evm_version `paris`, optimizer 999_999, via_ir |
| Foundry script | `script/Deploy.s.sol:Deploy` |
| Broadcast log | `broadcast/Deploy.s.sol/260425/run-latest.json` |

## Addresses

| Contract | Address | Role |
|---|---|---|
| **EntryPoint** (ERC-4337 v0.6) | `0xD94aC1d2F7aE809287dEA27Df140baB2fc9571c5` | UserOp dispatcher, vendored from eth-infinitism v0.6.0 |
| **etzhayyimActorAccount** (impl) | `0xFd0a3ed845635DD8E316BAa8E69cC1c9d1f9f400` | CoinbaseSmartWallet subclass, EntryPoint override; serves as the implementation behind every actor's ERC-1967 proxy |
| **CoinbaseSmartWalletFactory** | `0x0B71Ffb6D6cD7e9Ca7Fa6574084B55273efb9eE5` | Canonical Coinbase factory v1.1.0, points at `etzhayyimActorAccount` |
| **etzhayyimActorRegistry** | `0xc097cC8f6dfa6f3a539b0De36E9Bb550B9AA7025` | did:etzhayyim → smart-account index. Salt = `keccak256("etzhayyim-actor", didHash)` |
| **GCCStablecoin** (GCC) | `0x8e9A5162b2800E0D19acC1708A531A3954900E21` | USDC-style ERC-20. Supply cap 1B. owner / masterMinter / pauser / blacklister = Safe (Phase 3 complete 2026-04-28) |
| **DeployRegistry** | `0x995AD6A2bb4D8916Ba036f5B2e29E7739Ee243b5` | `etzhayyim deploy` provenance ledger. owner = Safe |
| **etzhayyimRootIdentityRegistry** (ADR-0074) | `0x11405300Fb75C5CDd665B9c0Ef445F8E312e3ee8` | ERC725 root identity registry. Maps root DID hashes to `etzhayyimRootIdentity` contracts and legacy/facade DID hashes to root DID hashes. owner = Safe. Deployed 2026-04-26 via `forge script script/DeployAgentRuntimeRegistries.s.sol:DeployAgentRuntimeRegistries --rpc-url https://geth.etzhayyim.com --broadcast` — broadcast log at `broadcast/DeployAgentRuntimeRegistries.s.sol/260425/run-latest.json`. `etzhayyim_ROOT_IDENTITY_REGISTRY_ADDR` is set on the `worker-authz` Worker. |
| **etzhayyimAgentRegistry** (ERC-8004-shaped) | `0xcA3480edDAfa39c9377B83eEB18291286C8Cb865` | Agent identity, validation, and reputation registry keyed by ERC725 root DID hash. owner = Safe, `openRegistration=false`, `nextTokenId=1`. Deployed with `etzhayyimRootIdentityRegistry` on 2026-04-26. |
| **MurakumoRegistry** | `0x4E3d742ece9483f97c3094b40c4b8C7901a6E3B6` | Inference operator stake + endpoint registry. minStake = 1000 GCC. owner = Safe |
| **MurakumoEscrow v1** *(deprecated)* | `0x4Fa80146EeB115C09C5E0Fe459cdBC19AE75616F` | v1 — abandoned in place. No active callers. Replaced by v2 `0xD0DAB2…` (ERC-1271). |
| **ClaimStakeEscrow v1** *(deprecated)* | `0x7C1d83E42Ac2860eA72Ae2A373e86F67726410A7` | v1 — abandoned in place. No active callers. Replaced by v2 `0x8448Bd…` (ERC-1271 + RegoArbiter arbiter). |
| **ActorRuntimeRegistry** (ADR-2604261830) | `0x9C730960e9BF7A403E610Dca0C8a565CF655b6a1` | EVM trust anchor for WASM/BPMN/browser/LangGraph runtime artifacts, execution receipts, and actor source-chain checkpoints. owner = Safe, `openRegistration=false`, `openReceipt=true` (opened 2026-04-29 via Safe tx `0x11a9f5c03626c4ab84148221fc44282e8d6acc088a016de95cbf5b3da6ec38ae`). Deployed 2026-04-26 via `forge script script/DeployActorRuntime.s.sol:DeployActorRuntime --rpc-url https://geth.etzhayyim.com --broadcast` at block `0x5916` (22806), tx `0x7efa15dbaddb9110992f30a746e4eb18cb4cb6f0360ac3bf3c87f10eb382967c`. |
| **RegoArbiter** | `0x53E29CA12Bd77fD35926627318036c7B2BBE245d` | ECDSA-verified arbiter for ClaimStakeEscrow v2. owner = Safe. signer (settler bot EOA) managed via `setSigner`. `etzhayyim_REGO_ARBITER_ADDR` set on `worker-authz`. |
| **MurakumoAgentBridge** (ADR-2604271400) | `0xE10149ECCdF963092a0C9DC99D72C8ADb860C04c` | ERC-8004 ↔ Murakumo operator join. Bidirectional `operatorDid (bytes32) ↔ agentTokenId (uint256)` mapping over `MurakumoRegistry` + `etzhayyimAgentRegistry`. Stateless (no escrow / no slash). Deployed 2026-04-28 via `forge script script/DeployMurakumoBridge.s.sol --rpc-url https://geth.etzhayyim.com --broadcast`. Live link: `operatorDid=0xb962…346a` (murakumo.etzhayyim.com) ↔ `agentTokenId=2` (stake=1000 GCC, endpoint=https://murakumo.etzhayyim.com/v1). `etzhayyim_MURAKUMO_BRIDGE_ADDR` set on authz + murakumo Workers. |
| **ContributionRoyaltyRegistry** (ADR-2604281400) | `0x689706981d7D10D4CC8244C2BF1a4cA8b0f67cD7` | OSS/media/model/dataset contributor GCC royalty pool. oracle=sealer EOA (BPMN credit() batch), owner=Safe (registerSource governance). Seeded 1,000 GCC (tx `0xa9fd94b0763e958019795f1ec243265c24cf6a5804bc6d67b24672cf34e0a729`). Deployed 2026-04-28 via `forge script script/DeployContributionRegistry.s.sol --rpc-url https://geth.etzhayyim.com --broadcast`. Full 10K GCC top-up from Safe pending (P1 governance step). |
| **AgentRuntimeLeaseEscrow** (ADR-2604301200) | `0x3B051e395edDFFDe4b91eF5B22c8223f9c26AA09` | GCC bond escrow for autonomous agent runtime leases. Records resource/policy hashes, locks runtime bond, supports renew, hibernate, release, and owner-governed slash. gcc=GCC, treasury=Safe, owner=Safe. Deployed 2026-04-30 via `forge script script/DeployAgentRuntimeLeaseEscrow.s.sol:DeployAgentRuntimeLeaseEscrow --rpc-url https://geth.etzhayyim.com --broadcast` at block `0x151fd`, tx `0x09548efc507765f56956237d96280d113898d492fe628f97938a1dd5749f2ff7`. `AGENT_RUNTIME_LEASE_ESCROW_ADDR` set on `mitama-udf/langserver-worker`. |

## Phase 3 — Gnosis Safe multisig (2026-04-28)

Deployed via `forge script script/DeploySafe.s.sol --broadcast` with sealer key.
Owners: K1/K2/K3 (EOA, macOS Keychain `service=etzhayyim.safe-owners`). Threshold: 2-of-3.

| Contract | Address | Role |
|---|---|---|
| **Safe singleton** (v1.4.1) | `0x37A9FaAf2cb17d204DC9b699E4d73a5485652b78` | Safe logic impl |
| **SafeProxyFactory** (v1.4.1) | `0xd6627E2174Fb97164C203cB8B0dC788006C39a42` | Proxy deployer |
| **CompatibilityFallbackHandler** | `0xD23302DBf6CFace527b21Ab1eD13eF8b8CD9F96B` | ERC-1271 + ERC-165 fallback |
| **Safe proxy** (2-of-3 multisig) | `0xc0C20918372bf200faf3587eB0C6685a830daFc1` | Governance multisig — target of `MigrateOwnersToSafe` |

Owners:
- K1: `0xf0A3ef1B20815622f76F583ADa4A7339F13F32d5`
- K2: `0xE6E974283b010538eAFe91C04392AD8f0B88B95A`
- K3: `0x04dA9E781A32EC41762A36Aa85c06150D40D130F`

**Status 2026-04-28**: All contracts migrated. 8 transferred via `MigrateOwnersToSafe.execute` earlier; `etzhayyimAgentRegistry` (script had wrong address `0xbfe7…`) migrated manually via `cast send transferOwnership(safe)` (tx `0x05cca2ab…`). `arbiter` (ClaimStakeEscrow v2) and `oracle` (MurakumoEscrow v2) intentionally remain as sealer EOA — v2 uses ERC-1271 so the Safe can also sign, but the settler/oracle bot uses the fast EOA path.

**Actor runtime update 2026-04-29**: Safe 2-of-3 executed
`ActorRuntimeRegistry.setOpenReceipt(true)` in tx
`0x11a9f5c03626c4ab84148221fc44282e8d6acc088a016de95cbf5b3da6ec38ae`.
The business profit BPMN artifact `business.profit.settleOpenAdnetwork.v1`
was registered as `BpmnLangServer` version 1 with artifact id
`0xc694a912aaebf02ff456a0905e5124503eb292f9ffd58edd271496ce1d59e782`
in tx `0x7b245b5a4c9aafa4d79511b8344c15461df619f65c2b0d6d7790eedaeb2c4a6f`.

## Phase 3 — ERC-1271 escrow v2 (2026-04-28)

`ClaimStakeEscrow` and `MurakumoEscrow` redeployed with ERC-1271 support in signature
verification. Both EOA (bot/sealer ECDSA) and contract (Safe multisig) signers are now
accepted as arbiter/oracle. Old v1 contracts are abandoned (no upgrade mechanism).

| Contract | Address | Notes |
|---|---|---|
| **ClaimStakeEscrow v2** | `0x8448Bd7FC883d0735D8A2416DAd0B7e4FbFA9767` | owner=Safe, arbiter=sealer, treasury=Safe, rewardPool=Safe |
| **MurakumoEscrow v2** | `0xD0DAB2B574948d4c8Bb9cF1D751CD0C6662f484d` | owner=Safe, oracle=sealer, treasury=Safe |

Worker secrets updated: `etzhayyim_CLAIM_STAKE_ESCROW_ADDR`, `etzhayyim_MURAKUMO_ESCROW_ADDR`.

## GCC initial distribution (2026-04-28)

`masterMinter=Safe` → Safe 2-of-3 granted `configureMinter(sealer, 10M GCC)` allowance.
Sealer minted initial supply:

| Recipient | Amount | Purpose |
|---|---|---|
| Safe (`0xc0C2…`) | 5,000 GCC | reward pool + treasury buffer (ClaimStakeEscrow rewardPool/treasury) |
| Sealer (`0xaFed…`) | 1,000 GCC added (total 2,010 GCC) | testnet claim posting / distribution |

Sealer remaining minterAllowance: ~9,994,000 GCC. To distribute GCC to a user:
```bash
SEALER_PRIV=$(security find-generic-password -s "etzhayyim.private-chain" -a "SEALER_PRIV" -w)
cast send 0x8e9A5162b2800E0D19acC1708A531A3954900E21 \
  'mint(address,uint256)' <RECIPIENT> <AMOUNT_WEI> \
  --rpc-url https://geth.etzhayyim.com --private-key "$SEALER_PRIV" --legacy
```

## Read-side callers (post-deploy integration targets)

- **authz Worker** (`60-apps/etzhayyim-project-auth/worker-authz/`): inject `ETH_PRIVATE_RPC_URL` + `etzhayyim_ACTOR_REGISTRY_ADDR` so `linkEthereumVerify` can also activate / look up the actor's smart-account address. Today the link path only stores a raw EOA — Phase 2-B will additionally call `etzhayyimActorRegistry.predictAddress(didHash, owners)` and persist the resulting smart-account address as a second `linked_auth_methods` row (`provider="ethereum-actor"`).
- **yoro UI** (`60-apps/etzhayyim-project-yoro/.../svelte/src/lib/auth/`): add a "Activate actor account" action that calls `linkPasskeyAdditional` flow + collects WebAuthn pubkey, then submits to authz which calls `etzhayyimActorRegistry.activate(didHash, [packedPubkey])` via the sealer (gas sponsor for now; Phase 3 paymaster).
- **deploy CLI** (formerly `70-tools/etzhayyim/etzhayyim/deploy.go`, removed 2026-05-20): after `registerProfileToYata` succeeded, this hashed `kotodama.jsonld` + build artifacts and called `DeployRegistry.recordDeploy(...)` from sealer key. Failure was non-fatal. Re-port pending (target: `e7m actor deploy` post-hook or a Foundry script).
- **Murakumo gateway** (`60-apps/etzhayyim-project-murakumo/`): on inbound inference request, (a) caller address must `gcc.approve(escrow, deposit)` then call `MurakumoEscrow.submitJob(jobId, operatorDid, modelId, deposit, referrer)`; (b) gateway selects an operator from `MurakumoRegistry.operators(...)` and forwards the request to its endpoint; (c) on completion, gateway signs `keccak256(jobId, actualCost, escrow, chainId)` with the oracle key and submits `MurakumoEscrow.settleJob(jobId, actualCost, sig)`. If the gateway is down the caller can `MurakumoEscrow.refund(jobId)` after 5 min.
- **Murakumo operator onboarding**: each inference operator (mac mini node, future GPU partner) `gcc.approve(registry, stake)` and calls `MurakumoRegistry.register(operatorDid, payoutAddress, endpoint, capabilities, stake)`. Stake ≥ 1000 GCC. payoutAddress should be the operator's `etzhayyimActorRegistry`-issued smart-account address.

## Sanity reads

```bash
kubectl -n geth-private port-forward svc/geth-private 18545:8545 &
RPC=http://localhost:18545

# 1. ActorImpl.entryPoint() returns our deployed EntryPoint (override works)
cast call 0xFd0a3ed845635DD8E316BAa8E69cC1c9d1f9f400 'entryPoint()(address)' --rpc-url $RPC
# → 0xD94aC1d2F7aE809287dEA27Df140baB2fc9571c5

# 2. CSWFactory points at our subclass impl
cast call 0x0B71Ffb6D6cD7e9Ca7Fa6574084B55273efb9eE5 'implementation()(address)' --rpc-url $RPC
# → 0xFd0a3ed845635DD8E316BAa8E69cC1c9d1f9f400

# 3. GCC metadata
cast call 0x8e9A5162b2800E0D19acC1708A531A3954900E21 'name()(string)'        --rpc-url $RPC
cast call 0x8e9A5162b2800E0D19acC1708A531A3954900E21 'symbol()(string)'      --rpc-url $RPC
cast call 0x8e9A5162b2800E0D19acC1708A531A3954900E21 'supplyCap()(uint256)'  --rpc-url $RPC

# 4. etzhayyimActorRegistry predicting an address before activation
DID_HASH=$(cast keccak "did:etzhayyim:test")
OWNERS_BYTES=$(cast abi-encode 'f(bytes[])' '[0x000000000000000000000000aaaa00000000000000000000000000000000aaaa]')
cast call 0xc097cC8f6dfa6f3a539b0De36E9Bb550B9AA7025 'predictAddress(bytes32,bytes[])(address)' \
  $DID_HASH "[0x000000000000000000000000aaaa00000000000000000000000000000000aaaa]" \
  --rpc-url $RPC

# 5. ActorRuntimeRegistry defaults
cast call 0x9C730960e9BF7A403E610Dca0C8a565CF655b6a1 'owner()(address)' --rpc-url $RPC
# → 0xc0C20918372bf200faf3587eB0C6685a830daFc1
cast call 0x9C730960e9BF7A403E610Dca0C8a565CF655b6a1 'openRegistration()(bool)' --rpc-url $RPC
# → false
cast call 0x9C730960e9BF7A403E610Dca0C8a565CF655b6a1 'openReceipt()(bool)' --rpc-url $RPC
# → true

# 6. ERC725 root identity registry
cast call 0x11405300Fb75C5CDd665B9c0Ef445F8E312e3ee8 'owner()(address)' --rpc-url $RPC
# → 0xaFed0Cb7633EDBd26aA52658e71528309F562501

# 7. Agent registry starts empty and closed
cast call 0xcA3480edDAfa39c9377B83eEB18291286C8Cb865 'owner()(address)' --rpc-url $RPC
# → 0xaFed0Cb7633EDBd26aA52658e71528309F562501
cast call 0xcA3480edDAfa39c9377B83eEB18291286C8Cb865 'nextTokenId()(uint256)' --rpc-url $RPC
# → 1
```

## Reproducibility

Re-running `forge script script/Deploy.s.sol:Deploy --broadcast` after deploys
will fail — the existing addresses are based on deployer nonce 0..6. To
redeploy from scratch you must reset the chain (wipe the StatefulSet PVC at
`50-infra/vultr/geth-private/manifests/10-statefulset.yaml`). Don't do this
casually — every actor smart-account address baked into the off-chain
indexes (`linked_auth_methods` provider="ethereum-actor") will move.
