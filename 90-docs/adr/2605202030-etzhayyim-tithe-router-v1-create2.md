---
id: adr-2605202030-etzhayyim-tithe-router-v1-create2
title: "ADR-2605202030: TitheRouter v1 — CREATE2 sequencing で Constitution.getMutable 経由の publicFund 読み出しを実現"
status: proposed
doc_type: adr
topic: etzhayyim-tithe-router-v1-create2
authoritative: true
last_verified: 2026-05-20
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "TitheRouter v0 (2026-05-20 deploy) は publicFund を constructor immutable として保持する deploy-time workaround を採用した。v1 では CREATE2 deterministic deployment を用いて Constitution.getMutable('public_fund.safe_address') を runtime read する原典実装に戻す。Phase 2 governance wiring 完了後の post-mainnet decision として scope。"
authoritative_for:
  - TitheRouter v0 → v1 migration plan
  - CREATE2 deterministic salt 計算方式
  - Constitution mutables 読み取りパス (publicFund + その他 reference addresses)
  - v0/v1 並存期間中の SDK switching
depends_on:
  - adr-2605192130-etzhayyim-tithe-redistribution
  - adr-2605192100-etzhayyim-mission-charter
related:
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
supersedes: []
superseded_by: []
---

# ADR-2605202030: TitheRouter v1 — CREATE2 sequencing で Constitution.getMutable 経由の publicFund 読み出しを実現

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

TitheRouter v0 (2026-05-20 Anvil-verified deploy) は publicFund Safe address を **constructor immutable** として保持する v0 workaround を採用した:

```solidity
// v0 TitheRouter
constructor(IERC20 _usdc, IConstitution _const, IChartersComplianceRegistry _ch, address _publicFund) {
    publicFund = _publicFund;  // immutable
}
```

これは元の ADR-2605192130 設計意図と部分的に矛盾している。ADR-2605192130 §3 では:

```solidity
// 元の設計 — Constitution.getMutable() 経由
address publicFund = address(uint160(uint256(constitution.getMutable(PUBLIC_FUND_ADDRESS_KEY))));
```

v0 workaround の理由: **deploy-time の circular dependency**。

```
Constitution mutables は constructor で初期化される
  ↓
mutable の "public_fund.safe_address" の値は deploy 時に必要
  ↓
v0 設計: Constitution deploy 前に PublicFundSafe address は既知 (5-of-7 Safe を手動 deploy 済)
       → constructor 引数として渡せる ✓
  ↓
v0 結果: publicFund は Constitution に書き込まれているが、TitheRouter はそれを読まず
        自身の immutable を使う → 二重管理
```

v0 の問題:

1. **二重管理** — Constitution mutable と TitheRouter immutable が同じ address を保持。乖離 risk
2. **governance 変更不可** — Constitution mutable は governance vote で変更可能だが、TitheRouter は immutable で変更不可。Public Fund Safe を将来 migration する場合に TitheRouter 再 deploy 必要
3. **元設計逸脱** — ADR-2605192130 §3 の Constitution-mediated lookup 原則から外れる

v1 で解決する。

# Decision

## CREATE2 deterministic deployment 経由の sequencing

```
Phase 1 deploy sequence (v0):
  1. Constitution(constants, mutables-with-publicFund-immediate)
  2. AdherentRegistry
  3. ChartersComplianceRegistry
  4. TitheRouter(usdc, constitution, charters, publicFund)  ← immutable
  5. LandRegistry
  6. PublicFundGovernance(adherent, charters, publicFundSafe)
  7. ForceAuthorization(adherent, charters)

Phase 1 deploy sequence (v1):
  0. Compute deterministic CREATE2 addresses for all 7 contracts via known salt
  1. Constitution(constants, mutables-with-predicted-references)
       ← reference mutables (public_fund.safe_address, tithe_router.address, etc.)
         set to PREDICTED v1 addresses at construction
  2. AdherentRegistry  (CREATE2 with salt 1)
  3. ChartersComplianceRegistry  (CREATE2 with salt 2)
  4. TitheRouterV1(usdc, constitution, charters)  ← NO publicFund arg
       (reads address(uint160(uint256(constitution.getMutable(PUBLIC_FUND_ADDRESS_KEY)))))
  5. LandRegistry
  6. PublicFundGovernance
  7. ForceAuthorization
```

