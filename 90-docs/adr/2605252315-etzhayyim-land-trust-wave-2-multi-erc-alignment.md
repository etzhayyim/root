---
id: adr-2605252315-etzhayyim-land-trust-wave-2-multi-erc-alignment
title: "ADR-2605252315: Land Trust Wave 2 — Multi-ERC Alignment (721 + 5192 + 7401 + 1155) for Inalienable Earth-Land Stewardship"
status: proposed
doc_type: adr
topic: land-trust-wave-2-multi-erc-alignment
authoritative: true
last_verified: 2026-05-25
priority: 6.5
axis: architecture
weight: 0.65
priority_note: "Wave 2 of the etzhayyim Land Trust. Adds explicit ERC-721 + ERC-5192 (soulbound) + ERC-7401 (nestable steward-tenure) + ERC-1155 (aggregate class) standard conformance. All new contracts R0 = revert(NotYetActivated) until Council Lv6+ ratify. No testnet deploy in this wave."
authoritative_for:
  - Land Trust multi-ERC architecture (4 standards layered, single SoT per parcel)
  - PublicLandRegistry.sol (Base L2 ERC-721 + ERC-5192 mirror — R0 scaffold)
  - StewardTenureRegistry.sol (ERC-7401 nestable steward-tenure child NFTs — R0 scaffold)
  - LandClassRegistry.sol (ERC-1155 supplementary aggregate class accounting — R0 scaffold)
  - LandRegistry.sol minimal ERC-5192 alignment (locked() always-true view, no functional change)
  - LANDS.md schema extension (4-ERC reference columns, steward-tenure linkage)
  - Constitutional invariants preserved (no transfer / no burn / no setOwner / no mint outside donate)
depends_on:
  - adr-2605252300-etzhayyim-charter-preamble-kingdom-of-god-on-blockchain
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192330-etzhayyim-extended-land-sovereignty-ocean-river-air-orbit
  - adr-2605192345-etzhayyim-steward-succession
  - adr-2605172600-etzhayyim-membership-ritual
related:
  - 50-infra/etzhayyim-chain-contracts/src/LandRegistry.sol
  - wellbecoming-karma-lean-proofs
  - LANDS.md
  - adr-2605252300-etzhayyim-charter-preamble-kingdom-of-god-on-blockchain
supersedes: []
superseded_by: []
---

# ADR-2605252315: Land Trust Wave 2 — Multi-ERC Alignment (721 + 5192 + 7401 + 1155) for Inalienable Earth-Land Stewardship

**Status**: proposed
**Date**: 2026-05-25
**Deciders**: Jun Kawasaki (author), Council Lv6+ ≥3 multisig (ratify — post 2026-06-19)

# Context

ADR-2605192245 (Global Land Sovereignty) established the 4-layer permanent land record:

1. **Base L2 NFT** (`PublicLandRegistry.sol` — TODO, ERC-721 non-transferable mirror)
2. **geth-private constitutional record** (`LandRegistry.sol` — IMPLEMENTED as custom struct mapping, not ERC-721)
3. **IPFS GeoJSON + satellite imagery + notarized deed bundle**
4. **git `/LANDS.md` PR**

Wave 1 (2026-05-19) delivered the geth-private constitutional record + 4-layer architecture + LANDS.md schema. As of 2026-05-25, **0 donations exist** (awaiting Bootstrap Council activation + founder symbolic donation per ADR-2605192415 daemon architecture).

The user-requested Wave 2 (2026-05-25) asks for: **"地球上の土地の登記、管理などを erc で行うように"** — explicit, standards-compliant ERC alignment so wallets / indexers / Etherscan / OpenSea-equivalents / land-data consumers recognize etzhayyim land NFTs without bespoke integration. Selected ERCs (per user 2026-05-25 question):

