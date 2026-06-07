---
id: 2605212030-etzhayyim-authz-erc725-root-issuance-design
title: "etzhayyim authz — ERC725 Root Identity Issuance on Base L2 (hybrid did:web facade)"
status: active
doc_type: adr
topic: etzhayyim-authz-root-issuance
authoritative: true
last_verified: 2026-05-21
priority: 8.5
axis: identity
weight: 0.85
priority_note: "Resolves the four open design questions of the etzhayyim-authz scaffold (ADR-2605211950 Open Item 1). Specifies which chain new etzhayyim DIDs anchor to, which DID format the surface uses, the cutover protocol for the ~96 vendor-issued roots, and the lexicon namespace."
authoritative_for:
  - chain selection for etzhayyim ERC725 root identity issuance (Base L2 public mainnet)
  - hybrid DID surface (did:web public + did:erc725 cryptographic root)
  - 5-phase forward-only cutover from vendor authz to etzhayyim authz
  - org.etzhayyim.authz.* lexicon namespace
related:
  - "ADR-2605211950 (substrate centralization axis)"
  - "ADR-2605172000 (etzhayyim RW-free substrate)"
  - "ADR-2605172100 (etzhayyim payments on-chain only)"
  - "ADR-2605171800 (langgraph MST IPFS L2 anchor pipeline)"
  - "ADR-2605192100 (etzhayyim mission charter)"
  - "vendor: ADR-0074 (ethereum-identity-bridge-cacao-webauthn)"
  - "vendor: ADR-0095 (3-layer identity rw-vault)"
depends_on:
  - "ADR-2605211950"
  - "ADR-2605172100"
supersedes: []
superseded_by: []
---

# ADR-2605212030: etzhayyim authz — ERC725 Root Identity Issuance on Base L2 (hybrid did:web facade)

**Status**: active
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

## Context

ADR-2605211950 made the centralization axis the constitutional split: decentralization primitives — including ERC725 root identity issuance — are etzhayyim-exclusive. The scaffold at `50-infra/etzhayyim-authz/` left four design questions open:

1. **DID format** — keep `did:erc725:` or adopt `did:web:` + on-chain anchor.
2. **Chain selection** — Base L2 public mainnet vs the vendor's private chain (`ETH_PRIVATE_CHAIN_ID = 260425`).
3. **Cutover protocol** — how to migrate the ~96 mitama actor roots + N org roots without invalidating downstream `vault_members` / `vertex_signal_identity` rows.
4. **Lexicon namespace** — `org.etzhayyim.authz.*` (new) vs reusing `com.etzhayyim.authz.*` with prefix.

Constraints from existing ADRs:

- ADR-2605172100 already commits etzhayyim **payments** to Base L2 + USDC + ERC-4337 Smart Wallet. Splitting identity onto a different chain creates dual-chain ops.
- ADR-2605192100 (mission charter) §1.12 mandates **transparent religious force**: full on-chain log + open-source. Private chain identity defeats public verifiability.
- ADR-2605192300 (Council governance, 1 SBT = 1 vote) requires the SBT registry to be on the same chain Council deliberates on — currently Base L2.
- `did:web:etzhayyim.com` is LIVE (CF Worker, since 2026-05-17), so the etzhayyim entity itself already has a public DID resolver.

## Decision

### D1. Chain selection — **Base L2 public mainnet (single chain)**

All etzhayyim ERC725 root identities are anchored on **Base L2 public mainnet** (chain id `8453`). The private chain (`260425`) used by vendor is **not** adopted by etzhayyim. Rationale:

- One-chain ops match the existing payment / paymaster / l2-anchor pipeline (ADR-2605171800, ADR-2605172100, `50-infra/etzhayyim-paymaster/`, `50-infra/l2-anchor-contract/`). No new RPC, no new bundler, no new gas funding.
- Public verifiability is constitutional (ADR-2605192100 §1.12). A private chain's transparency depends on the operator's willingness to publish; Base L2 is transparent by construction.
- Council 1 SBT = 1 vote (ADR-2605192300) already lives on Base L2; identity must share that chain so SBT membership and ERC725 root can be cross-checked atomically.
- Gas cost is bounded by the existing etzhayyim paymaster; users see zero gas (passkey-only UX).
- For **cohort-internal events** that must not be public (e.g. private Council deliberation drafts), use the K2 KarmaAnchor pattern (daily Merkle root → Base L2) rather than a separate chain. See ADR-2605212040.

### D2. DID format — **hybrid did:web facade + did:erc725 cryptographic root**

Etzhayyim DIDs have two surfaces:

| Surface | Format | Purpose | Resolution |
|---|---|---|---|
| **Public / discoverable** | `did:web:<handle>.etzhayyim.com` | Human-readable handle, federation, AT Protocol compatibility, social discovery | CF Worker at `50-infra/etzhayyim-did-web/` (extended to per-handle subdirectories) |
| **Cryptographic root** | `did:erc725:base:<contract-address>` | Authority, signing, key rotation, on-chain enforcement | ERC725 contract on Base L2; resolved via `viem` or contract `getData()` |

The `did:web` document **must** embed the `did:erc725:base:` value as `alsoKnownAs` plus a `verificationMethod` pointing to the on-chain key. Conversely, the ERC725 contract stores a `dwebHandle` data key referencing the canonical did:web. The two are 1:1.

Public-facing systems (AT Protocol federation, social handles, signed lexicons, MCP tool registry) MUST use `did:web:`. Internal governance and on-chain enforcement MUST use `did:erc725:`. Either format SHOULD resolve to the same actor through the bidirectional pointers.

Vendor's `did:erc725:etzhayyim:260425:<contract>` literals continue to exist in vendor Kotoba/Datomic columns as historical references; new etzhayyim roots use `did:erc725:base:<contract>` (chain id `8453` is implied by the `base` method-specific identifier per ADR-0095 amended naming).

### D3. Cutover protocol — **5-phase forward-only migration**

The ~96 mitama actor roots and N org roots in vendor are not deleted; they are **mirrored** with cryptographic continuity proof. No retroactive invalidation.

| Phase | Action | Reversible? |
|---|---|---|
| **P0** | Deploy etzhayyim authz on Base L2 (Foundry contracts under `50-infra/etzhayyim-authz/contracts/`, deploy script alongside `DeployReligiousCorp.s.sol`) | Yes — contracts can be redeployed |
| **P1** | Vendor `authz.etzhayyim.com` stops issuing **new** ERC725 roots. `linkEthereumBegin/Verify` return `Gone: 410` for new caller DIDs; existing DIDs still verify | Yes — vendor can resume issuing if rollback needed |
| **P2** | Existing vendor roots opt-in to etzhayyim mirror: actor signs a continuity proof `sig_vendor(did:erc725:base:<new>)` with their old vendor-issued key; etzhayyim authz mints the Base L2 root referencing the vendor root as `predecessor` | Yes — opt-in, no forced migration |
| **P3** | All new etzhayyim-scope writes (Council attestations, land donations, SBT mints) use the Base L2 root only. Vendor Kotoba/Datomic reads continue to resolve old vendor roots for historical queries | Partial — new writes can't easily be undone |
| **P4** | After 6 months of P3 (target: 2026-11), vendor `linkEthereum*` lexicons get `status: deprecated` at the lexicon level (not just description prefix). Vendor `sign-up.ts` Ethereum branch removed. Vendor contracts become read-only | No — vendor-side removal |

The "vendor sign-up.ts Ethereum branch removed" step is gated on observable migration progress; do not schedule it by date alone.

### D4. Lexicon namespace — **`org.etzhayyim.authz.*` (new namespace under `org/etzhayyim/`)**

New lexicons live under `00-contracts/lexicons/org/etzhayyim/authz/`. NSIDs follow the `org.etzhayyim.authz.*` convention. Initial set (Phase P0):

| NSID | Type | Replaces |
|---|---|---|
| `org.etzhayyim.authz.beginRootProvision` | procedure | vendor `com.etzhayyim.authz.linkEthereumBegin` |
| `org.etzhayyim.authz.completeRootProvision` | procedure | vendor `com.etzhayyim.authz.linkEthereumVerify` |
| `org.etzhayyim.authz.resolveRoot` | query | (new) — bidirectional did:web ↔ did:erc725:base |
| `org.etzhayyim.authz.mirrorVendorRoot` | procedure | (new, Phase P2) — continuity proof submission |
| `org.etzhayyim.authz.getProvenance` | query | (new) — full chain of did:web ↔ did:erc725 history |

The `org.etzhayyim.*` namespace mirrors the existing `org/etzhayyim/yobel/` pattern in this repo. Vendor's `com.etzhayyim.authz.*` remains valid during the migration window; only **new** etzhayyim-scope identity ops use the `org.etzhayyim.*` namespace.

## Consequences