Constitution.constructor() の `mutables` array に Phase 2 reference addresses を **事前 CREATE2 計算済の予測 address** で initialize。TitheRouter v1 deploy 時点で `getMutable("public_fund.safe_address")` は既に正しい値を返す。

## Deterministic CREATE2 salt 方式

```solidity
// CREATE2 address = address(keccak256(abi.encodePacked(
//   bytes1(0xff),
//   deployer,
//   salt,
//   keccak256(creationCode)
// )))

// salt schema for religious-corp wave:
salt = keccak256(abi.encode("etzhayyim.religious-corp-wave.v1", contractName, deployVersion));
```

例:
```solidity
salt_publicFundSafe        = keccak256(abi.encode("etzhayyim.religious-corp-wave.v1", "PublicFundSafe", 1));
salt_titheRouter           = keccak256(abi.encode("etzhayyim.religious-corp-wave.v1", "TitheRouterV1", 1));
salt_landRegistry          = keccak256(abi.encode("etzhayyim.religious-corp-wave.v1", "LandRegistry", 1));
// ...
```

これにより:

- Founder の deployer address + 同じ salt なら同じ CREATE2 address が得られる
- mainnet deploy 前にすべての address が予測可能
- Constitution.mutables に予測 address を埋め込める
- v1 redeploy も同じ salt で同じ address (但しコード変更があれば address 変わる — `keccak256(creationCode)` 依存)

## TitheRouter v1 contract changes

```solidity
contract TitheRouterV1 {
    IERC20 public immutable usdc;
    IConstitution public immutable constitution;
    IChartersComplianceRegistry public immutable charters;
    // publicFund immutable は削除

    bytes32 public constant PUBLIC_FUND_ADDRESS_KEY = keccak256("public_fund.safe_address");

    constructor(IERC20 _usdc, IConstitution _constitution, IChartersComplianceRegistry _charters) {
        usdc = _usdc;
        constitution = _constitution;
        charters = _charters;
    }

    function route(address recipient, uint256 grossAmount, bytes32 purpose) external {
        // ... gate checks ...
        address publicFund = address(uint160(uint256(constitution.getMutable(PUBLIC_FUND_ADDRESS_KEY))));
        require(publicFund != address(0), "TitheRouterV1: publicFund not wired");
        // ... transfer ...
    }
}
```

## v0 → v1 migration plan

```
Phase A (current):  TitheRouter v0 deployed, SDK calls it
Phase B (post-Council, post-mainnet ≥6 months):
  1. Deploy TitheRouter v1 via CREATE2
  2. Governance proposal: setMutable(tithe_router.address, V1_ADDRESS)
       (this updates Constitution's reference; was V0_ADDRESS)
  3. SDK upgrade: read constitution.getMutable("tithe_router.address") → use that
  4. Both v0 and v1 operate in parallel for 30 days
       (donations routed through v0 still atomic-split correctly)
  5. After 30 days: SDK only points at v1
  6. v0 contract is functionally orphaned (no SDK references it)
     v0 contract remains on-chain as immutable record (cannot be burned)
Phase C (post-migration ≥90 days):
  7. Council Lv6+ ≥3 attestation declaring v0 deprecated
  8. v0 receives no further donations (SDK + Pregel cell guard against)
```

ETzhayyim has no admin function to "disable" the v0 contract. Migration is achieved by stopping SDK references; the contract remains forever as historical record.

## Constitution.mutables initialization for v1

```solidity
// In Deploy.s.sol _mutables() for v1:
mK[9]  = K.PUBLIC_FUND_SAFE_ADDRESS;            mV[9]  = bytes32(uint256(uint160(SAFE_PREDICTED_ADDR)));
mK[10] = K.CHARTERS_COMPLIANCE_REGISTRY_ADDRESS; mV[10] = bytes32(uint256(uint160(CHARTERS_PREDICTED_ADDR)));
mK[11] = K.TITHE_ROUTER_ADDRESS;                 mV[11] = bytes32(uint256(uint160(TITHE_V1_PREDICTED_ADDR)));
mK[12] = K.LAND_REGISTRY_ADDRESS;                mV[12] = bytes32(uint256(uint160(LAND_PREDICTED_ADDR)));
mK[13] = K.FORCE_AUTHORIZATION_ADDRESS;          mV[13] = bytes32(uint256(uint160(FORCE_PREDICTED_ADDR)));
mK[14] = K.PUBLIC_FUND_GOVERNANCE_ADDRESS;       mV[14] = bytes32(uint256(uint160(PFG_PREDICTED_ADDR)));
```