| ERC | Purpose | Why |
|---|---|---|
| **ERC-721** | Per-parcel uniqueness (existing PublicLandRegistry plan) | Each donated parcel is unique; ERC-721 is the universal NFT standard, wallet-native. |
| **ERC-5192** | Minimal soulbound — `locked(uint256) view returns (bool)` always-true | Gas-cheap explicit signaling that this is non-transferable. Wallets / OpenSea hide transfer button when `locked()` returns true. Enforces constitutional inalienability at the standard layer. |
| **ERC-7401** | Nestable NFT — steward-tenure child NFTs nested under land NFT | Parent = land NFT (permanent, inalienable). Child = steward-tenure NFT (time-bounded, transferable only via Council attestation per ADR-2605192345 succession). Lease-to-SBT-holder model. Clean separation: parcel ≠ tenure. |
| **ERC-1155** | Multi-token — supplementary aggregate land-class accounting | Each land class (Agricultural / Residential / Forest / ReligiousFacility / Ocean / Water / Air / Orbit / Other) is a token ID. Holders are land NFTs (or stewards). Provides aggregate accounting ("total agricultural acres in trust", "ocean stewardship hours") without breaking per-parcel uniqueness. **Note**: User selected this even with the "individual parcel uniqueness" caveat; we resolve by making ERC-1155 strictly supplementary, not primary. |

**Why all four, not just one?** ERC-721 alone is wallet-recognizable but doesn't signal non-transferability — clients still show "Transfer" buttons that revert. ERC-5192 adds the soulbound signal cheaply. ERC-7401 separates parcel from tenure cleanly (steward succession is constitutional, parcel is inalienable — the two have different lifecycles). ERC-1155 enables aggregate analytics (Tree of Life ontology benefits: "how much of the biosphere is in trust?").

# Decision

## 1. Architecture: 3-Contract Mirror + 1 Aggregate Registry, all on Base L2

```
                    LandRegistry.sol  ← geth-private (chainId 2605) — UNCHANGED FUNCTIONALLY
                    [SoT for constitutional record]
                              │
                              │ (donation event mirrored via AnchorBridge)
                              ▼
        ┌────────────────────────────────────────────────────────┐
        │  Base L2 (chainId 8453) — Public Mirror                │
        │                                                         │
        │  ┌────────────────────────────────────────┐           │
        │  │ PublicLandRegistry.sol                  │           │
        │  │   = ERC-721 + ERC-5192                  │           │
        │  │   = per-parcel unique soulbound NFT     │           │
        │  │   = locked(tokenId) → true (always)     │           │
        │  └────────────────────────────────────────┘           │
        │              │                                          │
        │              │ (nesting per ERC-7401)                  │
        │              ▼                                          │
        │  ┌────────────────────────────────────────┐           │
        │  │ StewardTenureRegistry.sol               │           │
        │  │   = ERC-7401 nestable                   │           │
        │  │   = child NFTs (steward-tenure period) │           │
        │  │   = parent = LandRegistry tokenId      │           │
        │  │   = succession via Council ≥3 sig      │           │
        │  └────────────────────────────────────────┘           │
        │                                                         │
        │  ┌────────────────────────────────────────┐           │
        │  │ LandClassRegistry.sol                   │           │
        │  │   = ERC-1155                            │           │
        │  │   = token IDs = LandType enum (9 vals)  │           │
        │  │   = holder = LandRegistry tokenId addr  │           │
        │  │   = aggregate metric publishing only    │           │
        │  └────────────────────────────────────────┘           │
        └────────────────────────────────────────────────────────┘
```

## 2. Per-Contract Specifications

### 2.1 LandRegistry.sol (geth-private — UNCHANGED FUNCTIONALLY)

**Modification**: Add **ERC-5192 `locked(uint256) view returns (bool)`** returning `true` for every `landId` where `lands[landId].donatedAt > 0` (existing donation), reverts with `LandNotFound` otherwise. Add `supportsInterface` for `IERC5192` (`0xb45a3c0e`). No state-mutating functions added or modified. Test count: 110 → 112 (2 new tests for `locked()` view + supportsInterface).

**Constitutional invariants** (re-asserted in code comment):
- No `transfer()` / `transferFrom()` / `safeTransferFrom()` — donations inalienable
- No `burn()` / `delete()` — permanent record
- No `setOwner()` / `owner` — only `steward` role
- No `mint()` outside `donate()` ritual
- `locked()` returns `true` constantly for all valid `landId` (constitutional Soulbound signal)

### 2.2 PublicLandRegistry.sol (Base L2 — NEW R0 SCAFFOLD)

**Status**: R0 — `revert NotYetActivated()` on all state-mutating functions until Council Lv6+ ratify activation ADR. View functions OK.

**Inherits**: `ERC721` (OpenZeppelin v5) + `IERC5192`

**Constitutional invariants enforced by override**:

```solidity
// OpenZeppelin v5 ERC721 _update() override
function _update(address to, uint256 tokenId, address auth)
    internal override returns (address)
{
    address from = _ownerOf(tokenId);
    // Allow mint (from == address(0)) only by anchorBridge per AnchorBridge invariant
    // Reject ALL transfers (from != 0 AND to != 0) — soulbound
    // Reject burns (to == address(0)) — permanent
    if (from != address(0) && to != address(0)) revert LandSoulbound(tokenId);
    if (from != address(0) && to == address(0)) revert LandPermanent(tokenId);
    if (msg.sender != address(anchorBridge)) revert OnlyAnchorBridge();
    return super._update(to, tokenId, auth);
}

function locked(uint256 tokenId) external view returns (bool) {
    if (_ownerOf(tokenId) == address(0)) revert ERC721NonexistentToken(tokenId);
    return true;  // CONSTITUTIONAL: always-true per Charter §0.3 + ADR-2605192245
}

function supportsInterface(bytes4 interfaceId) public pure override returns (bool) {
    return interfaceId == type(IERC721).interfaceId
        || interfaceId == type(IERC721Metadata).interfaceId
        || interfaceId == type(IERC5192).interfaceId  // 0xb45a3c0e
        || interfaceId == type(IERC165).interfaceId;
}
```

**`mintFromAnchor(...)` function** (called by `AnchorBridge` when geth-private `LandRegistry.donate()` event is observed): mints token to steward address, sets `tokenURI` to IPFS bundle CID. All state-mutating callers MUST be AnchorBridge in mainnet, or Council multisig in testnet.

**R0 stub behavior**: All state-mutating functions including `mintFromAnchor` revert with `NotYetActivated()`. Activation requires Council Lv6+ ≥3 multisig calling `activate()` (which is itself gated). Activation is reserved for the post-testnet wave.

### 2.3 StewardTenureRegistry.sol (Base L2 — NEW R0 SCAFFOLD)

**Status**: R0 — `revert NotYetActivated()` on all state-mutating functions.

**Inherits**: ERC-7401 nestable interface (we ship our own minimal nestable interface in `src/interfaces/IERC7401.sol` to avoid heavy dependency; full RMRK implementation is overkill for R0).

**Semantics**:
- Each steward tenure = 1 child NFT, parent = `PublicLandRegistry` tokenId
- Tenure NFT has `(startedAt, expectedEndAt, actualEndAt, stewardSbtId, tenureType)` metadata
- TenureType enum: Founder / Successor / Interim / Council-Appointed
- Tenure NFT is itself **soulbound while active** (locked() returns true). Only Council ≥3 multisig can `terminate(tenureId, reason)` and `nestNew(landTokenId, successorStewardSbt)` per ADR-2605192345 (Steward Succession).
- **No direct transfer** — succession is always Council-mediated burn-and-mint of the child NFT.

**Key constraint**: A land NFT (parent) MAY have multiple historical tenure NFTs nested under it (one active + N terminated). This provides on-chain steward history per parcel.

**R0 stub behavior**: `nestNew()` / `terminate()` / `acceptChild()` all revert `NotYetActivated()`. Only view functions (`activeTenureOf(landId) → tenureId` / `tenureHistoryOf(landId) → tenureId[]`) return zero / empty array in R0.

### 2.4 LandClassRegistry.sol (Base L2 — NEW R0 SCAFFOLD)

**Status**: R0 — `revert NotYetActivated()` on all state-mutating functions.

**Inherits**: `ERC1155` (OpenZeppelin v5) — minimal

**Token IDs** (constant, frozen with `LandType` enum from `LandRegistry.sol`):
- `0` = Agricultural
- `1` = Residential
- `2` = Forest
- `3` = ReligiousFacility
- `4` = Other
- `5` = Ocean
- `6` = Water
- `7` = Air
- `8` = Orbit

**Semantics**:
- Token holder = `PublicLandRegistry` per-parcel tokenId computed as `address(uint160(uint256(keccak256(abi.encode("land", landTokenId)))))` — a deterministic synthetic address per land NFT. (This is a stateless mapping; no per-parcel deployment needed.)
- Token balance = `areaM2` of the parcel of that class
- `totalSupply(landClassId)` = total area-in-trust of that class (Tree of Life aggregate)
- **Soulbound**: `_update()` override rejects all `from != address(0)` transfers — class assignment is fixed at donation time

