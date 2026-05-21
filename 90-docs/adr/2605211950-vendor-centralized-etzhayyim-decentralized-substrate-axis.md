---
id: 2605211950-vendor-centralized-etzhayyim-decentralized-substrate-axis
title: "Substrate Centralization Axis — gftdcojp = Centralized Exclusive, etzhayyim = Decentralized Exclusive"
status: active
doc_type: adr
topic: vendor-etzhayyim-centralization-axis
authoritative: true
last_verified: 2026-05-21
priority: 8.5
axis: architecture
weight: 0.85
priority_note: "Sharpens the vendor/etzhayyim boundary established by ADR-2605152100 + 2605172000 + 2605172100 + 2605172400. Adds the centralization axis as a constitutional rule: decentralization primitives (Ethereum / Base L2 / IPFS / AT MST / did:web / did:plc / ERC-4337 / ERC725) live exclusively in etzhayyim; centralized substrate (fiat / Stripe / RisingWave / operator-controlled storage / central JWT) lives exclusively in gftdcojp."
authoritative_for:
  - rule: decentralization primitives are etzhayyim-exclusive
  - rule: centralized substrate is vendor-exclusive
  - rule: crossover is vendor → etzhayyim only via paid-tier XRPC (progressive enhancement)
related:
  - "ADR-2605152100 (etzhayyim github org boundary)"
  - "ADR-2605172000 (etzhayyim RW-free substrate)"
  - "ADR-2605172100 (etzhayyim payments on-chain only)"
  - "ADR-2605172400 (vendor 3-axis split rule)"
  - "vendor: ADR-0074 (ethereum-identity-bridge-cacao-webauthn)"
  - "vendor: ADR-0095 (3-layer identity rw-vault)"
  - "vendor: ADR-2604261830 (ethereum-anchored-wasm-bpmn-runtime)"
  - "vendor: ADR-2604262100 (erc725-erc8004-k8s-ipfs-agent-runtime)"
depends_on:
  - "ADR-2605152100"
  - "ADR-2605172000"
  - "ADR-2605172100"
  - "ADR-2605172400"
supersedes: []
superseded_by: []
---

# ADR-2605211950: Substrate Centralization Axis — gftdcojp = Centralized Exclusive, etzhayyim = Decentralized Exclusive

**Status**: active
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

## Context

The vendor/etzhayyim boundary is governed by four prior ADRs:

- ADR-2605152100 — GitHub org boundary (etzhayyim/root vs gftdcojp/ai-gftd-apps-gftdcojp).
- ADR-2605172000 — etzhayyim is RW-free (AT MST + IPFS + Base L2 only, no centralized DB).
- ADR-2605172100 — etzhayyim payments are on-chain only (Base L2 + USDC + ERC-4337, no fiat processor).
- ADR-2605172400 — vendor 3-axis split rule (Liability × Custody × Settlement) for per-project classification.

These set rules for *etzhayyim* (must be decentralized) and for *per-project classification* (3-axis). They do not, however, state the dual rule for *vendor*: that **centralization primitives are vendor-exclusive and decentralization primitives are not allowed to live in vendor**.

Today the vendor repo still holds decentralization primitives:

- `did:erc725:gftd:260425:{contract}` root identity issuance (`60-apps/ai-gftd-project-auth/worker-authz/src-ts/sign-up.ts`, `70-tools/scripts/provision-actors-erc725.mjs`).
- Ethereum private chain handle (`ETH_PRIVATE_CHAIN_ID` env, internal RPC).
- K2 ecosystem (`KarmaAnchor.sol`, ERC-4337 bundler, zk-SNARK `RebirthGate`, Filecoin pin).
- ERC-8004 agent runtime path (ADR-2604262100).
- `linkEthereumBegin` / `linkEthereumVerify` lexicons under `00-contracts/lexicons/ai/gftd/authz/`.
- Stripe Issuing → ERC-4337 + USDC bridge (vendor-side bridge between fiat and chain).

This mixes the two layers and creates two operational risks:

1. **Identity provenance ambiguity.** ERC725 root issued by `authz.gftd.ai` is constitutionally a decentralization primitive (cryptographic, censorship-resistant), but issued by a centralized operator (Gftd Japan). The trust assumption silently inherits vendor trust.
2. **Crossover direction drift.** ADR-2605172100 requires vendor → etzhayyim as paid-tier XRPC. With decentralization primitives in vendor, the crossover can go the other way (etzhayyim depending on vendor for on-chain identity), inverting the substrate hierarchy.

The user-stated principle on 2026-05-21 makes the rule explicit:

> 基本的に gftdcojp は 中央集権, etzhayyim は 非中央集権

This ADR records that principle as the canonical vendor/etzhayyim substrate-axis rule.

## Decision