- `50-infra/etzhayyim-authz/` becomes a real implementation directory in Phase P0. Sub-structure:
  - `contracts/` — Foundry Solidity (ERC725 implementation, key rotation, predecessor tracking)
  - `src/` — XRPC handler code (Cloudflare Worker or k8s pod, TBD per existing etzhayyim infra pattern)
  - `scripts/` — provisioning scripts (mirror of vendor's `provision-actors-erc725.mjs`, ported)
- `50-infra/etzhayyim-did-web/` CF Worker is extended to serve per-handle `did:web:<handle>.etzhayyim.com` documents, each embedding the matching `did:erc725:base:<contract>` and `verificationMethod`.
- Council operations (attestations, SBT mints) gain a new precondition: the actor must hold a Base L2 ERC725 root. Vendor-only roots are not accepted as identity for new Council operations after P3.
- The existing 96 mitama actors face an opt-in migration window between P1 and P3 (~ 6 months). Migration is voluntary but is required to participate in new etzhayyim governance.
- Vendor `actor_did` / `org_did` columns in Kotoba/Datomic continue to operate; values from Phase P2 onward are `did:erc725:base:<new>` instead of `did:erc725:etzhayyim:260425:<old>`. Both formats coexist in the column (string-typed).

## Alternatives Considered

1. **Stay on the vendor private chain `260425`.** Rejected: violates the substrate centralization axis (chain operated by a centralized entity) and the religious-corp transparency invariant (ADR-2605192100). Private-chain identity cannot be publicly cross-checked against the on-chain Council, which lives on Base L2.

2. **Adopt `did:web:` only, no on-chain ERC725 anchor.** Rejected: did:web alone has no cryptographic key rotation enforcement on-chain. Compromising the CF Worker would let an attacker rewrite identity history. ERC725 anchor provides immutable audit + key rotation discipline.

3. **Adopt `did:erc725:` only, no did:web facade.** Rejected: AT Protocol federation, social handles, and human-readable handles all require a DID method that resolves to a URL. `did:erc725:base:0xabc...` is not a usable user-facing handle. The hybrid model lets us keep AT-compat without sacrificing on-chain authority.

4. **Bridge contract on private chain `260425` + nightly anchor to Base L2.** Rejected: this is the K2 KarmaAnchor pattern, which is appropriate for **events** but not for identity. Identity must be immediately verifiable on the chain where governance happens (Base L2). Latency of nightly anchor breaks 1 SBT = 1 vote freshness.

5. **Mass-migrate all 96 vendor roots in a single big-bang cutover.** Rejected: actors hold their original signing keys; forced migration without per-actor cryptographic continuity proof is either insecure (no proof = etzhayyim claims arbitrary roots) or impossible (some actors may have lost their vendor key). Opt-in continuity proof is the only sound path.

6. **Keep `com.etzhayyim.authz.*` namespace and add `etzhayyim:` prefix.** Rejected: AT NSIDs are namespace-purpose-method triples; bolting on a prefix breaks tooling that splits by dots. `org.etzhayyim.authz.*` is the clean separation and matches the existing `org/etzhayyim/yobel/` precedent.

## Open Items

- Specific Foundry contract layout for the ERC725 implementation (which OpenZeppelin / ERC725.js base contract, key types supported, gas-optimal storage layout).
- Continuity-proof signature scheme — straightforward EIP-191 vs EIP-712 typed-data. EIP-712 is preferred for replay protection across chains.
- Whether `org.etzhayyim.authz.resolveRoot` should be served by CF Worker (low latency, no chain RPC) or by an etzhayyim k8s pod (closer to chain state). CF Worker preferred for read paths; mutations via k8s pod that owns the bundler key.
- KeyChain integration: client-side passkey signing path (WebAuthn → P256 verifier on-chain) is shared with `etzhayyim-paymaster`. Confirm code reuse.
- Eligibility for `mirrorVendorRoot` — should it require an active vendor session (proof of original control) or just possession of the vendor signing key? Recommended: both, to mitigate stolen-key risk.

## References

- ADR-2605211950 — substrate centralization axis
- ADR-2605172100 — etzhayyim payments on-chain only
- ADR-2605172000 — etzhayyim RW-free substrate
- ADR-2605171800 — langgraph MST IPFS L2 anchor pipeline
- ADR-2605192100 — etzhayyim mission charter
- ADR-2605192300 — Council governance
- `50-infra/etzhayyim-did-web/` (CF Worker, did:web LIVE)
- `50-infra/etzhayyim-paymaster/` (ERC-4337 Paymaster, Foundry)
- `50-infra/l2-anchor-contract/` (Stage 5a Foundry)
- `50-infra/etzhayyim-authz/README.md` (scaffold)
- Vendor: `60-apps/etzhayyim-project-auth/worker-authz/src-ts/sign-up.ts` (Ethereum branch — migration source)
- Vendor: ADR-0074, ADR-0095 (migration source)