**No fractional ownership semantics** — ERC-1155 balance is areaM2, but it is NOT a fungible economic token. It is an **accounting hash** only. Class membership cannot be transferred (soulbound). The standard's transfer methods all revert.

**Aggregate views**:
- `totalAreaByClass(LandType) → uint256` — total m² in trust by class
- `parcelsByClass(LandType) → uint256[]` — array of landTokenIds in this class (paginated)

**R0 stub behavior**: All state-mutating functions revert `NotYetActivated()`. View functions return zero.

### 2.5 ERC interface IDs (for supportsInterface)

| ERC | Interface ID |
|---|---|
| ERC-165 | `0x01ffc9a7` |
| ERC-721 | `0x80ac58cd` |
| ERC-721 Metadata | `0x5b5e139f` |
| ERC-5192 | `0xb45a3c0e` |
| ERC-7401 nestable | `0x42b0e56f` (we define minimal interface) |
| ERC-1155 | `0xd9b67a26` |
| ERC-1155 Metadata URI | `0x0e89341c` |

## 3. Constitutional Invariants — Re-Asserted at Multi-ERC Layer

| Invariant | Where Enforced |
|---|---|
| Donated land is inalienable (no transfer / no burn) | `LandRegistry.sol` (geth-private, intentional absence) + `PublicLandRegistry.sol._update()` revert + `locked()` always-true + `StewardTenureRegistry` soulbound-while-active + `LandClassRegistry._update()` revert |
| Only steward role exists, no "owner" | `LandRegistry.sol.lands[].steward` (no `lands[].owner`) + ERC-721 `ownerOf()` returns steward address (semantic naming for ERC-721 compliance only) |
| Donations are permanent | All burns rejected in `_update()` override + StewardTenureRegistry tenure burns only via Council ≥3 sig |
| Only `donate()` ritual creates land record | `LandRegistry.donate()` + `PublicLandRegistry.mintFromAnchor()` (anchor-only) + `LandClassRegistry._update()` (anchor-only) |
| Steward succession is Council-mediated | `StewardTenureRegistry.nestNew()` + `terminate()` require Council ≥3 multisig + ADR-2605192345 quorum semantics |

## 4. Non-Goals (R0)

- **N1**: No mainnet deploy (Council ratify pending Bootstrap Council RFP closure 2026-06-19)
- **N2**: No testnet deploy in this wave (per user scope choice "Preamble + ERC alignment, no testnet")
- **N3**: No first donation execution (separate activation ADR — likely 2605260000+ after Council)
- **N4**: No on-chain bidirectional sync mechanism (geth-private LandRegistry → Base L2 PublicLandRegistry only flows one way via AnchorBridge; reverse flow is out of scope)
- **N5**: No RMRK full implementation — we ship minimal IERC7401 interface only (~50 LoC). Full RMRK is deferred to post-mainnet wave if/when steward-tenure complexity demands it
- **N6**: No fractional ownership (ERC-1155 area-m² balance is accounting hash, not transferable token)
- **N7**: No DEX listing / marketplace integration (constitutional soulbound — no market for land)
- **N8**: No upgradeable proxy pattern — all contracts are immutable per Constitution.sol pattern (ADR-2605192100 §1.7 + Constitution.sol design)
- **N9**: No off-chain ERC-4337 paymaster integration for `donate()` gas — donor pays gas themselves (intentional — token incentive avoidance per §2(b) Charter Rider)

## 5. Deliverables (this wave)

### 5.1 Files modified (1)
- `50-infra/etzhayyim-chain-contracts/src/LandRegistry.sol` — add `locked()` view + `supportsInterface(IERC5192)` + IERC5192 interface import. No state-mutating change.

### 5.2 Files created (5)
- `50-infra/etzhayyim-chain-contracts/src/interfaces/IERC5192.sol` — minimal interface (1 function)
- `50-infra/etzhayyim-chain-contracts/src/interfaces/IERC7401.sol` — minimal nestable interface (~15 functions, R0 only what we need)
- `50-infra/etzhayyim-chain-contracts/src/PublicLandRegistry.sol` — Base L2 mirror ERC-721 + ERC-5192 (R0 scaffold)
- `50-infra/etzhayyim-chain-contracts/src/StewardTenureRegistry.sol` — ERC-7401 nestable (R0 scaffold)
- `50-infra/etzhayyim-chain-contracts/src/LandClassRegistry.sol` — ERC-1155 aggregate (R0 scaffold)

