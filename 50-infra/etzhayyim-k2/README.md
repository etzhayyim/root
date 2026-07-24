# etzhayyim-k2 — K2 ecosystem on-chain components

**Status**: Phase β P0 landed — KarmaAnchor + CohortLifecycle Foundry contracts + tests + deploy script. Bundler / RebirthGate (zk-SNARK) / Filecoin pin pending.
**Design**: ADR-2605212040 (chain / bundler / zk / Filecoin / K2-vs-yobel)
**Tracking**: ADR-2605211950 Open Item (2)
**Originating ADRs**: vendor ADR-2604261830 (ethereum-anchored-wasm-bpmn-runtime) + ADR-2604262100 (erc725-erc8004-k8s-ipfs-agent-runtime)

## Phase β P0 — what landed

- `contracts/src/KarmaAnchor.sol` — Council-owned daily Merkle-root + IPFS CID anchor per epoch. Inline `verifyLeaf` for sorted-pair proof verification (OZ-compatible). No upgrade, no pause.
- `contracts/src/CohortLifecycle.sol` — Council-owned cohort state machine (Genesis / Active / Fissioned / Decommissioned / Resumed) with fission parent ↔ children edges + decommission reason hash. Used by yobel and other scriptural consumers via `slugHash → cohortId`.
- `contracts/script/Deploy.s.sol` — `run(councilSafe)` for testnet/mainnet + `runLocal()` for Anvil.
- `contracts/test/{KarmaAnchor,CohortLifecycle}.t.sol` — 22 tests (10 anchor + 12 lifecycle). All passing locally.
- `contracts/lib/forge-std` submodule.

## Phase β P1+ — what's next

- Base Sepolia testnet deploy (mirror of the etzhayyim-authz runbook; `forge script ... --rpc-url base_sepolia`).
- ERC-4337 bundler (rundler) — k8s deploy. Container image + manifests.
- RebirthGate zk-SNARK — Noir circuits + Solidity verifier (PLONK / Honk).
- Filecoin pin client — web3.storage UCAN wrapper, with redundant ipfs-pinner Tier 1.
- yobel refactor (`orgs/etzhayyim/com-etzhayyim-yobel/cells/release_settlement/`) to use K2 cohort primitives.

## Why this directory exists

Per ADR-2605211950 (substrate centralization axis), all **on-chain
mutation** and **IPFS pinning** are etzhayyim-exclusive. The K2
ecosystem currently lives partly in the vendor repo and partly
on-chain via the private 260425 chain; under the substrate axis the
chain-touching components migrate here while the off-chain compute
(k8s pods, BPMN engines, Kotoba/Datomic projections) stays vendor.

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
   a `yobel` cohort actor under `orgs/etzhayyim/com-etzhayyim-yobel/`. Resolve the
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
