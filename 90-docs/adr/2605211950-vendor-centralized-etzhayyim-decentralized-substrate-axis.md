---
id: 2605211950-vendor-centralized-etzhayyim-decentralized-substrate-axis
title: "Substrate Centralization Axis — etzhayyim = Centralized Exclusive, etzhayyim = Decentralized Exclusive"
status: active
doc_type: adr
topic: vendor-etzhayyim-centralization-axis
authoritative: true
last_verified: 2026-05-21
priority: 8.5
axis: architecture
weight: 0.85
priority_note: "Sharpens the vendor/etzhayyim boundary established by ADR-2605152100 + 2605172000 + 2605172100 + 2605172400. Adds the centralization axis as a constitutional rule: decentralization primitives (Ethereum / Base L2 / IPFS / AT MST / did:web / did:plc / ERC-4337 / ERC725) live exclusively in etzhayyim; centralized substrate (fiat / Stripe / RisingWave / operator-controlled storage / central JWT) lives exclusively in etzhayyim."
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

# ADR-2605211950: Substrate Centralization Axis — etzhayyim = Centralized Exclusive, etzhayyim = Decentralized Exclusive

**Status**: active
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

## Context

The vendor/etzhayyim boundary is governed by four prior ADRs:

- ADR-2605152100 — GitHub org boundary (etzhayyim/root vs etzhayyim/etzhayyim-root).
- ADR-2605172000 — etzhayyim is RW-free (AT MST + IPFS + Base L2 only, no centralized DB).
- ADR-2605172100 — etzhayyim payments are on-chain only (Base L2 + USDC + ERC-4337, no fiat processor).
- ADR-2605172400 — vendor 3-axis split rule (Liability × Custody × Settlement) for per-project classification.

These set rules for *etzhayyim* (must be decentralized) and for *per-project classification* (3-axis). They do not, however, state the dual rule for *vendor*: that **centralization primitives are vendor-exclusive and decentralization primitives are not allowed to live in vendor**.

Today the vendor repo still holds decentralization primitives:

- `did:erc725:etzhayyim:260425:{contract}` root identity issuance (`60-apps/etzhayyim-project-auth/worker-authz/src-ts/sign-up.ts`, `70-tools/scripts/provision-actors-erc725.mjs`).
- Ethereum private chain handle (`ETH_PRIVATE_CHAIN_ID` env, internal RPC).
- K2 ecosystem (`KarmaAnchor.sol`, ERC-4337 bundler, zk-SNARK `RebirthGate`, Filecoin pin).
- ERC-8004 agent runtime path (ADR-2604262100).
- `linkEthereumBegin` / `linkEthereumVerify` lexicons under `00-contracts/lexicons/com/etzhayyim/authz/`.
- Stripe Issuing → ERC-4337 + USDC bridge (vendor-side bridge between fiat and chain).

This mixes the two layers and creates two operational risks:

1. **Identity provenance ambiguity.** ERC725 root issued by `authz.etzhayyim.com` is constitutionally a decentralization primitive (cryptographic, censorship-resistant), but issued by a centralized operator (etzhayyim Japan). The trust assumption silently inherits vendor trust.
2. **Crossover direction drift.** ADR-2605172100 requires vendor → etzhayyim as paid-tier XRPC. With decentralization primitives in vendor, the crossover can go the other way (etzhayyim depending on vendor for on-chain identity), inverting the substrate hierarchy.

The user-stated principle on 2026-05-21 makes the rule explicit:

> 基本的に etzhayyim は 中央集権, etzhayyim は 非中央集権

This ADR records that principle as the canonical vendor/etzhayyim substrate-axis rule.

## Decision

The **centralization axis** is now the constitutional split between vendor and etzhayyim. Per-project Liability/Custody/Settlement classification (ADR-2605172400) continues to apply, and the centralization axis is added on top as a substrate-layer rule.

### Allowed primitives per side