The **centralization axis** is now the constitutional split between vendor and etzhayyim. Per-project Liability/Custody/Settlement classification (ADR-2605172400) continues to apply, and the centralization axis is added on top as a substrate-layer rule.

### Allowed primitives per side

| Layer | etzhayyim/root (decentralized exclusive) | gftdcojp vendor (centralized exclusive) |
|---|---|---|
| **Identity** | `did:web:etzhayyim.com`, `did:plc:*`, ERC-4337 Smart Wallet (DID-bound), WebAuthn passkey, **ERC725 root identity** | Operator JWT, internal account ID, vendor-issued session token, OAuth (Gftd-side IdP) |
| **Payment / settlement** | Base L2 + USDC, ERC-4337 UserOp, 0xSplits, Superfluid, etzhayyim Paymaster, on-chain escrow | Stripe (Charges + Issuing), bank ACH/wire, PayPal/Square/Razorpay, fiat invoicing, tax-recognized commercial relationship |
| **State / persistence** | AT Protocol MST + IPFS + Base L2 anchor (ADR-2605171800), did:web cloudflare worker | RisingWave / PostgreSQL / Hyperdrive / Kysely, S3 / B2 (operator-controlled), Cloudflare KV/D1, internal materialized views |
| **Compute / runtime** | langGraph cells on murakumo fleet (launchd), CF Worker edge proxy, k8s pods that read MST | k8s pods over RisingWave, BuildKit on remote builder, vendor-internal cron, vendor CI |
| **DNS / domain** | `etzhayyim.com` + did:web resolver | `gftd.ai`, `gftd.co.jp` and subdomains, vendor-controlled DNS |
| **Governance** | 1 SBT = 1 vote (on-chain), Council attestation (on-chain), Charter Rider (license + on-chain Council) | Vendor org chart, employment contracts, internal RACI, board governance |
| **Storage of off-chain blobs** | IPFS via etzhayyim ipfs-pinner | S3 / B2 / R2 (operator-owned bucket) |
| **Anchoring** | l2-anchor-contract → Base L2 (ADR-2605171800 Stage 5) | Vendor-internal audit log, AWS CloudTrail, vendor-only retention |

### Hard rules

1. **No decentralization primitive may be implemented or operated in `ai-gftd-apps-gftdcojp/`**, including:
   - Ethereum / Base L2 / Polygon / any EVM chain RPC, signing, or anchoring.
   - ERC725, ERC-4337, ERC-8004, ERC-1271, Smart Wallet, Smart Account.
   - IPFS pinning, IPLD, content-addressable hash anchoring.
   - AT Protocol Repo / MST / firehose origination (XRPC consumer-side reads are OK).
   - DID creation / resolution as the system of record (`did:web` / `did:plc` / `did:erc725` issuance).

2. **No centralization primitive may be implemented in `etzhayyim/root/`**, including:
   - Stripe / PayPal / Square / Razorpay / fiat processor SDKs.
   - RisingWave / PostgreSQL / Kysely / Hyperdrive (consumer-side read via vendor paid-tier XRPC OK).
   - Operator-owned S3/B2 buckets that aren't IPFS-mirrored.
   - Vendor-issued JWTs as primary trust root (consume vendor JWT only as a paid-tier session, never as identity).

3. **Crossover direction is asymmetric**:
   - **vendor → etzhayyim**: vendor MAY expose a paid-tier XRPC (Stripe, RW analytic query, K8s heavy compute, etc.) that etzhayyim apps call as progressive enhancement (per ADR-2605172000 upstream carve-out). The etzhayyim app remains operational without it.
   - **etzhayyim → vendor**: an etzhayyim app MUST NOT depend on a vendor service for its core decentralized operation. If a decentralization primitive currently lives in vendor (ERC725 root issuance, K2 anchors), that primitive is in **migration debt** and is treated as a deprecated path.

4. **Identity issuance is etzhayyim-exclusive going forward.** New ERC725 / Smart Wallet provisioning MUST be performed by an etzhayyim service (eligible candidate: `50-infra/etzhayyim-did-web/` extension, or a new actor under `20-actors/`). Vendor `authz.gftd.ai` continues to issue vendor session tokens for paid-tier access only, never DIDs.

## Consequences

- The vendor repo accumulates **migration debt** for the decentralization primitives it currently hosts. Concretely:
  - ERC725 root identity issuer (`authz.gftd.ai` `linkEthereumBegin/Verify` + `provision-root-identity` + `sign-up.ts` Ethereum branch) → relocate to etzhayyim authz.
  - K2 ecosystem on-chain components (`KarmaAnchor.sol`, ERC-4337 bundler, zk-SNARK `RebirthGate`, Filecoin pinning) → relocate to `etzhayyim/root/50-infra/`.
  - `00-contracts/lexicons/ai/gftd/authz/linkEthereum*.json` lexicons → either move to etzhayyim lexicon namespace or deprecate.
  - Stripe Issuing → ERC-4337 + USDC bridge → split: Stripe Issuing stays vendor, ERC-4337 + USDC moves to etzhayyim. The bridge is reframed as a vendor → etzhayyim XRPC call (vendor mints a fiat credit, etzhayyim mints the on-chain USDC equivalent).

