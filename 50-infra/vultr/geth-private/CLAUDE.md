# geth-private — etzhayyim private EVM (chainId 260425)

Single-sealer Clique PoA Ethereum chain on Vultr VKE. Root identity and
settlement layer for ADR-0074 (ERC725 root identity, credits ERC-20, deploy
receipt registry, ERC-4337 Coinbase Smart Wallet-compatible execution
accounts with WebAuthn owners).

**Native gas token**: `neth` (symbol `NETH`, 18 decimals). Smallest unit
is `wu` (1 NETH = 10^18 wu). This is purely UI/wallet metadata — the EVM
has no on-chain string for the native token, so the 2026-04-27 rename
from `ETH/wei` did **not** require a genesis change, chain reset, or any
contract redeploy. Surfaced via the `geth-rpc-proxy` GET status page,
EIP-3085 `wallet_addEthereumChain` payloads in the yoro Smart account
panel, and `[geth_private.chain.native_currency]` in `deps.toml`.

Phase 2-A contracts deployed 2026-04-25 — see
[`contracts/ADDRESSES.md`](contracts/ADDRESSES.md) for the canonical address
table. Key picks: EntryPoint v0.6, etzhayyimActorAccount (CoinbaseSmartWallet
subclass), CoinbaseSmartWalletFactory, etzhayyimActorRegistry, GCCStablecoin
(GCC), DeployRegistry. **ERC725 root registries deployed 2026-04-26**:
etzhayyimRootIdentityRegistry and etzhayyimAgentRegistry, also listed in
`contracts/ADDRESSES.md`.

| Field | Value |
|---|---|
| chainId | **260425** (`0x3f949`) |
| Consensus | Clique PoA, 5s block period, 30k epoch |
| Sealer | `0xaFed0Cb7633EDBd26aA52658e71528309F562501` (single signer) |
| Genesis hash | `0x944c4a5e5c95ddad221cd8cb5f2356628b88de9dcebdfbbd0b84d0d8b8ef4c13` |
| Geth version | `ethereum/client-go:v1.13.15` (last release with native PoA support; v1.14+ requires external CL) |
| Cluster | Vultr VKE `vke-a61d513b-…` (lax), namespace `geth-private` |
| Node pool | `risingwave-pool-32gb` (shared with RisingWave; geth req 100m CPU / 256Mi) |
| Storage | 50 GiB Vultr Block Storage (`vultr-block-storage` SC) |
| RPC (in-cluster) | `http://geth-private.geth-private.svc.cluster.local:8545` |
| WS (in-cluster)  | `ws://geth-private.geth-private.svc.cluster.local:8546` |
| External access | `https://geth.etzhayyim.com` — CF Worker proxy (`50-infra/cloudflare/workers/geth-rpc-proxy/`) → Cloudflare Tunnel (`50-infra/vultr/cloudflared/geth-tunnel.yaml`, namespace `geth-private`, replicas=2) → in-cluster `geth-private:8545` (cutover 2026-05-07, tunnel ID `69cf11d5-001f-494c-abce-4a1422ac47d8`) |

## Layout

```
50-infra/vultr/geth-private/
├── CLAUDE.md            this file
├── .gitignore           ignores .local-secrets/
├── .local-secrets/      sealer keypair + keystore (NEVER commit)
│   ├── sealer.priv
│   ├── sealer.address
│   ├── sealer.password
│   └── sealer-keystore.json
├── manifests/
│   ├── 00-namespace.yaml
│   ├── 10-statefulset.yaml
│   ├── 20-service.yaml         ClusterIP-only (CF Tunnel is the public path post-2026-05-07)
│   ├── 40-tls-proxy.yaml       (RETIRED post-soak 2026-05-08) caddy + Vultr LoadBalancer for the legacy public path
│   ├── apply.sh                idempotent apply (re-runnable)
│   └── genesis.json            emitted by gen-sealer.mjs
└── scripts/
    └── gen-sealer.mjs   one-shot keypair + genesis generator
```

## Bring-up (one-time)

```bash
node 50-infra/vultr/geth-private/scripts/gen-sealer.mjs   # writes .local-secrets + genesis.json
bash 50-infra/vultr/geth-private/manifests/apply.sh       # creates ns/cm/secret/sts/svc
```

The script refuses to overwrite an existing `.local-secrets/sealer.priv`. To
truly start over, `rm -rf 50-infra/vultr/geth-private/.local-secrets/` and
re-run — but note that the sealer address is baked into `genesis.json`, so
this also forces a chain reset (`kubectl delete pvc data-geth-private-0`).

## Re-deploy (config changes)