| Layer | etzhayyim/root (decentralized exclusive) | etzhayyim vendor (centralized exclusive) |
|---|---|---|
| **Identity** | `did:web:etzhayyim.com`, `did:plc:*`, ERC-4337 Smart Wallet (DID-bound), WebAuthn passkey, **ERC725 root identity** | Operator JWT, internal account ID, vendor-issued session token, OAuth (etzhayyim-side IdP) |
| **Payment / settlement** | Base L2 + USDC, ERC-4337 UserOp, 0xSplits, Superfluid, etzhayyim Paymaster, on-chain escrow | Stripe (Charges + Issuing), bank ACH/wire, PayPal/Square/Razorpay, fiat invoicing, tax-recognized commercial relationship |
| **State / persistence** | AT Protocol MST + IPFS + Base L2 anchor (ADR-2605171800), did:web cloudflare worker | RisingWave / PostgreSQL / Hyperdrive / Kysely, S3 / B2 (operator-controlled), Cloudflare KV/D1, internal materialized views |
| **Compute / runtime** | langGraph cells on murakumo fleet (launchd), CF Worker edge proxy, k8s pods that read MST | k8s pods over RisingWave, BuildKit on remote builder, vendor-internal cron, vendor CI |
| **DNS / domain** | `etzhayyim.com` + did:web resolver | `etzhayyim.com`, `etzhayyim.com` and subdomains, vendor-controlled DNS |
| **Governance** | 1 SBT = 1 vote (on-chain), Council attestation (on-chain), Charter Rider (license + on-chain Council) | Vendor org chart, employment contracts, internal RACI, board governance |
| **Storage of off-chain blobs** | IPFS via etzhayyim ipfs-pinner | S3 / B2 / R2 (operator-owned bucket) |
| **Anchoring** | l2-anchor-contract → Base L2 (ADR-2605171800 Stage 5) | Vendor-internal audit log, AWS CloudTrail, vendor-only retention |

### Hard rules

1. **No decentralization primitive may be implemented or operated in `etzhayyim-root/`**, including:
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

4. **Identity issuance is etzhayyim-exclusive going forward.** New ERC725 / Smart Wallet provisioning MUST be performed by an etzhayyim service (eligible candidate: `50-infra/etzhayyim-did-web/` extension, or a new actor under `20-actors/`). Vendor `authz.etzhayyim.com` continues to issue vendor session tokens for paid-tier access only, never DIDs.

## Consequences

- The vendor repo accumulates **migration debt** for the decentralization primitives it currently hosts. Concretely:
  - ERC725 root identity issuer (`authz.etzhayyim.com` `linkEthereumBegin/Verify` + `provision-root-identity` + `sign-up.ts` Ethereum branch) → relocate to etzhayyim authz.
  - K2 ecosystem on-chain components (`KarmaAnchor.sol`, ERC-4337 bundler, zk-SNARK `RebirthGate`, Filecoin pinning) → relocate to `etzhayyim/root/50-infra/`.
  - `00-contracts/lexicons/com/etzhayyim/authz/linkEthereum*.json` lexicons → either move to etzhayyim lexicon namespace or deprecate.
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
- User directive 2026-05-21: 「etzhayyim は ethereum 不使用で ok」「基本的に etzhayyim は 中央集権, etzhayyim は 非中央集権」.

## Open Items (migration debt)

These are tracked as future work, not part of this ADR's cutover. Updated 2026-05-21 (end-of-session):

1. **Relocate ERC725 root identity issuance** from `etzhayyim/etzhayyim-root` authz to an etzhayyim service.
   - Design: **ADR-2605212030** — Base L2 mainnet + hybrid did:web/did:erc725 + 5-phase opt-in cutover + `org.etzhayyim.authz.*` namespace.
   - **Phase α P0 (contract)**: ✅ landed. `EtzhayyimAuthz.sol` Foundry contract + Deploy script + 17 tests passing + Anvil 31337 E2E smoke validated.
   - **Phase α P1 (XRPC / chain client / docs)**: ✅ landed. CF Worker scaffold (`50-infra/etzhayyim-authz/src/worker.ts`) + viem chain reader (resolveRoot fully functional once env vars set) + Council Safe proposal builder + 5 lexicons under `00-contracts/lexicons/org/etzhayyim/authz/` + Base Sepolia deploy runbook + Council multisig SOP. did:web Worker extended with `/actor/<handle>/did.json` path-based per-handle DID document.
   - **Phase α P2+ pending**: Base Sepolia actual deploy (funded key) → wrangler.toml [vars] AUTHZ_CONTRACT_ADDRESS set → KV provisioning → event log scan for `getProvenance` → wildcard DNS + subdomain CF route for canonical `did:web:<handle>.etzhayyim.com` form.