PUBLIC_FUND_SAFE_ADDRESS は Safe を手動 deploy 後に手動指定 (v0 と同じ); 残り 5 reference は CREATE2 で予測。

# Consequences

## 正の効果

- 元 ADR-2605192130 §3 設計意図の完全実装
- Public Fund Safe migration が governance proposal で可能になる (Constitution.setMutable で変更すれば TitheRouter が自動的に新 Safe を使う)
- 二重管理排除 — Constitution が唯一の source of truth
- 他 reference contract (PublicFundGovernance / LandRegistry / etc.) の address も Constitution mutables から resolve できる pattern が固まる → 将来 contract migrations が容易

## 負の効果 / コスト

- CREATE2 salt + deployment script complexity 増加
- v1 redeploy は creationCode が変わると CREATE2 address も変わる → 真の immutability は salt + bytecode の固定が必要
- v0 → v1 migration 30+90 日 grace period の operational overhead
- v0 contract が永続的に on-chain に残る (religious-corp の immutability 原則と整合的だが、新参 dev には混乱)

## 中立 / トレードオフ

- v0/v1 並存中の SDK の dual-path code → 30日後に v1-only に simplify される
- v1 自体も将来 v2 にする migration を想定 → 都度 CREATE2 salt 更新 + Constitution.setMutable

# Alternatives Considered

## A. v0 を永続維持

Pro: 単純。Con: 元 ADR-2605192130 §3 設計から永続的に逸脱。Public Fund Safe migration 不可能。却下。

## B. Constitution.setMutable に bootstrap exception 追加

```solidity
function bootstrapSetMutable(bytes32 key, bytes32 value) external {
    require(msg.sender == bootstrapDeployer, "only bootstrap");
    require(bootstrapPhase, "bootstrap closed");
    _mutables[key] = value;
}
```

Pro: CREATE2 不要。Con: Constitution の "no admin" 原則違反。bootstrap deployer = 中央集権的 risk。却下。

## C. UUPS Proxy パターン

TitheRouter を upgradeable にする。Pro: future-proof。Con: ADR-2605172300 + 2605192200 の immutability 原則違反。Religious-corp の "no admin / no upgrade" doctrine に矛盾。却下。

## D. v0 の immutable をそのまま保持 + v1 を新 ADR で別 contract として並走

Pro: v0 SDK call は変更不要、v1 は新機能のみ。Con: SDK で両方 maintain 必要、二重管理問題が解決しない。却下: migrate-and-deprecate が cleaner。

# Open Questions

1. **CREATE2 salt schema の forward compatibility** — v2 / v3 で salt 計算 algorithm を変えるか?
2. **bytecode 変更時の address 変更** — TitheRouter v1.1 (microfix) が v1 と異なる address になる。Mitigation: Constitution.setMutable で v1.1 address に切り替え (v1 contract は永続放置)
3. **v0 deprecation Council attestation の specific Lexicon** — `com.etzhayyim.apps.etzhayyim.contract-deprecation` future Lexicon が必要
4. **mainnet timing** — v1 を mainnet 初回 deploy にするか、v0 mainnet → 6ヶ月後 v1 migration にするか。Decision (本 ADR): mainnet 初回は v0 (simpler operational), 6ヶ月後 v1 (mature)

# References

- ADR-2605192130 §3 (元 TitheRouter 設計, Constitution.getMutable() 原則)
- ADR-2605192200 v2.0 (immutability 原則)
- ADR-2605172300 §8 (no admin / no upgrade constitutional invariant)
- v0 TitheRouter source: `50-infra/etzhayyim-chain-contracts/src/TitheRouter.sol`
- v1 TitheRouter source: `50-infra/etzhayyim-chain-contracts/src/TitheRouterV1.sol` (本 ADR 承認後 scaffold)
- CREATE2 spec: EIP-1014
- v0 Anvil deploy: 2026-05-20 (TitheRouter @ 0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9)