```bash
bash 50-infra/vultr/geth-private/manifests/apply.sh
# kubectl rollout restart sts/geth-private -n geth-private  # if sts spec unchanged
```

ConfigMap and Secret use server-side `apply` so updates land safely. The PVC
holds chaindata across rollouts.

## Operational notes

- **Sealer key custody (CRITICAL)**: `.local-secrets/` is the working
  copy of the sealer private key. Loss = chain becomes immutable (no new
  blocks) and contracts at the addresses in `contracts/ADDRESSES.md` lose
  their owner / masterMinter / oracle. Treat this directory like a TLS
  root CA private key.
  - **Local backup (active)**: replicated to **macOS Keychain** under
    service `etzhayyim.private-chain` with accounts `SEALER_PRIV`,
    `SEALER_ADDRESS`, `SEALER_PASSWORD`, `SEALER_KEYSTORE`. iCloud
    Keychain syncs across the user's Apple devices.
    Read back: `security find-generic-password -s "etzhayyim.private-chain" -a "SEALER_PRIV" -w`
  - **Team backup (manual followup)**: the previous `etzhayyim vault` workflow
    was removed along with the etzhayyim CLI (2026-05-20). Until a replacement
    lands, mirror the sealer secrets to 1Password manually (per repo-root
    `CLAUDE.md` "Do not commit secrets" rule). macOS Keychain + 1Password
    mirror is the canonical local + team backup pair. Loss of both =
    unrecoverable chain.
- **Sealer balance**: pre-funded to `0x2 * 10^60` wu (~ 10^41 NETH-equiv).
  More than enough for gas across deploys + contract bootstraps. The sealer
  also receives priority fees but `--miner.tipthreshold` is at default (no
  meaningful tip on a private chain anyway).
- **Block production stalls**: with `--maxpeers=0 --nodiscover` the node is
  fully isolated; if the sealer pod is down, no blocks → in-flight tx stay
  pending. Running a second signer would require both manifests AND a
  Clique vote to add — defer until we actually have a second region.
- **State scheme**: default (`path`). Do **not** add `--gcmode=archive`; in
  v1.13.15 it forces the legacy `hash` scheme and refuses to read a `path`
  chaindata. Receipts (event logs) are kept regardless of gcmode, so the
  credit/deploy event tracing path works without archive mode.
- **Upgrading geth**: pinning to v1.13.15 is intentional. v1.14+ rejects
  PoA chains at startup (`only PoS networks are supported, please transition
  old ones with Geth v1.13.x`). To move past v1.13 we'd need to (a) run a
  beacon-chain stub CL alongside geth, or (b) cut over to besu/nethermind.
  Both add operational surface without value for a single-tenant chain.
- **Backup**: chaindata lives only on the PVC. State snapshots can be taken
  with `geth export` from inside the pod. Full backup loop is deferred —
  current data volume (genesis + a handful of empty 5s blocks) is tiny and
  the sealer key + genesis.json are sufficient to rebuild from scratch.

## Operations cheatsheet

```bash
# tail logs
kubectl -n geth-private logs -f geth-private-0 -c geth

# RPC port-forward
kubectl -n geth-private port-forward svc/geth-private 18545:8545
curl -X POST http://localhost:18545 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}'
# → {"jsonrpc":"2.0","id":1,"result":"0x3f949"}    # 260425

# attach an interactive geth console
kubectl -n geth-private exec -it geth-private-0 -- geth attach /data/geth.ipc
```

## Caller integration

- **authz Worker** (`60-apps/etzhayyim-project-auth/worker-authz/`) — chainId
  `ETH_PRIVATE_CHAIN_ID=260425`, RPC `ETH_PRIVATE_RPC_URL=https://geth.etzhayyim.com`.
  `getActorAccount` XRPC reads `etzhayyimActorRegistry.actorByDid` via eth_call.
- **etzhayyim CLI** (removed 2026-05-20) — previously emitted
  `DeployRegistry.recordDeploy` per `etzhayyim deploy` via `cast send` against
  `https://geth.etzhayyim.com`, signed with SEALER_PRIV from macOS Keychain. Until
  a replacement lands (e.g. `e7m chain deploy-receipt`), the recordDeploy
  side-effect must be issued manually with `cast send`.
- **Phase 2 contracts** are deployed via the Foundry project at
  `50-infra/vultr/geth-private/contracts/`. Local development uses
  `kubectl -n geth-private port-forward svc/geth-private 18545:8545` and
  points `RPC_URL=http://localhost:18545`; production-style runs target
  `https://geth.etzhayyim.com` directly.
