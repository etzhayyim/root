# etzhayyim-k2 — migration target for K2 ecosystem on-chain components

**Status**: scaffold (no code yet)
**Tracking**: ADR-2605211950 Open Item (2)
**Originating ADRs**: vendor ADR-2604261830 (ethereum-anchored-wasm-bpmn-runtime) + ADR-2604262100 (erc725-erc8004-k8s-ipfs-agent-runtime)

## Why this directory exists

Per ADR-2605211950 (substrate centralization axis), all **on-chain
mutation** and **IPFS pinning** are etzhayyim-exclusive. The K2
ecosystem currently lives partly in the vendor repo and partly
on-chain via the private 260425 chain; under the substrate axis the
chain-touching components migrate here while the off-chain compute
(k8s pods, BPMN engines, RisingWave projections) stays vendor.

## Components in migration scope

| Component | Vendor source | etzhayyim target subdir | Notes |
|---|---|---|---|
| **KarmaAnchor.sol** | vendor Solidity contracts under `50-infra/vultr/geth-private/contracts/` (or equivalent) | `etzhayyim-k2/karma-anchor/` | Daily Merkle-root anchor of karma updates to ETH L2 (per ADR-2604262100 "L4 Blockchain anchor"). Becomes Base L2 contract under etzhayyim Foundry pipeline. |
| **ERC-4337 bundler** | vendor ops (bundler URL) | `etzhayyim-k2/erc4337-bundler/` | Bundler operation moves to etzhayyim ops. Coexists with the existing `etzhayyim-paymaster` (Foundry) under `50-infra/etzhayyim-paymaster/`. |
| **RebirthGate (zk-SNARK)** | `RebirthVerifier.sol` drafted in vendor | `etzhayyim-k2/rebirth-gate/` | zk-SNARK verifier for K2 ecosystem "rebirth" lifecycle event. Solidity + circuit artifacts. |
| **Filecoin pin** | vendor IPFS-to-Filecoin bridge | `etzhayyim-k2/filecoin-pin/` | Long-term retention pin for IPFS content (cell-runner audit logs, K2 cohort genesis records). Operationally similar to existing `50-infra/ipfs-pinner/`. |
| **K2 cohort genesis / fission contract** | vendor Solidity drafts (per ADR-2604262100 §K2) | `etzhayyim-k2/cohort/` | Cohort lifecycle (genesis, fission, resume) — chain-side only. |

## Out of scope (stays vendor)

- **K8s pod runtime** that **reads** the K2 contracts — stays vendor
  per ADR-2604262100. Vendor pods continue to use `viem` or equivalent
  read-only clients but **must not write** to K2 contracts after
  migration.
- **BPMN engine + LangServer** running K2-flavored actor lifecycle
  workflows — stays vendor. The on-chain mutation step is delegated
  to etzhayyim via XRPC (vendor pod builds the UserOp payload, etzhayyim
  bundler submits it).
- **MCP registry** for K2 agents — stays vendor (centralized service
  discovery primitive).

## Coexistence with existing etzhayyim chain infra

This directory does **not** create a parallel chain stack. It joins
the existing pieces:

| Existing etzhayyim infra | K2 component layered on top |
|---|---|
| `50-infra/etzhayyim-paymaster/` (ERC-4337 Paymaster, Foundry) | K2 bundler uses this paymaster for gas sponsorship. |
| `50-infra/etzhayyim-did-web/` (LIVE CF Worker) | K2 contracts resolve actor identity via did:web → ERC725 root (issued by `etzhayyim-authz/`). |
| `50-infra/ipfs-pinner/` (Stage 4 scaffold) | K2 Filecoin pin layer extends the IPFS pinner for long-term archival. |
| `50-infra/l2-anchor-contract/` (Stage 5a, Foundry) | KarmaAnchor reuses or sits beside the existing L2 anchor contract; sharing the same `anchor-cron` (Stage 5b) is preferred. |

## Open design questions (defer to follow-up ADR)

1. **Chain consolidation** — vendor's private 260425 chain vs.
   etzhayyim's Base L2 public mainnet. K2 may stay on a private chain
   for cohort-internal events (lower visibility), with merkle roots
   anchored to Base L2 daily. Decision pending.
2. **Bundler vendor** — operate our own ERC-4337 bundler vs. use a
   public bundler (StackUp / Pimlico / Alchemy). Cost vs. censorship-
   resistance tradeoff.
3. **zk-SNARK circuit deployment** — Groth16 vs. PLONK vs. STARK for
   RebirthGate; trusted setup ceremony required for Groth16.
4. **Filecoin storage provider selection** — direct deals (we operate
   a Boost node) vs. aggregator (web3.storage, Filebase). Cost,
   reliability, and ADR-2605172000 substrate purity all factor in.
5. **K2 vs. yobel cohort lifecycle overlap** — vendor's K2 ecosystem
   has a "fission / resume" cohort lifecycle; etzhayyim already has
   a `yobel` cohort actor under `20-actors/yobel/`. Resolve the
   overlap (one absorbs the other, or they're orthogonal layers).

## Hand-off path

When this scaffold is filled in:

1. Author etzhayyim ADR documenting K2 design decisions (chain
   selection, bundler operator, circuit toolchain, storage provider,
   K2/yobel overlap resolution).
2. Stand up `etzhayyim-k2/karma-anchor/` and `etzhayyim-k2/rebirth-gate/`
   as Foundry projects; deploy to Base Sepolia first.
3. Wire `etzhayyim-k2/erc4337-bundler/` to existing `etzhayyim-paymaster`.
4. Vendor ADR-2604261830 / ADR-2604262100 get
   `superseded_by: etzhayyim:adr-XXXXXXXXX` for the chain-mutation portions.
5. Vendor K2-mutating code paths are reframed as etzhayyim XRPC calls.