2. **Relocate K2 on-chain components** (`KarmaAnchor.sol`, ERC-4337 bundler, RebirthGate, Filecoin pin) to `etzhayyim/root/50-infra/`.
   - Design: **ADR-2605212040** — Base L2 + own rundler bundler + Noir/Honk PLONK + web3.storage with redundant ipfs-pinner + yobel-as-K2-consumer.
   - **Phase β P0 (contracts)**: ✅ landed. `KarmaAnchor.sol` (10 tests) + `CohortLifecycle.sol` (12 tests) Foundry under `50-infra/etzhayyim-k2/contracts/` + Deploy script. All 22 tests passing locally.
   - **Phase β P1+ pending**: Base Sepolia deploy → rundler bundler k8s deploy → RebirthGate Noir circuits + Solidity verifier → Filecoin pin client (web3.storage + redundant ipfs-pinner) → yobel `release_settlement` refactor to consume K2 cohort primitives.
3. **Move `00-contracts/lexicons/com/etzhayyim/authz/linkEthereum*.json`** to etzhayyim or deprecate.
   - **Done (2026-05-21)**: deprecation marker landed in vendor lexicons (vendor branch `260521-substrate-axis-vendor-side`); new etzhayyim namespace `org.etzhayyim.authz.*` defined in ADR-2605212030 §D4 and 5 lexicon JSONs landed under `00-contracts/lexicons/org/etzhayyim/authz/`.
4. **Split Stripe Issuing → ERC-4337 bridge** into vendor (Stripe side) + etzhayyim (ERC-4337 side) connected via XRPC.
   - Design: **ADR-2605212050** — vendor approves Stripe authorization → XRPC `org.etzhayyim.payment.creditFromFiat` → etzhayyim mints USDC from Council-multisig reserve + atomic 90/10 split + Council-multisig daily cap.
   - **Phase δ P0 (Reserve contract)**: ✅ landed. `Reserve.sol` Foundry under `50-infra/etzhayyim-fiat-bridge/contracts/` + Deploy script + 25 tests passing (idempotency replay + daily cap rollover + tithe split + Council config + withdraw + solvency-strict).
   - **Phase δ P1+ pending**: XRPC handler Worker scaffold + 4 payment lexicons under `00-contracts/lexicons/org/etzhayyim/payment/` + cross-repo vendor refund callback lexicon + Reserve solvency monitor cron + Base Sepolia deploy.
5. **Update `60-apps/etzhayyim-project-murakumo/CLAUDE.md`** (vendor side) project topology to drop references to vendor-side chain anchoring.
   - **N/A (2026-05-21)**: investigation found the murakumo CLAUDE.md does not contain chain-anchoring references; it documents LLM inference only. No edit needed. Will revisit if vendor-side Stripe-bridge or K2 docs surface here.
6. **Vendor ADR supersession PRs** for ADR-0074, ADR-0095, ADR-2604261830, ADR-2604262100.
   - **Partial (2026-05-21)**: migration-note callouts + cross-reference to ADR-2605211950 landed in vendor branch `260521-substrate-axis-vendor-side`. Formal `superseded_by` will be authored once the etzhayyim code migrations (Items 1 + 2) reach Base Sepolia testnet deploy + 1-month operation.

## Session 2026-05-21 progress log

End-of-day summary for the substrate-axis migration. Branches:
- etzhayyim/root: `260521-yorishiro-phase1` (pushed)
- etzhayyim/etzhayyim-root: `260521-substrate-axis-vendor-side` (pushed, PR-ready)

| # | Open Item | Status before | Status after | Lines landed |
|---|---|---|---|---|
| 1 | ERC725 issuer relocation | scaffold only | Phase α P0 + P1 (contract + XRPC + chain client + docs + did:web ext) | ≈ 2 600 |
| 2 | K2 on-chain | scaffold only | Phase β P0 (KarmaAnchor + CohortLifecycle + tests) | ≈ 660 |
| 3 | linkEthereum* lexicons | open | done (vendor deprecation + etzhayyim namespace) | small |
| 4 | Stripe-ERC4337 bridge | design only | Phase δ P0 (Reserve.sol + 25 tests) | ≈ 570 |
| 5 | vendor murakumo CLAUDE.md | open | N/A (investigated, no edit needed) | — |
| 6 | vendor ADR supersession | open | partial (migration notes + cross-ref) | small |

Test totals: **64 Solidity tests passing locally** (17 EtzhayyimAuthz + 10 KarmaAnchor + 12 CohortLifecycle + 25 Reserve). Anvil 31337 smoke verified EtzhayyimAuthz provisionRoot E2E.

Three design ADRs authored this session (2605212030, 2605212040, 2605212050) resolving the open design questions from the scaffold READMEs. `deps.toml [platform.l2.*]` extended with `authz_contract`, `karma_anchor_contract`, `cohort_lifecycle_contract`, `fiat_bridge_reserve` SSoT pointers (addresses pending Base Sepolia deploy).
