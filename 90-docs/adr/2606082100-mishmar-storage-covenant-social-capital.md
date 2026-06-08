---
id: adr-2606082100-mishmar-storage-covenant-social-capital
title: "ADR-2606082100: Mishmar Storage Covenant — social-capital-funded bonded pinning for unstoppable persistence (donation-native, anchor-chain staking, anti-usury)"
status: proposed
doc_type: adr
topic: mishmar-storage-covenant
authoritative: true
last_verified: 2026-06-08
priority: 7.0
axis: substrate-boundary
weight: 0.7
priority_note: "Closes the single largest unstoppability gap in the kotoba substrate: there is currently NO permissionless economic incentive for third parties to keep data alive — persistence depends entirely on the operator (kotobase extended pin + B2 account + Murakumo witness fleet). Bitcoin (PoW + full replication), Ethereum (PoS bond + slashing) and Holochain (agent-redundancy + membrane validation) each solve this with a 'bond-at-risk + reward' loop, but a transferable yield violates Charter §2(b) speculative-finance prohibition and the Yobel/Shmita usury prohibition. This ADR adapts the slashing primitive WITHOUT yield, and — critically — sources the 'reward' from SOCIAL CAPITAL minted by AI-agent information-disclosure + wellbecoming intervention, not from external cash or open-market issuance. Social capital becomes the denominator of the donation/economic system. Staking/bonding + slashing live on the existing anchor chain (AnchorBridge → Base L2); kotoba stays read+verify only."
authoritative_for:
  - Mishmar Storage Covenant — bonded pinning + proof-of-availability + slash-to-commons
  - Social Capital ledger — wellbecoming-intervention + information-disclosure minting, non-transferable + decaying
  - donation-economic-system definition — social capital as the denominator of the persistence retainer
  - anchor-chain staking placement (MishmarBondEscrow on geth-private → Base L2)
  - Charter §2(b) / Yobel anti-usury compliance pattern for storage incentives
depends_on:
  - "2605231400"  # kotoba-datomic Holochain-iso substrate — witness quorum >=3-of-5 reused as PoA attestor
  - "2605282100"  # mKOTO economy — L6 settlement bridge gets its concrete lander here
  - "2604261717"  # staked-claim truth-incentive — ClaimStakeEscrow state-machine type-reused
  - "2605192100"  # mission charter — wellbecoming mission, multi-generational stewardship
  - "2605192200"  # Charter Rider v2.0 — §2(b) speculative-finance prohibition
  - "2605192130"  # 10% tithe auto-split — slashed bond + retainer routed via TitheRouter
  - "2605192145"  # Public Fund Safe — slash destination + retainer source
  - "2605172100"  # payments-on-chain — allowed payment categories (donation/tithe only externally)
  - "2605172300"  # AnchorBridge — the anchor chain this ADR stakes onto
  - "0075"        # yoro engagement wellbecoming — wellbecoming negative-feedback definition
  - "2605240001"  # kotoba cleanroom — gas + CitationLedger primitives
  - "2605231525"  # server-side signing / caller-DID auth — proofs are pinner-DID CACAO-signed
related:
  - "2605260004"  # on-chain settlement bridge — this ADR is its concrete destination
  - "2605240200"  # KaizenObserver self-reflection — wellbecoming-Δ measurement feed
  - "50-infra/etzhayyim-yobel-contract/"      # Yobel/Shmita jubilee — bond release + obligation forgiveness
  - "50-infra/etzhayyim-chain-contracts/"     # AnchorBridge.sol + TitheRouter.sol
  - "50-infra/vultr/geth-private/contracts/"  # ClaimStakeEscrow.sol — the mirrored primitive
supersedes: []
superseded_by: []
---

# ADR-2606082100: Mishmar Storage Covenant — social-capital-funded bonded pinning

**Status**: proposed
**Date**: 2026-06-08
**Deciders**: Jun Kawasaki

> Mishmar (משמר) — the priestly *watch* / *charge*: the standing duty to **keep**.
> A pinner does not *speculate* on data; it *keeps watch* over it. The bond is
> at risk but bears no yield (anti-usury / Yobel); the reward is **social
> capital**, not money.

## Context

The unstoppability/persistence analysis (session 2026-06-08) scored the kotoba
substrate against Bitcoin, Ethereum, and Holochain across eight axes. The
substrate scores well on identity sovereignty (DID + CACAO + Passkey) and is
structurally **Holochain-isomorphic** (ADR-2605231400). But two axes are near-zero
in the current implementation:

- **④ economic security / Sybil resistance** — no bond, no slashing, no cost to lie about availability.
- **⑧ incentive self-sufficiency** — persistence depends entirely on the
  operator (kotobase extended pin, the B2 account, the Murakumo witness fleet).
  **No permissionless party has any reason to keep data alive.**

This is exactly the gap that the three reference systems solve with a
**"bond-at-risk + reward"** loop:

| | Bitcoin | Ethereum (PoS) | Holochain |
|---|---|---|---|
| Sybil resistance | PoW (energy) | capital bond | membrane validation + agent cost |
| reward (得) | block subsidy + fee | issuance + fee | none (intrinsic) |
| punishment (損) | orphaned block (wasted energy) | **slashing (bond burned)** | DHT eviction / warrant |
| persistence | full replication | state + DA sampling | interested-party + neighbour redundancy |

The naive port — "stake ETH as collateral, slash on data loss, pay yield" — is
**doubly prohibited**:

1. **Charter §2(b)** (ADR-2605192200) prohibits speculative finance. A
   transferable, yield-bearing stake with a secondary market is a security.
2. **Yobel / Shmita** (50-infra/etzhayyim-yobel-contract) encodes the usury
   prohibition: a bond that *grows* by being locked is interest.

Two design moves resolve the contradiction.

### Move 1 — keep the slashing, drop the yield

Borrow Ethereum's **bond-at-risk + slashing** strictly. Make the loss
asymmetric and the bond **non-yielding**: a pinner deposits a refundable bond,
loses it on a failed availability proof, and gets **exactly the bond back** on
honest release — never more. Slashed value goes to the **commons** (Public Fund
via TitheRouter), never to competing stakers — so there is no extraction game,
no MEV, no validator cartel.

### Move 2 — source the reward from SOCIAL CAPITAL, not cash (the economic core)

This is the load-bearing decision and the answer to "what *is* the donation /
economic system." The reward for keeping watch is **not** money and **not** an
open-market token. It is **social capital**:

> **AI agents / LLMs generate value by two acts — information disclosure
> (情報開示, verifiable transparency) and wellbecoming intervention
> (wellbecoming 介入, ADR-0075 negative-feedback-aligned actions that improve a
> population's long-term 情緒健康). When those acts are validated, they MINT
> social capital. Social capital — non-transferable, DID-bound, decaying — is
> the denominator of the donation pool that funds persistence. Generating social
> capital *is* the economic system.**

The loop closes:

```
agent discloses / intervenes (wellbecoming+)
        │  witness quorum + KaizenObserver wellbecoming-Δ + Council attest
        ▼
   social capital minted  (non-transferable, decaying — must be re-earned)
        │  denominates + directs
        ▼
   donation retainer pool  (USD donors enter via TitheRouter; social capital
        │                    decides WHO/WHAT gets funded persistence)
        ▼
   Mishmar bonded pinning  (bond-at-risk, anchor-chain, no yield)
        ▼
   the disclosed/intervention data STAYS ALIVE & available
        ▲                                                   │
        └──────── enables more disclosure / intervention ◄──┘
```

Unstoppability is therefore **funded by the social value the data itself
creates**, not by speculation. This is unstoppable *within a covenant
community*, not via anonymous mercenary capital (see Consequences — that
trade-off is deliberate and is a Charter matter, not a design one).

## Decision

Adopt the **Mishmar Storage Covenant**: a four-part composition layered on
existing primitives, with all staking/slashing on the **anchor chain**.

### Part A — Social Capital ledger (L0, the new economic base)

`social/capital/<DID>/<epoch>` Quad, minted by validated value-acts, governed by:

| property | rule | reason |
|---|---|---|
| transferable | **no** (Soulbound, DID-bound) | not a security (§2(b)); Holochain-intrinsic |
| yield | **none** | anti-usury (Yobel) |
| decay | exponential per epoch (must be re-earned) | anti-hoarding; keeps it a *flow*, not a *store of wealth* |
| mint: disclosure | `attest/*` + CitationLedger hit, witness ≥3-of-5 validated | rewards verifiable transparency |
| mint: wellbecoming | KaizenObserver wellbecoming-Δ > 0 (ADR-0075 negative-feedback), Council Lv6+ ≥3 attested | rewards long-term 情緒健康 over short-term engagement |
| burn | proven harm / disclosure later falsified | symmetric downside |

Social capital is **read** by Part C to size retainers and **direct** which
roots get persistence priority. It never leaves the religious-corp accounting
boundary.

### Part B — `MishmarBondEscrow` on the anchor chain (staking placement)

Type-reuse of the deployed `ClaimStakeEscrow.sol` state machine
(ADR-2604261717), remapped from "claim truth" to "data availability". Lives on
geth-private (PoA) and is anchored to Base L2 via the existing `AnchorBridge`.
kotoba never calls it — kotoba only **observes** it (Part D).

```solidity
// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies.
// Mirrors ClaimStakeEscrow (ADR-2604261717): bond → challenge → witness-proof → settle.
interface IMishmarBondEscrow {
    // pinner commits to keep `rootCid` available for `durationEpochs`.
    // gated: Adherent SBT held + CharterComplianceRegistry.isNonAligned(pinner)==false.
    // rootCid MUST equal a root already committed via AnchorBridge.commitRoot (cross-check).
    function postPin(bytes32 rootCid, uint256 bond, uint64 durationEpochs) external returns (bytes32 pinId);

    // anyone OR the scheduled witness set issues a random-block availability challenge.
    function challenge(bytes32 pinId, bytes32 nonce) external;

    // pinner answers with >=3-of-5 kotoba-datomic witness attestations (ECDSA/EIP-1271
    // verified — reuses ClaimStakeEscrow arbiter-sig verification path).
    function proveAvailability(bytes32 pinId, bytes calldata witnessQuorumSig) external;

    // settle: proof in time → bond stays, reputation SBT++, retainer mKOTO credit emitted.
    //         timeout       → SLASH: bond → TitheRouter.route(publicFund, bond, "storage-slash")
    //                         (90/10 atomic), reputation SBT-- .
    function settle(bytes32 pinId) external;

    // end of duration, no open challenge → bond returned IN FULL (no interest — Yobel).
    function release(bytes32 pinId) external;

    // Shmita/Yobel cycle → all bonds force-released, obligations forgiven (Yobel registry).
    function yobelRelease() external;

    event Pinned(bytes32 indexed pinId, bytes32 indexed rootCid, address indexed pinner, uint256 bond, uint64 durationEpochs);
    event Challenged(bytes32 indexed pinId, bytes32 nonce, address challenger);
    event Proven(bytes32 indexed pinId, uint64 epoch);
    event Slashed(bytes32 indexed pinId, uint256 bond, bytes32 purpose); // purpose == keccak256("storage-slash")
    event Released(bytes32 indexed pinId, uint256 bond);
}
```

Reused as-is (configuration / wiring only, no new invention):

- **`AnchorBridge.commitRoot`** (permissionless) — the anchor layer; `pinId`
  references the same `rootHash`, so any third party cross-checks geth-private ↔
  Base L2 ↔ IPFS CID.
- **`TitheRouter.route(..., "storage-slash")`** — 90/10 atomic split, already
  purpose-gated + Charter-compliance-registry-gated. Add `"storage-slash"` to the
  titheable-purpose set (and `"persistence-retainer"` for inflow).
- **`Yobel*Registry`** — `release` / `yobelRelease` jubilee semantics (the
  availability *obligation* is the "debt" that is periodically forgiven).
- **kotoba-datomic witness quorum ≥3-of-5** (`hash(cid)%N`, ADR-2605231400) —
  the proof-of-availability attestor.

### Part C — donation routing denominated by social capital

The Public Fund pinning-retainer pool is allocated **proportional to the social
capital of the data's originating agents**. External USD donations still enter
via `TitheRouter` (category `donation`, 90/10 tithe); social capital decides
**which roots** get bonded-pinning priority and **how large** a retainer a pinner
DID may receive. Retainer is paid in **mKOTO** (mKOTO economy L3 wallet,
ADR-2605282100) — internal accounting Quad, **non-transferable, no secondary
market, redeemable only for kotoba compute/storage services**. This makes
ADR-2605260004's deferred L6 settlement bridge land here concretely.

### Part D — kotoba stays read+verify only (boundary preserved)

Every staking/slashing/SBT/social-capital-settlement action is on the anchor
chain or in the internal Quad ledger. kotoba **observes and verifies** via its
existing EVM read surface (`eth_getLogs` / `eth_call` / EIP-1271 — kotoba-auth
`eth/*`, kotoba-runtime `bind_evm`). It never signs a tx, never custodies a
bond, never settles on-chain. The operating-entity boundary (ADR-2605231525)
is unchanged. See companion sketch: `40-engine/kotoba/docs/MISHMAR-OBSERVATION.md`.

## Charter compliance (CRITICAL)

| Constraint | How honored |
|---|---|
| §2(b) speculative-finance prohibition | bond non-yielding; mKOTO + social capital non-transferable, no secondary market; slash → commons (no extraction game) |
| Yobel / Shmita usury prohibition | bond never grows; `yobelRelease()` periodically forgives obligations |
| ADR-2605172100 payment categories | external inflow: `donation` only; slash: `tithe`; never `subscription` |
| §1.5 anti-commercialization | no "storage priced to external parties"; donors get "donation acknowledged → mKOTO credit + social capital", not a price |
| ADR-2605192130 10% tithe | both slash and retainer flow through TitheRouter 90/10 |
| ADR-0075 wellbecoming | social-capital minting uses the wellbecoming **negative-feedback** score, so the economy rewards long-term 情緒健康, not short-term engagement |
| ADR-2605231525 no platform keys | proofs are pinner-DID CACAO-signed; no platform service-account writes a balance or a social-capital Quad |
| ADR-2605215000 Murakumo-only | witness attestors are the existing Murakumo fleet cells; no external compute added |

## Consequences

### Positive

- Closes the ④ (economic security) and ⑧ (incentive self-sufficiency) axes:
  projected impl score 32 → ≈48–50 (/80), reaching the substrate's own design
  ceiling (52) and surpassing Holochain (51) on the persistence axes — **without
  touching the operating-entity boundary or the Charter**.
- The economy is **internally sourced**: persistence is funded by the social
  value (disclosure + wellbecoming) the data itself produces, not by external
  cash dependency or speculation.
- ADR-2605260004's L6 settlement bridge gets a concrete, Charter-clean lander.

### Negative / honest limits

- Because reward is **non-transferable and donation/social-capital-bounded**,
  the system **cannot attract anonymous mercenary capital** the way
  Filecoin/Arweave/EigenLayer do. Unstoppability is "**operator-less within a
  covenant community**", not "**unstoppable via anonymous global mercenaries**".
  This is a deliberate Charter trade-off; lifting it is a §2(b) amendment
  question for the Council, not a design change.
- Social-capital minting introduces a **measurement-gaming surface** (agents
  optimizing for wellbecoming-Δ score). Mitigated by: decay (gains evaporate),
  Council Lv6+ attestation on the wellbecoming mint path, and symmetric burn on
  later-falsified disclosure. A robustness ADR (cf. organism-adversarial-
  robustness-r0) is a follow-up.
- Witness quorum currently maps to a fixed Murakumo fleet; permissionless
  bonded witnesses (to harden ④ further) is a follow-up.

### Neutral

- No new cryptographic primitive: `MishmarBondEscrow` is a remap of the
  deployed `ClaimStakeEscrow`; the witness quorum, AnchorBridge, TitheRouter,
  and Yobel registries already exist.

## Implementation plan

| # | Step | Target |
|---|---|---|
| 1 | This ADR | shipped with this commit |
| 2 | `40-engine/kotoba/docs/MISHMAR-OBSERVATION.md` — kotoba read+verify observation sketch | shipped with this commit |
| 3 | Social Capital ledger spec — Quad predicates + decay fn + mint/burn rules (kotoba-server) | follow-up |
| 4 | `MishmarBondEscrow.sol` on geth-private + AnchorBridge cross-check + TitheRouter purpose extension | follow-up |
| 5 | Witness PoA challenge schedule + ≥3-of-5 attestation persistence (kotoba-datomic quorum) | follow-up |
| 6 | mKOTO L6 retainer settlement (lands ADR-2605260004) denominated by social capital | follow-up |
| 7 | Adversarial-robustness ADR for social-capital minting (anti-gaming) | follow-up |

## Future work

- **Permissionless bonded witnesses** — generalize the ≥3-of-5 attestor set beyond the Murakumo fleet, each witness bonded + slashable, to harden ④ toward Ethereum-grade.
- **Cross-pin redundancy proof** — k-of-n distinct-operator constraint on `postPin` so a single operator cannot satisfy the whole covenant (Bitcoin-style replication, encoded as a covenant predicate).
- **Secondary export to Filecoin/Arweave** — funded from the retainer pool as `donation`, to raise ① and ⑦ toward full-replication grade without an open market.

## Closing record (2026-06-08)

This ADR closes the 2026-06-08 persistence/economic-security gap review by
choosing the Charter-clean incentive shape for third-party storage persistence:
non-yielding bonded pinning, slash-to-commons, and social-capital-denominated
retainer routing.

Landed scope is documentation and registry only. The Solidity escrow, social
capital ledger predicates, witness scheduler, and mKOTO retainer settlement stay
explicit follow-ups gated by Council/operator approval. No Kubernetes resources,
no default namespace resources, no live staking surface, and no external-payment
path are created by this closing.
