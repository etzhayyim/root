---
id: 2605212040-etzhayyim-k2-ecosystem-ownership-split
title: "etzhayyim K2 Ecosystem — Chain + Bundler + zk + Filecoin Ownership Decisions"
status: active
doc_type: adr
topic: etzhayyim-k2-ownership
authoritative: true
last_verified: 2026-05-21
priority: 8.0
axis: infrastructure
weight: 0.80
priority_note: "Resolves the five open design questions of the etzhayyim-k2 scaffold (ADR-2605211950 Open Item 2). Specifies which chain K2 contracts deploy to, which entity operates the ERC-4337 bundler, which zk toolchain implements RebirthGate, which Filecoin storage path is canonical, and how K2 relates to the existing yobel actor."
authoritative_for:
  - K2 KarmaAnchor + cohort lifecycle contracts on Base L2 mainnet
  - ERC-4337 bundler operation by etzhayyim (own rundler on k8s)
  - RebirthGate zk-SNARK toolchain (Noir + Barretenberg / Honk PLONK)
  - Filecoin storage path (web3.storage + redundant ipfs-pinner pin; Boost node Phase 2)
  - K2 ↔ yobel relation (K2 = technical primitive; yobel = scriptural consumer)
related:
  - "ADR-2605211950 (substrate centralization axis)"
  - "ADR-2605212030 (etzhayyim authz ERC725 root issuance)"
  - "ADR-2605171800 (langgraph MST IPFS L2 anchor pipeline)"
  - "ADR-2605192100 (etzhayyim mission charter)"
  - "ADR-2605192315 (transparent religious force)"
  - "vendor: ADR-2604261830 (ethereum-anchored-wasm-bpmn-runtime)"
  - "vendor: ADR-2604262100 (erc725-erc8004-k8s-ipfs-agent-runtime)"
depends_on:
  - "ADR-2605211950"
  - "ADR-2605212030"
  - "ADR-2605172100"
supersedes: []
superseded_by: []
---

# ADR-2605212040: etzhayyim K2 Ecosystem — Chain + Bundler + zk + Filecoin Ownership Decisions

**Status**: active
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

## Context

ADR-2605211950 routed the K2 ecosystem's on-chain components (KarmaAnchor.sol, ERC-4337 bundler, RebirthGate zk-SNARK verifier, Filecoin pin, cohort genesis / fission contract) to `50-infra/etzhayyim-k2/`. The scaffold left five design questions open:

1. **Chain consolidation** — vendor's private chain `260425` vs etzhayyim's Base L2 public mainnet.
2. **Bundler operator** — etzhayyim-operated own bundler vs public bundler (StackUp / Pimlico / Alchemy).
3. **zk-SNARK toolchain** — Groth16 vs PLONK vs STARK.
4. **Filecoin storage path** — direct Boost node vs aggregator (web3.storage / Filebase).
5. **K2 vs yobel overlap** — both touch cohort lifecycle; resolve.

This ADR settles all five. ADR-2605212030 already decided that etzhayyim runs a single chain (Base L2), so K2 inherits that.

## Decision

### D1. Chain — **Base L2 public mainnet, with off-chain log + on-chain anchor for cohort-internal events**

KarmaAnchor and all K2 cohort-lifecycle contracts deploy to **Base L2 public mainnet** (chain id `8453`). This is consistent with ADR-2605212030 (identity) and ADR-2605172100 (payments). No K2 contracts on the vendor private chain.

**Cohort-internal events** (e.g. private cohort deliberation, intra-cell coordination) that must not be publicly visible follow a two-layer pattern:

| Layer | Purpose | Storage |
|---|---|---|
| L1 — append log | full event detail | encrypted append-only log on IPFS (pinned by etzhayyim ipfs-pinner) |
| L2 — anchor | daily Merkle root of the log | on-chain KarmaAnchor contract, Base L2 |

The Merkle root is public; the leaves are encrypted under cohort-scoped keys (derived from cohort SBT). External observers see the root but not the leaves; cohort members can decrypt via the SBT membership. This satisfies ADR-2605192100 §1.12 (transparent force: full audit possible if Council multisig releases cohort keys) without putting raw deliberation drafts on a public chain.

### D2. Bundler — **etzhayyim-operated own bundler (`rundler` on etzhayyim k8s)**

The ERC-4337 bundler is operated by etzhayyim, not a third party. Implementation:

- Bundler binary: **`rundler`** (Foundry Operations, Rust ERC-4337 bundler). Mature, Apache 2.0, integrates with `etzhayyim-paymaster`.
- Deployment: k8s under `50-infra/etzhayyim-k2/erc4337-bundler/` (k8s manifests + container image). Existing etzhayyim k8s cluster.
- Gas funding: existing `50-infra/etzhayyim-paymaster/` covers UserOp gas via the anchor-batch fee skim (ADR-2605171800 Stage 5).
- Fallback: if the etzhayyim bundler is offline, UserOps may fall back to a **read-only** public bundler endpoint for emergency submission. This is configured via a single env var; default OFF.