### 5.3 Files updated (3)
- `LANDS.md` — schema columns: add `tenureNftId` + `landClassTokenId` + `publicLandTokenId`; document 4-ERC architecture
- `50-infra/etzhayyim-land-registry/README.md` — update with 4-ERC architecture diagram
- `deps.toml` — register ADR-2605252300 + 2605252315 + 3 new modules
- `90-docs/adr/README.md` — add ADR index entries
- `CLAUDE.md` — Status row 46 (this wave)

### 5.4 Tests (R0)
- `LandRegistry.t.sol` — 2 new tests for `locked()` + supportsInterface IERC5192 (target: 112/112)
- New contracts: scaffold-only, no tests in R0 (revert-on-call is trivial; tests land with activation ADR)

## 6. Activation Path (post-Council, separate ADRs)

- **ADR-26060X1...** (post 2026-06-19): Bootstrap Council ratification of Preamble §0 + Wave 2 ADRs. Status: proposed → active.
- **ADR-26060X2...**: PublicLandRegistry / StewardTenureRegistry / LandClassRegistry activation — Council Lv6+ ≥3 multisig `activate()`. Testnet (Base Sepolia) first.
- **ADR-26060X3...**: AnchorBridge wiring (geth-private LandRegistry.donate event → Base Sepolia PublicLandRegistry.mintFromAnchor).
- **ADR-26060X4...**: Founder symbolic first donation (per ADR-2605192415 daemon architecture).
- **ADR-26060X5...**: Mainnet (Base L1/L2) deploy.

Each subsequent activation ADR requires its own Council ratification cycle.

# Consequences

### Positive

1. **Standard-compliant wallet integration**: Once activated, OpenSea-equivalents / Etherscan / Rainbow Wallet / Coinbase Wallet show land NFTs natively. `locked()` signal hides transfer buttons. No bespoke integration needed.
2. **Cleaner steward succession semantics**: Parcel NFT (parent) is permanent; tenure NFT (child) has lifecycle. Succession is "burn child + mint child", not "transfer". Burn-and-mint is constitutionally cleaner than transfer.
3. **Aggregate Tree of Life accounting**: `LandClassRegistry.totalAreaByClass()` provides queryable "how much of the biosphere is in trust by class" without indexer scraping per-parcel.
4. **Reusable building blocks**: PublicLandRegistry pattern (ERC-721 + ERC-5192 soulbound) is reusable for any inalienable trust object (future: water-rights, biodiversity-credits, ancestral artifacts).
5. **Charter §0.3 (Blockchain Substrate) reified**: Preamble §0.3 lists "土地登記 = 4-layer (Base L2 ERC-721 + geth-private + IPFS + git)" as constitutional substrate element. Wave 2 fulfills this for the ERC-721 layer.

### Negative / Risks

1. **R0 scaffold without tests is a maintenance hazard**: Activation ADR must include test suite (target: ≥40 tests for the 3 new contracts). **Mitigation**: R0 scaffold revert-on-call is trivial; tests are deferred but tracked in activation ADR.
2. **ERC-1155 area-m² balance semantic confusion risk**: "Balance" in ERC-1155 normally means transferable token amount; here it means soulbound area accounting. **Mitigation**: README + contract NatSpec must declare "accounting hash, not fungible token" prominently. `_update()` reverts all transfers as defensive measure.
3. **ERC-7401 nestable is a young standard (finalized 2024)**: Wallet support is limited. **Mitigation**: We ship minimal interface (no RMRK dependency). Wallet adoption is not required for constitutional function — Council multisig is authoritative.
4. **AnchorBridge dependency**: PublicLandRegistry mint flow requires AnchorBridge to observe geth-private events. AnchorBridge is existing infrastructure but the event-observation logic for LandRegistry.Donated is new. **Mitigation**: Defer wiring to activation ADR.
5. **OpenZeppelin v5 dependency**: PublicLandRegistry and LandClassRegistry inherit from OZ v5 contracts. Charter Rider requires Apache-2.0 + Rider, OZ is MIT — compatible per Apache-2.0 §4 (we add Rider to first-party code only; OZ is third-party preserved per OZ MIT NOTICE). **Mitigation**: Document in NOTICE; `charter-rider-applicator` already skips third-party.

### Mitigation Matrix