- Vendor ADRs that placed decentralization primitives in vendor are **not yet superseded by this ADR**; they remain in effect until the migration lands. This ADR establishes the rule and the migration target, not the cutover.
  - ADR-0074 (ethereum-identity-bridge-cacao-webauthn) — vendor-scoped, becomes a historical pointer once etzhayyim authz absorbs the function.
  - ADR-0095 (3-layer identity rw-vault) — the RW + Vault parts stay vendor; the ERC725 column becomes a vendor-side **reference** to an etzhayyim-issued DID rather than a vendor-issued identity.
  - ADR-2604261830 (ethereum-anchored-wasm-bpmn-runtime) and ADR-2604262100 (erc725-erc8004-k8s-ipfs-agent-runtime) — runtime stays in vendor as compute, but the *chain interaction* (signing, anchoring, ERC725 mutation) moves to etzhayyim.

- The 3-axis split rule (ADR-2605172400) is **not replaced** — it continues to govern per-project classification (e.g. whether project X is etzhayyim or vendor by Liability/Custody/Settlement). This ADR adds the substrate axis as a separate, additional rule applied within the project that the 3-axis already routes.

- `Tranche F` and subsequent project splits gain a fifth check: in addition to L/C/S, the project's substrate primitives must match the side it lands on (no vendor project using Ethereum, no etzhayyim project using Stripe).

- The CLAUDE.md root summary at `etzhayyim/root/CLAUDE.md` is updated in a separate commit to add this rule to the substrate boundary table (deferred until migration commits to keep history clean).

## Alternatives Considered

1. **Keep the status quo** — vendor retains ERC725, etzhayyim runs on-chain payments, no explicit rule that decentralization is vendor-exclusive. Rejected: this is what produced the current drift; ambiguity in the rule made it OK to keep Ethereum in vendor.

2. **Only the inverse rule (etzhayyim must be decentralized) without the dual (vendor must be centralized only).** Rejected: the asymmetry leaks. As long as vendor can host Ethereum, etzhayyim apps will be tempted to call vendor for chain operations (cheaper, already running), which inverts the substrate hierarchy.

3. **Merge etzhayyim and vendor into one repo with feature flags.** Rejected: violates ADR-2605152100 GitHub org boundary, mixes operating entity payoff attribution, and conflicts with the religious-corp constitutional license (Charter Rider).

4. **Per-project axis only (no substrate axis).** Rejected: substrate decisions are constitutional (Charter, ADR-2605192100), not per-project. Allowing per-project substrate choice would let a centralized vendor project use ERC725, which violates the central/decentralized framing the user stated.

## References

- ADR-2605152100 — etzhayyim GitHub org boundary
- ADR-2605172000 — etzhayyim RW-free substrate
- ADR-2605172100 — etzhayyim payments on-chain only
- ADR-2605172400 — vendor 3-axis split rule
- ADR-2605192100 — etzhayyim mission charter (constitutional invariants)
- Vendor: ADR-0074 (ethereum-identity-bridge-cacao-webauthn), ADR-0095 (3-layer identity rw-vault), ADR-2604261830 (ethereum-anchored-wasm-bpmn-runtime), ADR-2604262100 (erc725-erc8004-k8s-ipfs-agent-runtime) — to be migrated/superseded as decentralization primitives move out of vendor.
- User directive 2026-05-21: 「gftdcojp は ethereum 不使用で ok」「基本的に gftdcojp は 中央集権, etzhayyim は 非中央集権」.

## Open Items (migration debt)

These are tracked as future work, not part of this ADR's cutover:

1. Relocate ERC725 root identity issuance from `gftdcojp/ai-gftd-apps-gftdcojp` authz to an etzhayyim service.
2. Relocate K2 on-chain components (`KarmaAnchor.sol`, ERC-4337 bundler, RebirthGate, Filecoin pin) to `etzhayyim/root/50-infra/`.
3. Move `00-contracts/lexicons/ai/gftd/authz/linkEthereum*.json` to etzhayyim or deprecate.
4. Split Stripe Issuing → ERC-4337 bridge into vendor (Stripe side) + etzhayyim (ERC-4337 side) connected via XRPC.
5. Update `60-apps/ai-gftd-project-murakumo/CLAUDE.md` (vendor side) project topology to drop references to vendor-side chain anchoring.
6. Vendor ADR supersession PRs for ADR-0074, ADR-0095, ADR-2604261830, ADR-2604262100 — author once the migration lands, mark this ADR as `superseded_by` in those vendor ADRs.