Rationale: censorship-resistance is constitutional (ADR-2605192100 §1.12, ADR-2605192315). Public bundlers (StackUp / Pimlico / Alchemy) are centralized services that can deplatform etzhayyim or be compelled to refuse specific UserOps. Owning the bundler closes that loophole. Operational cost is bounded by paymaster solvency.

### D3. zk-SNARK toolchain — **Noir + Barretenberg / Honk (PLONK with KZG, universal trusted setup)**

RebirthGate (and any future zk-SNARK verifiers — e.g. cohort eligibility, private vote tallies, anti-Sybil proofs) use:

- **Frontend**: Noir (Aztec's domain-specific language for zk circuits). Type-safe, modern, large stdlib.
- **Backend**: Barretenberg / Honk — PLONK proving system with KZG polynomial commitments.
- **Trusted setup**: **Universal** (Powers of Tau ceremony already complete; we don't run our own per-circuit ceremony). No doctrinal risk from operator-controlled trusted setup.
- **On-chain verifier**: Solidity verifier auto-generated by Barretenberg. Deployed alongside KarmaAnchor.
- **Repo layout**: `50-infra/etzhayyim-k2/rebirth-gate/{circuits,contracts,proofs}/` — circuits in Noir source, contracts in Foundry, proof artifacts pinned to IPFS.

Rationale:

- **Groth16** requires per-circuit trusted setup. Each new circuit needs a ceremony, which is operationally expensive and creates a doctrinal hazard (whoever holds toxic waste can forge proofs). Rejected.
- **PLONK** uses universal setup (one ceremony for all circuits up to a degree bound). Powers of Tau is the canonical ceremony, completed by the Ethereum Foundation with thousands of participants. No new ceremony needed. ✅
- **STARK** is post-quantum and transparent (no trusted setup), but verifier gas is ~5x higher and tooling is less mature for general-purpose zk-SNARKs. Reconsider when STARK verifier gas falls or post-quantum becomes urgent.

Noir is preferred over Circom because:

- Type system catches more circuit bugs at compile time.
- First-class Aztec / Barretenberg integration (the Honk backend is Noir's primary target).
- Better stdlib (hashes, signatures, Merkle proofs) without per-circuit reinvention.

### D4. Filecoin storage — **web3.storage primary + redundant ipfs-pinner pin; Boost node Phase 2**

Long-term archival of K2 ecosystem artifacts (cohort genesis records, audit logs, anchored proof artifacts) uses a **two-tier redundant pin**:

| Tier | Provider | Role |
|---|---|---|
| **Tier 1 (hot)** | etzhayyim-operated ipfs-pinner (`50-infra/ipfs-pinner/`) | content-addressable, available immediately, owned by etzhayyim |
| **Tier 2 (cold)** | web3.storage (Storacha) via UCAN | long-term Filecoin retention via aggregator; not single-point-trustable |

Every K2 artifact is pinned to **both** tiers. Loss of either tier alone does not lose the artifact. Loss of web3.storage as a service does not break etzhayyim because Tier 1 ipfs-pinner is the system of record.

**Phase 2 (deferred)**: when long-tail K2 storage exceeds ~10 TiB or web3.storage's reliability degrades, deploy an etzhayyim-operated **Boost node** (Filecoin SP) and add it as Tier 2′. The Tier 2 aggregator becomes optional. No code path change above the pin abstraction.

Filebase is rejected as the primary aggregator because it is an S3-compatible operator-controlled gateway (centralized primitive). web3.storage uses UCAN-based decentralized authorization, which is closer alignment with the substrate axis. The dependency is still on a third-party service, which is why we maintain Tier 1 as the system of record.

### D5. K2 ↔ yobel relation — **K2 is the technical primitive; yobel is one scriptural consumer**

K2 and yobel both touch "cohort lifecycle", but at different layers:

| Layer | K2 (this ADR) | yobel (`20-actors/yobel/`) |
|---|---|---|
| Domain | technical primitive | scriptural / ceremonial consumer |
| Events | genesis, fission, resume, decommission | 50-year cycle: debt release, land return, slave manumission |
| Frequency | per-cohort (any cadence) | one cycle per 50 years (shmita-of-shmitas) |
| Code | `50-infra/etzhayyim-k2/cohort/` (contracts) + cells | `20-actors/yobel/cells/release_settlement/` (cells consuming K2) |
| Doctrinal scope | none — pure infra | full — bound to Leviticus 25, ADR-2605192245 land trust |

Structurally, yobel **uses** K2 primitives:

- The 50-year cohort *is* a K2 cohort instance (yobel `genesis` invokes K2 `cohort.genesis`).
- yobel cycle close *is* a K2 `cohort.decommission` event, with yobel-specific cells (`release_settlement`) attached as cohort-decommission handlers.
- yobel's per-cycle Merkle root is anchored via the same KarmaAnchor contract.

This avoids duplicating cohort lifecycle code. yobel imports from K2; yobel does not re-implement cohort genesis.

## Consequences

- `50-infra/etzhayyim-k2/` becomes a real implementation directory in two phases:
  - **Phase α (immediate)**: contracts directory (`karma-anchor/`, `rebirth-gate/`, `cohort/`) — Foundry projects, Base Sepolia deploy first.
  - **Phase β (post-α)**: bundler (`erc4337-bundler/`) — k8s deploy.
  - **Phase γ (Filecoin)**: pin client wrappers (`filecoin-pin/`) — wraps web3.storage UCAN client + existing ipfs-pinner.
- `20-actors/yobel/cells/release_settlement/` is refactored to depend on K2 cohort primitives (currently it likely treats yobel cohort as a custom concept).
- `50-infra/etzhayyim-paymaster/` paymaster is shared between identity ops (ADR-2605212030), bundler ops (this ADR), and any future ERC-4337 path. Capacity needs to be sized for the union.
- The K8s cluster gets a new long-running service (rundler bundler). Operational footprint grows.
- The Noir / Barretenberg toolchain becomes a build-time dependency for any circuit work. Add to `deps.toml` toolchain versions section.
- Vendor's K2-touching code paths (RebirthVerifier.sol drafts, ERC-4337 bundler config) are deprecated; no equivalent contract is deployed on vendor private chain after migration.

## Alternatives Considered

1. **Deploy K2 contracts on vendor private chain `260425` with daily anchor to Base L2.** Rejected for the same reasons as ADR-2605212030 D1: chain operator is centralized, latency breaks 1 SBT = 1 vote semantics, dual-chain ops overhead.

2. **Use a public ERC-4337 bundler (StackUp / Pimlico).** Rejected: censorship-resistance is constitutional. Public bundlers can be served subpoenas, deplatform contracts, or refuse specific UserOps. The operational savings do not outweigh the constitutional risk.

3. **Use Groth16 for RebirthGate.** Rejected: per-circuit trusted setup ceremony is doctrinally hazardous (whoever holds toxic waste can forge proofs forever). PLONK universal setup is the equivalent of a one-time, broadly-witnessed ceremony — sufficient for our threat model.

4. **Run our own Filecoin Boost node from day one.** Rejected as Phase α scope: operationally expensive (~$X/mo + SLA risk for storage proofs). web3.storage is good enough for early scale; promote to Boost when volume justifies it.

5. **Treat yobel as a top-level peer to K2 (parallel cohort lifecycle).** Rejected: leads to code duplication and divergent definitions of "cohort genesis". yobel-as-K2-consumer is the clean separation.

6. **Layered chain split** — identity on Base L2, K2 on a separate L2 (Optimism / Arbitrum). Rejected: cross-L2 messaging adds operational complexity without changing the centralization-axis classification. Single chain is simpler and equally constitutional.

## Open Items

- Choose the exact OpenZeppelin / vendored Solidity base contract for KarmaAnchor (likely `Ownable` + `EIP-712` for cohort signer recovery + custom Merkle library).
- Decide rundler version pinning + image registry path. Probable: ghcr.io/etzhayyim/rundler:vX.Y.Z.
- Noir version pinning + Barretenberg version pinning. Probable: latest stable as of P0; documented in `deps.toml`.
- web3.storage UCAN delegation key custody — held by etzhayyim ipfs-pinner pod; rotation cadence TBD.
- yobel refactor scope — when does `release_settlement` get switched to use K2 cohort primitives? Recommended: after K2 cohort contracts land on Base Sepolia and pass a smoke test.
- Anchor cadence — daily is the default; cohort-sensitive events may need faster anchor. Confirm against per-cohort SLA.
- Vendor K2-touching code removal schedule (currently `RebirthVerifier.sol` is a draft; clearer once we know what's actually deployed). Tracking as migration debt under ADR-2605211950.

## References

- ADR-2605211950 — substrate centralization axis
- ADR-2605212030 — etzhayyim authz ERC725 root issuance
- ADR-2605172100 — etzhayyim payments on-chain only
- ADR-2605171800 — langgraph MST IPFS L2 anchor pipeline
- ADR-2605192100 — etzhayyim mission charter
- ADR-2605192245 — etzhayyim global land sovereignty (yobel land context)
- ADR-2605192315 — transparent religious force
- `50-infra/etzhayyim-paymaster/` (existing, ERC-4337 paymaster)
- `50-infra/l2-anchor-contract/` (existing, Stage 5a)
- `50-infra/anchor-cron/` (existing, Stage 5b)
- `50-infra/ipfs-pinner/` (existing, Stage 4 scaffold)
- `50-infra/etzhayyim-k2/README.md` (scaffold)
- `20-actors/yobel/` (existing, scriptural consumer)
- Foundry Operations rundler — https://github.com/alchemyplatform/rundler (Apache 2.0)
- Aztec Noir — https://noir-lang.org/
- Barretenberg / Honk PLONK backend — https://aztec.network/
- web3.storage (Storacha) — https://web3.storage/
- Vendor: ADR-2604261830 + ADR-2604262100 (migration source)