| Risk | Severity | Mitigation | Owner |
|---|---|---|---|
| R0 untested contracts deployed accidentally | HIGH | All state-mutating functions revert `NotYetActivated()` unconditionally | Wave 2 code |
| Council ratify delay blocks all subsequent waves | MEDIUM | Wave 2 ADRs status: proposed, no code dependency on activation | Wave 2 ADR sequence |
| ERC-7401 wallet support limited | LOW | Council multisig is authoritative, not wallet | activation ADR |
| ERC-1155 "balance" misread as transferable | MEDIUM | NatSpec prominent declaration + revert all transfers | LandClassRegistry NatSpec |
| Anchor bridge event-observation correctness | MEDIUM | Defer to activation ADR with explicit test plan | activation ADR test suite |

# Alternatives Considered

### A. ERC-721 only (drop ERC-5192 / 7401 / 1155)
**Reject**: ERC-721 alone doesn't signal non-transferability — wallets show transfer button that reverts. User UX bad. ERC-5192 (1 function) is gas-cheap and standard. ERC-7401 and ERC-1155 add steward and aggregate semantics that are otherwise expensive (custom indexer required).

### B. Skip PublicLandRegistry — use only geth-private LandRegistry
**Reject**: Charter Preamble §0.3 declares "土地登記 = 4-layer (Base L2 + geth-private + IPFS + git)" as constitutional substrate. geth-private alone is 1-layer. Public verifiability requires Base L2 mirror.

### C. Use ERC-3525 (Semi-Fungible Token) instead of ERC-1155 for land classes
**Reject**: ERC-3525 (semi-fungible) is more complex than needed. We don't need slot-based fractional value; we need simple aggregate accounting per class. ERC-1155 is simpler and more widely supported.

### D. Use RMRK full implementation for ERC-7401 nestable
**Reject**: RMRK is heavy (~3000 LoC dependency). We use only `nestNew` / `terminate` / `acceptChild` / `parentOf` — minimal interface (~50 LoC) is sufficient for steward-tenure semantics. Full RMRK if/when complex inventory semantics emerge (post-mainnet).

### E. Make LandRegistry.sol itself ERC-721 (refactor existing 110-test contract)
**Reject**: Existing LandRegistry.sol is constitutional record (geth-private chainId 2605) and is verified by 110 tests. Refactoring to inherit ERC-721 changes interfaces, breaks tests, and creates a coupling between constitutional (geth-private) and public (Base L2) layers that the 4-layer design intentionally separates. PublicLandRegistry is the Base L2 mirror — that's where ERC-721 belongs.

### F. Soulbound via ERC-4973 (Account-Bound Token) instead of ERC-5192
**Reject**: ERC-4973 is Final but has lower wallet adoption than ERC-5192. ERC-5192 is the minimal "this NFT is soulbound" signaling standard, no extra functions required. Lower complexity wins.

### G. Defer ERC-7401 nestable to future wave; treat tenure as off-chain record
**Consider, reject**: Off-chain tenure record breaks Preamble §0.3 (substrate doctrine). Steward tenure is constitutional (Council-mediated succession per ADR-2605192345) — it must be on-chain. ERC-7401 is the standard for this pattern. Including in Wave 2 R0 scaffold is correct.

# References

- ADR-2605252300 (Charter §0 Preamble — sibling, parent doctrinal source)
- ADR-2605192100 (Mission Charter)
- ADR-2605192200 (Charter Rider v2.0)
- ADR-2605192245 (Global Land Sovereignty — 4-layer architecture)
- ADR-2605192330 (Extended Land Sovereignty — Ocean / River / Air / Orbit)
- ADR-2605192345 (Steward Succession — multisig + dual-permanent record)
- ADR-2605172600 (Membership Ritual — dual-permanent record pattern reused)
- `50-infra/etzhayyim-chain-contracts/src/LandRegistry.sol` (existing geth-private record)
- `50-infra/etzhayyim-land-registry/README.md` (4-layer architecture overview)
- `LANDS.md` (git-side roster)
- EIP-721 (Non-Fungible Token Standard)
- EIP-5192 (Minimal Soulbound NFTs)
- EIP-7401 (Parent-Governed Nestable Non-Fungible Tokens)
- EIP-1155 (Multi Token Standard)
- OpenZeppelin Contracts v5 (ERC721 / ERC1155 base)
